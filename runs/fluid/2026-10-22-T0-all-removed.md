# Run: Fluid (Fluid Lending, fwstETH) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Fluid Lending, Ethereum; vault "Fluid Wrapped liquid staked Ether 2.0" (fwstETH) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xb7b8a2f919ab46a5f46552714a982cc3356aa9aa` (#99: #100 is a contract; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-25T14:23:00Z |

**Ground rules and contamination:** as in every run (SPEC §1, §9, §10). The vault address came from a 7-day on-chain
ERC-4626 `Deposit` scan; the exit function was named by the fixed list; behavior from other holders' traces.

## Setup notes (selection, SPEC §8)

- DefiLlama: Fluid Lending is the largest product ($0.48B); largest asset **wstETH (27%)**. Fluid-named ERC-4626 vaults
  (7-day scan): fUSDC 134.5M, fUSDT 130.5M, fGHO 24.1M, fLiteUSD 42.0M, fUSDtb 1.6M, fWETH 778.65, **fwstETH 753.35 wstETH**.
- wstETH **has** a receipt (fwstETH), so the rule picks it, even though it's small: most of DefiLlama's wstETH figure must
  be collateral held elsewhere.
- fwstETH has 188 holders; #100 is a contract → **#99**, an EOA (nonce 12), **0.00796 fwstETH**.

## Steps

| Step | What | Result |
|------|------|--------|
| 1 | Account facts (14:23:00Z) | ETH 0.0345; nonce 12; plain EOA |
| 2 | Every token contract (5s) | 16 contracts; exact match **fwstETH 0.007964**, minted to the user by their own `deposit(uint256,address)` on the vault (block 23,277,040) |
| 3a | Selectors | fwstETH: 19,617 bytes, **not a proxy**; 48 functions; basic 9; **fixed list 6**: `deposit` ×2, `mint` ×2, **`withdraw(uint256,address,address)`, `redeem(uint256,address,address)`** |
| 3b | Behavior (7 days) | 12 transfers; 4 mints; **5 burns**, 4 of them **direct `redeem`/`withdraw` on the vault, sent by the holder**. Traces: `redeem(0.158764, sender, sender)` → **0.164876 wstETH to the holder**; `withdraw(0.022, sender, sender)` → 0.022 wstETH. The wstETH comes from `0x52aa…e497` |
| 4 | Exit for our user | `redeem(0.007963872662638097, user, user)` → tx `0xcdbbf923…`, status 1: **fwstETH 0, wallet wstETH 0.008271** |
| 5 | Liquidity | the wstETH source `0x52aa899454998be5b000ad077a46bbe360f4e497` held **42,455.06 wstETH** at the fork block vs the vault's 753.35 → no constraint for this vault |

**Raw data:** `data/step2/`, `data/step3/`, `data/step3b/` (flows, traces), `data/step4/step4.json`, `data/step5/liquidity.json`.

---

## Result: Fluid (fwstETH), T0 — ✅ Exits cleanly

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed | ✅ **Full exit, one call** | `redeem` named by the fixed list on the position contract; sent by the holder |
| D4 | Not needed | |

**Capital exposed to D4:** none found. **Caveat:** the test position is tiny (the rule picked the receipt of the largest
asset, which itself is small); most of Fluid's TVL sits in collateral positions this run didn't touch.

### Timings (raw)
Queries/execution ~1 min; analysis ~6 min; wall clock 14:23:00Z → ~14:26Z.
