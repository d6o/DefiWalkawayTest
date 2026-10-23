# Run: Aave — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Aave (V3, Ethereum) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x462a336dcac6eaf544106266914caa5a18b831d0` (see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`), same block as every protocol (SPEC §6) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-23T01:18:46Z |

## Ground rules

- We play a user who has their **address** and knows they deposited **weETH** into **Aave** and got **aEthweETH** (SPEC §1).
  They don't know any contract addresses or how to exit.
- Every address and function we use must come from **an earlier step's output** or from **basic knowledge**
  (SPEC §9: ERC-20/721/1155 core, standard proxy slots, JSON-RPC). Function names only via the fixed list (SPEC §9).
- Every step is logged with what we tried, what we found, and the time.

**Contamination disclosure:** both operators know Aave well. Picking the token and address (setup) used Aave knowledge
and DefiLlama/Ethplorer. Each step below notes what knowledge it used, so a reviewer can check it.
The scripts built during the Lido run are reused unchanged.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 01:18:46Z → 01:18:47Z (~1s).
**Knowledge used:** standard JSON-RPC only.

| Query | Result |
|-------|--------|
| chainId / block | 1 / 26,248,199 (2026-10-22T12:37:23Z) |
| ETH balance | 1.0567 ETH |
| Nonce (txs sent) | 295 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "aEthweETH"
**Time:** scan 01:18:56Z → 01:19:46Z (50s, `scripts/discover.py --match aEthweETH`), then reading the results (~5 min).
**Knowledge used:** standard transfer events and ERC-20 view functions; the token symbol the user knows ("aEthweETH");
the protocol name the user knows ("Aave").

**Raw data:** `data/step2/raw_logs.json`, `data/step2/contracts.json`, `data/step2/contracts.md` (all 65 contracts).

**Logs found:** 236 transfers in, 218 transfers out, 0 ERC-1155.

**Exact symbol match:** **1**: `0xbdfa7b7893081b35fb54027489e2bc7a38275129`, "Aave Ethereum weETH" / aEthweETH,
balance **456.4827**, one incoming transfer at block 25,338,622.

**Every contract whose `name()` contains "Aave"** (the user knows the protocol name, SPEC §1):

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0xbdfa7b7893081b35fb54027489e2bc7a38275129` | Aave Ethereum weETH | aEthweETH | 1 | 0 | **456.4827** |
| `0x0b925ed163218f6662a35e0f0371ac234f9e9371` | Aave Ethereum wstETH | aEthwstETH | 14 | 13 | **4,515.3880** |
| `0xea51d7853eefb32b6ee06b1c12e6dcca88be0ffe` | Aave Ethereum **Variable Debt** WETH | variableDebtEthWETH | 15 | 12 | **5,763.7603** |

**Other contracts (62), grouped** (full list in `contracts.md`):

| Group | Examples |
|-------|----------|
| Tokens with a real-looking name and history, now 0 balance | stETH (26 in / 8 out), wstETH (73 / 78), WETH (19 / 12), eETH (5 / 2), weETH (5 / 5) |
| Positions in **another** protocol ("Spark" in the name) | Spark wstETH / spwstETH **8,284.09**; Spark Variable Debt WETH **9,416.08** |
| ETH / wstETH look-alikes with fake "outgoing" transfers (address poisoning, as in the Lido run) | ~35 contracts named ETH, Ether, ĖTḨ, E឴឴ꓔH, wstETH (fake) … |
| Spam / airdrops | DOG, AICC, ZIK, PVC, GLAMDOG, "Morpho Vault", … |

**Findings (chain only):**
1. **The user's Aave-named holdings are more than the token they know about.** Besides 456.48 aEthweETH, two more contracts
   named "Aave …" report balances: 4,515.39 (`aEthwstETH`) and 5,763.76 (`variableDebtEthWETH`, **named** "Variable Debt WETH").
   The wallet holds 1.06 ETH.
2. The user's history shows wstETH / WETH / weETH moving in and out many times.
3. The same address holds tokens named after another protocol (Spark), which is outside this test.

**Hypotheses (not shown by the chain yet):** the 5,763.76 balance is a **debt**, and it **limits withdrawals** of the
deposits; the in/out pattern is a leveraged position. The only evidence for "debt" is a token name, which isn't trustworthy
(step 2 of the Lido run). These will be tested by trying to withdraw.

**Correction:** a first version of these findings stated "debt" and "leveraged position" as facts, and Claude proposed
options based on them (e.g. funding the repayment). That came from Claude's Aave knowledge, not from the chain. It was
replaced by the hypotheses above, and no decision was taken on it.

### Step 3a.1: is the aEthweETH contract a proxy, and where does its logic live?
**Time:** 01:27:01Z → 01:27:03Z (~2s) plus reading (~1 min).
**Knowledge used:** standard proxy slots, EVM opcodes, ERC-20 `name()`, `debug_traceCall`.

**Bytecode** (`data/step3/aweeth_code.hex`, `.asm`): 2,400 bytes; 3 `DELEGATECALL`, 1 `CALL`, 3 `SLOAD`.

| Slot | Value |
|------|-------|
| EIP-1967 implementation | **`0xadc45df3cf1584624c97338bef33363bf5b97ada`** |
| EIP-1967 beacon / admin, EIP-1822, legacy OZ | empty |

**Trace of `name()`** (`data/step3/trace_name.json`): `user → 0xbdfa…5129 (aEthweETH)` → `DELEGATECALL → 0xadc45df3…7ada`.

**Findings:**
1. **aEthweETH is a standard EIP-1967 proxy.** The standard check finds the logic directly (unlike stETH).
2. The logic lives at `0xadc45df3…7ada` (10,477 bytes).
3. The EIP-1967 **admin** slot is empty, so who can change the logic isn't visible from the standard slot.

### Step 3a.2: list the functions and try to name them
**Time:** 01:27:11Z (~1s, `scripts/selectors.py`) plus reading (~2 min).
**Knowledge used:** EVM opcodes, basic signatures, the fixed list (SPEC §9).

**Raw data:** `data/step3/selectors_impl.json`, `data/step3/selectors_proxy.json`.

| Contract | Functions | Basic | Fixed list | **Unnamed** |
|----------|-----------|-------|------------|-------------|
| Logic `0xadc45df3…7ada` (10,477 B) | 35 | 9 (ERC-20 core) | **0** | **26** |
| Proxy `0xbdfa…5129` (2,400 B) | 5 | 0 | 0 | 5 |

Proxy functions: `0x3659cfe6`, `0x4f1ef286`, `0x5c60da1b`, `0xd1f57894`, `0xf851a440`.

**Contamination note:** Claude recognizes several of these selectors from memory. Not used.

**Findings:**
1. **Same as Lido: at T0 the token's own functions can't be named** beyond the ERC-20 basics. None of the 20 verbs
   (withdraw, redeem, burn, …) matched with 0–3 common argument types.
2. Next: learn from behavior (step 3b), since the exit may live in another contract.

### Step 3b, part 1: where do aEthweETH tokens go?
**Time:** ~01:27:30Z (`scripts/flows.py`, a few seconds) plus reading (~2 min).
**Window:** same 7 days as the Lido run: blocks 26,197,800 → 26,248,199.
**Raw data:** `data/step3b/raw_transfer_logs.json`, `flows.json`, `recipients.md`, `senders.md`.

| | |
|-|-|
| Transfer logs / txs | 95 / 86 |
| Recipients | 31 (9 contracts) |
| **Mints** (from `0x0`) | 51 logs, 3,072.21 aEthweETH, to 29 addresses |
| **Burns** (to `0x0`) | **39 logs, 6,059.83 aEthweETH, from 24 holders** |
| Largest contract recipients | small and single-sender (top: `0x7231…44bf`, 1,234.02 from 1 sender) |

**Finding:** unlike stETH (0 burns in the same week), aEthweETH is **burned** regularly, by 24 different holders.
That's the usual sign of tokens being redeemed. Next: what do the burning txs call?

### Step 3b, phase 1: what did users call? (all 86 txs)
**Time:** 01:27:55Z → 01:27:57Z (1.3s, `scripts/txgroups.py` with **all** recipients, including `0x0`) plus reading (~3 min).
**Raw data:** `data/step3b/phase1/txs.json`, `groups.json`, `groups.md` (16 groups).

| tx.to | Selector | Txs | Senders | Burns | Mints | Calldata words |
|-------|----------|-----|---------|-------|-------|----------------|
| **`0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2`** | `0x617ba037` | 30 | 18 | 0 | **30** | 4 |
| **`0x8787…a4e2`** | `0x69328dec` | 26 | 17 | **26** | 0 | 3 |
| `0x8787…a4e2` | `0x9cd19996` | 2 | 2 | 0 | 2 | 32, 69 |
| `0x8787…a4e2` | `0xac9650d8` | 1 | 1 | 0 | 1 | 13 |
| 12 other groups | various | 1–6 each | **1 each** | 13 | 22 | varies (smart wallets, routers) |

**Findings:**
1. **One contract, `0x8787…a4e2`, carries most of the activity**, with two simple, fixed-length functions:
   `0x617ba037` (always mints) and `0x69328dec` (always burns).
2. The other 12 groups each have a single sender, the same smart-wallet / router pattern as in the Lido run.

### Step 3a (on `0x8787…a4e2`): proxy and function names
**Time:** ~01:29Z (a few seconds) plus reading (~2 min).
**Knowledge used:** standard proxy slots, `debug_traceCall`, `scripts/selectors.py` with the fixed list (SPEC §9).

- `0x8787…a4e2`: 2,400 bytes, **standard EIP-1967 proxy**. Implementation slot → **`0x728a138a4823392c2efa55e028d434f526fe03cf`**
  (21,146 bytes). Confirmed by trace (`data/step3b/trace_pool_probe.json`).
- Logic: 68 functions; basic 0; **fixed list 1**; unnamed 67 (`data/step3b/selectors_pool_impl.json`).

| Selector | In dispatcher | Name (source) | Observed behavior |
|----------|---------------|---------------|-------------------|
| `0x69328dec` | ✅ | **`withdraw(address,uint256,address)`** (fixed list) | 26 txs, 17 senders, always burns aEthweETH |
| `0x617ba037` | ✅ | unnamed | 30 txs, 18 senders, always mints aEthweETH |
| `0x9cd19996`, `0xac9650d8` | ✅ | unnamed | 1–2 txs |

**Contamination note:** Claude recognizes `0x8787…a4e2` and some of its selectors from memory. Not used. The name above
comes only from the fixed list, which was set before any protocol was tested.

**Findings:**
1. **At T0, the fixed list names the function that burns aEthweETH: `withdraw(address,uint256,address)`.**
   Unlike Lido, the user can find a recognizably named exit, with its argument types.
2. The function users call to get aEthweETH (`0x617ba037`) can't be named.
3. Still not shown: what the user **gets back** when aEthweETH is burned. Next: trace examples.

### Step 3b, phase 2: trace the two main `0x8787` functions
**Time:** ~01:28Z (6 traces in 1.4s, `scripts/tracetx.py`) plus reading (~3 min).
**Knowledge used:** `debug_traceTransaction`, standard `Transfer` events, calldata words.
**Raw data:** `data/step3b/phase2/traces/*.json`, `data/step3b/phase2/summaries.json`. Examples: first / middle / last.

**`0x69328dec` = `withdraw(address,uint256,address)`** (3 of 3 alike):

| Tx | word 0 | word 1 (amount) | word 2 | Tokens |
|----|--------|-----------------|--------|--------|
| `0x2d30055d…` | `0xcd5f…b7ee` | **2²⁵⁶−1** | sender | aEthweETH 1,524.0450 burned from sender; **weETH 1,524.0450 from `0xbdfa…` (aEthweETH) to sender** |
| `0x3073cb1e…` | `0xcd5f…b7ee` | 150 × 10¹⁸ | sender | aEthweETH 149.99999 burned; **weETH 150.0 to sender** |
| `0xb63b294b…` | `0xcd5f…b7ee` | 287.3036 × 10¹⁸ | sender | aEthweETH 287.3036 burned; **weETH 287.3036 to sender** |

**`0x617ba037`** (unnamed, 3 of 3 alike): word 0 `0xcd5f…b7ee`, word 1 amount, word 2 sender, word 3 `0`.
weETH goes from the sender **into `0xbdfa…` (aEthweETH)**, and aEthweETH is minted to the sender (~1:1).

`0xcd5f…b7ee` is the contract that step 2 found **named** "Wrapped eETH" / weETH, in the user's own history.

**Findings:**
1. **The exit is one step:** `withdraw(weETH, amount, recipient)` on `0x8787…a4e2`. It burns aEthweETH and sends weETH
   to the recipient ~1:1, in the same transaction. No waiting and no other actor in these examples.
2. **Amount = 2²⁵⁶−1 withdrew the holder's whole balance** (example 1).
3. The weETH sits in the aEthweETH contract itself (in on mint, out on withdraw).
4. All three argument types were readable from the data: the asset address, an amount, the recipient.
5. **Still to test for our user:** whether the other Aave-named balances (step 2 hypotheses) affect this.

### Step 4 (part 1): try `withdraw` for our user, simulation only
**Time:** 01:29:23Z → 01:29:49Z (~26s, 75 `eth_call`s), nothing sent.
**Knowledge used:** the call layout from step 3b phase 2 (`withdraw(weETH, amount, recipient)` on `0x8787…a4e2`), `eth_call`.
**Raw data:** `data/step4/max_withdraw_aweeth.json`.

| Amount | Result |
|--------|--------|
| 2²⁵⁶−1 (everything, as other holders did) | ❌ custom error **`0x6679996d`** (no arguments) |
| 456.482736854341547308 (exact balance) | ❌ `0x6679996d` |
| 1 weETH | ✅ |
| 1 wei | ✅ |

**Binary search for the largest amount that succeeds** (71 calls):
- **Max withdrawable: 61.672942239804441619 weETH = 13.5% of the 456.48 balance.**
- 1 wei more → `0x6679996d`.

**Findings:**
1. **Our user can't withdraw their whole aEthweETH balance**, unlike the 3 traced holders. Only **13.5%** goes through;
   anything above is rejected with `0x6679996d`.
2. **The chain doesn't say why.** The error has no arguments and can't be named at T0. The step 2 hypothesis (the
   "Variable Debt WETH" balance limits withdrawals) is consistent with this, but not shown.

### Step 4 (part 2): actually withdraw the allowed amount
**Time:** 01:34:39Z → ~01:40Z (~5 min including the failed attempts).
**Knowledge used:** same as part 1; anvil `evm_setNextBlockTimestamp`, `eth_sendTransaction` via plain JSON-RPC.
**Fork snapshot before this step:** `0x0` (`data/step4/snapshot.txt`).
**Raw data:** `data/step4/withdraw_receipt.json` (failed), `data/step4/withdraw_receipt_ok.json`, `data/step4/partial_withdraw.json`.

**⚠️ Contamination (T2 source leaked):** the first attempt used `cast send`. Its gas estimation reverted, and `cast`
printed a **name** for error `0x6679996d`, looked up automatically from a **hosted signature database**. That's a T2
source, not allowed at T0, so the name isn't used or repeated in this run. From here on, calls go through plain JSON-RPC
so nothing is decoded automatically. Noted for T2: with a signature database, the revert reason appears immediately.

**Attempts:**

| # | What | Block timestamp | Result |
|---|------|-----------------|--------|
| 1 | `cast send` withdraw 61.672942239804441619 (part 1 max) | wall clock (~13h after fork) | ❌ gas estimation reverted `0x6679996d` |
| 2 | Same amount, plain JSON-RPC, next block pinned to fork time **+12s** | 1,792,672,655 | ❌ mined, **status 0** |
| 3 | Re-measure the max on the current block (+12s): **61.672902005868166952** (−0.000040233936 vs fork block) | — | — |
| 4 | Withdraw **61.671902005868166952** (new max − 0.001), next block +1s | 1,792,672,656 | ✅ **status 1**, 359,455 gas |

**Result of attempt 4** (tx `0x791837677789ae1daac481165c9d7b9145a54786e70f2318a2e61f27c85de8b9`):
- aEthweETH burned from the user: 61.67186; **weETH from `0xbdfa…` (aEthweETH) to the user: 61.67190.**
- Wallet weETH: **0 → 61.6719**. aEthweETH: 456.4827 → 394.8108.
- Max still withdrawable afterwards: **0.000997 weETH** (the margin left in attempt 4).

**Findings:**
1. **Partial exit confirmed on the fork: 61.67 weETH (13.5% of the aEthweETH position) reached the wallet**, using only
   the chain. No frontend, API, indexer, or privileged actor was involved.
2. **The rest of the position (394.81 aEthweETH) can't be withdrawn now**; anything above the limit reverts with `0x6679996d`.
3. **The limit shrinks over time** (−0.00004 weETH in 12s), while the aEthweETH balance itself grows slightly. So an
   amount that passes a simulation can fail a few seconds later. Users have to leave a margin.
4. Why there is a limit, and why it shrinks, isn't shown by the chain yet.

### Step 5: is there an on-chain link between aEthweETH and the "Variable Debt WETH" token?
**Time:** 01:40:39Z → ~01:43Z (queries ~30s, reading ~3 min).
**Knowledge used:** `debug_traceCall`, `debug_traceTransaction`, `eth_getStorageAt` (EIP-1967 slot), searching bytecode for
an address, the user's own history from step 2.
**Raw data:** `data/step5/trace_withdraw_all.json`, `data/step5/trace_debt_mint.json`.

**Check 1: what does `withdraw` read before rejecting?** Trace of `withdraw(weETH, 2²⁵⁶−1, user)` (reverts `0x6679996d`):
```
USER -> 0x8787 (0x69328dec) → logic 0x728a…03cf → DELEGATECALL 0x584c…7d8c (0x186dea44)
   STATICCALL aEthweETH            0x1da24f3e(…)
   CALL       aEthweETH            0xb18d6afd(…)
   STATICCALL variableDebtEthWETH  0x1da24f3e(user) → 5,196.9906   (balanceOf: 5,763.7603)
   STATICCALL aEthwstETH           0x1da24f3e(user) → 4,508.7622   (balanceOf: 4,515.3880)
   → revert 0x6679996d
```
`0x8787` reads the user's figure from **all three** Aave-named contracts with the same unnamed function, right before
rejecting. The values differ from `balanceOf`, so it's an internal figure, but it's an input to the decision.

**Check 2: what created the user's "Variable Debt WETH" balance?** From the user's history (step 2): 15 mints and 12 burns,
**all in txs the user sent to `0xd01607c3c5ecaba394d8be377a08590149325722`** (mints via `0xe74f7b85`, burns via `0xbcc3c255`).
Trace of the first mint (`0xb81bd692…`, block 25,080,540):
```
USER -> 0xd016 (0xe74f7b85)
  0xd016 -> 0x8787 (0xa415bcad)              → 0x8787 mints 1,400 variableDebtEthWETH to USER
  WETH 1,400: 0x4d5f…14e8 -> 0xd016
  0xd016 -> WETH withdraw(uint256)            → 1,400 ETH to 0xd016   (name from the fixed list)
  0xd016 -> USER                              → 1,400 ETH
```
**In one transaction the user received 1,400 ETH and `0x8787` minted them 1,400 of the debt-named token.**

**Check 3: do the contracts reference each other?** EIP-1967 implementation of each, then search its code for `0x8787`'s address:

| Token | Implementation | Size | Contains `0x8787…a4e2` |
|-------|----------------|------|------------------------|
| aEthweETH | `0xadc45df3…7ada` | 10,477 B | ✅ |
| aEthwstETH | `0xadc45df3…7ada` (**same logic**) | 10,477 B | ✅ |
| variableDebtEthWETH | `0xb27c52c7…e330` | 7,198 B | ✅ |

**Where the hypothesis stands:**

| Claim | Status |
|-------|--------|
| The debt-named balance is minted by `0x8787` while the user receives the same amount of ETH | ✅ shown |
| `0x8787`'s withdraw logic reads it (and the other deposit) | ✅ shown |
| It **causes** the cap on withdrawals | ⚠️ consistent, not yet shown → step 6 |

**Finding (usability):** this link was only found with call traces, bytecode searches, and following a helper contract
through the user's own history. The chain contains everything, but **a normal user couldn't realistically put it together
without expert tooling or AI assistance.**

### Step 6: does the "Variable Debt WETH" balance cause the cap? (cause-and-effect test)
**Time:** 01:48:50Z → 01:49:21Z (~30s of execution) plus reading (~3 min).
**Knowledge used:** the user's own burn path, read from their history (trace of their last burn, `data/step6/trace_debt_burn.json`):
```
USER -> 0xd016 (0xbcc3c255)  value 220 ETH; args [0x8787…a4e2, 220e18, USER]
  0xd016 -> WETH (0xd0e30db0)        220 ETH → WETH
  0xd016 -> 0x8787 (0x573ade81)      args [WETH, 220e18, 2, USER]
     → burns 219.9973 variableDebtEthWETH from USER; WETH 220 → 0x4d5f…14e8
```
**Design:** use only the user's own funds. Each action in its own block, +1s apart; after each one, binary-search the
max withdrawable weETH again.
- **Control:** a plain 0.1 ETH transfer to self.
- **Treatment:** **1 ETH** through the user's own path: `0xd016.0xbcc3c255(0x8787…a4e2, 1e18, USER)` with 1 ETH.

**Raw data:** `data/step6/causal_test.json`.

| State | Block | User ETH | Debt-named `balanceOf` | Max withdrawable weETH | Change in max |
|-------|-------|----------|------------------------|------------------------|---------------|
| Start | 26,248,201 | 1.056550 | 5,763.760349 | 0.000996647 | — |
| After control (tx `0x9330f61f…`) | 26,248,202 | 1.056547 | 5,763.760353 | 0.000993294 | **−0.000003353** |
| After treatment (tx `0xc348270c…`, status 1, 162,930 gas) | 26,248,203 | 0.056529 | **5,762.760357** | **0.952506820** | **+0.951513526** |

**Findings:**
1. **Shown: lowering the debt-named balance raises the cap.** −1.0 on that balance → **+0.95 weETH** withdrawable.
   The control changed nothing beyond time drift.
2. **Why the cap shrinks over time:** the debt-named balance **grows by itself** (+0.000004 in 1s with no action),
   and the cap shrinks with it (step 4).
3. So the step 2 hypothesis is now supported by evidence: the balance minted by `0x8787` when the user received ETH
   (step 5) **limits how much of the deposit can be withdrawn**, and it grows over time.
4. **To withdraw everything, the user has to bring back what they received** (~5,762.76, sent through the same path).
   They hold 0.06 ETH and 61.67 weETH. That's a **capital** limit, not a dependency (D1–D5): the protocol path itself
   needed no frontend, API, indexer, or privileged actor.
