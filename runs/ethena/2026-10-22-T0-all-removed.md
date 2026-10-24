# Run: Ethena (USDe) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Ethena USDe, Ethereum |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xa29e963992597b21bcdcaa969d571984869c4ff5` (#99: #100 is a contract; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`); caller-test fork at 26,247,942 |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-24T00:20:46Z |

## Ground rules

- We play a user who has their **address** and knows they hold **USDe** from **Ethena** (SPEC §1). They don't know any
  contract addresses or how to exit.
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.
  Revert texts in the standard `Error(string)` format are read directly (plain ABI decoding, no outside database).

**Contamination disclosure:** both operators know Ethena. The USDe address came from the chain (common `asset()` of all
USDe-named ERC-4626 vaults). The redemption contract, its function, the role check, and the 20 role holders were all
found from transactions and fork tests. The role is only a hash (`0x44ac…77cc`); its name isn't recoverable at T0 and
isn't given from memory.

## Setup notes (selection, SPEC §8)

- DefiLlama: Ethena USDe is the largest product ($4.65B); its breakdown is 98% USDe itself → position token **USDe**
  (`0x4c9e…68b3`, totalSupply **4,655,090,585** at the fork block).
- USDe's address: found as the common `asset()` of every USDe-named ERC-4626 vault in a 24h `Deposit` scan
  (largest: "Staked USDe", 942M shares). Snapshot: `data/selection/2026-10-22-usde-vaults-onchain.json`.
- #100 is a contract → **#99**, an EOA with **122,478 txs sent**: **191,358.70 USDe**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 00:20:46Z (~1s).

| Query | Result |
|-------|--------|
| ETH balance | 43.07 ETH |
| Nonce (txs sent) | **122,478** (a very busy, likely automated wallet) |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "USDe"
**Time:** 00:20:47Z → 00:39:16Z (log scan ~14 min; the first metadata pass timed out; `scripts/discover.py` was
improved to batch reads and reuse the saved logs, then took 226s).
**Raw data:** `data/step2/raw_logs.json.gz` (147 MB uncompressed: **102,689 transfers in, 104,126 out, 125 ERC-1155**),
`contracts.json`, `contracts.md` (**2,102 contracts**).

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0x4c9edd5852cd905f086c759e8383e09bff1e68b3` | USDe | **USDe** (exact) | 1 | 0 | **191,358.70** |
| `0x57e114b691db790c35207b2e685d4a43181e6061` | ENA | ENA | 40 | 56 | 143,013.97 |

Busiest contracts in the history: `0xdac17f95…` (87,808 logs), `0xa0b86991…` (77,748).

**How the USDe arrived:** one plain ERC-20 `transfer()` from EOA `0xc333…f771` at block 26,092,560. **The user never
minted or redeemed USDe themselves.**

**Finding (cost of T0 discovery):** for a busy wallet, the T0 scan took ~18 minutes and 147 MB of logs to find
**one** relevant token among 2,102.

### Step 3a: is USDe a proxy, and can its functions be named?
**Time:** 00:39:48Z (~1s). **Raw data:** `data/step3/`.
- USDe: **7,567 bytes, not a proxy** (no `DELEGATECALL`, EIP-1967 slot empty). 25 functions; basic 9; **fixed list 2**:
  `mint(address,uint256)`, `burn(uint256)`; 14 unnamed.

### Step 3b: who creates and destroys USDe, and how?
**Time:** 00:40:01Z → ~00:41Z. **Window:** blocks 26,197,800 → 26,248,199. **Raw data:** `data/step3b/`.

**Flows:** 18,168 transfers in 10,115 txs, 1,805 recipients. **Mints: 38 (73.68M USDe, 19 recipients). Burns: 165
(158.15M USDe, 30 holders).**

**Every mint and every burn went through one contract:**

| Kind | tx.to | Selector | Txs | **Tx senders** | Token holders | Amount |
|------|-------|----------|-----|----------------|---------------|--------|
| Burn | **`0xe3490297a08d6fc8da46edb7b6142e4f461b62d3`** | `0x75c890dc` (unnamed) | 165 | **20** | 30 | 158.15M |
| Mint | `0xe349…62d3` | `0x96eea750` (unnamed) | 38 | 16 | 19 | 73.68M |

**Traces of 3 burns (first / middle / last):** 19-word calldata. Words 6 and 7 are addresses; word 8 a token; words 9
and 10 amounts; word 4 a timestamp; plus extra data at the end.

| Tx | Tx sender | USDe burned from (word 6) | Collateral to (word 7) | Collateral (word 8) |
|----|-----------|---------------------------|------------------------|---------------------|
| `0xf4d4302d…` | `0x9b68…` | `0xb89a…` 851,590.00 | `0xdf91…` | 850,733.77 USDC (`0xa0b8…`, named in the user's history) |
| `0xdb3793b7…` | `0x6fd5…` | `0x8099…` 103,166.56 | `0x8099…` | token `0xe343…` |
| `0x67c3cf25…` | `0x950c…` | `0x8d3b…` 8,019.67 | `0x9374…` | 8,011.42 USDT (`0xdac1…`) |

**Finding:** the tx sender is **never** the USDe holder. Each redemption carries the holder, a recipient, a
collateral token, amounts, an expiry, and extra data: an order authorized by the holder and **submitted by someone else**.

### Step 4: what can our user do alone?
**Time:** 00:42:23Z → 00:42:26Z. **Raw data:** `data/step4/step4.json`.

| Attempt | Result |
|---------|--------|
| Submit a redemption order for their own USDe (observed layout, user as holder and recipient) | ❌ `Error(string)`: "AccessControl: account 0xa29e…4ff5 is missing role 0x44ac9762…77cc" |
| `burn(uint256)` (fixed list), 1 USDe, on a snapshot | ✅ but **USDe destroyed, nothing returned** (rolled back) |

Where holders send USDe in practice (top contract recipients by distinct senders): `0x0000…8a90` (177 senders),
the "Staked USDe" vault `0x9d39…3497` (69; still USDe exposure), and trading routers (`0x0cef…`, `0x8f10…`, …): the
**fallback** (SPEC §4).

### Step 5: who can submit a redemption? (caller test)
**Time:** ~00:41Z → ~00:42Z. Fork at **26,247,942**, one block before the last redemption in the window
(`0x67c3cf25…`). Same calldata, same state, only the caller changes. **Raw data:** `data/step5/caller_test.json`.

| Submitted by | Result |
|--------------|--------|
| Its original sender `0x950c…` | ✅ |
| **The USDe holder itself** (`0x8d3b…`) | ❌ "AccessControl: account 0x8d3b… is missing role 0x44ac…77cc" |
| The collateral recipient (`0x9374…`) | ❌ same |
| A random address | ❌ same |
| **Each of the other 19 redemption senders of the week** | ✅ **19 / 19** |

**Findings:**
1. **Redemption is gated by a role.** Only addresses holding role `0x44ac…77cc` can submit a redemption, even one the
   holder authorized. The holder can't submit it themselves.
2. **20 addresses held that role in practice** (all 20 senders this week; each can submit any of the observed orders).
3. Not shown: whether the holder must also be approved to *create* an order (orders are signed off-chain; on a fork we
   can't sign for the user). It doesn't matter for the result: without a role holder, no order gets submitted.

---

## Result: Ethena (USDe), T0 — 🔴 Blocked

| Scenario | Result | Why |
|----------|--------|-----|
| **D4 removed** (the role holders stop submitting) | 🔴 **Blocked** | Steps 4–5: redemption requires role `0x44ac…77cc`; the holder can't submit their own order |
| D4 present | Redemption possible **only through a role holder** | Observed: 165 redemptions by 20 role holders for 30 holders |
| Each of D1, D2, D3, D5 removed individually | Same | The run never used them |

**Unlike Lido and ether.fi**, there's no queue and no claim: the protocol's exit itself (USDe → collateral) can only be
**submitted** by a small set of permissioned addresses. For a regular holder, the practical exit is selling (fallback).

**Capital exposed to D4 (fork block):** **4,655,090,585 USDe** (`totalSupply()`): every USDe needs a role holder to be
redeemed through the protocol.

**Why T1/T2 aren't run (SPEC §3):** blocked by a permission check.

### Required infrastructure (this run)

| Capability | Used in |
|------------|---------|
| `eth_getLogs` over all history (**206,815 logs** for this address) | 2, 3b |
| `eth_getTransactionByHash` (batched) | 2, 3b |
| `eth_call` (batched, 2,102 × 4), with chosen `from` | 2, 3a, 4, 5 |
| `debug_traceTransaction` | 3b |
| Forks at two blocks, impersonation, snapshot/revert | 4, 5 |

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract (2,102) | ~18 min (incl. a timed-out first pass) | ~3 min |
| 3a | Selectors | ~1s | ~1 min |
| 3b | Flows (18,168 logs), mint/burn grouping, 3 traces | ~1 min | ~4 min |
| 4 | User's own attempts | ~3s | ~1 min |
| 5 | Caller test (4 + 19 callers) | ~30s | ~2 min |
| **Total** | | **~20 min** | **~11 min** |

Wall clock: 00:20:46Z → ~00:45Z (24 min), dominated by the discovery scan.
