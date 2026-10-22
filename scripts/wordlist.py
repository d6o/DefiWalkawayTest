#!/usr/bin/env python3
"""
Build the fixed T0 signature list (SPEC §9): every verb × every argument list of 0–3 common types.
Writes data/methodology/signatures.json: { "0x12345678": ["verb(type,...)", ...], ... }

Pure Python (Keccak-256 implemented below), no external services or packages.
Usage: scripts/wordlist.py [outfile]
"""
import itertools, json, os, sys

# ---- Fixed inputs (SPEC §9). Do not change after matching has started. ----
VERBS = ["withdraw", "redeem", "unstake", "claim", "exit", "burn", "unwrap", "release", "collect", "harvest",
         "close", "repay", "remove", "cancel", "unlock", "leave", "deposit", "stake", "wrap", "mint"]
TYPES = ["uint256", "address", "uint256[]", "bool", "bytes"]
MAX_ARGS = 3

# ---- Keccak-256 (original Keccak padding, as used by Ethereum) ----
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B,
       0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088,
       0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
       0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
       0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M = (1 << 64) - 1


def _rol(x, n):
    return ((x << n) | (x >> (64 - n))) & _M if n else x


def _f(A):
    for rc in _RC:
        C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
        A = [[A[x][y] ^ D[x] for y in range(5)] for x in range(5)]
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2 * x + 3 * y) % 5] = _rol(A[x][y], _ROT[x][y])
        A = [[B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
        A[0][0] ^= rc
    return A


def keccak256(data: bytes) -> bytes:
    rate = 136
    p = bytearray(data) + b"\x01"
    p += b"\x00" * ((-len(p)) % rate)
    p[-1] |= 0x80
    A = [[0] * 5 for _ in range(5)]
    for off in range(0, len(p), rate):
        block = p[off:off + rate]
        for i in range(rate // 8):
            x, y = i % 5, i // 5
            A[x][y] ^= int.from_bytes(block[8 * i:8 * i + 8], "little")
        A = _f(A)
    out = b"".join(A[i % 5][i // 5].to_bytes(8, "little") for i in range(4))
    return out[:32]


def selector(sig: str) -> str:
    return "0x" + keccak256(sig.encode()).hex()[:8]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "data/methodology/signatures.json"
    arglists = [()]
    for n in range(1, MAX_ARGS + 1):
        arglists += list(itertools.product(TYPES, repeat=n))
    table = {}
    for v in VERBS:
        for args in arglists:
            sig = f"{v}({','.join(args)})"
            table.setdefault(selector(sig), []).append(sig)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"verbs": VERBS, "types": TYPES, "max_args": MAX_ARGS,
               "signatures": sum(len(s) for s in table.values()),
               "selectors": dict(sorted(table.items()))}, open(out, "w"), indent=1)
    collisions = {k: v for k, v in table.items() if len(v) > 1}
    print(f"{sum(len(s) for s in table.values())} signatures, {len(table)} unique selectors, "
          f"{len(collisions)} internal collisions -> {out}")


if __name__ == "__main__":
    main()
