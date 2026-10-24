# Run: Maple (Syrup USDC) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Maple, Ethereum; vault "Syrup USDC" (syrupUSDC) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x90eb6dc08e61fbec7d46a803a32d684635b29c8c` (100th holder; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`); caller-test fork at 26,247,887 |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-24T02:25:29Z |

## Ground rules

- We play a user who has their **address** and knows they deposited **USDC** into **Maple** and got **syrupUSDC**
  (SPEC §1). They don't know any contract addresses or how to exit.
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC;
  `Error(string)` revert texts are read with plain ABI decoding.

**Contamination disclosure:** both operators know Maple. Setup used DefiLlama (product, asset, and which vault name it
attributes to Maple) and the on-chain ERC-4626 scan. Nothing from memory is used in the run.

## Setup notes (selection, SPEC §8)

- DefiLlama: one Maple product on Ethereum ($2.79B); largest asset **USDC (80%)**, then USDT (12%), USDG (8%).
- DefiLlama's yields data attributes the vault named **"Syrup USDC"** to Maple. The only on-chain ERC-4626 USDC vault
  with that name is **`0x80ac24aa929eaf5013f6436cda2a7ba190f5cc0b`** (symbol syrupUSDC, 6 decimals, ~1.04B USDC
  `totalAssets()`; DefiLlama reports $2.76B for the pool, a discrepancy we can't resolve on-chain).
- 100th holder: an EOA (nonce 5), **336,380.81 syrupUSDC**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 02:25:29Z (~1s).

| Query | Result |
|-------|--------|
| ETH balance | 0.0622 ETH |
| Nonce (txs sent) | 5 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "syrupUSDC"
**Time:** 02:25:29Z → 02:25:34Z (5s) plus reading (~2 min). **Raw data:** `data/step2/` (8 contracts).

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0x80ac24aa929eaf5013f6436cda2a7ba190f5cc0b` | Syrup USDC | **syrupUSDC** (exact) | 1 | 0 | **336,380.8055** |
| `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` | USD Coin | USDC | 1 | 1 | 0.7709 |
| `0x0ff874c51e302737816704a98e801361922ebfec` | **USD Coin** | **USDC** | 1 | 0 | 0 — a **look-alike**: same name and symbol as the real USDC, different address |
| others | PYUSD, MORPHO, "Paypal USD Main" (another product), 2 unnamed | | | | |

**How the syrupUSDC arrived:** in a tx **the user sent** to `0x134ccaaa4f1e4552ec8aecb9e4a2360ddcf8df76`
(`0xa6d061fb`), which forwarded 336,380.81 syrupUSDC to the user (block 26,045,201): the user's own deposit, via an
intermediary contract.

### Step 3a: is syrupUSDC a proxy, and can its functions be named?
**Time:** 02:25:53Z. **Raw data:** `data/step3/`.
- **11,660 bytes, not a proxy.** 42 functions; basic 9; **fixed list 4**: `deposit(uint256,address)`,
  `mint(uint256,address)`, `withdraw(uint256,address,address)`, `redeem(uint256,address,address)`; 29 unnamed.

### Step 3b: what do holders do, and who destroys syrupUSDC?
**Time:** 02:25:53Z → ~02:27Z. **Window:** blocks 26,197,800 → 26,248,199. **Raw data:** `data/step3b/`.

**Flows:** 1,186 transfers in 742 txs; 107 mints (14.55M, to **3** recipients); **161 burns (32.35M), all from one
address: `0x1bc47a0dd0fdab96e9ef982fdf1f34dc6207cfe3`**.

| tx.to | Selector | Txs | Senders | What it does (traces) |
|-------|----------|-----|---------|-----------------------|
| **vault `0x80ac…cc0b`** | **`0x107703ab`** (unnamed) | 154 | **80** | words [shares, sender]: shares **sender → `0x7ad5…` → `0x1bc4…`**. Nothing burned, nothing paid. A **request**. |
| `0x134c…df76` | `0x6807c8dc` / `0xa6d061fb` / `0xc9630cb0` | 58 / 16 / 10 | 35 / 16 / 6 | mints via the intermediary (deposits) |
| **`0x1bc4…cfe3`** | **`0xb4dc8294`** | **152** | **1** (`0xfb2c579c1d5f82c7b0f2a3479e5f9bc26bd22b62`) | words [shares]: syrupUSDC burned from `0x1bc4…`; **USDC from the vault to the requester** |

**Traces of 3 processing txs:** 850.11 → **1,010.06 USDC**; 8,474.81 → **10,074.80 USDC**; 84.08 → **100.00 USDC**
(~1.19 USDC per share), each sent to the address that requested.

**Finding:** a **request-then-process queue**. Holders request (80 senders); shares wait in `0x1bc4…`; **one address**
processed every request in the window (152 txs).

### Step 4: what can our user do alone?
**Time:** 02:27:48Z → 02:27:59Z. **Raw data:** `data/step4/step4.json`. Gas: experimenter set ETH to 0.1 (disclosed).

| Attempt | Result |
|---------|--------|
| Vault's named `redeem(all shares, user, user)` | ❌ `Error(string)` **"WM:PE:TOO_MANY_SHARES"** |
| Vault's named `withdraw(1,000 USDC, user, user)` | ❌ **"PM:PW:NOT_ENABLED"** |
| **Request** `0x107703ab(336,380.81 shares, user)` | ✅ shares → `0x7ad5…` → escrow `0x1bc4…` |
| Process their own request (`0x1bc4.0xb4dc8294(shares)`) right away | ❌ **"WM:NOT_REDEEMER"** |
| Same, **after +7 days** | ❌ **"WM:NOT_REDEEMER"** |
| `redeem` after +7 days | ❌ "WM:PE:TOO_MANY_SHARES" |

**Result for our user:** all 336,381 shares sit in the escrow; **0 USDC back**.

### Step 5: who can process a request? (caller test + proof)
**Time:** ~02:27Z → 02:28:20Z. Fork at **26,247,887**, one block before processing tx `0x7c3c0c54…` (84.08 shares →
100 USDC for requester `0xee01…6e62`). **Raw data:** `data/step5/caller_test.json`.

| Processing sent by | Result |
|--------------------|--------|
| The original processor `0xfb2c…2b62` | ✅ — sent for real on the fork: **requester's USDC 5,000.00 → 5,100.00 (+100.00)** |
| **The requester themself** | ❌ **"WM:NOT_REDEEMER"** |
| A random address | ❌ **"WM:NOT_REDEEMER"** |

**Findings:**
1. **Processing withdrawals is restricted** ("not redeemer"); the requester can't process their own request, and
   waiting doesn't change that.
2. **One address** did all processing in the observed week.
3. The vault's standard-named `redeem`/`withdraw` don't offer a way around it ("too many shares" / "not enabled").

---

## Result: Maple (Syrup USDC), T0 — 🔴 Blocked

| Scenario | Result | Why |
|----------|--------|-----|
| **D4 removed** (the processor stops) | 🔴 **Blocked** | Steps 4–5: requests can only be processed by a "redeemer"; one address did all of it |
| D4 present | Exits via the processor | Observed: 152 processing txs, ~1.19 USDC per share |
| Each of D1, D2, D3, D5 removed individually | Same | The run never used them |

**Capital exposed to D4 (fork block):** **872,764,779 syrupUSDC** (`totalSupply()`, ~1.04B USDC of `totalAssets()`):
every share needs the processor. At the fork block, **42,044.25** shares were waiting in the escrow.

**Why T1/T2 aren't run (SPEC §3):** blocked by a permission check.

**Note for the talk:** the vault exposes the standard functions (`withdraw`, `redeem`) that worked directly on Morpho and
Sky, but here they're switched off or limited ("NOT_ENABLED", "TOO_MANY_SHARES"). A recognizable interface doesn't
mean a permissionless exit.

### Required infrastructure (this run)

| Capability | Used in |
|------------|---------|
| `eth_getLogs` over all history | 2, 3b |
| `eth_getTransactionByHash` (batched) | 3b |
| `eth_call` with chosen `from`, `Error(string)` decoding | 4, 5 |
| `debug_traceTransaction` | 3b |
| Forks at two blocks, impersonation, clock control | 4, 5 |

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract | 5s | ~2 min |
| 3a | Selectors | ~1s | ~1 min |
| 3b | Flows, 742 txs, 6 traces | ~30s | ~4 min |
| 4 | User's own attempts | ~11s | ~1 min |
| 5 | Caller test + proof | ~30s | ~2 min |
| **Total** | | **~1.5 min** | **~10 min** |

Wall clock: 02:25:29Z → 02:28:20Z (**3 min**).
