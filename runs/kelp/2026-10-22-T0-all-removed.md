# Run: Kelp (rsETH) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Kelp, Ethereum; rsETH |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xcbe6362d5bdcde0ababd571d10d34e1d603a1054` (100th holder; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`); proof fork at 26,247,337 |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-25T14:16:22Z |

## Ground rules

- We play a user who has their **address** and knows they hold **rsETH** from **Kelp** (SPEC §1).
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators have general knowledge of Kelp. The rsETH address came from the chain (the
only token minted in the last 7,200 blocks with symbol rsETH). The escrow, its functions, the operator contract, and the
signature check were all found from logs, traces, and fork tests. **Note:** in step 3c Claude first labelled the two
holder calls the wrong way round; the token movements in the traces corrected it before anything was sent.

## Setup notes (selection, SPEC §8)

- DefiLlama: one product ($0.96B); deposits stETH 51% / ETH 36% / ETHx 13%, **one receipt token for all: rsETH**
  `0xa129…e5a7` (totalSupply **367,430.04**).
- 100th holder: an EOA (nonce 54), **10.36 rsETH**.

## Steps

### Step 1–2: account facts; every token contract
**Time:** 14:16:22Z → 14:16:28Z. ETH 10.27; nonce 54; plain EOA. 35 contracts; exact match **rsETH 10.360754**; one phishing
token ("kelplabs.org").
**History:** rsETH **minted** to the user by their own tx to `0x0366…d375d` (`0xc3ae1766`, block 19,116,948: a deposit);
later moved out through other contracts and back via transfers from `0x85d4…`.

### Step 3a: rsETH
**Time:** 14:16:29Z. 2,837-byte EIP-1967 proxy → logic `0x7159…7783` (9,669 B); 33 functions; basic 9; fixed list 1:
`mint(address,uint256)`. **No nameable burn or exit.**

### Step 3b: who destroys rsETH?
**Time:** 14:16:47Z → 14:16:53Z. **Window:** blocks 26,197,800 → 26,248,199. **Raw data:** `data/step3b/`.
378 transfers; 15 mints (36.95); **5 burns (8,578.93 rsETH), all from one address: `0x62de59c08eb5dae4b7e6f7a8cad3006d6965ec16`**,
in 4 txs to `0xcbcdd778aa25476f203814214dd3e9b9c46829a1` (`0x6a761202`) from 2 senders.

### Step 3c: everything `0x62de…` (the escrow) recorded, and traces
**Time:** ~14:17Z. **Raw data:** `data/step3c/` (`events.json`, `flow_traces.json`, `traces/`).

| Event | Count | Senders | Via |
|-------|-------|---------|-----|
| `0xca13475b` | 61 | 53 | escrow `0xd3a86833` (holders) |
| `0xd1ff3688` | 47 | 40 | escrow `0xc5a67b01` (holders) |
| `0xca2245f2` | 108 | 88 | both |
| **`0x72e38cd9`** | **5** | **2** | **`0xcbcd…` → escrow `0xa2ccd14f`** |

Traces (3 each):

| Call | Calldata | What moves |
|------|----------|------------|
| **Request** `0xc5a67b01(asset, rsETH amount, text)` | asset = stETH / ETH (`0xeeee…`) / token `0xa35b…`; text may be empty | **rsETH holder → escrow** (e.g. 4,080 rsETH) |
| **Operator unlock** (`0xcbcd…` → escrow `0xa2ccd14f(asset, …)`) | | **rsETH burned from the escrow; the matching asset brought in** (e.g. 1,457.85 of `0xa35b…`; 4,937.77 ETH in another) |
| **Claim** `0xd3a86833(asset, text)` | | **asset escrow → holder** (e.g. 1,999.39 stETH; 1,447.07 of `0xa35b…`) |

**Finding:** a three-step queue: **request** (holder) → **unlock** (only via `0xcbcd…`, a few times a week) → **claim** (holder).

### Step 4: run the exit for our user
**Time:** 14:18:21Z → 14:19:02Z. **Raw data:** `data/step4/step4.json`.

| Attempt | Result |
|---------|--------|
| Request without approval | ❌ "ERC20: insufficient allowance" → `approve(escrow, 10.36)` ✅ |
| **Request** `0xc5a67b01(stETH, 10.360754, "")` | ✅ tx `0x55673b61…`: **10.36 rsETH → escrow** |
| Claim right away | ❌ `0x321116dc` |
| **Claim after +7 days** | ❌ `0x321116dc` |

**Result for our user:** rsETH **0**, stETH **0**; the claim stays locked.

### Step 5: proof — what makes a claim payable, and who can do it?
**Fork at 26,247,337**, one block before the operator unlock `0x45447ebe…` (asset `0xa35b…`). Holder: `0xf746…`, whose real
claim (`0x169ee037…`, block 26,247,559) came right after it. **Raw data:** `data/step5/proof.json`.

| # | Action | Result |
|---|--------|--------|
| A | Holder claims before the unlock | ❌ `0x321116dc` |
| B | **Random address calls the escrow's unlock** (same data) | ❌ `0xa178e9e5` |
| B′ | `0xcbcd…` calls it (same data) | ✅ → **only `0xcbcd…` may unlock** |
| B″ | Random address **relays the operator's exact tx** to `0xcbcd…` | ✅ (simulation) → `0xcbcd…` doesn't check the tx sender |
| B‴ | Same tx with **one unlock value changed**, from random / from the original sender | ❌ / ❌ `"GS026"` → **authorization is in signed data** inside the tx |
| C | Original sender replays the operator tx | ✅ |
| D | Holder claims | ✅ **+1,447.07** of `0xa35b…` |

**Findings:**
1. **A claim pays only after an unlock**, and **only `0xcbcd…` can unlock**.
2. `0xcbcd…` accepts anyone's relay **but only for data it has authorized** (changing one value fails for everyone):
   the same "anyone can execute, only approved data works" pattern as ether.fi, with signatures instead of on-chain reports.
3. Who holds that authorization isn't visible beyond the 2 addresses that sent unlocks this week.

---

## Result: Kelp (rsETH), T0 — 🔴 Blocked

| Scenario | Result | Why |
|----------|--------|-----|
| **D4 removed** (whoever authorizes `0xcbcd…`'s unlocks stops) | 🔴 **Blocked** | Steps 4–5: claims pay only after an unlock; only `0xcbcd…` can unlock, and only with authorized data |
| D4 present | Exits in three steps | Observed: 61 claims and 47 requests this week; 5 unlocks |
| D1, D2, D3, D5 removed individually | Same | Never used |

**Capital exposed to D4:** **367,430.04 rsETH** (`totalSupply()`).
**Why T1/T2 aren't run (SPEC §3):** blocked by a permission check.

### Timings (raw)

| Step | Queries / execution | Analysis (approx.) |
|------|---------------------|--------------------|
| Setup (finding rsETH) | ~2 min | ~3 min |
| 1–3c | ~1 min | ~6 min |
| 4 | ~40s | ~1 min |
| 5 | ~1 min | ~4 min |
| **Total** | **~5 min** | **~14 min** |
