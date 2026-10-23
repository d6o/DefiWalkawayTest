# Run: Sky (Savings USDS, sUSDS) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Sky, Ethereum; "Savings USDS" (sUSDS) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x03ba33a6be869d02edece6db89624e8252d02f96` (#98: #100 and #99 are contracts; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`), same block as every protocol (SPEC §6) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-23T13:23:24Z |

## Ground rules

- We play a user who has their **address** and knows they hold **sUSDS** from **Sky** (SPEC §1). They don't know any
  contract addresses or how to exit.
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators know Sky/Maker. Setup used DefiLlama, Ethplorer, and an on-chain
ERC-4626 scan (no addresses from memory). The Morpho run (done just before) showed the same four nameable functions; here
they are re-derived from sUSDS's own bytecode and confirmed from other holders' transactions.

## Setup notes (selection, SPEC §8)

- DefiLlama: Sky Lending is the largest product ($5.60B, category CDP). Its largest assets, USDC (73%) and WETH (25%),
  are reserves/collateral with **no receipt token** (no USDC/WETH vault named after Sky appears in a 24h ERC-4626 scan).
- Sky-named ERC-4626 vaults, from a 24h scan of standard `Deposit` events, ranked by on-chain `totalSupply()`:
  **Savings USDS 4.34B shares** (205 deposits/24h) ≫ Staked USDS 166M ≫ Savings Dai 139M ≫ others.
  Snapshots: `data/selection/2026-10-22-sky-vaults-onchain.json`, `2026-10-22-defillama-sky-lending.json`,
  `2026-10-22-ethplorer-susds-top100.json`.
- #100 and #99 are contracts (171 B each) → **#98**, an EOA (nonce 3), **1,844,121.97 sUSDS**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 13:23:24Z (~1s).

| Query | Result |
|-------|--------|
| chainId / block | 1 / 26,248,199 |
| ETH balance | 0.2391 ETH |
| Nonce (txs sent) | 3 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "sUSDS"
**Time:** 13:23:24Z → 13:23:37Z (12s, `scripts/discover.py --match sUSDS`) plus reading (~2 min).
**Raw data:** `data/step2/` (all 13 contracts).

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0xa3931d71877c0e7a3148cb7eb4463524fec27fbd` | Savings USDS | **sUSDS** (exact match) | 1 | 0 | **1,844,121.9691** |
| `0x83f20f44975d03b1b09e64809b757c47f942beea` | Savings Dai | sDAI | 2 | 4 | 0 |
| 11 others | spam / airdrops (ETH35.com, SPK Genesis Rewards, spkrewards.com, HEX, …) | | | | |

**How the sUSDS arrived:** one plain ERC-20 `transfer()` (`0xa9059cbb`) from another EOA (`0xb3d6…8c9f`) at block
23,917,738. **The user never deposited anything themselves**, so their own history gives no hint of how to exit.

### Step 3a: is sUSDS a proxy, and can its functions be named?
**Time:** 13:23:55Z → 13:23:56Z (~1s) plus reading (~1 min). **Raw data:** `data/step3/`.

- sUSDS `0xa393…7fbd`: **170 bytes**, EIP-1967 proxy → logic **`0x4e7991e5c547ce825bdeb665ee14a3274f9f61e0`** (11,231 bytes).
  Confirmed by the `name()` trace.
- Logic: 50 functions; basic 9; **fixed list 4** (in the dispatcher) + 1 (as a constant, not a function of this contract); unnamed 37.

| Selector | Name (fixed list) |
|----------|-------------------|
| `0x6e553f65` | `deposit(uint256,address)` |
| `0x94bf804d` | `mint(uint256,address)` |
| `0xb460af94` | `withdraw(uint256,address,address)` |
| `0xba087652` | `redeem(uint256,address,address)` |
| `0xef693bed` (constant only) | `exit(address,uint256)` — a selector the logic **calls on another contract** |

### Step 3b: what do holders call, and what comes back?
**Time:** 13:24:09Z → 13:25:40Z (~1.5 min of queries) plus reading (~4 min). **Raw data:** `data/step3b/`.
**Window:** blocks 26,197,800 → 26,248,199. Busy token: **6,169 transfers in 2,930 txs**; 1,461 mints (1.06B sUSDS,
177 recipients); **1,697 burns (1.16B, 148 holders)**. 464 groups (342 single-sender).

**Direct calls on sUSDS:**

| Selector | Name | Txs | Senders | Burns | Mints |
|----------|------|-----|---------|-------|-------|
| `0x9b8d6d38` | unnamed | 84 | 54 | 0 | 84 |
| **`0xba087652`** | **`redeem`** | 39 | 31 | **39** | 0 |
| **`0xb460af94`** | **`withdraw`** | 34 | 25 | **34** | 0 |
| `0x6e553f65` | `deposit` | 5 | 5 | 0 | 5 |
| `0xa9059cbb` | `transfer` | 45 | 27 | 0 | 0 |

**Traces (3 per function):** every call burns sUSDS and sends a token `0xdc03…384f` from the sUSDS contract to the sender.

| Function | word 0 equals… | Example |
|----------|----------------|---------|
| `withdraw(uint256, addr, addr)` | **the amount of `0xdc03…` received** (700,000 → 700,000.000000) | `0x134b776b…` |
| `redeem(uint256, addr, addr)` | **the sUSDS burned** (898,232.769576 → 898,232.769576) | `0x6c99e12b…` |

Words 1 and 2 were always the sender; the chain can't tell the two addresses apart, so a user copies the pattern with both
set to their own address. Rate this week: ~1.11 `0xdc03…` per sUSDS. Inside every call: `0x35d1…492b`, `0x3c0f…7feb`.

### Step 4: run the exit for our user
**Time:** 13:25:58Z → 13:26:02Z (~4s). **Fork snapshot before:** `0x0`. **Raw data:** `data/step4/step4.json`.

- The output token `0xdc035d45d973e3ec169d2276ddab16f1e407384f` reads `name()` = "USDS Stablecoin", `symbol()` = "USDS".
  It's the asset the vault is named after ("Savings **USDS**"). Not in the user's history (they received sUSDS by transfer).

| Simulation (`eth_call`) | Result |
|-------------------------|--------|
| `redeem(1,844,121.969…, user, user)` (all) | ✅ returns **2,053,783.140627** |
| all + 1 wei | ❌ `Error(string)` |
| 2²⁵⁶−1 | ❌ `0x4e487b71…11` (arithmetic panic), as with Morpho |
| 1 share | ✅ 1.113692 |

**Sent:** `redeem(all, user, user)` → tx `0x1a3d756f…`, **status 1**, 142,845 gas.
sUSDS **1,844,121.97 burned**; **USDS 2,053,783.14 from the sUSDS contract to the user** (+11.4% vs shares).
After: sUSDS **0**, wallet USDS **2,053,783.14** (from 0).

### Step 5: where does the USDS come from, and can it run out?
**Time:** 13:26:15Z → 13:26:38Z (~25s). **Raw data:** `data/step5/`.

**Trace of our redeem:**
```
USER -> sUSDS redeem → logic 0x4e79…61e0
  sUSDS -> 0x35d1…492b (0xf24e23eb)
  sUSDS -> 0x3c0f…7feb (0xef693bed = exit(address,uint256), fixed list)
     0x3c0f… -> 0x35d1…492b (0xbb35783b)
     0x3c0f… -> USDS mint (0x40c10f19)        279.89 USDS minted to sUSDS   ← accrued interest
  sUSDS -> USDS transfer                       2,053,783.14 → USER
```
- The sUSDS contract **already held 4,829,947,098 USDS** before the call; the mint only added the interest since the
  last update. **Total supply 4,335,036,380 sUSDS ≈ 4,827,930,016 USDS at the current rate: fully backed on-chain.**

**Drain test** (snapshotted and reverted): impersonate the sUSDS contract and move its USDS out, leaving 1,000.

| Holder `0x176f…` (1,028,568,757 sUSDS) redeems | Result |
|------------------------------------------------|--------|
| everything | ❌ `Error(string)` |
| 1 share / ~800 USDS worth | ✅ / ✅ |
| max (binary search) | **903.04 shares → 1,005.71 USDS** = the 1,000 left + the interest mint |

**Findings:**
1. **The exit draws on USDS the contract holds itself**, and it holds ≈ 100% of what all shares are worth.
2. If that balance were gone, redemptions above it fail and smaller ones work: a **capital-type** limit (tracks the balance;
   no privileged actor involved). Not shown: what, if anything, can move USDS out of the contract in real life besides redemptions.
3. The interest part is **minted** during the call via `0x3c0f…7feb`; whether that can be paused wasn't tested.

---

## Result: Sky (Savings USDS), T0 — ✅ Exits cleanly

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed, user's own funds | ✅ **Full exit, one transaction** | Step 4: 1,844,122 sUSDS → 2,053,783 USDS; nothing left |
| Each of D1, D2, D3, D5 removed individually | Same | The run never used any of them |
| D4 (privileged actor) | **Not needed** on the path used | A single `redeem` by the holder |

**Why T1/T2 aren't run (SPEC §3):** T0 completed. **Capital exposed to D4:** none found on the path used.

**Caveats (not tested):** who can upgrade the proxies (sUSDS, USDS); whether the interest mint can be paused;
what could move USDS out of the sUSDS contract besides redemptions.

### Required infrastructure (this run)

| Capability | Used in |
|------------|---------|
| `eth_getLogs` over all history | 2, 3b |
| `eth_getTransactionByHash` (2,930 txs, batched) | 3b |
| `eth_call` against the fork, chosen `from` | 3a, 4, 5 |
| `debug_traceCall` / `debug_traceTransaction` | 3a, 3b, 5 |
| Fork, impersonation, snapshot/revert | 4, 5 |

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract | 12s | ~2 min |
| 3a | Proxy check + selectors | ~1s | ~1 min |
| 3b | Flows, all 2,930 txs, 6 traces | ~1.5 min | ~4 min |
| 4 | Simulations + redeem | ~4s | ~1 min |
| 5 | USDS source + drain test | ~25s | ~3 min |
| **Total** | | **~2.5 min** | **~11 min** |

Wall clock (run only): 13:23:24Z → 13:26:38Z (**3 min**).
