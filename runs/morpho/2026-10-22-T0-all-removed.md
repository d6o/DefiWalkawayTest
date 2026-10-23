# Run: Morpho (Morpho Blue, Gauntlet USDC Prime vault) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Morpho Blue, Ethereum; vault "Gauntlet USDC Prime" (gtusdcp) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x1c424df78d4fcc3b9635be62054fdab3f9b38a49` (100th holder; see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`), same block as every protocol (SPEC §6) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-23T12:25:20Z |

## Ground rules

- We play a user who has their **address** and knows they deposited **USDC** into **Morpho** and got **gtusdcp**
  (SPEC §1). They don't know any contract addresses or how to exit.
- Every address and function must come from **an earlier step's output** or from **basic knowledge** (SPEC §9).
  Function names only via the fixed list. Evidence rules: SPEC §10. Calls that may revert go through plain JSON-RPC.

**Contamination disclosure:** both operators know Morpho. During **setup**, Claude first used a vault address from
memory (`0xBEEF01…64CB`, "Steakhouse USDC"); it turned out to be the smaller of two same-named vaults, so the selection
was redone from chain data (ERC-4626 `Deposit` events → USDC-asset vaults → largest `totalAssets()`), which is what the
spec now records. Nothing from memory is used in the run itself.

## Setup notes (selection, SPEC §8)

- DefiLlama: Morpho Blue is the largest product ($5.05B). Its largest assets are **collateral** (cbBTC $0.81B, wstETH
  $0.64B, kBTC $0.52B), which has **no receipt token**. The largest asset with one is the loan asset **USDC**
  ($0.99B borrowed + $0.14B idle). USDC has many vaults; by on-chain `totalAssets()` at the fork block, the largest
  Morpho one is **Gauntlet USDC Prime** (`0x8c10…a3d0`, $111.08M), just ahead of Steakhouse Prime USDC ($103.3M).
  Snapshots: `data/selection/2026-10-22-defillama-morpho-blue.json`, `2026-10-22-morpho-usdc-vaults-onchain.json`,
  `2026-10-22-ethplorer-gtusdcp-top100.json`. New §8 sub-rules were added for this case.
- The 100th holder is an EOA (nonce 64), **123,530.05 gtusdcp**.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 12:25:20Z (~1s).

| Query | Result |
|-------|--------|
| chainId / block | 1 / 26,248,199 |
| ETH balance | 0.0410 ETH |
| Nonce (txs sent) | 64 |
| Code | none (plain EOA) |

### Step 2: find every token contract the address touched, then find "gtusdcp"
**Time:** 12:25:20Z → 12:25:59Z (39s, `scripts/discover.py --match gtusdcp`) plus reading (~2 min).
**Raw data:** `data/step2/raw_logs.json`, `contracts.json`, `contracts.md` (all 49 contracts).

**Logs:** 119 transfers in, 91 out, 3 ERC-1155 in.

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0x8c106eedad96553e64287a5a6839c3cc78afa3d0` | Gauntlet USDC Prime | **gtusdcp** (exact match) | 4 | 3 | **123,530.0523** |
| `0x58d97b57bb95320f9a05dc918aef65434969c2b2` | Morpho Token | MORPHO | 1 | 1 | 0 |

Other: a position named after another protocol (Aave Ethereum USDC, 62,856), spam/airdrops (ha138.com, AICC, ETHG, …).
**No token named "Debt"** or similar in the history.

**Findings:** one exact match, one Morpho-named token with zero balance, nothing else Morpho-related.

### Step 3a: is the vault token a proxy, and can its functions be named?
**Time:** 12:26:13Z → 12:26:14Z (~1s) plus reading (~1 min).
**Raw data:** `data/step3/`.

- `0x8c10…a3d0`: **21,808 bytes, not a proxy** (EIP-1967 implementation and beacon slots empty; the `name()` trace has no
  delegation). First non-proxy position contract in this study.
- 97 functions; basic 9 (ERC-20 core); **fixed list 4**; unnamed 84.

| Selector | Name (fixed list) |
|----------|-------------------|
| `0x6e553f65` | `deposit(uint256,address)` |
| `0x94bf804d` | `mint(uint256,address)` |
| `0xb460af94` | `withdraw(uint256,address,address)` |
| `0xba087652` | `redeem(uint256,address,address)` |

**Finding:** **the exit functions are nameable on the token itself**, before looking at any other user.

### Step 3b: what do holders call, and what comes back?
**Time:** 12:26:28Z → 12:26:56Z (~30s of queries) plus reading (~4 min).
**Window:** blocks 26,197,800 → 26,248,199. **Raw data:** `data/step3b/`.

**Flows:** 378 transfers in 315 txs; **97 mints** (53.0M shares, 54 recipients); **196 burns** (69.7M shares, 66 holders).

**All 315 txs, grouped** (38 groups; 28 single-sender):

| tx.to | Selector | Txs | Senders | Burns | Mints | Calldata words |
|-------|----------|-----|---------|-------|-------|----------------|
| `0xd8b444ac665b0de3a9135ad7be1a45f88ac97b3c` | `0xba087652` (`redeem`) | 46 | 39 | 46 | 0 | 3 |
| `0x0291…650b` | `0x932084a8` / `0x6bbba4e0` | 34 / 32 | 28 / 27 | 34 / 0 | 0 / 32 | 12 / 10–14 |
| **`0x8c10…a3d0` (the vault)** | **`0xba087652` (`redeem`)** | 16 | 13 | **16** | 0 | 3 |
| **`0x8c10…a3d0` (the vault)** | `0x6e553f65` (`deposit`) | 14 | 5 | 0 | 14 | 2 |
| others | various | ≤18 | mostly 1 | | | smart wallets / routers |

**Traces (3 per group):**

| Call | Example | Words | What happens |
|------|---------|-------|--------------|
| vault `deposit(assets, receiver)` | `0xebea5223…` | [102,500,000, sender] | USDC 102.50 sender → vault; **98.642 gtusdcp minted** to sender |
| vault **`redeem(shares, receiver, owner)`** | `0x4f35f224…` | [19.258e18, sender, sender] | gtusdcp 19.258 burned; **USDC 20.013 vault → sender** |
| vault `redeem` | `0x69068ce6…` | [1,415.5e18, sender, sender] | 1,415.50 burned; **USDC 1,471.65 → sender** |
| vault `redeem` | `0x8f9f0bd6…` | [7,035.29e18, sender, sender] | 7,035.29 burned; **USDC 7,315.60 → sender** |
| `0xd8b4…7b3c` `redeem` | 3 txs | [shares, sender, sender] | `0xd8b4` burns its own token, then the vault burns gtusdcp held by `0xd8b4` and sends USDC to the sender |

Inside every call, the vault calls the same three contracts (`0x870a…00bc`, `0xbbbb…ffcb`, `0xdf62…a22f`); USDC comes
from the vault's address. `0xd8b4…7b3c` is a **wrapper** around the vault; our user holds the vault token directly.

**Findings:**
1. **Exit confirmed from behavior:** `redeem(shares, receiver, owner)` on the vault burns shares and sends USDC to the
   receiver, in one step, at ~1.04 USDC per share this week. No other actor involved in the traced examples.
2. **Deposits and redemptions both run through the vault token itself.**

### Step 4: run the exit for our user
**Time:** 12:27:12Z → 12:27:26Z (~14s).
**Fork snapshot before:** `0x0`. **Raw data:** `data/step4/step4.json`.

| Simulation (`eth_call`) | Result |
|-------------------------|--------|
| `redeem(123,530.052…, user, user)` (all shares) | ✅ returns **128,453.457948** |
| all shares + 1 wei | ❌ `0x4e487b71…11` (standard Solidity panic: arithmetic over/underflow) |
| 2²⁵⁶−1 | ❌ same panic (the vault doesn't accept "everything" as a sentinel, unlike Aave/Spark) |
| 1 share | ✅ returns 1.039855 |

**Sent:** `redeem(123,530.05227055399 × 10¹⁸, user, user)` → tx `0x178745ee…`, **status 1**, 362,885 gas.
- gtusdcp **123,530.0523 burned**; **USDC 128,453.458127 from the vault to the user.**
- After: shares **0**, wallet USDC **128,453.46** (from 0), ETH 0.0409 (gas only).

---

## Result: Morpho (Gauntlet USDC Prime vault), T0 — ✅ Exits cleanly

| Scenario | Result | Why |
|----------|--------|-----|
| All of D1–D5 removed, user's own funds | ✅ **Full exit, one transaction** | Step 4: 123,530 shares → 128,453.46 USDC; nothing left in the vault |
| Each of D1, D2, D3, D5 removed individually | Same | The run never used any of them |
| D4 (privileged actor) | **Not needed** on the path used | A single `redeem` call by the holder |

**Why T1/T2 aren't run (SPEC §3):** T0 completed. **Capital exposed to D4:** none found on the path used.

**What made this the easiest run so far:**
1. The position contract **isn't a proxy** and **its exit functions are nameable with the fixed list**
   (`withdraw`, `redeem`), so the user doesn't have to learn the exit from other users at all; behavior only confirmed it.
2. No debt-named tokens and no shared limits: the whole balance comes out, with interest (USDC 128,453 for a deposit
   that minted 123,530 shares; +4.0%).
3. Only trap found: "2²⁵⁶−1 = everything" doesn't work here (arithmetic panic); the user must pass their exact share balance.

**Caveats (not tested):** the vault calls three other contracts on every deposit/redeem (`0x870a…00bc`, `0xbbbb…ffcb`,
`0xdf62…a22f`); whether redemptions can be limited by liquidity in those (the vault held 0 USDC directly, so the USDC
comes from elsewhere during the call) wasn't probed. The 7-day window showed 196 successful burns by 66 holders.

### Timings (raw)

| Step | What | Queries / execution | Analysis (approx.) |
|------|------|---------------------|--------------------|
| 1–2 | Account facts; every token contract | 39s | ~2 min |
| 3a | Proxy check + selectors | ~1s | ~1 min |
| 3b | Flows, all 315 txs, 9 traces | ~30s | ~4 min |
| 4 | Simulations + redeem | ~14s | ~1 min |
| **Total** | | **~1.5 min** | **~8 min** |

Wall clock (run only): 12:25:20Z → 12:27:26Z (**2 min**). Setup (vault selection) took longer than the run.
