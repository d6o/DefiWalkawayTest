# Run: Uniswap (V3 positions) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Uniswap V3, Ethereum; position NFTs |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xda9488177dee53e051b29648853ad1a3d7238514` (100th holder **by NFT count**; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-24T02:36:14Z |

## Ground rules

- We play a user who has their **address** and knows they provided liquidity on **Uniswap** and hold **position NFTs**
  (SPEC §1). They don't know any contract addresses, what's in their positions, or how to exit.
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators know Uniswap well, including the names of the functions used below. None of
those names is used: the two exit functions stay **unnamed** (`0x0c49ccbe`, `0xfc6f7865`); their role and arguments come
only from other users' traces, and the amount comes from the position's own event history.

## Setup notes (selection, SPEC §8)

- DefiLlama: Uniswap V3 is the largest Uniswap product on Ethereum ($0.89B; V4 $0.81B; V2 $0.80B). **No token
  breakdown** is available, and V3 positions are all one NFT collection, so the per-asset rule doesn't apply.
- The collection's address came from the chain: ERC-721 mints in the last 300 blocks, `name()` = "Uniswap V3 Positions
  NFT-V1" → **`0xc36442b4a4522e871399cd717abdd847ab11fe88`** (`data/selection/2026-10-22-erc721-mints-onchain.json`).
- Ethplorer ranks NFT holders **by count** (#1: 14,896 NFTs; #50: 18; #100: 3). The 100th, an EOA (nonce 180), holds **3**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 02:36:14Z (~1s).

| Query | Result |
|-------|--------|
| ETH balance | 0.0277 ETH |
| Nonce (txs sent) | 180 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find the position NFTs
**Time:** 02:36:14Z → 02:36:22Z (7s) plus reading (~2 min). **Raw data:** `data/step2/` (63 contracts, `position_ids.json`).

| Contract | name() | Std | In | Out | Balance |
|----------|--------|-----|----|-----|---------|
| `0xc36442b4a4522e871399cd717abdd847ab11fe88` | Uniswap V3 Positions NFT-V1 | ERC-721 | 3 | 0 | **3** |
| `0xf20ef17b889b437c151eb5ba15a47bfc62bff469` | Uniswap V2 | ERC-20 | 1 | 1 | 0 (an old, already-exited position) |
| `0xa45a9824b1982c7d039928a35a602a7379da3d4d` | "Uniswap Airdrop Recipient" | ERC-1155 | 1 | 0 | spam |

**Position NFT IDs** (each minted directly to the user): **465,526** (block 16,831,593), **1,289,822** (25,154,500),
**1,295,351** (25,198,103).

### Step 3a: the NFT contract
**Time:** 02:36:45Z. **Raw data:** `data/step3/selectors_nft.json`.
- 24,384 bytes, not an EIP-1967 proxy. 38 functions; basic 14 (ERC-721 / ERC-165 / ERC-20-like); **fixed list 1:
  `burn(uint256)`**; 23 unnamed. Nothing nameable takes liquidity out.

### Step 3a′: what's inside each position? (the user's own history)
**Raw data:** `data/step3/user_mints.json`, `trace_mint_*.json`. Traces of the three txs that created the NFTs:

| NFT | User's tx → NFT contract | Put in |
|-----|--------------------------|--------|
| 465,526 | `0xac9650d8` | 3,902.58 LUSD + **2.87 ETH** (tx value) |
| 1,289,822 | `0xac9650d8` | 4,625.69 USDC + **1.78 ETH** |
| 1,295,351 | `0x88316456` | 4,995.57 PYUSD + 9,048.23 USDC |

### Step 3b: how do holders take liquidity out? (behavior)
**Time:** 02:37:06Z → 02:40:28Z (events ~3 min; traces ~30s). **Window:** blocks 26,197,800 → 26,248,199.
**Raw data:** `data/step3b/events.json`, `raw_logs.json`, `txs.json`, `exit_traces.json`, `traces/`.

**Every event the NFT contract emitted** (29,744 events in 12,164 txs):

| Event | Count | Senders | Main direct calls |
|-------|-------|---------|-------------------|
| `0x40d0efd1` | 8,932 | 2,095 | `0xac9650d8` (3,581), **`0xfc6f7865`** (1,125) |
| NFT `Transfer` | 7,047 | 1,371 | 3,832 mints, **1,513 burns** (311 via `burn(uint256)`) |
| `0x3067048b` | 5,966 | 1,582 | `0x88316456` (1,403), `0x219f5d17` (899) |
| `0x26f6a048` | 4,404 | 1,316 | `0xac9650d8` (2,534), **`0x0c49ccbe`** (279) |

**Traces (3 each, first / middle / last):**

| Call | Words | Result |
|------|-------|--------|
| `0x0c49ccbe` alone | [NFT id, an amount, 0, 0, a timestamp] | emits `0x26f6a048`; **no tokens move** |
| `0xfc6f7865` alone | [NFT id, recipient, 2¹²⁸−1, 2¹²⁸−1] | emits `0x40d0efd1`; **tokens to the recipient** (or nothing if nothing is owed) |
| `0xac9650d8` bundles | list of inner calls | inner **`0x0c49ccbe` → `0xfc6f7865`** (sometimes `0x49404b7c`, `0xdf2ab5bb` after); tokens/ETH to sender |

**Finding:** the exit is two calls: **release** (`0x0c49ccbe`) an amount of the position, then **collect**
(`0xfc6f7865`) to a recipient. Anyone holding the NFT did this themselves; no other actor appears.

### Step 3c: how much to release? (the position's own event history)
For each of the user's IDs, every `0x3067048b` (+) and `0x26f6a048` (−) with that ID as `topic1`, all history; the first
data word is the amount (it matches word 1 of `0x0c49ccbe` in the traces).

| NFT | Events | Amount left (sum of word 0) |
|-----|--------|-----------------------------|
| 465,526 | + (16,831,593), − (20,466,696), − (24,538,994) | **0** |
| 1,289,822 | + (25,154,500), − (25,187,307) | **0** |
| 1,295,351 | + (25,198,103), − (25,643,766) | **25,749,654,944,424** |

Check by simulation: releasing exactly that amount ✅; one unit more ❌. **The event history gives the exact amount**,
without any indexer.

### Step 4: run the exit for our user
**Time:** 02:40:55Z → 02:41:37Z. **Fork snapshot before:** in `data/step4/exit.json`. Gas: experimenter set ETH to 0.1
(user had 0.0277; disclosed).

| # | Action | Result |
|---|--------|--------|
| 1 | Simulate collect on all 3 (before release) | 465,526: (0, 0); 1,289,822: (0, 0); 1,295,351: (28,735,123, 28,862,856) already owed |
| 2 | Release `0x0c49ccbe(1,295,351, 25,749,654,944,424, 0, 0, deadline)` | ✅ no tokens move |
| 3 | Collect `0xfc6f7865(id, user, 2¹²⁸−1, 2¹²⁸−1)` for all 3 | ✅ ✅ ✅ — **1,295,351 → 3,665.69 PYUSD + 4,115.86 USDC**; the other two return nothing |
| 4 | Release 1 more unit on each | ❌ nothing left |
| 5 | `burn(uint256)` each NFT (fixed list) | ✅ ✅ ✅ |

**After:** 0 position NFTs; wallet **4,115.86 USDC + 3,665.69 PYUSD** (from 0). Two positions had already been emptied
by the user in the past (step 3c); the third came out in full.

---

## Result: Uniswap (V3 positions), T0 — 🟡 Harder but possible

**Tag: 🟡** (SPEC §5: "harder but possible, e.g. log scans are needed instead of a subgraph"). The exit is fully
permissionless and complete, but **nothing about it is visible without work**: what's in each position came from tracing
the user's own deposits; the two exit functions are unnamed and were learned from other users' traces; the amount to
release had to be **rebuilt from the position's full event history**, which is exactly what an indexer normally provides.

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed | 🟡 **Full exit, harder** | Step 4: release + collect + burn, all by the holder |
| Each of D1, D2, D3, D5 removed individually | Same | Never used |
| D4 (privileged actor) | **Not needed** | Every step is called by the NFT holder |

**Capital exposed to D4:** none found.
**Why T1/T2 aren't run (SPEC §3):** T0 completed (higher tiers would mainly name the two functions and the amount view).

**Notes:**
- The 100th holder by **count** held small positions, two of them already empty; ranking by count is a limitation of
  Ethplorer for NFTs (recorded in SPEC §8).
- ETH-paired positions pay WETH; the bundled exits also call `0x49404b7c`/`0xdf2ab5bb` afterwards (likely turning WETH into
  ETH and sweeping). Not needed here (this position was PYUSD/USDC).

### Required infrastructure (this run)

| Capability | Used in |
|------------|---------|
| `eth_getLogs` over all history, filtered by topic (position ID) | 2, 3b, 3c |
| `eth_getTransactionByHash` (12,164 txs, batched) | 3b |
| `debug_traceTransaction` | 3a′, 3b |
| `eth_call` (simulate release/collect), fork, impersonation | 3c, 4 |

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract | 7s | ~2 min |
| 3a / 3a′ | Selectors; what's in each position | ~10s | ~2 min |
| 3b | All NFT-contract events (29,744), 9 traces | ~3.5 min | ~4 min |
| 3c | Amount from event history | ~5s | ~2 min |
| 4 | Release, collect, burn | ~40s | ~1 min |
| **Total** | | **~4.5 min** | **~11 min** |

Wall clock: 02:36:14Z → 02:41:37Z (5.5 min).
