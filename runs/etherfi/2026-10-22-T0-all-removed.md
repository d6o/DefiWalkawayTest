# Run: ether.fi (eETH) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | ether.fi Stake, Ethereum; eETH |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xd26d430c382059806dfd22d5c30227fa89f1aacf` (100th holder; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`); proof forks at 26,247,023 and 26,246,927 |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-23T13:33:05Z |

## Ground rules

- We play a user who has their **address** and knows they staked ETH with **ether.fi** and got **eETH** (SPEC §1).
  They don't know any contract addresses or how to exit.
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators know ether.fi. The eETH / weETH addresses for setup came from the Aave run's
on-chain history (`name()` = "ether.fi ETH" / "Wrapped eETH"), not from memory. The Lido run (a similar claims design)
made a queue-and-batch design an expected **hypothesis**; every part below is shown from ether.fi's own data.

## Setup notes (selection, SPEC §8)

- DefiLlama: ether.fi Stake is the largest product ($4.56B), asset ETH (99.6%). Receipt token: **eETH** `0x35fa…8ac2`
  (totalSupply 2,267,689.80 at the fork block); **97%** of it sits in the weETH wrapper (2,195,119 eETH). As with Lido
  (stETH rather than wstETH), the base receipt is the main token.
- 100th holder: an EOA (nonce 4), **43.64 eETH**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 13:33:05Z (~1s).

| Query | Result |
|-------|--------|
| ETH balance | **0.00057 ETH** (not enough for most transactions) |
| Nonce (txs sent) | 4 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "eETH"
**Time:** 13:33:05Z → 13:34:02Z (57s) plus reading (~2 min). **Raw data:** `data/step2/` (all 74 contracts).

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0x35fa164735182de50811e8e2e824cfb9b6118ac2` | ether.fi ETH | **eETH** (exact) | 1 | 0 | **43.6430** |
| `0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee` | Wrapped eETH | weETH (partial) | 1 | 0 | 39.3308 |
| `0xf0bb20865277abd641a307ece5ee04e79073416c` | Ether.Fi Liquid ETH | liquidETH | 1 | 0 | 9.9823 |
| ~65 others | spam: stETH/ETH look-alike airdrops, "claim rewards" NFTs (≈50 ERC-1155) | | | | |

**How the eETH arrived:** the user's own tx to **`0x308861a430be4cce5502d0a12724771fc6daf216`**, selector `0xf340fa01`,
sending **42.128 ETH**; 42.128 eETH minted to the user (block 22,518,094). The balance has grown to 43.64 since.

**Note:** the user also holds weETH (39.33) and liquidETH (9.98). This run tests **eETH** (SPEC §8). weETH can be turned
into eETH (step 3b); liquidETH is a different product (Ether.Fi Liquid) and outside this test.

### Step 3a: proxies and function names
**Time:** 13:34:16Z → 13:34:17Z. **Raw data:** `data/step3/`.

| Contract | Proxy → logic | Functions | Fixed list names |
|----------|---------------|-----------|------------------|
| eETH `0x35fa…8ac2` | 845 B, EIP-1967 → `0xd190…0527` (14,897 B) | 45 | **0** |
| Deposit contract `0x3088…f216` (from the user's own deposit) | 845 B, EIP-1967 → `0x17a1…4a45` (22,607 B) | 68 | **5**: `deposit()`, `deposit(address)` (= the user's own `0xf340fa01`), `deposit(address,address)`, `withdraw(uint256,uint256)`, `withdraw(address,uint256)` |

### Step 3b: where does eETH go, and what do holders call?
**Time:** 13:34:32Z → 13:35:59Z (~1.5 min of queries) plus reading (~4 min). **Raw data:** `data/step3b/`.
**Window:** blocks 26,197,800 → 26,248,199.

**Flows:** 1,922 transfers in 971 txs; 398 mints (12,999 eETH, 31 recipients); **229 burns (26,605 eETH) by only 2 addresses**.
Top contract recipient by senders: **`0x7d5706f6ef3f89b3951e23e557cdfbc3239d4e2c`** (87 senders, 25,879 eETH).

| tx.to | Selector | Txs | Senders | What it does (traces, 3 each) |
|-------|----------|-----|---------|-------------------------------|
| deposit contract `0x3088…f216` | `0x397a1b28` (unnamed) | 92 | 83 | words [sender, amount]: **eETH sender → `0x7d57…`; a new ERC-721 minted to the sender by `0x7d57…`** (ids 83,559 → 83,766). **No ETH back.** |
| weETH `0xcd5f…b7ee` | `0xde0e9a3e` (unnamed) | 81 | 77 | weETH burned from sender; eETH from the weETH contract → sender (~1.106 eETH per weETH) |

### Step 3c: everything the claims contract `0x7d57…` recorded
**Time:** 13:36:07Z → ~13:38Z. **Raw data:** `data/step3c/` (`events.json`, `burn_traces.json`, traces).

- **215 NFT mints** (ids 83,554 → 83,768) and **223 burns** (ids 83,532 → 83,756); 8 transfers between addresses.
- Event `0xe8c5062a` (215×, one per request): topic1 = **NFT id**, data = [eETH amount, a second unit, an address-like value].
- Event `0x31712d80` (223×, one per burn): topic1 = NFT id, data = [amount, second unit, …].
- **Claims are burned in ~2 days:** for the 201 claims minted and burned in the window, wait **min 7.0h, median 14.2h, max 56.1h**.
  The highest burned id (83,756) is below the highest minted (83,768).

**Who burns the claims (traces):**

| Call on `0x7d57…` | Txs | What happens |
|-------------------|-----|--------------|
| `0xb13acedd(id)` | 9 | The **NFT owner** calls it with their claim id; NFT burned; **ETH from `0x7d57…` → owner** |
| `0x24fccdcf(ids[])` | 21 | **A non-owner** passes a list of ids; each NFT burned and **ETH sent to each owner** (e.g. 6 claims, one receiving 35.07 ETH) |

**Finding:** the exit is a **two-step design**: hand in eETH → claim NFT → later, the claim is burned and ETH paid
(by the owner with `0xb13acedd(id)`, or in bulk by someone else).

### Step 3d–3f: what makes a claim payable?
**Raw data:** `data/step3d/` (deposit contract's events), `data/step3e/` (`0x0ef8…d705` events), `data/step3f/` (`0x57aa…6a41` events).

1. The deposit contract emits event `0x11c6bf55` **39 times in 7 days**, always in a tx **from one EOA (`0x4293…23e2`) to
   `0x0ef8fa4760db8f5cd4d993f3e3416f30f942d705`** (`0x2e03931e`). Trace of the last one (10-22 08:41): it reads
   `0x57aaf0004c716388b21795431cd7d5f9d3bb6a41` and the deposit contract, then **the deposit contract sends 245.74 ETH to `0x7d57…`**.
   → **Batches that fund the claims contract**, about every 4 hours.
2. **`0x57aaf000…`** (consulted at the start of every batch) was written to by **only 3 EOAs all week**:
   `0x9b705e51…`, `0xc2f2a630…`, `0x4293664628…` (~40 txs each, all `0xcaf0216d`, 119 total). A second event fired 39 times,
   once per batch → **reports from 3 submitters, approved when enough agree.**

### Step 4: run the exit for our user
**Time:** 13:37:30Z → 13:37:58Z. **Fork snapshot before:** recorded in `data/step4/step4.json`.

- **Experimenter intervention (disclosed):** the user has 0.00057 ETH, not enough for gas; set to 0.1 ETH.
- Request without approval → ❌ `0x8d6f21e1`. Other users' traces show an eETH `Approval` to the deposit contract →
  `approve(deposit contract, 43.64)` ✅.
- **Request:** `0x397a1b28(user, 43.642970314355004)` on the deposit contract → tx `0x61fd4c68…` ✅ (193,111 gas):
  **eETH 43.643 → `0x7d57…`; claim NFT #83,769 minted to the user** (request record: 43.643 / 39.451).
- **Claim right away:** `0xb13acedd(83,769)` → ❌ `0xd399e3e5`. **After +7 days (no batch):** ❌ same.

**Result for our user:** all 43.64 eETH handed in, **no ETH back**, holding claim #83,769, which can't be redeemed without a batch.

### Step 5: proof — what is needed for a claim to pay?
**Time:** 13:39:42Z → ~13:47Z. **Raw data:** `data/step5/`, `data/step3f/submit_caller_test.json`.

**5.1 Same claim, with and without the batch** (fork at 26,247,023, one block before the last batch `0x72e949be…`;
claim **83,757**, owned by EOA `0xd721…b564`, minted at block 26,244,558):

| # | Action | Result |
|---|--------|--------|
| A | Owner claims, no batch yet | ❌ `0xd399e3e5` |
| B | **Random address sends the real batch tx** | ✅ status 1 |
| B′ | Owner claims | ✅ |
| C | Original sender replays it | ❌ status 0 (already applied) |
| D | Owner claims for real | ✅ **+36.66 ETH** |
| D′ | Highest pending claim (83,762), outside this batch | ❌ `0xd399e3e5` |

**5.2 Is the batch data free?** Same fork, `eth_call`:

| Batch data | From a random address | From the original sender |
|------------|----------------------|--------------------------|
| Original | ✅ | ✅ |
| Claim range end changed (83,757 → 83,762) | ❌ `0x9cb6fb7c` | ❌ `0x9cb6fb7c` |
| ETH amount +1 | ❌ `0x9cb6fb7c` | ❌ `0x9cb6fb7c` |
| Same data resent after it was applied / previous batch's data / +1 day | ❌ | — |

The check is on the **data**, not the caller: only data matching what `0x57aaf000…` has approved works.
(Traces: `0x57aaf000…`'s `0xb66e6bcc` returns a different value for modified data, then the call reverts.)

**5.3 Who can approve data?** Fork at 26,246,927 (one block before the approval of that batch, tx `0x550e3b9c…`):

| Submitting the approving report (`0xcaf0216d` on `0x57aaf000…`) | Result |
|-----------------------------------------------------------------|--------|
| Its original submitter (`0x9b705e51…`) | ✅ |
| Another of the 3 submitters (`0xc2f2a630…`) | ✅ |
| **A random address** | ❌ `0xaba47339` |

All 3 submitters are plain EOAs.

**Findings:**
1. **Shown: a claim pays if and only if an approved batch covers it.** Anyone can *execute* an approved batch (5.1 B),
   but only approved data works (5.2), and **only 3 addresses can approve data** (5.3).
2. **This is the D4 dependency**, split in two steps: permissioned approval (3 EOAs) + permissionless execution.
   If the 3 stop submitting, no new batch can be approved, and new claims, like our user's #83,769, stay unpaid.

### Step 6: how many of the 3 submitters are needed? (quorum test)
**Time:** ~14:10Z → ~14:25Z (several forks; ~3 min of execution). **Raw data:** `data/step6/quorum_test.json`, `data/step3f/quorum.json`.

**From the events (all 39 approved reports this week):** approval happened **exactly at the 3rd submission** every time;
every report was submitted by all three (`0x9b705e51…`, `0xc2f2a630…`, `0x4293664628…`); no submissions after approval.

**On a fork at 26,246,927**, when only 1 of 3 had submitted the report behind the last batch (`0x72e949be…`), trying
that batch from a random address after each step:

| State | Clock | Batch |
|-------|-------|-------|
| 1 of 3 submitted | fork time | ❌ `0x9cb6fb7c` |
| 2 of 3 (replayed `0xc2f2…`'s real submission) | +10 min / +1 h / **+1 day** | ❌ / ❌ / ❌ (fresh fork) |
| 3 of 3 (replayed `0x9b70…`'s too) | +1 min | ❌ |
| 3 of 3 | **+10 min** / real batch time (+19 min) | ✅ / ✅ |

**Findings:**
1. **All 3 of 3 submitters are needed.** With 2 of 3, the batch stays invalid even a day later.
   **If any single one of the three stops, no new batch can be approved.**
2. After approval there's a **waiting period of 1–10 minutes** before the batch can be executed.

### Step 7: the user's other ether.fi position (weETH)
**Time:** 14:28:03Z → 14:28:05Z. **Raw data:** `data/step7/weeth.json`.

The user also held **39.33 weETH** (step 2). Using the call other holders used (step 3b, `0xde0e9a3e(amount)` on weETH):
- Unwrap all → tx ✅: weETH 39.33 burned; **eETH 43.51 from the weETH contract to the user**.
- `approve` + request (`0x397a1b28`) → ✅, **claim #83,770** minted to the user.
- Claim → ❌ `0xd399e3e5`, same as #83,769.

**Finding:** the weETH position converts to eETH without any dependency, then hits **the same D4 block**.
The user now holds two unpayable claims (#83,769: 43.64 eETH; #83,770: 43.51 eETH). (liquidETH, 9.98, is a separate
product, Ether.Fi Liquid, and outside this test.)

### Required infrastructure (this run)

| Capability | Used in |
|------------|---------|
| `eth_getLogs` over all history | 2, 3b, 3c–3f |
| `eth_getTransactionByHash` (971 + 446 txs, batched) | 3b, 3c–3f |
| `eth_call` against past state, chosen `from` | 3a, 4, 5, 6, 7 |
| `debug_traceCall` / `debug_traceTransaction` | 3a, 3b, 3c, 3d, 5 |
| Forks at several past blocks, impersonation, clock control, snapshot/revert | 4, 5, 6, 7 |

---

## Result: ether.fi (eETH), T0 — 🔴 Blocked

| Scenario | Result | Why |
|----------|--------|-----|
| **D4 removed** (**any one** of the 3 report submitters stops) | 🔴 **Blocked** | Steps 4–7: claims can't be paid without an approved batch; approval needs **all 3** EOAs |
| D4 present | ✅ Exits (two steps) | Step 5: once a batch covers the claim, the owner redeems alone with `0xb13acedd(id)`. This week: median ~14h, max ~56h |
| Each of D1, D2, D3, D5 removed individually | Same as above | The run never used them |

**Both positions** (eETH and the weETH unwrapped to eETH, step 7) end in the same block.

**Difference from Lido:** in Lido the batch itself could only be sent by specific callers. In ether.fi **anyone can send
the batch**, but only once its data has been approved by **3 permissioned submitters**. The dependency is the same:
nobody else can make new claims payable.

**Capital exposed to D4 (fork block 26,248,199):**
- **2,267,689.80 eETH** (eETH `totalSupply()`): every eETH needs an approved batch to exit through the protocol.
- Already waiting in claims: **1,854.51 eETH** held by `0x7d57…`; `0x7d57…` also held **197.23 ETH** for claims already covered.

**Why T1/T2 aren't run (SPEC §3):** blocked by a permission check; tiers add information, not permissions.
**Fallback (not a pass):** selling eETH/weETH on a trading route (routers seen in step 3b).

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract | 57s | ~2 min |
| 3a | Proxies + selectors | ~1s | ~1 min |
| 3b | Flows, 971 txs, 6 traces | ~1.5 min | ~4 min |
| 3c–3f | Claims contract, batches, approvals | ~1.5 min | ~6 min |
| 4 | Request + claim attempts | ~30s | ~1 min |
| 5 | Proof (same claim, data test, approval caller test) | ~2 min | ~6 min |
| 6 | Quorum test | ~3 min | ~5 min |
| 7 | weETH position | ~2s | ~1 min |
| **Total** | | **~9.5 min** | **~26 min** |

Wall clock: 13:33:05Z → ~13:50Z (17 min).
