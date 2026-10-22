#!/usr/bin/env python3
"""
T0 function discovery from bytecode (SPEC §9).

1. Parse the bytecode and record EVERY PUSH4 constant (nothing filtered out).
2. Flag PUSH4s used as dispatcher comparisons (followed within 3 instructions by EQ/GT/LT),
   which is how Solidity routes a call to a function.
3. Name selectors using only:
   - "basic": ERC-20/721/1155 core functions (allowed without lookup, SPEC §9)
   - "wordlist": data/methodology/signatures.json (the fixed 3,120-signature list)

Usage: scripts/selectors.py <code.hex> <out.json> [--label NAME]
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from wordlist import selector

BASIC = [
    # ERC-20
    "name()", "symbol()", "decimals()", "totalSupply()", "balanceOf(address)", "transfer(address,uint256)",
    "transferFrom(address,address,uint256)", "approve(address,uint256)", "allowance(address,address)",
    # ERC-721
    "ownerOf(uint256)", "safeTransferFrom(address,address,uint256)", "safeTransferFrom(address,address,uint256,bytes)",
    "setApprovalForAll(address,bool)", "getApproved(uint256)", "isApprovedForAll(address,address)", "tokenURI(uint256)",
    # ERC-1155
    "balanceOfBatch(address[],uint256[])", "safeTransferFrom(address,address,uint256,uint256,bytes)",
    "safeBatchTransferFrom(address,address,uint256[],uint256[],bytes)", "uri(uint256)",
    # ERC-165
    "supportsInterface(bytes4)",
]
OP_EQ, OP_GT, OP_LT = 0x14, 0x11, 0x10


def parse(code: bytes):
    """Yield (pc, opcode, immediate_bytes)."""
    pc = 0
    while pc < len(code):
        op = code[pc]
        n = op - 0x5f if 0x60 <= op <= 0x7f else 0
        yield pc, op, code[pc + 1:pc + 1 + n]
        pc += 1 + n


def main():
    args = sys.argv[1:]
    label = None
    if "--label" in args:
        i = args.index("--label"); label = args[i + 1]; del args[i:i + 2]
    code_hex, out = args[0], args[1]
    code = bytes.fromhex(open(code_hex).read().strip().removeprefix("0x"))
    ins = list(parse(code))

    wl = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "methodology", "signatures.json")))["selectors"]
    basic = {}
    for s in BASIC:
        basic.setdefault(selector(s), []).append(s)

    found = {}
    for i, (pc, op, imm) in enumerate(ins):
        if op != 0x63 or len(imm) != 4:  # PUSH4
            continue
        sel = "0x" + imm.hex()
        nxt = [o for _, o, _ in ins[i + 1:i + 4]]
        cmp = "EQ" if OP_EQ in nxt else "GT" if OP_GT in nxt else "LT" if OP_LT in nxt else None
        r = found.setdefault(sel, {"selector": sel, "pcs": [], "dispatcher": False, "compare_ops": set()})
        r["pcs"].append(pc)
        if cmp:
            r["dispatcher"] = r["dispatcher"] or cmp == "EQ"
            r["compare_ops"].add(cmp)

    rows = []
    for sel, r in found.items():
        names, source = [], None
        if sel in basic:
            names, source = basic[sel], "basic"
        elif sel in wl:
            names, source = wl[sel], "wordlist"
        rows.append({**r, "compare_ops": sorted(r["compare_ops"]), "names": names, "name_source": source})
    rows.sort(key=lambda r: (not r["dispatcher"], r["name_source"] is None, r["selector"]))

    disp = [r for r in rows if r["dispatcher"]]
    summary = {
        "label": label, "code_bytes": len(code), "push4_total": len(rows),
        "dispatcher_selectors": len(disp),
        "named_basic": sum(1 for r in disp if r["name_source"] == "basic"),
        "named_wordlist": sum(1 for r in disp if r["name_source"] == "wordlist"),
        "unnamed": sum(1 for r in disp if r["name_source"] is None),
        "non_dispatcher_push4": len(rows) - len(disp),
    }
    json.dump({"summary": summary, "selectors": rows}, open(out, "w"), indent=1)
    print(json.dumps(summary, indent=1))
    for r in rows:
        tag = "dispatch" if r["dispatcher"] else "other   "
        print(f"  {tag} {r['selector']}  {r['name_source'] or '-':8}  {', '.join(r['names']) or ''}")


if __name__ == "__main__":
    main()
