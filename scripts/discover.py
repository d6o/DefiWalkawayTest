#!/usr/bin/env python3
"""
T0 discovery: find every token contract an address sent or received, using standard JSON-RPC only.

Steps:
  2a. eth_getLogs over [0, to_block] for token transfer events where the address is sender or recipient:
        - Transfer(address,address,uint256)           ERC-20 (3 topics) and ERC-721 (4 topics)
        - TransferSingle(address,address,address,uint256,uint256)   ERC-1155
        - TransferBatch(address,address,address,uint256[],uint256[]) ERC-1155
  2b. For every contract seen, read name() / symbol() / decimals() via eth_call at to_block.
  2c. Write raw logs + a table of ALL contracts (matches are flagged, nothing is filtered out).

Usage:
  scripts/discover.py <address> <to_block> <outdir> [--match SYMBOL]

Env:
  LOGS_RPC_URL  RPC used for eth_getLogs (default: $ETH_RPC_URL)
  CALL_RPC_URL  RPC used for eth_call (default: http://127.0.0.1:8545, the fork)
"""
import json, os, sys, time, urllib.request, urllib.error
from collections import defaultdict
from datetime import datetime, timezone

LOGS_RPC = os.environ.get("LOGS_RPC_URL") or os.environ["ETH_RPC_URL"]
CALL_RPC = os.environ.get("CALL_RPC_URL", "http://127.0.0.1:8545")

TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOPIC_1155_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
TOPIC_1155_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"

_id = 0


def rpc(url, method, params, retries=8):
    global _id
    for attempt in range(retries):
        _id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": _id, "method": method, "params": params}).encode()
        req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
        except urllib.error.HTTPError as e:
            resp = {"error": {"message": e.read().decode()[:300]}}
        except Exception as e:  # network hiccup
            resp = {"error": {"message": str(e)}}
        if "error" not in resp:
            return resp["result"]
        msg = json.dumps(resp["error"])
        # transient: plan rollout / rate limits
        if any(s in msg for s in ("Free tier", "429", "rate", "timeout", "Timed out")):
            time.sleep(2 * (attempt + 1))
            continue
        raise RuntimeError(f"{method}: {msg}")
    raise RuntimeError(f"{method}: gave up after {retries} retries")


def get_logs_split(topics, frm, to):
    """eth_getLogs over [frm, to]; split the range in half if the provider refuses (too many results)."""
    try:
        return rpc(LOGS_RPC, "eth_getLogs", [{"fromBlock": hex(frm), "toBlock": hex(to), "topics": topics}])
    except RuntimeError as e:
        if "exceeded" in str(e) or "10K" in str(e) or "too many" in str(e).lower():
            mid = (frm + to) // 2
            return get_logs_split(topics, frm, mid) + get_logs_split(topics, mid + 1, to)
        raise


def pad(addr):
    return "0x" + "0" * 24 + addr.lower()[2:]


def decode_string(data):
    """ABI string, or bytes32 (old tokens). Returns None if undecodable."""
    if not data or data == "0x":
        return None
    b = bytes.fromhex(data[2:])
    try:
        if len(b) >= 64:
            off = int.from_bytes(b[0:32], "big")
            ln = int.from_bytes(b[off:off + 32], "big")
            return b[off + 32:off + 32 + ln].decode("utf-8", "replace")
        if len(b) == 32:
            return b.rstrip(b"\x00").decode("utf-8", "replace")
    except Exception:
        pass
    return None


def call(to, selector, block):
    try:
        return rpc(CALL_RPC, "eth_call", [{"to": to, "data": selector}, hex(block)], retries=3)
    except RuntimeError:
        return None


def main():
    args = sys.argv[1:]
    match = None
    if "--match" in args:
        i = args.index("--match"); match = args[i + 1]; del args[i:i + 2]
    addr, to_block, outdir = args[0].lower(), int(args[1]), args[2]
    os.makedirs(outdir, exist_ok=True)
    t0 = datetime.now(timezone.utc)

    queries = {
        "transfer_in": [TOPIC_TRANSFER, None, pad(addr)],
        "transfer_out": [TOPIC_TRANSFER, pad(addr)],
        "1155_single_in": [TOPIC_1155_SINGLE, None, None, pad(addr)],
        "1155_single_out": [TOPIC_1155_SINGLE, None, pad(addr)],
        "1155_batch_in": [TOPIC_1155_BATCH, None, None, pad(addr)],
        "1155_batch_out": [TOPIC_1155_BATCH, None, pad(addr)],
    }
    raw, counts = {}, {}
    for name, topics in queries.items():
        logs = get_logs_split(topics, 0, to_block)
        raw[name] = logs
        counts[name] = len(logs)
        print(f"  {name:16} {len(logs):6} logs", flush=True)
    json.dump(raw, open(os.path.join(outdir, "raw_logs.json"), "w"), indent=1)

    # aggregate per contract
    c = defaultdict(lambda: {"in": 0, "out": 0, "standard": set(), "first_block": None, "last_block": None})
    for name, logs in raw.items():
        for lg in logs:
            a = lg["address"].lower()
            d = c[a]
            d["in" if name.endswith("_in") else "out"] += 1
            if name.startswith("transfer"):
                d["standard"].add("ERC-20" if len(lg["topics"]) == 3 else "ERC-721" if len(lg["topics"]) == 4 else f"Transfer/{len(lg['topics'])}t")
            else:
                d["standard"].add("ERC-1155")
            b = int(lg["blockNumber"], 16)
            d["first_block"] = b if d["first_block"] is None else min(d["first_block"], b)
            d["last_block"] = b if d["last_block"] is None else max(d["last_block"], b)

    rows = []
    for a, d in c.items():
        name = decode_string(call(a, "0x06fdde03", to_block))
        symbol = decode_string(call(a, "0x95d89b41", to_block))
        dec = call(a, "0x313ce567", to_block)
        bal = call(a, "0x70a08231" + pad(addr)[2:], to_block)
        rows.append({
            "contract": a,
            "name": name, "symbol": symbol,
            "decimals": int(dec, 16) if dec and dec != "0x" and len(dec) <= 66 else None,
            "balanceOf_raw": int(bal, 16) if bal and bal != "0x" and len(bal) <= 66 else None,
            "standard": ",".join(sorted(d["standard"])),
            "transfers_in": d["in"], "transfers_out": d["out"],
            "first_block": d["first_block"], "last_block": d["last_block"],
            "symbol_matches": bool(match and symbol and symbol.strip().lower() == match.lower()),
            "symbol_contains": bool(match and symbol and match.lower() in symbol.lower()),
        })
    rows.sort(key=lambda r: (-r["symbol_matches"], -r["symbol_contains"], r["first_block"]))
    t1 = datetime.now(timezone.utc)

    summary = {
        "address": addr, "to_block": to_block, "match": match,
        "started": t0.isoformat(timespec="seconds"), "ended": t1.isoformat(timespec="seconds"),
        "seconds": round((t1 - t0).total_seconds(), 1),
        "log_counts": counts, "contracts": len(rows),
        "rpc_calls_note": "eth_getLogs via LOGS_RPC_URL; eth_call via CALL_RPC_URL (fork)",
    }
    json.dump({"summary": summary, "contracts": rows}, open(os.path.join(outdir, "contracts.json"), "w"), indent=1)

    # human-readable table of ALL contracts
    def fmt_bal(r):
        if r["balanceOf_raw"] is None:
            return "—"
        if r["decimals"] is not None and r["decimals"] <= 36:
            return f"{r['balanceOf_raw'] / 10 ** r['decimals']:,.4f}"
        return str(r["balanceOf_raw"])
    lines = ["| # | Match | Contract | name() | symbol() | Std | In | Out | First block | Last block | balanceOf @ fork |",
             "|---|-------|----------|--------|----------|-----|----|-----|-------------|------------|------------------|"]
    for i, r in enumerate(rows, 1):
        m = "**exact**" if r["symbol_matches"] else ("partial" if r["symbol_contains"] else "")
        clean = lambda s: (s or "—").replace("|", "\\|").replace("\n", " ")[:40]
        lines.append(f"| {i} | {m} | `{r['contract']}` | {clean(r['name'])} | {clean(r['symbol'])} | {r['standard']} | "
                     f"{r['transfers_in']} | {r['transfers_out']} | {r['first_block']} | {r['last_block']} | {fmt_bal(r)} |")
    open(os.path.join(outdir, "contracts.md"), "w").write("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
