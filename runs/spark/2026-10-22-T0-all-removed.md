# Run: Spark (SparkLend) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Spark: SparkLend, Ethereum |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x50e835c1088dd06747312c06ac0839ecc773cb42` (#99: #100 is a contract; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`), same block as every protocol (SPEC §6) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-23T03:03:01Z |

## Ground rules

- We play a user who has their **address** and knows they deposited **wstETH** into **Spark** and got **spwstETH**
  (SPEC §1). They don't know any contract addresses or how to exit.
- Every address and function we use must come from **an earlier step's output** or from **basic knowledge**
  (SPEC §9). Function names only via the fixed list. Evidence rules: SPEC §10.
- Calls that may revert go through plain JSON-RPC (SPEC §6).

**Contamination disclosure:** both operators know Spark, and the Aave run (done just before) showed a very similar token
naming scheme. Anything carried over from the Aave run is used only as a **hypothesis** to test here, never as evidence.

## Setup notes (selection, SPEC §8)

- DefiLlama groups SparkLend ($5.10B), Spark Liquidity Layer ($2.32B), Spark Savings ($1.19B) under "Spark".
  Largest product: **SparkLend**. Largest asset: **wstETH** ($3.55B, 67.9%). Receipt token: **spwstETH**
  `0x12B5…66E9` ("Spark wstETH", totalSupply 1,150,270 at the fork block).
- Ethplorer #100 `0xbb73…17d6` is a contract (45 bytes) → moved up to **#99**, an EOA.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 03:03:01Z (~1s).

| Query | Result |
|-------|--------|
| chainId / block | 1 / 26,248,199 |
| ETH balance | 10.1654 ETH |
| Nonce (txs sent) | 161 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "spwstETH"
**Time:** 03:03:01Z → 03:04:18Z (77s, `scripts/discover.py --match spwstETH`) plus reading (~3 min).
**Raw data:** `data/step2/raw_logs.json`, `contracts.json`, `contracts.md` (all 93 contracts).

**Logs found:** 210 transfers in, 104 out, 0 ERC-1155.

**Every contract whose `name()` contains "Spark"** (SPEC §1):

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0x12b54025c112aa61face2cdb7118740875a566e9` | Spark wstETH | spwstETH (exact match) | 1 | 0 | **403.2920** |
| `0x3cfd5c0d4acaa8faee335842e4f31159fc76b008` | Spark weETH | spweETH | 1 | 0 | **199.6726** |
| `0x59cd1c87501baa753d0b5b5ab5d8416a45cd71db` | Spark WETH | spWETH | 3 | 1 | 0 |
| `0x529b6158d1d2992e3129f7c69e81a7c677dc3b12` | Spark **Variable Debt** USDT | variableDebtUSDT | 1 | 0 | **138,108.7397** |
| `0x8c147debea24fb98ade8dda4bf142992928b449e` | Spark **Variable Debt** USDS | variableDebtUSDS | 1 | 0 | **119,077.6911** |
| `0xf705d2b7e92b3f38e6ae7afadaa2fee110fe5914` | Spark **Variable Debt** DAI | variableDebtDAI | 1 | 0 | **155,817.8829** |

**Other contracts (87), grouped** (full list in `contracts.md`):

| Group | Examples |
|-------|----------|
| Tokens named after **other** protocols (outside this test) | Aave (aEthweETH 427.67, aEthLBTC, aEtheBTC, Aave "Variable Debt" USDT/USDC/DAI), Pendle (PT/YT/PLP …), Yield Basis, Strata, Instadapp iETHv2, sPENDLE |
| Plain tokens held | UNI 34,502.80, LDO 22,480.66, AAVE 598.02, PENDLE 422.30, WETH 11.10, wNXM 1,061.31, … |
| Spam / airdrops | Monster Energy, AFK, Ainance, DOG, AICC, ZIK, PVC, Duhash.games, … |

**Findings (chain only):**
1. **The user's Spark-named holdings are more than the token they know about:** besides 403.29 spwstETH, a second
   deposit-named token (199.67 spweETH) and three tokens **named** "Variable Debt" (USDT 138,108.74, USDS 119,077.69,
   DAI 155,817.88).
2. The user is also active in many other protocols; those positions are outside this test.

**Hypotheses (not shown yet):** the "Variable Debt" balances are debts that limit withdrawals, as shown for Aave.
The only evidence here is the names. They'll be tested the same way (try to withdraw; check links; cause-and-effect).

### Step 3a: is spwstETH a proxy, and can its functions be named?
**Time:** 03:44:49Z → 03:44:51Z (~2s) plus reading (~1 min).
**Knowledge used:** standard proxy slots, `debug_traceCall`, `scripts/selectors.py` with the fixed list (SPEC §9).
**Raw data:** `data/step3/` (code, disassembly, trace, selectors).

- spwstETH `0x12b5…66e9`: 2,400 bytes, **standard EIP-1967 proxy**, implementation **`0x6175ddec3b9b38c88157c10a01ed4a3fa8639cc6`**
  (13,783 bytes). The trace of `name()` confirms the hand-off. Beacon and admin slots are empty.

| Contract | Functions | Basic | Fixed list | Unnamed |
|----------|-----------|-------|------------|---------|
| Logic `0x6175…9cc6` | 34 | 9 (ERC-20 core) | **0** | 25 |
| Proxy `0x12b5…66e9` | 5 | 0 | 0 | 5 |

**Finding:** as in the Aave run, the token's own functions can't be named beyond the ERC-20 basics.

### Step 3b: what do holders call, and what comes back?
**Time:** 03:45:05Z → ~03:47Z (flows, all txs, `0xc13e` check, 9 traces; ~15s of queries) plus reading (~5 min).
**Window:** blocks 26,197,800 → 26,248,199 (same 7 days as every run).
**Raw data:** `data/step3b/` (`raw_transfer_logs.json`, `flows.json`, `phase1/`, `phase2/traces/`, `trace_pool_probe.json`,
`selectors_pool_impl.json`).

**Flows:** 132 transfer logs in 103 txs; **57 mints** (31,738.37 spwstETH, 30 recipients); **62 burns** (28,573.12, 28 holders).

**All 103 txs, grouped** (20 groups; 16 have a single sender):

| tx.to | Selector | Txs | Senders | Burns | Mints | Calldata words |
|-------|----------|-----|---------|-------|-------|----------------|
| **`0xc13e21b648a5ee794902342038ff3adab66be987`** | `0x69328dec` | 26 | 15 | **26** | 0 | 3 |
| `0xc13e…e987` | `0x02c205f0` | 20 | 14 | 0 | **20** | 8 |
| `0xc13e…e987` | `0x617ba037` | 4 | 2 | 0 | **4** | 4 |
| 17 other groups | various | 1–18 | mostly 1 | 36 | 33 | varies (wallets, routers) |

**`0xc13e…e987`:** 2,400 bytes, **standard EIP-1967 proxy** → logic **`0x5ae329203e00f76891094dcfedd5aca082a50e1b`** (21,754 bytes).
46 functions; fixed list names **1**: **`0x69328dec` = `withdraw(address,uint256,address)`**; 45 unnamed.

**Traces (3 per group, first / middle / last):**

| Function | Tx | word 0 | word 1 (amount) | word 2 | Tokens |
|----------|----|--------|-----------------|--------|--------|
| `withdraw` | `0x07672268…` | `0x7f39…2ca0` | 178.342646 × 10¹⁸ | sender | spwstETH 178.342646 burned; **`0x7f39` 178.342646 from spwstETH contract → sender** |
| `withdraw` | `0x415794e4…` | `0x7f39…2ca0` | 300 × 10¹⁸ | sender | spwstETH 300 burned; **`0x7f39` 300 → sender** |
| `withdraw` | `0xff19c194…` | `0x7f39…2ca0` | **2²⁵⁶−1** | sender | spwstETH 625.936148 burned; **`0x7f39` 625.936148 → sender** |
| `0x02c205f0` | 3 txs | `0x7f39…2ca0` | amount | sender | `0x7f39` sender → spwstETH contract; spwstETH minted to sender (1:1) |
| `0x617ba037` | 3 txs | `0x7f39…2ca0` | amount | recipient | same, minted to word 2 |

`0x7f39…2ca0` is the contract **named** "wstETH" (user's history, step 2).

**Contamination note:** Claude recognizes `0xc13e…e987` and expected `0x69328dec` from the Aave run. Here the name comes
only from the fixed list, and the behavior only from these traces.

**Findings:**
1. **Exit found at T0:** `withdraw(wstETH, amount, recipient)` on `0xc13e…e987`. One step, ~1:1, no other actor in the
   traced examples. Amount 2²⁵⁶−1 withdrew a holder's whole balance.
2. The wstETH sits in the spwstETH contract itself.

### Step 4: try `withdraw` for our user
**Time:** 03:46:17Z → ~03:49Z (~3 min, including rollbacks).
**Knowledge used:** call layout from step 3b; plain JSON-RPC (`scripts/rpcutil.py`); `evm_snapshot` / `evm_revert`.
**Raw data:** `data/step4/step4.json`.

**4.1 spwstETH (the token the user knows):** simulations with 2²⁵⁶−1, the exact balance, 1 wstETH, and 1 wei all **succeed**.
Binary search: **max = 403.291968816777284701 = 100% of the balance**. 1 wei more → `Error(string)` with text **"32"**
(standard ABI error format; the code can't be interpreted at T0). Withdrawn on the fork, then the rest with 2²⁵⁶−1:
wallet wstETH **0 → 403.2920**, spwstETH → 0.

**4.2 The second deposit (spweETH, 199.67):** which token does the spweETH contract hold?
- **Correction:** the first attempt picked the **largest raw holding**, which was a **spam token** (100,000,000,000 "ha138.com"
  airdropped to the spweETH contract). Simulations with it failed. Corrected rule: use the holding that **matches the
  contract's totalSupply**: **weETH `0xcd5f…b7ee` 38,372.00 vs totalSupply 38,372.00**.
- After withdrawing all wstETH: spweETH max = **5.294687 of 199.672562 (2.65%)**; 1 wei more → `Error(string)` **"35"**.

**4.3 Do the two deposits share one limit?** Rolled back to the starting state (snapshot) and measured:

| From the starting state | Max withdrawable |
|-------------------------|------------------|
| spwstETH alone | **403.29 (100%)** |
| spweETH alone | **199.67 (100%)** |
| **Order A:** all wstETH first, then weETH | 403.29 wstETH + **5.29 weETH (2.65%)** |
| **Order B:** all weETH first (tx `0xc00dfe6f…`), then wstETH | 199.67 weETH + **239.05 wstETH (59.28%)** |

Each deposit can be fully withdrawn on its own, **but not both**: they share one limit, and the order decides what
comes out. Which order is worth more depends on prices, which aren't available at T0, so both are recorded.

**4.4 Partial exit, done for real (order A)** after rolling back to the start:
- `withdraw(wstETH, 2²⁵⁶−1)` tx `0x9e07f4ae…` ✅; `withdraw(weETH, max − 0.001)` tx `0x5fd81e3e…` ✅.
- **Wallet: 403.2920 wstETH + 5.2937 weETH.** Still locked: **194.3789 spweETH.**

**Findings:**
1. **Partial exit with the user's own funds**, at T0, with no frontend, API, indexer, or privileged actor.
2. **The two deposits share one withdrawal limit:** all of either one, not both. The order decides the outcome
   (A: all wstETH + 2.65% of weETH; B: all weETH + 59.28% of wstETH).
3. **Spam tokens are sent to protocol contracts too**, so "which token does this contract hold" must be matched against its supply.

### Step 5: is there an on-chain link between the limit and the "Variable Debt" tokens?
**Time:** 03:48:50Z → 03:49:13Z (~25s of queries) plus reading (~3 min).
**Raw data:** `data/step5/trace_withdraw_rest.json`, `checks.json`, `check2_debt_mints.json`, `trace_mint_*.json`.

**Check 1: what does the rejected withdrawal read?** `withdraw(weETH, 2²⁵⁶−1)` after the partial exit → reverts
(`Error(string)`). Before reverting, `0xc13e` reads the user's figure with `0x1da24f3e` from:

| Contract | Value read |
|----------|------------|
| spweETH | 194.3789 |
| variableDebtDAI | 126,521.45 |
| variableDebtUSDT | 114,027.40 (6-decimal units) |
| variableDebtUSDS | 110,551.48 |

**Check 2: what created the debt-named balances?** The user's own history (step 2): one mint each, all in txs **the
user sent directly to `0xc13e`** with **`0xa415bcad`**:

| Debt-named token minted | User received in the same tx | Block | Tx |
|-------------------------|------------------------------|-------|----|
| variableDebtUSDT 134,933 | **134,933 "Tether USD"** | 24,721,118 | `0xc96b4965…` |
| variableDebtUSDS 116,374 | **116,374 "USDS Stablecoin"** | 24,721,125 | `0x4dff5a12…` |
| variableDebtDAI 152,179 | **152,179 "Dai Stablecoin"** | 24,721,129 | `0x3bc9201a…` |

**Check 3: do the token logics reference `0xc13e`?**

| Token | Implementation | Contains `0xc13e…e987` |
|-------|----------------|------------------------|
| spwstETH, spweETH | `0x6175…9cc6` (**shared**) | ✅ |
| variableDebtUSDT, USDS, DAI | `0x86c7…b985` (**shared**) | ✅ |

**Status of the hypothesis:**

| Claim | Status |
|-------|--------|
| Each debt-named balance was minted by `0xc13e` while the user received the same amount of that stablecoin | ✅ shown |
| `0xc13e`'s withdrawal logic reads all three debt-named balances and the remaining deposit | ✅ shown |
| They **cause** the limit | ⚠️ not yet → step 6 |

### Step 6: do the debt-named balances cause the limit? (cause-and-effect test)
**Time:** 03:50:50Z → ~03:52Z (~2 min including the failed first attempt).
**Knowledge used:** the repay path, learned from **other users'** burns of variableDebtDAI in the 7-day window
(`data/step6/debtdai_*`): 11 burn txs, all through smart wallets/routers; inside them, `0xc13e` receives
**`0x573ade81(asset, amount, 2, onBehalfOf)`** (3 times), the same shape seen in the Aave run. Standard ERC-20 `approve` first.
**Raw data:** `data/step6/causal_test.json`.

**First attempt failed:** the repay reverted because the user holds **0 DAI** (the 152,179 DAI they received in the mint
tx was moved out later). **Experimenter intervention (disclosed):** 1,000 DAI sent to the user from the largest recent DAI
recipient (`0xf6e7…3042`, impersonated). Then, from the state after the partial exit (step 4.4):

| State | Block | Debt-named DAI | Max withdrawable weETH | Change |
|-------|-------|----------------|------------------------|--------|
| Funded 1,000 DAI | 26,248,205 | 155,817.884245 | 0.000998691 | — |
| After control (0.1 ETH to self) | 26,248,206 | 155,817.884465 | 0.000998430 | **−0.000000262** |
| After `approve` + **repay 1,000 DAI** (`0x36132a28…`, status 1) | 26,248,208 | **154,817.884903** | **0.471641596** | **+0.470643166** |

**Findings:**
1. **Shown:** lowering the debt-named DAI balance by 1,000 raised the weETH cap from 0.001 to 0.47; the control changed nothing
   beyond drift. The balance grows by itself (+0.0002/s), as in the Aave run.
2. The repay path at T0 was only visible **inside** other users' smart-wallet transactions (traces), not from the outer calls.

### Step 7: full exit, with the capital provided by the experimenter
**Time:** 03:52:37Z → 04:05:36Z (one script hung on a USDT log query and was rerun with a narrower range; ~2 min of execution).
**Experimenter intervention (disclosed):** each stablecoin (debt + 1%) sent to the user from the largest recent recipient
of that token (impersonated). The stablecoin addresses come from the user's own history (step 2: "Dai Stablecoin",
"USDS Stablecoin", "Tether USD", received in the same txs that minted the debt-named tokens, step 5).
**Raw data:** `data/step7/full_exit.json`.

| # | Action | Status |
|---|--------|--------|
| 1 | Fund: 156,366 DAI, 120,268 USDS, 139,490 USDT | ✅ |
| 2 | `approve` + `0x573ade81(DAI, 2²⁵⁶−1, 2, USER)` → paid **154,817.89** | ✅ |
| 3 | same for USDS → paid **119,077.69** | ✅ |
| 4 | same for USDT → paid **138,108.74** | ✅ |
| 5 | `withdraw(wstETH, 2²⁵⁶−1)` | ❌ (nothing left: spwstETH was already 0 from step 4.4) |
| 6 | `withdraw(weETH, 2²⁵⁶−1)` → **194.3789 weETH** | ✅ |

| | Start of run | After partial exit (step 4.4) | **Final** |
|-|--------------|-------------------------------|-----------|
| wstETH (wallet) | 0 | 403.2920 | **403.2920** |
| weETH (wallet) | 0 | 5.2937 | **199.6726** |
| spwstETH / spweETH | 403.29 / 199.67 | 0 / 194.38 | **0 / 0** |
| Debt-named DAI / USDS / USDT | 155,818 / 119,078 / 138,109 | same | **0 / 0 / 0** |

**Findings:**
1. **Full exit achieved at T0:** every Spark-named balance is 0; both deposited assets are in the wallet.
2. **Capital needed: 154,817.89 DAI + 119,077.69 USDS + 138,108.74 USDT** (≈ $412k in stablecoins).
3. No frontend, API, indexer, or privileged actor was involved on any path used.

---

## Result: Spark (SparkLend), T0 — ◐ Partial exit

**Tag: ◐ Partial exit** (SPEC §5). With only their own funds, the user gets **all 403.29 wstETH plus 5.29 weETH (2.65%)**
out (or, in the other order, all weETH plus 59% of the wstETH). A **full exit is possible** (step 7, with ≈ $412k of
stablecoins provided by the experimenter), but it's **very challenging to find without assistance**: the shared limit,
its cause, and the repay path were only found through traces of other users' smart-wallet transactions, bytecode
searches, the user's own history, and a cause-and-effect test (steps 4–6).

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed, **user's own funds only** | **◐ Partial exit** | Step 4: all wstETH + 2.65% of weETH (order A), or all weETH + 59.28% of wstETH (order B); the deposits share one limit |
| All of D1–D5 removed, **user brings the capital** | ✅ **Full exit** | Step 7: repay three stablecoin debts, then withdraw everything |
| Each of D1, D2, D3, D5 removed individually | Same as above | The run never used any of them |
| D4 (privileged actor) | **Not needed** on the paths used | No permissioned step found on the repay or withdraw paths |

**Why T1/T2 aren't run (SPEC §3):** T0 wasn't blocked by a permission check or lack of information; the exit completed.
**Capital exposed to D4:** none found on the observed paths.

**Caveats (not tested):** who can upgrade the (EIP-1967) proxies or pause assets; whether the repay function behaves
differently for other inputs (only `(asset, amount, 2, user)` was used, as observed).

**Contamination summary:** the Aave run (done just before) made the token scheme, `withdraw`, and the repay shape
expected. Every one of them was re-derived here from Spark's own data: the fixed list named `withdraw`; the repay call
was taken from other users' traces; the debt link and its effect were shown with Spark's own transactions and a
cause-and-effect test.

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract | 77s | ~3 min |
| 3a | spwstETH proxy + selectors | ~2s | ~1 min |
| 3b | Flows, all 103 txs, `0xc13e` check, 9 traces | ~15s | ~5 min |
| 4 | Withdraw simulations, limits, order test, partial exit | ~3 min | ~5 min |
| 5 | Link checks (trace, history, bytecode) | ~25s | ~3 min |
| 6 | Repay path from other users; cause-and-effect test | ~2 min | ~3 min |
| 7 | Full exit with capital | ~2 min (+ one hung query) | ~2 min |
| **Total** | | **~9 min** | **~22 min** |

Wall clock: 2026-10-23 03:03:01Z → 04:05:36Z (63 min), of which ~10 min was a hung script.
