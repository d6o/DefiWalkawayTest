# Run: Curve (DEX, crvUSD/USDT pool) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Curve DEX, Ethereum; pool "Curve.fi Factory Plain Pool: crvUSD/USDT" (LP token = the pool) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x1e18d2cdbfad75c34c475844050025dafa404604` (100th holder; EOA with EIP-7702 delegation; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-25T02:09:18Z |

## Ground rules

- We play a user who has their **address** and knows they provided liquidity on **Curve** and hold **crvUSDUSDT-f** (SPEC §1).
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators know Curve, including the names of the exit functions. Those names are
**not** used: the functions stay unnamed (`0x1a4d01d2`, `0x5b36389c`); their roles and arguments come from other
holders' traces.

## Setup notes (selection, SPEC §8)

- DefiLlama: Curve DEX is the largest product ($1.13B); largest asset **crvUSD (13.9%)**. crvUSD's address came from
  DefiLlama's pool data; `name()` = "Curve.Fi USD Stablecoin".
- Pools holding crvUSD, from crvUSD transfers in the last 3,000 blocks: the largest holders have **no `name()`**
  (not LP tokens; likely other Curve products). Among **named** pool tokens, the largest crvUSD holder is
  **crvUSD/USDT** `0x390f…7bf4` (22.88M crvUSD; LP supply 45.25M).
- **LP concentration:** two contracts hold ~83% of the LP: an unnamed one (25.1M) and one named "Curve.fi
  crvUSDUSDT-f **Gauge Deposit**" (12.4M). Wallet holdings fall fast: #20 holds 95.8 LP, #50 1.05, **#100 0.00195**.
  The rule picks #100: a **dust** position. The mechanism is tested on it, and checked at larger sizes in step 4.

## Steps

### Step 1: what the node tells us about the address directly
ETH **0.0000002**; nonce 51; code = EIP-7702 delegation (counts as a wallet).

### Step 2: find every token contract the address touched
**Time:** 02:09:18Z → 02:09:24Z (6s). 21 contracts. **One exact match:** crvUSDUSDT-f, **0.001954057686996578 LP**.
**How it arrived:** the user's own tx to the pool, `0x0b4c7e4d([2000, 0], 1953471469690479)`: 0.002 USDT in, 0.001954 LP minted.

### Step 3a: can the pool's functions be named?
**Time:** 02:09:38Z. **Raw data:** `data/step3/`.
- The pool is a **45-byte minimal proxy**; `name()` delegates to logic `0x67fe41a9…4286` (18,267 bytes).
- `scripts/selectors.py` found **no dispatcher entries** (this compiler's routing pattern isn't recognized). Checked
  directly instead: the basic ERC-20 selectors appear in the code; **none of the 3,120 fixed-list selectors appears
  anywhere**. **The exit function can't be named at T0.**

### Step 3b: how do holders exit? (behavior)
**Time:** 02:10:12Z → 02:10:18Z. **Window:** blocks 26,197,800 → 26,248,199. **Raw data:** `data/step3b/`.
**Flows:** 233 transfers in 94 txs; 38 mints (755,873 LP, 13 recipients); **48 burns (737,450 LP, 18 holders)**.

| tx.to | Selector | Txs | Senders | sender == holder | What it does (traces) |
|-------|----------|-----|---------|------------------|------------------------|
| **pool** | **`0x1a4d01d2`** | 8 | 8 | **8 / 8** | words [LP, 0, a minimum]: LP burned; **USDT to the holder** (e.g. 19,365.15 LP → 19,901.32 USDT; word 2 = 19,895.35, just under) |
| **pool** | **`0x5b36389c`** | 2 | 2 | **2 / 2** | words [LP, min, min]: LP burned; **USDT + crvUSD to the holder** (4,800 LP → 2,714.77 USDT + 2,217.76 crvUSD) |
| routers / other contracts | various | 30 | — | 0 | (not the holder) |

**Finding:** holders exit **in one call on the pool, themselves**: one token back (`0x1a4d01d2`) or both
(`0x5b36389c`). No other actor.

### Step 4: run the exit for our user
**Time:** 02:10:42Z → 02:10:47Z. **Raw data:** `data/step4/`. Gas: experimenter set ETH to 0.01 (disclosed).

| Simulation | Result |
|------------|--------|
| `0x5b36389c(all LP, 0, 0)` | ✅ returns [1,019, 988,149,862,240,364] |
| `0x1a4d01d2(all LP, 0, 0)` | ✅ returns 2,007 |

**Sent:** `0x5b36389c(0.001954057686996578 LP, 0, 0)` → tx `0x367b0313…`, status 1. **LP 0;
wallet 0.001019 USDT + 0.000988 crvUSD.**

**Same call, simulated for larger holders:** #20 (95.79 LP) → 50.00 USDT + 48.44 crvUSD ✅; #5 (2,412 LP) → 1,259.00 USDT
+ 1,219.81 crvUSD ✅; #3 (a contract, 13,890 LP) → 7,249.56 USDT + 7,023.86 crvUSD ✅.

---

## Result: Curve (crvUSD/USDT pool), T0 — 🟡 Harder but possible

**Tag: 🟡.** The exit is **one call by the holder, fully permissionless**, but **the function can't be named at T0**: it
was learned, with its arguments, only from other holders' traces (like Uniswap). Morpho, Sky, Rocket Pool, and Compound got
✅ because their exit was nameable on the position contract itself.

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed | 🟡 **Full exit, one call** | Step 4 (dust); same call simulated at 95–13,890 LP |
| Each of D1, D2, D3, D5 removed individually | Same | Never used |
| D4 | **Not needed** | |

**Not tested:** the ~83% of LP that sits in other contracts (one is named "… Gauge Deposit"). Holders there have an
extra layer to exit first; that layer wasn't part of this run.

**Capital exposed to D4:** none found. **Why T1/T2 aren't run:** T0 completed.

### Timings (raw)

| Step | Queries / execution | Analysis (approx.) |
|------|---------------------|--------------------|
| 1–2 | 6s | ~2 min |
| 3a–3b | ~15s | ~4 min |
| 4 | ~10s | ~2 min |
| **Total** | **~30s** | **~8 min** |

Wall clock: 02:09:18Z → ~02:11Z (2 min).
