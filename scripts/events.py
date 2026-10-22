#!/usr/bin/env python3
"""
T0: every event a contract emitted in a block window, grouped by event type (topic0).

1. eth_getLogs(address=<contract>, [from, to]), any topics (split on provider limits)
2. fetch every tx (batched) to get tx.from / tx.to / selector
3. per topic0: logs, distinct txs, distinct tx senders, top senders, (tx.to, selector) combos, first/last block
4. ERC-721 Transfer (4 topics) emitted by the contract: split into mints / burns / transfers between addresses
Writes raw logs, txs, and summaries. Nothing is filtered out.

Usage: scripts/events.py <contract> <from_block> <to_block> <outdir>
Env:   LOGS_RPC_URL (default $ETH_RPC_URL)
"""
import json, os, sys
from collections import defaultdict, Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
from flows import post
from txgroups import get_txs

T_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40


def get_logs(addr, frm, to):
    r = post({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
              "params": [{"address": addr, "fromBlock": hex(frm), "toBlock": hex(to)}]})
    if "error" in r:
        msg = json.dumps(r["error"])
        if frm < to and any(s in msg for s in ("exceeded", "10K", "10,000", "too many", "Log response size")):
            mid = (frm + to) // 2
            return get_logs(addr, frm, mid) + get_logs(addr, mid + 1, to)
        raise RuntimeError(msg)
    return r["result"]


def main():
    addr, frm, to, outdir = sys.argv[1].lower(), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    os.makedirs(outdir, exist_ok=True)
    t0 = datetime.now(timezone.utc)
    logs = get_logs(addr, frm, to)
    json.dump(logs, open(os.path.join(outdir, "raw_logs.json"), "w"))
    hashes = sorted({l["transactionHash"] for l in logs})
    txs = get_txs(hashes)
    txinfo = {h: {"from": t["from"].lower(), "to": (t["to"] or "").lower(), "selector": t["input"][:10],
                  "block": int(t["blockNumber"], 16)} for h, t in txs.items()}
    json.dump(txinfo, open(os.path.join(outdir, "txs.json"), "w"), indent=1)

    by = defaultdict(list)
    for l in logs:
        by[(l["topics"][0] if l["topics"] else "(anonymous)", len(l["topics"]))].append(l)
    types = []
    for (t0_, nt), ls in by.items():
        hs = {l["transactionHash"] for l in ls}
        senders = Counter(txinfo[h]["from"] for h in hs)
        combos = Counter((txinfo[h]["to"], txinfo[h]["selector"]) for h in hs)
        blocks = [int(l["blockNumber"], 16) for l in ls]
        types.append({
            "topic0": t0_, "topics": nt, "data_words": (len(ls[0]["data"]) - 2) // 64,
            "logs": len(ls), "txs": len(hs), "distinct_senders": len(senders),
            "top_senders": senders.most_common(5),
            "tx_to_selector": [{"to": k[0], "selector": k[1], "txs": v} for k, v in combos.most_common(10)],
            "first_block": min(blocks), "last_block": max(blocks),
            "example_txs": [sorted(hs, key=lambda h: txinfo[h]["block"])[i] for i in sorted({0, len(hs) // 2, len(hs) - 1})],
        })
    types.sort(key=lambda x: -x["logs"])

    nft = {"mints": 0, "burns": 0, "transfers": 0, "mint_ids": [], "burn_ids": [], "transfer_examples": []}
    for l in logs:
        if l["topics"] and l["topics"][0] == T_TRANSFER and len(l["topics"]) == 4:
            f, t, i = "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], int(l["topics"][3], 16)
            if f == ZERO:
                nft["mints"] += 1; nft["mint_ids"].append(i)
            elif t == ZERO:
                nft["burns"] += 1; nft["burn_ids"].append(i)
            else:
                nft["transfers"] += 1
                if len(nft["transfer_examples"]) < 20:
                    nft["transfer_examples"].append({"id": i, "from": f, "to": t, "tx": l["transactionHash"]})
    for k in ("mint_ids", "burn_ids"):
        ids = nft[k]
        nft[k] = {"count": len(ids), "min": min(ids) if ids else None, "max": max(ids) if ids else None}

    t1 = datetime.now(timezone.utc)
    summary = {"contract": addr, "from_block": frm, "to_block": to, "logs": len(logs), "txs": len(hashes),
               "event_types": len(types), "nft_721": nft,
               "started": t0.isoformat(timespec="seconds"), "ended": t1.isoformat(timespec="seconds"),
               "seconds": round((t1 - t0).total_seconds(), 1)}
    json.dump({"summary": summary, "event_types": types}, open(os.path.join(outdir, "events.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    for x in types:
        print(f"\n{x['topic0']}  topics={x['topics']} data_words={x['data_words']}  logs={x['logs']} txs={x['txs']} "
              f"senders={x['distinct_senders']}  blocks {x['first_block']}..{x['last_block']}")
        print(f"   top senders: {[(a[:10], n) for a, n in x['top_senders']]}")
        print(f"   tx.to/selector: {[(c['to'][:10], c['selector'], c['txs']) for c in x['tx_to_selector'][:6]]}")


if __name__ == "__main__":
    main()
