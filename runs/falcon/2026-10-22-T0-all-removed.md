# Run: Falcon Finance (USDf) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Falcon Finance, Ethereum; USDf |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xd3dbb6556a683f4c21e38ba6473d737d6f90417b` (100th holder; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-25T03:13:32Z |

## Ground rules

- We play a user who has their **address** and knows they hold **USDf** from **Falcon Finance** (SPEC §1).
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators have general knowledge of Falcon Finance. The USDf address came from the chain
(`asset()` of the vault "Staked Falcon USD"). Everything below comes from logs, traces, and fork calls.

## Setup notes (selection, SPEC §8)

- DefiLlama: one product on Ethereum ($1.72B); breakdown is **100% USDf** itself → position token USDf
  `0xfa2b…cec2` ("Falcon USD", totalSupply **1,727,683,714** at the fork block).
- 100th holder: an EOA, **36,060.31 USDf**.

## Steps

### Step 1: what the node tells us about the address directly
ETH **0**; nonce **0** (never sent a tx; can't pay gas); plain EOA.

### Step 2: find every token contract the address touched
**Time:** 03:13:33Z → 03:13:37Z (4.5s). **One contract in total:** USDf, **36,060.31**.
**How it arrived:** one plain `transfer()` from EOA `0x6614…3d69` (nonce 1,485) at block 24,345,496. The user never
minted or redeemed USDf.

### Step 3a: is USDf a proxy, and can its functions be named?
**Time:** 03:14:00Z. USDf: 793-byte EIP-1967 proxy → logic `0x3adf…b789` (8,253 B). 27 functions; basic 10; **fixed list 2:
`mint(address,uint256)`, `burn(address,uint256)`**; 15 unnamed. Note: **burn takes an address**, i.e. it burns *someone's* tokens.

### Step 3b: the 7-day window
**Time:** 03:14:00Z → 03:14:05Z. **Raw data:** `data/step3b/`.
483 transfers in 262 txs; **11 mints (0.54M USDf), all sent by one address** via `0x3a4f…cc59` (`0x5cec23e7`);
**0 burns**. Nothing to learn an exit from in the window.

### Step 3c: the token's entire history (mints and burns only)
**Time:** ~03:15Z → ~03:20Z. **Raw data:** `data/step3c/` (`all_history_mint_burn_logs.json`, `burn_groups_all.json`,
`burner_inflows.json`, `intermediate.json`, `payback_check.json`).

**All history:** 7,624 mints (3,678.27M USDf); **131 burns (1,950.59M USDf)**, between blocks 22,152,553 and 26,180,688.

| Burns | Value |
|-------|-------|
| Function | **`burn(address,uint256)` on USDf** (all 131) |
| Tx sender | **one address**: `0x4873f9acff54bdfa97b5f4a7276627dce88c6fdd`, a plain EOA whose **131 txs are all these burns** |
| Whose tokens | **its own** (sender == burned-from in 131 / 131) |

**How USDf reaches the burner** (~90 days before the fork block):
- `0x4873…` received USDf **3 times (94.78M), all plain transfers from `0x76ef4e84618785ae375ae66c58728cc6b3a6a0f4`**, a plain
  EOA (nonce 237).
- `0x76ef…` received **115 plain USDf transfers (95.22M) from 61 addresses**, each sent by the holder themselves (`transfer`).

**Does anything come back?** For the top 3 senders to `0x76ef…` (21, 13, and 8 transfers), every token transfer they
received within **3 days** after each one: only **more USDf** (from other addresses) and spam (TOWN). **No USDC, USDT, or
any other collateral-like token.** If they were paid, it isn't visible on Ethereum.

### Step 4: what can our user do alone?
**Raw data:** `data/step3c/burner_inflows.json`.

| Attempt | Result |
|---------|--------|
| `burn(own address, all)` (fixed list) | ❌ custom error `0xe2517d3f` with data = **our user's address + a 32-byte value `0x3c11d16c…a848`** (the same "account lacks permission X" shape seen in Ethena, encoded as data instead of text) |
| Any contract that takes USDf and returns collateral | **None found**: the only USDf-removing path in history is plain transfers to an operator EOA, then burns by a second EOA |

---

## Result: Falcon Finance (USDf), T0 — 🔴 Blocked

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed | 🔴 **No on-chain exit found** | The holder can't burn (permission); the only observed redemption path is sending USDf to an operator wallet, with **nothing visible coming back on-chain** |
| D4 / D2 | **The whole exit depends on operators** | Two EOAs collect and burn every redeemed USDf; whatever is paid back happens off this chain or off-chain |
| Each of D1, D3, D5 removed individually | Same | Never used |

**Compared with Ethena:** in Ethena, redemptions are **on-chain** but only role holders can submit them. In Falcon, there is
**no on-chain redemption at all** in the token's history: holders hand USDf to an operator's wallet and trust them.

**Capital exposed to D4 (fork block):** **1,727,683,714 USDf** (`totalSupply()`).
**Why T1/T2 aren't run (SPEC §3):** blocked by a permission check / no on-chain path. Higher tiers (docs, APIs) might show
an off-chain redemption process, which would itself be a D2 dependency.
**Fallback (not a pass):** selling USDf on a trading route.

**Limits of this run:** "nothing comes back" was checked for the top 3 senders, within 3 days, on Ethereum only.

### Timings (raw)

| Step | Queries / execution | Analysis (approx.) |
|------|---------------------|--------------------|
| 1–2 | 5s | ~1 min |
| 3a–3b | ~10s | ~2 min |
| 3c (all history, flows to burner) | ~2 min | ~6 min |
| 4 | ~2s | ~1 min |
| **Total** | **~2.5 min** | **~10 min** |

Wall clock: 03:13:32Z → ~03:22Z.
