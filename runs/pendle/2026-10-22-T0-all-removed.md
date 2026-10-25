# Run: Pendle (V2, PT-reUSD-10DEC2026) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Pendle V2, Ethereum; PT-reUSD-10DEC2026 |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xc1de2b10763e101f675e939c82f907a74edcb98e` (#99: #100 is a contract; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`), with clock moved forward in step 4 |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-25T14:33:02Z |

**Ground rules and contamination:** as in every run. Pendle's token names (PT/YT/SY) were read from the chain. None of the
exit functions is nameable with the fixed list; all were learned from other users' traces. **Corrections in this run:**
(1) the position was first misread as dust (6-decimal token divided by 10¹⁸); (2) a first probe measured call success
instead of payout (see step 4); (3) two attempts at the last step used a wrong call shape. All are logged below.

## Setup notes (selection, SPEC §8)

- DefiLlama: Pendle V2 ($0.80B); largest asset **reUSD (34%)**. Pendle tokens containing "reUSD" minted in the last 24h:
  **PT reUSD 10DEC2026 (271.1M)**, YT reUSD 10DEC2026 (271.1M, paired), SY reUSD (251.5M) → PT (largest; assumed worth more per
  unit than YT). `data/selection/2026-10-22-pendle-reusd-tokens-onchain.json`.
- #100 is a contract → **#99**, an EOA (nonce 1,161): **103,889.86 PT** (6 decimals).

## Steps

### Step 1–2: account facts; every token contract
ETH 0.081; nonce 1,161; plain EOA. 236 contracts. **PT-reUSD-10DEC2026: 103,889.856165**, bought through the user's own txs to
`0x8888…f946` (`0xc81f847a`) from `0x1328…` (a market). Other "PT …" tokens in the history (USD3, reUSDe, siUSD) don't mention
the protocol in their names, so they're outside this test (SPEC §1). **No YT** in the user's history.

### Step 3a: PT contract
5,858 bytes, **not a proxy**; 19 functions; basic 9; **fixed list 0**.

### Step 3b: how PT is destroyed (7 days)
**Raw data:** `data/step3b/`. 2,432 transfers; 604 mints (19.04M); **33 burns (0.36M), all inside `0xa8bd…63d7` = the YT
token itself**, via router `0x8888…` (several functions).

Traces (2 router txs): PT **and an equal amount of YT** are sent to the YT contract; then **YT `0xbcb7ea5d(receiver)`** (or batch
`0xb0d88981`) burns both and sends **SY** to the receiver; then **SY `0x769f8e5d(receiver, amount, token out, min, 1)`** burns SY
(held by the SY contract) and sends the underlying token `0x5086…0c72` ("reUSD").

### Step 4: what can a PT-only holder do, and when?
**Raw data:** `data/step4/step4.json`.

**4a. First attempt (wrong measurement, kept on record):** probing "does redeem succeed?" returned OK at every date: the call
**succeeds even when it pays nothing**. Done for real, the user's PT went into the YT contract and **0 SY** came back. Fork restarted.

**4b. Probing the payout** (send PT to the YT contract, then YT `0xbcb7ea5d(user)`, on a snapshot at each date):

| Date | SY paid for 103,889.86 PT |
|------|---------------------------|
| Fork time (2026-10-22) … 2026-12-03 (weekly) | **0** |
| **2026-12-09 (day 48)** | **0** |
| **2026-12-10 (day 49)** and every later probe to 2027-01-14 | **93,709.36** |

**Redeeming PT alone pays nothing until 10 Dec 2026 (the date in its name), then pays in full.** No other actor is involved.

**4c. Real exit at 2026-12-10:**

| # | Action | Result |
|---|--------|--------|
| 1 | `transfer(PT → YT contract)` | ✅ |
| 2 | YT `0xbcb7ea5d(user)` | ✅ **93,709.364514 SY** |
| 3 | SY `0x769f8e5d(user, amount, reUSD, 0)` (4 args, without sending SY first) | ❌ reverted, no data |
| 4 | `transfer(SY → SY contract)`, then the 4-arg call | ❌ reverted (SY now sitting in the SY contract) |
| 5 | SY `0x769f8e5d(user, amount, reUSD, 0, **1**)` (5th arg as in the traces) | ✅ **93,709.364514 reUSD** |

**Final:** PT 0, SY 0, **reUSD 93,709.36** in the wallet.

---

## Result: Pendle (PT-reUSD-10DEC2026), T0 — 🟡 Harder but possible (time-locked until maturity)

| Scenario | Result | Why |
|----------|--------|-----|
| D1–D5 removed, **at the fork date** | No protocol exit for PT alone **until 10 Dec 2026** (49 days) | Redeem pays 0 before maturity; it needs the matching YT, which the user doesn't hold |
| D1–D5 removed, **from 10 Dec 2026** | 🟡 **Full exit, holder alone** | Steps 4b–4c; unnamed functions, learned from traces |
| D4 | **Not needed** | Only time |

**What's new in this run: a time lock, not a permission.** Nobody can block the exit, but nobody can speed it up either
(before maturity, the PT holder's options are buying matching YT or selling PT in a market: a fallback, SPEC §4).

**Traps a frontend/router normally hides** (a T0 user is very exposed to them):
1. Redeeming PT alone before maturity **succeeds and pays 0**, leaving the PT in the YT contract.
2. Both redemption steps are "send tokens to the contract, then call": a plain wallet needs **two transactions**, and in
   between the tokens sit in a contract. Whether someone else could claim them in that window **wasn't tested**.
3. The last step needs an exact 5-argument call; a wrong call leaves the SY stuck until the right one is made.

**Capital exposed to D4:** none found. **Why T1/T2 aren't run:** T0 completed (after the time lock).

### Timings (raw)
Queries/execution ~4 min (incl. the restart); analysis ~15 min; wall clock 14:33:02Z → ~14:45Z.
