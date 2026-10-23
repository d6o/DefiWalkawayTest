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
