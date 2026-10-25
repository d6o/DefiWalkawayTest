# Run: Rocket Pool (rETH) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Rocket Pool, Ethereum; rETH |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x85f39e455d42af435e907924fb5adef5dc4ad5ce` (100th holder; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-25T01:13:46Z |

## Ground rules

- We play a user who has their **address** and knows they hold **rETH** from **Rocket Pool** (SPEC §1). They don't know
  any contract addresses or how to exit.
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC;
  `Error(string)` revert texts are read with plain ABI decoding.

**Contamination disclosure:** both operators know Rocket Pool. The rETH address came from the Spark run's on-chain
history (`name()` = "Rocket Pool ETH"). The exit function was named by the fixed list; its behavior and limits come from
traces and fork tests.

## Setup notes (selection, SPEC §8)

- DefiLlama: one product on Ethereum ($1.17B), asset ETH (100%). Receipt token **rETH** `0xae78…6393`
  (totalSupply **309,405.21** at the fork block).
- 100th holder: an EOA (nonce 44), **419.29 rETH**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 01:13:46Z (~1s).

| Query | Result |
|-------|--------|
| ETH balance | 52.98 ETH |
| Nonce (txs sent) | 44 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "rETH"
**Time:** 01:13:46Z → 01:13:57Z (10s) plus reading (~2 min). **Raw data:** `data/step2/` (207 contracts).

| Contract | name() | symbol() | In | Out | Balance |
|----------|--------|----------|----|-----|---------|
| `0xae78736cd615f374d3085123a210448e74fc6393` | Rocket Pool ETH | **rETH** (exact) | 2 | 0 | **419.2924** |
| 8 others whose name mentions the protocol | "rocket-pools.com", "$ RocketLR.com", "Rocket Pool: Airdrop NFT Voucher", "Rocket Pool: Airdrop Withdrawal Badge", "rocketpool.world", "apy-rocketpool.net", "$ rEthLP.com", "$ reth.farm" | spam / phishing | 1 each | 0 | fake balances |

**How the rETH arrived:** two txs **the user sent** to router `0x68b3…fc45` (`0x5ae401dc`) with **250 ETH** and **200 ETH**;
233.02 + 186.27 rETH came from `0xa4e0…` (a trading pool). The user **bought** rETH; they never deposited at Rocket Pool.

**Finding:** **8 phishing tokens imitate the protocol's name** in this one wallet. Under SPEC §1 they're "possible
positions"; only the exact rETH match holds a real balance.

### Step 3a: is rETH a proxy, and can its functions be named?
**Time:** 01:14:19Z. **Raw data:** `data/step3/`.
- **8,800 bytes, not a proxy.** 21 functions; basic 9; **fixed list 2: `burn(uint256)`, `mint(uint256,address)`**; 10 unnamed.

### Step 3b: who creates and destroys rETH, and what comes back?
**Time:** 01:14:19Z → ~01:16Z. **Window:** blocks 26,197,800 → 26,248,199. **Raw data:** `data/step3b/`.

**Flows:** 4,177 transfers in 1,983 txs; **24 mints** (125.10 rETH); **968 burns (5,663.29 rETH) by 84 holders**,
through 68 different contracts (mostly bot-like: hundreds of one-off selectors).

**Direct burns:** **44 calls to `burn(uint256)` on rETH itself, each sent by the holder** (41 holders, 788.13 rETH).
Traces (first / middle / last):

| Tx | Holder | burn(amount) | ETH |
|----|--------|--------------|-----|
| `0xe6bc1d61…` | `0xce8a…` | 66.000000 rETH | **77.481520 ETH from the rETH contract → holder** |
| `0x49489a1c…` | `0xf259…` | 0.000150 | 0.000176 ETH → holder |
| `0x5eeeea63…` | `0xe50b…` | 0.230977 | 0.271226 ETH → holder |

**Finding:** **the holder burns their own rETH and receives ETH in the same call, from the rETH contract** (~1.174 ETH per
rETH). No queue, no claim, no other actor.

### Step 4: run the exit for our user
**Time:** 01:15:28Z → ~01:16Z. **Fork snapshot before:** in `data/step4/step4.json`.

| Simulation | Result |
|------------|--------|
| `burn(all 419.292408)` | ✅ |
| Max (binary search) | **419.292408 = 100%**; +1 wei → "Insufficient rETH balance" |

**Sent:** `burn(419.292407534986490214)` → tx `0x77e431e5…`, **status 1**. User ETH **52.98 → 545.33** (**+492.36 ETH**
before gas). rETH left: **0**.

### Step 5: is there a limit? (liquidity test)
**Raw data:** `data/step5/liquidity.json`, `trace_big_burn.json`. (Run on the fork **after** our user's burn.)

| Test | Result |
|------|--------|
| ETH held by the rETH contract | **3,631.09** at the fork block; 3,138.74 after our user's burn |
| Largest EOA holder (`0x5313…`, 5,670.46 rETH) burns everything | ❌ "**Insufficient ETH balance for exchange**" |
| Their max (binary search) | **2,672.96 rETH → 3,138.74 ETH** = exactly the ETH left in the rETH contract |
| Trace of that max burn | ETH moves only **rETH contract → holder**; nothing pulled from elsewhere |

**Findings:**
1. **Instant redemption is limited to the ETH the rETH contract holds**: 3,631 ETH at the fork block, against
   309,405 rETH (~363k ETH) of supply, so **~1.2% of supply** could exit this way at that moment.
2. This is a **capital-type limit** (it tracks a balance; no permission involved), like Morpho and Sky, but much tighter.
   Our user (419 rETH) fit; the largest holder would get a partial exit.
3. Not shown: what refills the rETH contract's ETH, and whether that depends on any privileged actor.

---

## Result: Rocket Pool (rETH), T0 — ✅ Exits cleanly

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed (our user) | ✅ **Full exit, one call** | Step 4: `burn(all)` → 492.36 ETH, sent by the holder |
| Large holders | **Liquidity-limited** (capital-type, not a permission) | Step 5: only up to the ETH in the rETH contract (~1.2% of supply at the fork block) |
| Each of D1, D2, D3, D5 removed individually | Same | Never used |
| D4 (privileged actor) | **Not needed** on the path used | |

**The contrast for the talk:** Lido, ether.fi, and Rocket Pool are all liquid staking tokens. Lido and ether.fi pay out
only after permissioned batches (🔴). **Rocket Pool lets any holder burn rETH for ETH in one call, with no one's
permission**, but only as far as the ETH on hand goes.

**Capital exposed to D4:** none found. **Why T1/T2 aren't run (SPEC §3):** T0 completed.

### Required infrastructure (this run)

| Capability | Used in |
|------------|---------|
| `eth_getLogs` over all history | 2, 3b |
| `eth_getTransactionByHash` (batched) | 3b |
| `debug_traceTransaction` / `debug_traceCall` | 3b, 5 |
| `eth_call` (simulation, binary search), fork, impersonation | 4, 5 |

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract | 10s | ~2 min |
| 3a | Selectors | ~1s | ~1 min |
| 3b | Flows (4,177 logs), burn/mint grouping, 3 traces | ~1 min | ~4 min |
| 4 | Simulation + burn | ~10s | ~1 min |
| 5 | Liquidity test | ~30s | ~2 min |
| **Total** | | **~2 min** | **~10 min** |

Wall clock: 01:13:46Z → ~01:17Z (3.5 min).
