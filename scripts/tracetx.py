#!/usr/bin/env python3
"""
T0 step 3b part 2, phase 2: trace example transactions and summarize what the sender got back.

For each example tx (debug_traceTransaction, callTracer, withLog=true):
  - ETH: every call frame with value > 0, and the total ETH sent TO the tx sender
  - Tokens: every Transfer / TransferSingle / TransferBatch log in the trace, flagged when the sender is involved
    (ERC-20 = 3 topics, ERC-721 = 4 topics: a token id, e.g. a receipt NFT)
  - Calls: flat list of call frames (type, from, to, selector, value)
Writes the full trace + a per-tx summary. Nothing is filtered out.

Usage: scripts/tracetx.py <groups.json> <outdir> [--direct-only]
Env:   LOGS_RPC_URL (default $ETH_RPC_URL)
"""
import json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

RPC = os.environ.get("LOGS_RPC_URL") or os.environ["ETH_RPC_URL"]
T_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
T_1155_S = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
T_1155_B = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"


def rpc(method, params, retries=6):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.load(r)
            if "result" in resp:
                return resp["result"]
        except Exception:
            pass
        time.sleep(2 * (a + 1))
    raise RuntimeError(f"{method} failed")


def flatten(frame, depth=0, out=None):
    out = [] if out is None else out
    out.append({"depth": depth, "type": frame["type"], "from": frame["from"].lower(), "to": (frame.get("to") or "").lower(),
                "selector": (frame.get("input") or "0x")[:10], "value_eth": int(frame.get("value") or "0x0", 16) / 1e18,
                "error": frame.get("error"), "logs": frame.get("logs", [])})
    for c in frame.get("calls", []):
        flatten(c, depth + 1, out)
    return out


def addr(topic):
    return "0x" + topic[-40:]


def summarize(h, trace, sender):
    frames = flatten(trace)
    eth_to_sender = sum(f["value_eth"] for f in frames if f["to"] == sender and f["type"] in ("CALL", "CALLCODE") and f["depth"] > 0)
    eth_from_sender = int(trace.get("value") or "0x0", 16) / 1e18
    transfers = []
    for f in frames:
        for lg in f["logs"]:
            t = lg.get("topics", [])
            if not t:
                continue
            if t[0] == T_TRANSFER and len(t) in (3, 4):
                std = "ERC-20" if len(t) == 3 else "ERC-721"
                amt = int(lg["data"], 16) if (std == "ERC-20" and lg["data"] not in ("0x", "")) else None
                tid = int(t[3], 16) if std == "ERC-721" else None
                transfers.append({"token": lg["address"].lower(), "std": std, "from": addr(t[1]), "to": addr(t[2]),
                                  "amount_raw": amt, "token_id": tid})
            elif t[0] in (T_1155_S, T_1155_B) and len(t) == 4:
                transfers.append({"token": lg["address"].lower(), "std": "ERC-1155", "from": addr(t[2]), "to": addr(t[3]),
                                  "amount_raw": None, "token_id": None})
    other_events = sorted({(lg["address"].lower(), lg["topics"][0]) for f in frames for lg in f["logs"]
                           if lg.get("topics") and lg["topics"][0] not in (T_TRANSFER, T_1155_S, T_1155_B)})
    return {
        "hash": h, "sender": sender, "to": trace["to"].lower(), "selector": trace["input"][:10],
        "status": "reverted" if trace.get("error") else "ok",
        "eth_from_sender": eth_from_sender, "eth_to_sender": eth_to_sender,
        "tokens_received_by_sender": [x for x in transfers if x["to"] == sender],
        "tokens_sent_by_sender": [x for x in transfers if x["from"] == sender],
        "all_token_transfers": transfers,
        "other_events": [{"emitter": a, "topic0": t} for a, t in other_events],
        "calls": [{k: v for k, v in f.items() if k != "logs"} for f in frames],
    }


def main():
    gpath, outdir = sys.argv[1], sys.argv[2]
    direct_only = "--direct-only" in sys.argv
    os.makedirs(os.path.join(outdir, "traces"), exist_ok=True)
    G = json.load(open(gpath))["groups"]
    if direct_only:
        G = [g for g in G if g["to_is_candidate"]]
    txs = json.load(open(os.path.join(os.path.dirname(gpath), "txs.json")))
    sender_of = {t["hash"]: t["from"] for t in txs}
    jobs = [(g, h) for g in G for h in g["examples"]]

    def work(job):
        g, h = job
        tr = rpc("debug_traceTransaction", [h, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        json.dump(tr, open(os.path.join(outdir, "traces", f"{h}.json"), "w"))
        s = summarize(h, tr, sender_of[h])
        s["group"] = {"to": g["to"], "selector": g["selector"]}
        return s

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(work, jobs))
    json.dump(res, open(os.path.join(outdir, "summaries.json"), "w"), indent=1)
    print(f"traced {len(res)} txs in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
