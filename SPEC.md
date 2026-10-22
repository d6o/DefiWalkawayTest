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

## 4. What counts as success

The user **finds every position in the protocol being tested** and **gets all the assets back to their wallet, rewards included**.

A **partial exit** (e.g. principal recovered but rewards not) is recorded as its own result, not a pass.

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

## 6. Environment

- Mainnet fork pinned to a specific block (recorded with each run).
- Real holder addresses are impersonated to reproduce historical positions.
- All runs must be reproducible from the repo.
- **Node stand-in:** a hosted archive RPC (Alchemy, Pay As You Go) stands in for "your own node".
  - Only **standard Ethereum JSON-RPC** methods are allowed. Provider-specific APIs
    (e.g. `alchemy_getAssetTransfers`, `alchemy_getTokenBalances`) are indexers, so they're not allowed at T0.
  - Disclosure: a hosted provider answers faster than a self-run node, so measured times are **optimistic**.
  - Limit to know about: `eth_getLogs` accepts any block range if the result is under 10K logs, or any
    result size if the range is under 10K blocks. Larger searches have to be split.

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

Picking the address is experiment setup. The walkaway test itself starts after this, from the user's point of view.

| Protocol | Token | Address | Balance | Snapshot |
|----------|-------|---------|---------|----------|
| Lido | stETH | `0xde804e46f67ebeecbe4c0a54efe33143cb7ab9e2` | 5,084 stETH | `data/selection/2026-10-22-ethplorer-steth-top100.json` (~block 26,248,199) |

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

---

## Open questions (to decide later)

- How is **recovery time** measured? (scripted agent, human, LLM agent?)
- How is **capital exposed** calculated? (value behind 🟠/🔴 dependencies at the fork block?)
- DefiLlama groups versions/products under one name (e.g. Aave V2 + V3, SparkLend + Spark Savings).
  Which products/versions do we test for each protocol? → next step
- Save the DefiLlama **.csv** export alongside the screenshot.
