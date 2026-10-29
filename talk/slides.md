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
