# The DeFi Walkaway Test — Slides

Target: 15–20 minutes. Each slide: what's on it, speaker notes, time.
Source for every number: [`RESULTS.md`](../RESULTS.md) and the run logs in `runs/`.

---

## Slide 1 — Title
*(Diego: title and name.)*

**Time:** 0:30

---

## Slide 2 — Chapter: "The problem"

**On the slide:** The problem

**Time:** 0:05

---

## Slide 3 — The thought experiment

**On the slide:**
> **Tomorrow, the team disappears.**
> The website goes dark. The API stops answering. The indexer is gone.
> **The contracts are still there.**
>
> **Can you get your money out?**

**Speaker notes:**
"We say DeFi is non-custodial because the contracts are immutable and live forever. But a user doesn't interact with
contracts; they interact with a website, an API, an indexer. So imagine they all vanish tomorrow. The contracts are
still on-chain. Can you still get your money out?"

**Time:** 1:00

---

## Slide 4 — "I tested it"

**On the slide:**
> **I tested it.**
>
> *(logos of the 16 protocols)*
> Lido · Aave · Spark · Morpho · Sky · ether.fi · Ethena · Maple · Uniswap · Rocket Pool · Compound · Curve ·
> Falcon Finance · Kelp · Fluid · Pendle

**Speaker notes:**
"I didn't want to guess, so I tested it on 16 of the largest DeFi protocols on Ethereum, chosen by TVL. Take a second:
which of these do you think you could still leave with nothing but a node? Keep your guess in mind; we'll come back to it."

**Time:** 0:45

---

## Slide 5 — Chapter: "The test"

**On the slide:** The test

**Time:** 0:05

---

## Slide 6 — The rules

**On the slide:**
> **The rules**
>
> **You have:** your address and a node.
>
> **You don't have:** the website · the team's API · an indexer · a block explorer · docs or ABIs
>
> **The question:** can you find your position and get your assets back, **without anyone's help or permission?**

**Speaker notes:**
"The rules are simple. You have your address and your own node: raw chain data. You don't have the website, the
team's API, an indexer, Etherscan, or even the docs. And the exit has to work without anyone else's help or permission.
If an exit needs a keeper, an operator, or a signer to act first, it doesn't count."

*(Maps to SPEC §2–§3: all of D1–D5 removed, tier T0. "Without anyone's permission" = D4, phrased as a
requirement rather than a removal: privileged actors stay on-chain; the test is whether the exit needs them.)*

**Time:** 1:00

---

## Slide 7 — How a run works

**On the slide** (two columns):

> **Who**
> - Top Ethereum protocols by TVL (DefiLlama)
> - 100th-largest holder of the main token
>   - Per Ethplorer's top-holders list
>   - Nearest plain wallet if it's a contract
> - Mainnet fork, same block for all

> **How**
> 1. Find the position
> 2. Find the protocol's contracts
> 3. Learn the exit from other users' transactions
> 4. Try it on the fork, as that wallet
> 5. Prove what blocks it (change one thing, compare)

**Speaker notes:**
"For each protocol, I took the 100th-largest holder of its main token: a real address, not a whale and not dust. Then I
forked mainnet at the same block for every protocol and played that user. First, find your position with nothing but
logs. Then find the protocol's contracts. Since you have no docs and can't even read function names, you learn the exit
by watching what other users do on-chain: which contract they call, and what comes back. Then you try it yourself on the
fork. And when something blocks you, you prove why: same state, change one thing, compare. For example, the same
transaction sent from a different address. Everything comes from the chain: no docs, no memory, and every claim is in
the open repo."

*(If asked "why the 100th?": it's the deepest Ethplorer's free API goes, and it gives a real user rather than an
exchange, a whale, or dust. For Uniswap, NFT positions are ranked by count, not value.)*

**Time:** 1:30

---

## Final deck (2026-10-30)

The deck as presented is saved as [`deck.pdf`](deck.pdf) (29 slides; earlier versions are in git history). Slides 1–7
follow the drafts above (with Diego's wording); the rest:

| # | Slide | Content |
|---|-------|---------|
| 8 | Lido (chapter) | |
| 9 | Meet the user | `0xde80…b9e2`, 5,084 stETH, plain wallet, deposited 5,000 ETH in Feb 2026; block 26,248,199; a developer who knows Ethereum standards, no protocol knowledge |
| 10–12 | Step 1: gather information | balance, nonce, code; `eth_getLogs` transfers to/from the address; `name`/`symbol`/`decimals`/`balanceOf`; 78 contracts, address poisoning; the user's own 5,000 ETH deposit identifies the real stETH |
| 13 | Step 1: the contract | `debug_traceCall` → proxy; logic `0x028271e3…cdb0`; selectors: 86 candidates, 9 ERC-20, no fixed-list match |
| 14–19 | Step 2: watch others | 7-day stETH flows (stETH: 1,352 mints, 0 burns); `0x889e…f9b1` (most senders); `0xacf41e4d` → numbered NFT; all events of `0x889e`; `0xe3afe0a3` burns the NFT and pays ETH |
| 20–21 | Step 3: try it, as that user | example flow (1 stETH; the full run in the repo hands in all 5,084 as claims 139,412–139,417); cashing the claim fails (`0x4ae50228`) |
| 22–23 | Step 4: why it fails | batch events (`0x197874c7`, `0x6bd5c950`) carry a claim-ID range; one batch a day ~12:22 UTC; the last covered up to #139,310, ours is #139,412 |
| 24 | Step 4: prove it | at block 26,248,128 (one block before the 10-22 batch): cash #139,267 ❌; random address sends the batch ❌ (`0x1db3b859`); usual sender ✅; cash after the batch ✅. Screenshot: `cast call … --from 0x1234…7890 --block 26248128` (plain `eth_call` on the archive node). The full fork replay that paid 1:1 is step 5 of the Lido run |
| 25 | Blocked | "So close, yet so far": privileged batch senders; ~1 hour of expert work to get here |
| 26 | Full results | Blocked: Lido, ether.fi, Ethena, Maple, Falcon Finance, Kelp · Partial exit: Aave V3\*, Spark\* · Hard but possible: Aave V3, Spark, Uniswap V3, Curve, Pendle · Full exit: Morpho, Sky, Rocket Pool, Compound, Fluid · repo link. \* said aloud: partial with your own funds; a full exit is possible but very hard to discover without assistance |
| 27 | Recommendations | permissionless fallback for every privileged step; standard exit functions that work; one call, no traps; run the walkaway test before launch |
| 28 | For users | who has to act before I can leave; liquidity on hand, not TVL; keep your deposit tx; beware scam tokens; an archive node with tracing |
| 29 | Thank you | |
