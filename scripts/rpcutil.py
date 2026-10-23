#!/usr/bin/env python3
"""
Plain JSON-RPC helpers for fork experiments (SPEC §6: no tool that auto-decodes errors via hosted databases).

    from rpcutil import Fork
    f = Fork("http://127.0.0.1:8545")
    f.call(frm, to, data)            -> (ok, result_or_revert_data)
    f.send(frm, to, data, value=0)   -> (tx_hash, receipt)   # next block = latest timestamp + 1s
    f.bal(token, who), f.eth(who), f.max_ok(fn, hi)  (binary search for the largest amount where fn(amount) succeeds)
"""
import json, time, urllib.request


class Fork:
    def __init__(self, url="http://127.0.0.1:8545"):
        self.url = url

    def rpc(self, method, params):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.url, body, {"Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=300))

    def result(self, method, params):
        r = self.rpc(method, params)
        if "error" in r:
            raise RuntimeError(f"{method}: {r['error']}")
        return r["result"]

    # reads
    def call(self, frm, to, data, block="latest", value=0):
        tx = {"from": frm, "to": to, "data": data}
        if value:
            tx["value"] = hex(value)
        r = self.rpc("eth_call", [tx, block])
        if "error" in r:
            d = r["error"].get("data")
            return False, d if isinstance(d, str) else r["error"].get("message")
        return True, r["result"]

    def bal(self, token, who, block="latest"):
        ok, r = self.call(who, token, "0x70a08231" + who[2:].lower().rjust(64, "0"), block)
        return int(r, 16) if ok and r not in ("0x", "") else None

    def eth(self, who, block="latest"):
        return int(self.result("eth_getBalance", [who, block]), 16)

    def block(self, tag="latest"):
        return self.result("eth_getBlockByNumber", [tag, False])

    def ts(self):
        return int(self.block()["timestamp"], 16)

    # writes (fork only)
    def impersonate(self, who):
        self.result("anvil_impersonateAccount", [who])

    def snapshot(self):
        return self.result("evm_snapshot", [])

    def send(self, frm, to, data="0x", value=0, gas=3_000_000, ts_step=1):
        self.result("evm_setNextBlockTimestamp", [self.ts() + ts_step])
        tx = {"from": frm, "to": to, "data": data, "gas": hex(gas)}
        if value:
            tx["value"] = hex(value)
        r = self.rpc("eth_sendTransaction", [tx])
        if "error" in r:
            return None, {"status": "send-error", "error": r["error"]}
        h = r["result"]
        for _ in range(60):
            rc = self.result("eth_getTransactionReceipt", [h])
            if rc:
                return h, rc
            time.sleep(0.5)
        return h, None

    # search
    @staticmethod
    def max_ok(fn, hi, lo=0):
        """Largest amount in [lo, hi] for which fn(amount) is True (assumes monotonic)."""
        while lo < hi:
            m = (lo + hi + 1) // 2
            if fn(m):
                lo = m
            else:
                hi = m - 1
        return lo


def word(x):
    if isinstance(x, str):
        return x[2:].lower().rjust(64, "0")
    return format(x, "064x")


def calldata(selector, *args):
    return selector + "".join(word(a) for a in args)


def transfers(receipt_or_logs, who=None):
    """ERC-20 Transfer logs (3 topics) from a receipt; optionally only those involving `who`."""
    logs = receipt_or_logs["logs"] if isinstance(receipt_or_logs, dict) else receipt_or_logs
    out = []
    for l in logs:
        t = l["topics"]
        if t and t[0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef" and len(t) == 3:
            f, to = "0x" + t[1][-40:], "0x" + t[2][-40:]
            if who is None or who.lower() in (f, to):
                out.append({"token": l["address"].lower(), "from": f, "to": to, "amount": int(l["data"], 16)})
    return out
