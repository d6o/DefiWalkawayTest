# Run: Compound (V3, WETH market) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Compound V3, Ethereum; market "Compound WETH" (cWETHv3) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xe8bde08a933dc0744c3a9dca7d0f1c3978c2be90` (100th holder; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-25T01:34:54Z |

## Ground rules

- We play a user who has their **address** and knows they supplied **ETH** to **Compound** and hold **cWETHv3** (SPEC §1).
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators know Compound. Market addresses came from the chain (contracts named
"Compound …" exchanging WETH/USDC in the last 300 blocks). The exit function was named by the fixed list; its
arguments and behavior came from other holders' traces.

## Setup notes (selection, SPEC §8)

- DefiLlama: Compound V3 is the largest product ($1.30B). Largest assets WBTC (40%) and wstETH (24%) are collateral with
  **no receipt token**; next is **WETH (21%)**, whose receipt is the WETH market **cWETHv3** `0xa175…ae94` (50,804.68
  supplied). USDC's market (cUSDCv3) is smaller in DefiLlama's net figures (3.9%).
- 100th holder: an EOA (nonce 296), **10.48 cWETHv3**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 01:34:54Z. ETH 1.97; nonce 296; plain EOA.

### Step 2: find every token contract the address touched
**Time:** 01:34:54Z → 01:35:02Z (7s). **Raw data:** `data/step2/` (95 contracts).

| Contract | name() | symbol() | Balance |
|----------|--------|----------|---------|
| `0xa17581a9e3356d9a858b789d68b4d866e593ae94` | Compound WETH | **cWETHv3** (exact) | **10.4811** |
| `0x39aa…7563`, `0x4ddc…70ed5`, `0xface…ed0c7`, `0xf650…dcc9`, `0x70e3…f8e4` | Compound USD Coin / Ether / ChainLink / USDT / Collateral | cUSDC, cETH, cLINK, cUSDT, cCOMP | 0 (older positions, closed) |
| `0xc00e94cb662c3520282e6f5717214004a7f26888` | Compound | COMP | 0 |
| 5 phishing tokens | "ClaimCompound.com", "Compound-Claim.com", "compoundcoin.net", "nft-compound.finance" ×2, "apycompound.com" | | fake |

**How the cWETHv3 arrived:** two txs **the user sent** to `0xa397a8c2…00c7` (`0x555029a6`) with **3 ETH** and **7 ETH**;
3.0 + 7.0 cWETHv3 minted to the user (block 20,352,144 / 20,352,209). No debt-named token appears in the history.

### Step 3a: proxy and function names
**Time:** 01:35:22Z. cWETHv3: 1,878-byte EIP-1967 proxy → logic `0xb647…4f51` (18,599 B), 67 functions; basic 5; the fixed
list matches **`withdraw(address,uint256)`** (`0xf3fef3a3`) in the logic's code. *(Our extractor labels it "other" rather
than "dispatcher": this contract routes calls with a different comparison pattern. Behavior confirms it's callable, step 3b.)*

### Step 3b: who burns cWETHv3, and what do they get?
**Time:** 01:35:22Z → ~01:36Z. **Window:** blocks 26,197,800 → 26,248,199. **Raw data:** `data/step3b/`.
**Flows:** 55 transfers in 43 txs; 33 mints (450.68), **22 burns (184.67) by 17 holders**.

| tx.to | Selector | Txs | Senders | sender == holder |
|-------|----------|-----|---------|------------------|
| helper `0xa397…00c7` (the one the user deposited with) | `0x555029a6` | 9 | 8 | 9 / 9 |
| `0x7251…6dd2` | `0xec5b999d` | 4 | 4 | 4 / 4 |
| cWETHv3 | `transfer` | 3 | 2 | 3 / 3 |
| **cWETHv3** | **`withdraw(address,uint256)`** | 1 | 1 | 1 / 1 |

**Traces:** direct `withdraw(0xc02a…, 9.019964e18)` → cWETHv3 burned from the holder; **WETH 9.019964 from cWETHv3 →
holder**. Helper calls (3): the helper calls cWETHv3 `0x26441318(holder, helper, WETH)` on the holder's behalf, receives
WETH, turns it into ETH and sends it to the holder (13.66 / 0.058 / 58.24 ETH).

**Finding:** **holders exit in one call, themselves**, directly or through the helper; no other actor.

### Step 4: run the exit for our user
**Time:** 01:36:11Z → 01:36:20Z. **Raw data:** `data/step4/step4.json`.
- Simulation: `withdraw(WETH, exact balance)` ✅; max = balance; +1 wei → `0xe273b446`.
- **Sent:** `withdraw(WETH, 10.481104556483629153)` → tx `0x01b45788…`, status 1. **WETH 10.4811 → user**; cWETHv3 burned.
- After: cWETHv3 **0.000000005** (interest accrued during the 1-second block step; dust), wallet WETH **10.4811**.

### Step 5: liquidity
**Raw data:** `data/step5/liquidity.json`.
- WETH held by cWETHv3: **13,552.27** vs totalSupply **50,794.20** → **26.7% on hand**; the rest is lent out.
- Largest EOA holder (`0xce27…`, 29,976.85) withdrawing everything → ❌ (reverts). A **capital-type** limit, like
  Morpho, Sky, and Rocket Pool. Our user fit easily.

---

## Result: Compound (V3 WETH market), T0 — ✅ Exits cleanly

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed (our user) | ✅ **Full exit, one call** | `withdraw(WETH, balance)` named by the fixed list; arguments copied from another holder's trace |
| Large holders | **Liquidity-limited** (capital-type) | Only 26.7% of supplied WETH on hand at the fork block |
| Each of D1, D2, D3, D5 removed individually | Same | Never used |
| D4 | **Not needed** | |

**Capital exposed to D4:** none found. **Why T1/T2 aren't run (SPEC §3):** T0 completed.

### Timings (raw)

| Step | Queries / execution | Analysis (approx.) |
|------|---------------------|--------------------|
| 1–2 | 8s | ~2 min |
| 3a–3b | ~30s | ~4 min |
| 4–5 | ~10s | ~2 min |
| **Total** | **~1 min** | **~8 min** |

Wall clock: 01:34:54Z → 01:36:20Z (1.5 min).
