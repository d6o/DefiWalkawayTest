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
