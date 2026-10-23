# The DeFi Walkaway Test — Test Specification

**Question:** If the team, frontend, and hosted infrastructure disappear, can a user still find their position and fully exit using public artifacts alone?

## 1. Starting point

The user has their **address** (or a private key on a fork) and knows:
- the **protocol's name** (e.g. "I staked with Lido")
- the **position token's name/symbol** (e.g. "I got stETH")

They do **not** know any contract addresses or how to exit.
They have no frontend, browser history, or cached data.

Note: token names and symbols are not trustworthy on-chain (anyone can deploy a token called "stETH").
Telling the real contract apart from look-alikes is part of the test.

Because the user knows the protocol's name, **any token in their history whose `name()` mentions the protocol** is
treated as a possible position in it (e.g. "Aave Ethereum wstETH", "Aave Ethereum Variable Debt WETH").
What each one means still has to be shown from chain data.

## 2. What gets removed

Each dependency is removed **on its own**, then **all together**:

| # | Dependency | Examples |
|---|------------|----------|
| D1 | Frontend | app.protocol.xyz, IPFS-hosted UI |
| D2 | Company API | REST/GraphQL endpoints run by the team |
| D3 | Hosted indexer | The Graph subgraphs, team-run indexers |
| D4 | Privileged relayer / keeper / oracle | Withdrawal finalizers, Merkle-root publishers, solvers |
| D5 | Default RPC | The RPC hardcoded in the frontend or SDK |

## 3. What's allowed (tiers)

Results are reported for each tier, so it's clear what each exit depends on.

| Tier | Allowed |
|------|---------|
| **T0** | Your own node (or a mainnet fork) plus the chain only |
| **T1** | T0 plus artifacts in the protocol's public git repo (ABIs, deployment addresses, docs) |
| **T2** | T1 plus third-party public services (Etherscan, public RPCs, IPFS gateways) |

**Run order:** T0 first. If the T0 run is blocked by a **permission check** (D4), T1 and T2 aren't run:
tiers add information, not permissions, so the outcome can't change. If T0 is blocked for lack of information,
the higher tiers are run.

## 4. What counts as success

The user **finds every position in the protocol being tested** and **gets all the assets back to their wallet, rewards included**.
The assets are **the ones the user deposited** (e.g. weETH deposited into Aave → weETH back). Converting them further
(weETH → ETH) is another protocol's exit and isn't part of this test.

A **partial exit** (e.g. principal recovered but rewards not) is recorded as its own result, not a pass.

**Capital limits are not dependencies.** If the exit is limited by the user's own obligations (e.g. a debt that must be
repaid first), the run records:
1. the **partial exit** possible with the user's own funds, and
2. whether a **full exit** works once the experimenter provides the missing capital on the fork (disclosed, §10),
3. the **capital needed**.

That separates "the protocol can't be exited without a dependency" from "this user doesn't have the money".

**Only the protocol's own exit path counts.** Selling the position on a DEX or other secondary market
is recorded as a **fallback**, not a pass. Otherwise the test would measure market liquidity instead of
protocol dependencies. "You can only leave by selling at market" is still reported as a finding.

## 5. Result categories

| Result | Meaning |
|--------|---------|
| ✅ Exits cleanly | Works with no extra effort |
| 🟡 Harder but possible | e.g. log scans are needed instead of a subgraph |
| 🟠 Needs real work to recover | e.g. rebuilding a Merkle proof, reconstructing an ABI |
| 🔴 Blocked | Blocked until a privileged actor acts |
| ◐ Partial exit | Only part of the position comes out with the user's own funds (§4). The run records why, and whether a full exit is possible at all |

## 6. Environment

- Mainnet fork pinned to **one block for all protocols: 26,248,199** (2026-10-22 12:37:23 UTC), so results are
  directly comparable. Recorded with each run.
- Real holder addresses are impersonated to reproduce historical positions.
- All runs must be reproducible from the repo.
- **Node stand-in:** a hosted archive RPC (Alchemy, Pay As You Go) stands in for "your own node".
  - Only **standard Ethereum JSON-RPC** methods are allowed. Provider-specific APIs
    (e.g. `alchemy_getAssetTransfers`, `alchemy_getTokenBalances`) are indexers, so they're not allowed at T0.
  - Disclosure: a hosted provider answers faster than a self-run node, so measured times are **optimistic**.
  - Limit to know about: `eth_getLogs` accepts any block range if the result is under 10K logs, or any
    result size if the range is under 10K blocks. Larger searches have to be split.
- **Calls that may revert go through plain JSON-RPC.** Tools like `cast` decode revert errors by looking them up in a
  hosted signature database, which is a T2 source. At T0 that would leak names (it happened once in the Aave run, step 4).
- Fork state is **snapshotted** (`evm_snapshot`) before every state-changing step, so it can be rolled back.

## 7. Protocol selection

**Method:** the top 5 protocols by TVL on DefiLlama's Ethereum ranking
(`defillama.com/chain/ethereum`), using the site's default settings. No other filters.

**Snapshot:** 2026-10-22 — `data/selection/2026-10-22-defillama-ethereum.png`

| # | Protocol | Category (DefiLlama) | TVL |
|---|----------|----------------------|-----|
| 1 | Lido | Liquid Staking | $23.41B |
| 2 | Aave | Lending | $14.87B |
| 3 | Binance staked ETH | Liquid Staking | $8.48B |
| 4 | EigenCloud | Restaking | $6.25B |
| 5 | Spark | — | $6.09B |

## 8. Test address selection

**Method:** the **100th largest holder** of the protocol's main position token, according to
Ethplorer's top-holders API (`api.ethplorer.io/getTopTokenHolders/<token>?apiKey=freekey&limit=100`).

**Why 100th?** Because it's the deepest Ethplorer will give on the free plan.

**Rules:**
- If the 100th holder is a **contract**, move up the list (99th, 98th, ...) to the nearest plain wallet (EOA).
  Wallets with an EIP-7702 delegation count as plain wallets.
- **Snapshot:** save the full holder list with the date and block in `data/selection/`.
- If a protocol has **no position token**, define a fallback when we get to it.
- If a protocol has **several position tokens** (e.g. one per deposited asset), the main one is the receipt token of the
  **largest asset in DefiLlama's token breakdown** (default settings) for the protocol's **largest product on Ethereum**,
  using the last DefiLlama data point before the fork block. Same source and settings as the protocol selection (§7).
  - If the largest asset has **no receipt token** (e.g. collateral held without a token), use the largest asset that has one.
  - If that asset has **many receipt tokens** (e.g. one per vault), use the one with the largest on-chain `totalAssets()`
    at the fork block, found by scanning standard ERC-4626 `Deposit` events (no protocol-specific addresses needed).

Picking the address is experiment setup. The walkaway test itself starts after this, from the user's point of view.

| Protocol | Token | Address | Balance | Snapshot |
|----------|-------|---------|---------|----------|
| Lido | stETH | `0xde804e46f67ebeecbe4c0a54efe33143cb7ab9e2` | 5,084 stETH | `data/selection/2026-10-22-ethplorer-steth-top100.json` (~block 26,248,199) |
| Binance staked ETH | wBETH (`0xa2E3356610840701BDf5611a53974510Ae27E2e1`), single product/asset on Ethereum | `0x066eb6929f18a72093c5afc9eba6dd476df876bc` | 16.96 wBETH | `data/selection/2026-10-22-ethplorer-wbeth-top100.json`; `data/selection/2026-10-22-defillama-binance-staked-eth.json` |
| Morpho (Morpho Blue) | gtusdcp "Gauntlet USDC Prime" (`0x8c106eedad96553e64287a5a6839c3cc78afa3d0`). Largest product Morpho Blue ($5.05B). The largest assets in DefiLlama's breakdown are **collateral** (cbBTC, wstETH, kBTC), which has **no receipt token**; the largest asset **with** one is the loan asset USDC ($0.99B borrowed + $0.14B). Many USDC vaults exist; picked the largest by on-chain `totalAssets()` at the fork block (`data/selection/2026-10-22-morpho-usdc-vaults-onchain.json`) | `0x1c424df78d4fcc3b9635be62054fdab3f9b38a49` | 123,530 gtusdcp | `data/selection/2026-10-22-ethplorer-gtusdcp-top100.json`; `data/selection/2026-10-22-defillama-morpho-blue.json` |
| Sky (Sky Lending) | sUSDS "Savings USDS" (`0xa3931d71877c0e7a3148cb7eb4463524fec27fbd`). Largest product Sky Lending ($5.60B, CDP). DefiLlama's largest assets (USDC 73%, WETH 25%) are reserves/collateral with **no receipt token**; the largest Sky-named ERC-4626 vault by on-chain supply is Savings USDS (4.34B shares; `data/selection/2026-10-22-sky-vaults-onchain.json`) | `0x03ba33a6be869d02edece6db89624e8252d02f96` (**#98**: #100 and #99 are contracts) | 1,844,122 sUSDS | `data/selection/2026-10-22-ethplorer-susds-top100.json`; `data/selection/2026-10-22-defillama-sky-lending.json` |
| ether.fi (ether.fi Stake) | eETH "ether.fi ETH" (`0x35fa164735182de50811e8e2e824cfb9b6118ac2`). Largest product ether.fi Stake ($4.56B), asset ETH (99.6%). eETH is the base receipt (2.27M supply); 97% of it is held by the weETH wrapper, but as with Lido (stETH, not wstETH) the base receipt is the main token. Addresses from the Aave run's on-chain history (`name()` = "ether.fi ETH" / "Wrapped eETH") | `0xd26d430c382059806dfd22d5c30227fa89f1aacf` | 43.64 eETH | `data/selection/2026-10-22-ethplorer-eeth-top100.json`; `data/selection/2026-10-22-defillama-etherfi-stake.json` |
| Spark (SparkLend) | spwstETH (`0x12B54025C112Aa61fAce2CDB7118740875A566E9`); largest product SparkLend ($5.10B), largest asset wstETH ($3.55B, 67.9%) | `0x50e835c1088dd06747312c06ac0839ecc773cb42` (**#99**: #100 `0xbb73…17d6` is a contract) | 403.29 spwstETH | `data/selection/2026-10-22-ethplorer-spwsteth-top100.json`; `data/selection/2026-10-22-defillama-sparklend.json` |
| Aave V3 | aEthweETH (`0xBdfa7b7893081B35Fb54027489e2Bc7A38275129`) | `0x462a336dcac6eaf544106266914caa5a18b831d0` | 456.48 aEthweETH | `data/selection/2026-10-22-ethplorer-aethweeth-top100.json`; product/token choice: `data/selection/2026-10-22-defillama-aave-v3.json` |

## 9. Naming functions at T0

At T0 there's no ABI, no docs, and no signature database (4byte.directory, openchain, Etherscan are hosted services).
Contracts only expose 4-byte **selectors**. To name them, we hash a **fixed list of candidate signatures** and look for matches.

**Verbs (fixed, 20):**
> withdraw, redeem, unstake, claim, exit, burn, unwrap, release, collect, harvest,
> close, repay, remove, cancel, unlock, leave, deposit, stake, wrap, mint

**Argument lists:** every combination of 0–3 arguments from `uint256`, `address`, `uint256[]`, `bool`, `bytes` (156 lists).

**Result:** 20 × 156 = **3,120 signatures**, generated by `scripts/wordlist.py` (pure Python, no external services)
into `data/methodology/signatures.json`
(SHA-256 `156d202eab02631a2032eae5b2833fed799c7a1ea85a75532fd9e9cf3598b2e9`).

**Rules:**
- The list was **fixed on 2026-10-22, before matching it against any protocol**. It's used unchanged for all protocols.
- The ERC standards repo is **not** used: fetching it from GitHub would add a hosted dependency at T0.
- **Basic knowledge** any Ethereum developer knows by heart is allowed without lookup: ERC-20/721/1155 core functions
  and events (`Transfer`, `name()`, `symbol()`, `balanceOf()`, ...), and standard proxy slots (EIP-1967).
- Selectors that don't match stay **unnamed**. That's a finding. Their purpose is then worked out from behavior
  (what other users call, and which calls send assets back).
- Disclosure: we wrote the verb list, and we know these protocols. Fixing it in advance limits the bias; it doesn't remove it.

## 10. Evidence rules

Learned during the Lido and Aave runs, applied to every run from here on.

**Facts vs. hypotheses**
- Every claim in a run log is either **shown by chain data** (with the query, tx, or trace that shows it) or marked as a
  **hypothesis**. Names, symbols, and outside knowledge are never evidence on their own.
- When an interpretation turns out to be stated too strongly, the run log keeps a **correction note**. No silent edits.
- **Contamination notes:** when an operator recognizes an address, selector, or error from memory or from a leaked
  source, it's disclosed in the log and not used.

**Learning from other users (behavior)**
- Window: the **7 days before the fork block** (blocks 26,197,800 → 26,248,199).
- Read **every** transaction that moved the position token in the window; group by what the sender called (`tx.to` + selector).
- Trace **3 examples per group** (first / middle / last by block). If the examples disagree, trace more from that group.
- Smart-contract wallets hide the real call in the outer transaction; only traces show it.

**Cause and effect**
- When something is suspected to cause a block (e.g. a balance limiting withdrawals), it's tested on the fork with a
  **control** and a **treatment** from the same state: change only the suspected cause, and measure again.

**Experimenter interventions** (only on the fork, always disclosed in the run log)
- Impersonating the test address (all runs).
- Replaying a **real historical transaction** from its **original sender** on a fork before it (Lido step 5).
- **Providing capital** to the test address (Aave step 7).
- Moving the fork's clock (`evm_increaseTime`, `evm_setNextBlockTimestamp`).
- **Simulate before sending** (`eth_call`). Values that drift with time (e.g. a withdrawal cap) need a margin.

---

## Open questions (to decide later)

- How is **recovery time** reported? Each run records raw timings per step (queries/execution vs. analysis);
  how to turn them into one number is still open.
- **Capital exposed**, as used so far: if the exit is blocked by D4, the position token's `totalSupply()` at the fork
  block (Lido); if no D4 dependency is found, none (Aave). The capital a test user needs for a full exit is reported
  separately (§4). To be confirmed once more protocols are done.
- **EigenCloud has no position token**, so §8 can't pick its test address. Options discussed (2026-10-23), not decided:
  A. rank the largest asset's depositors from the protocol's own on-chain records (e.g. native-restaking pod owners by
  recorded amount at the fork block) and take the 100th; B. the same for stETH deposits (8.5% of TVL);
  C. a third-party ranking (e.g. Dune). Snapshot: `data/selection/2026-10-22-defillama-eigencloud.json`.
- Save the DefiLlama **.csv** export alongside the screenshot.

**Resolved:** which product/version to test when DefiLlama groups several under one name → the protocol's largest
product on Ethereum (§8).
