#!/usr/bin/env python3
"""
T0 step 3b part 1: where does a token go?

1. eth_getLogs for Transfer events EMITTED BY the token contract over [from_block, to_block]
   (only the contract itself can emit these, so they can't be spoofed by look-alikes).
2. Aggregate per recipient and per sender: count, amount, distinct counterparties.
3. eth_getCode for EVERY address seen (at to_block) to tell contracts from wallets.
4. Mints (from 0x0) and burns (to 0x0) are tracked separately.
Writes raw logs + full tables; nothing is filtered out.

Usage: scripts/flows.py <token> <from_block> <to_block> <outdir> [--decimals 18]
Env:   LOGS_RPC_URL (default $ETH_RPC_URL)
"""
import json, os, sys, time, urllib.request, urllib.error
from collections import defaultdict
from datetime import datetime, timezone

RPC = os.environ.get("LOGS_RPC_URL") or os.environ["ETH_RPC_URL"]
TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40


def post(payload, retries=8):
    body = json.dumps(payload).encode()
    for attempt in range(retries):
        req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code == 429 or "Free tier" in msg:
                time.sleep(2 * (attempt + 1)); continue
            return {"error": {"message": msg}}
        except Exception as e:
            time.sleep(2 * (attempt + 1)); last = str(e)
    raise RuntimeError(f"gave up after {retries} retries")


def get_logs(token, frm, to, stats):
    r = post({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
              "params": [{"address": token, "fromBlock": hex(frm), "toBlock": hex(to), "topics": [TOPIC_TRANSFER]}]})
    if "error" in r:
        msg = json.dumps(r["error"])
        if frm < to and any(s in msg for s in ("exceeded", "10K", "10,000", "too many", "Log response size")):
            mid = (frm + to) // 2
            stats["splits"] += 1
            return get_logs(token, frm, mid, stats) + get_logs(token, mid + 1, to, stats)
        raise RuntimeError(msg)
    stats["queries"] += 1
    return r["result"]


def get_codes(addrs, block):
    """Batch eth_getCode; returns {addr: code_size_bytes}."""
    out, addrs = {}, list(addrs)
    for i in range(0, len(addrs), 100):
        chunk = addrs[i:i + 100]
        batch = [{"jsonrpc": "2.0", "id": j, "method": "eth_getCode", "params": [a, hex(block)]} for j, a in enumerate(chunk)]
        for _ in range(5):
            resp = post(batch)
            if isinstance(resp, list) and all("result" in x for x in resp):
                break
            time.sleep(3)
        else:
            raise RuntimeError(f"getCode batch failed: {str(resp)[:300]}")
        for x in resp:
            out[chunk[x["id"]]] = (len(x["result"]) - 2) // 2
    return out


def kind(size):
    return "EOA" if size == 0 else "EOA+7702" if size == 23 else "contract"


def main():
    args = sys.argv[1:]
    dec = 18
    if "--decimals" in args:
        i = args.index("--decimals"); dec = int(args[i + 1]); del args[i:i + 2]
    token, frm, to, outdir = args[0].lower(), int(args[1]), int(args[2]), args[3]
    os.makedirs(outdir, exist_ok=True)
    t0 = datetime.now(timezone.utc)

    stats = {"queries": 0, "splits": 0}
    logs = get_logs(token, frm, to, stats)
    json.dump(logs, open(os.path.join(outdir, "raw_transfer_logs.json"), "w"))
    print(f"logs: {len(logs)}  (queries {stats['queries']}, splits {stats['splits']})", flush=True)

    rec = defaultdict(lambda: {"count": 0, "amount": 0, "senders": set(), "txs": set()})
    snd = defaultdict(lambda: {"count": 0, "amount": 0, "recipients": set(), "txs": set()})
    txs = set()
    for lg in logs:
        if len(lg["topics"]) != 3:
            continue
        f, t = "0x" + lg["topics"][1][-40:], "0x" + lg["topics"][2][-40:]
        amt = int(lg["data"][:66], 16) if lg["data"] != "0x" else 0
        h = lg["transactionHash"]; txs.add(h)
        rec[t]["count"] += 1; rec[t]["amount"] += amt; rec[t]["senders"].add(f); rec[t]["txs"].add(h)
        snd[f]["count"] += 1; snd[f]["amount"] += amt; snd[f]["recipients"].add(t); snd[f]["txs"].add(h)

    addrs = (set(rec) | set(snd)) - {ZERO}
    print(f"unique addresses: {len(addrs)}  -> eth_getCode ...", flush=True)
    codes = get_codes(addrs, to)
    codes[ZERO] = 0

    def rows(d, other):
        out = []
        for a, v in d.items():
            out.append({"address": a, "kind": "zero" if a == ZERO else kind(codes[a]), "code_bytes": codes[a],
                        "count": v["count"], "amount": v["amount"] / 10 ** dec,
                        f"distinct_{other}": len(v[other]), "distinct_txs": len(v["txs"])})
        return sorted(out, key=lambda r: -r["count"])

    R, S = rows(rec, "senders"), rows(snd, "recipients")
    t1 = datetime.now(timezone.utc)
    total_amt = sum(r["amount"] for r in R)
    summary = {
        "token": token, "from_block": frm, "to_block": to, "blocks": to - frm + 1,
        "started": t0.isoformat(timespec="seconds"), "ended": t1.isoformat(timespec="seconds"),
        "seconds": round((t1 - t0).total_seconds(), 1), "rpc": stats,
        "transfer_logs": len(logs), "distinct_txs": len(txs), "total_amount": total_amt,
        "recipients": len(R), "recipient_contracts": sum(r["kind"] == "contract" for r in R),
        "senders": len(S), "sender_contracts": sum(r["kind"] == "contract" for r in S),
        "mints_to_users": next((r for r in S if r["address"] == ZERO), None),
        "burns": next((r for r in R if r["address"] == ZERO), None),
    }
    json.dump({"summary": summary, "recipients": R, "senders": S},
              open(os.path.join(outdir, "flows.json"), "w"), indent=1)

    def table(rs, other, title):
        L = [f"## {title}", "", f"| # | Address | Kind | Code (B) | Transfers | Amount | % of amount | Distinct {other} | Txs |",
             "|---|---------|------|----------|-----------|--------|-------------|------------------|-----|"]
        for i, r in enumerate(rs, 1):
            pct = 100 * r["amount"] / total_amt if total_amt else 0
            L.append(f"| {i} | `{r['address']}` | {r['kind']} | {r['code_bytes']} | {r['count']} | {r['amount']:,.4f} | "
                     f"{pct:.2f}% | {r[f'distinct_{other}']} | {r['distinct_txs']} |")
        return "\n".join(L)
    open(os.path.join(outdir, "recipients.md"), "w").write(table(R, "senders", "All recipients (sorted by transfer count)") + "\n")
    open(os.path.join(outdir, "senders.md"), "w").write(table(S, "recipients", "All senders (sorted by transfer count)") + "\n")
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
