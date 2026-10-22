#!/usr/bin/env python3
"""
T0 step 3b part 2, phase 1: what do users call when their tokens move into candidate contracts?

For every token Transfer (from raw_transfer_logs.json) whose recipient is a candidate:
  1. fetch the transaction (eth_getTransactionByHash, batched)
  2. record: from, to, selector, ETH value, calldata length (32-byte words)
  3. record whether the token sender == tx sender (user moved their own tokens directly)
Then group by (tx.to, selector) and pick 3 examples per group (first / middle / last by block).
Nothing is filtered out: all txs are written to txs.json.

Usage: scripts/txgroups.py <raw_transfer_logs.json> <outdir> <candidate> [<candidate> ...]
Env:   LOGS_RPC_URL (default $ETH_RPC_URL)
"""
import json, os, sys, time, urllib.request, urllib.error
from collections import defaultdict, Counter
from datetime import datetime, timezone

RPC = os.environ.get("LOGS_RPC_URL") or os.environ["ETH_RPC_URL"]


def post(payload, retries=8):
    body = json.dumps(payload).encode()
    for attempt in range(retries):
        req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("gave up")


def get_txs(hashes):
    out, hashes = {}, list(hashes)
    for i in range(0, len(hashes), 100):
        chunk = hashes[i:i + 100]
        for _ in range(5):
            resp = post([{"jsonrpc": "2.0", "id": j, "method": "eth_getTransactionByHash", "params": [h]}
                         for j, h in enumerate(chunk)])
            if isinstance(resp, list) and all(x.get("result") for x in resp):
                break
            time.sleep(3)
        else:
            raise RuntimeError(f"batch failed: {str(resp)[:300]}")
        for x in resp:
            out[chunk[x["id"]]] = x["result"]
    return out


def main():
    logs_path, outdir, cands = sys.argv[1], sys.argv[2], [c.lower() for c in sys.argv[3:]]
    os.makedirs(outdir, exist_ok=True)
    t0 = datetime.now(timezone.utc)

    moves = defaultdict(list)  # tx -> [(token_from, candidate, amount)]
    for lg in json.load(open(logs_path)):
        if len(lg["topics"]) != 3:
            continue
        to = "0x" + lg["topics"][2][-40:]
        if to in cands:
            moves[lg["transactionHash"]].append(("0x" + lg["topics"][1][-40:], to, int(lg["data"][:66], 16) / 1e18))

    txs = get_txs(moves)
    rows = []
    for h, tx in txs.items():
        inp = tx["input"]
        rows.append({
            "hash": h, "block": int(tx["blockNumber"], 16), "from": tx["from"].lower(),
            "to": (tx["to"] or "").lower(), "selector": inp[:10] if len(inp) >= 10 else inp,
            "value_eth": int(tx["value"], 16) / 1e18, "calldata_words": max(0, (len(inp) - 10) // 64),
            "calldata_bytes": max(0, (len(inp) - 2) // 2), "input": inp,
            "token_moves": [{"from": f, "candidate": c, "amount": a} for f, c, a in moves[h]],
            "sender_moved_own_tokens": any(f == tx["from"].lower() for f, _, _ in moves[h]),
        })
    rows.sort(key=lambda r: (r["block"], r["hash"]))
    json.dump(rows, open(os.path.join(outdir, "txs.json"), "w"), indent=1)

    groups = defaultdict(list)
    for r in rows:
        groups[(r["to"], r["selector"])].append(r)
    G = []
    for (to, sel), rs in groups.items():
        rs.sort(key=lambda r: (r["block"], r["hash"]))
        picks = [rs[0], rs[len(rs) // 2], rs[-1]]
        ex = list(dict.fromkeys(r["hash"] for r in picks))
        G.append({
            "to": to, "selector": sel, "txs": len(rs), "distinct_senders": len({r["from"] for r in rs}),
            "candidates": dict(Counter(m["candidate"] for r in rs for m in r["token_moves"])),
            "token_amount": round(sum(m["amount"] for r in rs for m in r["token_moves"]), 4),
            "sender_moved_own_tokens": sum(r["sender_moved_own_tokens"] for r in rs),
            "txs_with_eth_value": sum(r["value_eth"] > 0 for r in rs),
            "calldata_words": dict(sorted(Counter(r["calldata_words"] for r in rs).items())),
            "to_is_candidate": to in cands,
            "examples": ex,
        })
    G.sort(key=lambda g: (-g["distinct_senders"], -g["txs"]))
    t1 = datetime.now(timezone.utc)
    summary = {"candidates": cands, "txs": len(rows), "groups": len(G),
               "started": t0.isoformat(timespec="seconds"), "ended": t1.isoformat(timespec="seconds"),
               "seconds": round((t1 - t0).total_seconds(), 1),
               "examples_to_trace": sum(len(g["examples"]) for g in G)}
    json.dump({"summary": summary, "groups": G}, open(os.path.join(outdir, "groups.json"), "w"), indent=1)

    short = lambda a: a[:6] + "…" + a[-4:]
    L = ["| # | tx.to | Selector | Txs | Senders | Own tokens | ETH sent | Candidates (tokens went to) | stETH | Calldata words | Examples |",
         "|---|-------|----------|-----|---------|------------|----------|-----------------------------|-------|----------------|----------|"]
    for i, g in enumerate(G, 1):
        cs = ", ".join(f"{short(c)}×{n}" for c, n in g["candidates"].items())
        cw = ", ".join(f"{k}:{v}" for k, v in g["calldata_words"].items())
        to = f"**`{short(g['to'])}`**" if g["to_is_candidate"] else f"`{short(g['to'])}`"
        L.append(f"| {i} | {to} | `{g['selector']}` | {g['txs']} | {g['distinct_senders']} | {g['sender_moved_own_tokens']} | "
                 f"{g['txs_with_eth_value']} | {cs} | {g['token_amount']:,.2f} | {cw} | {len(g['examples'])} |")
    open(os.path.join(outdir, "groups.md"), "w").write("\n".join(L) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
