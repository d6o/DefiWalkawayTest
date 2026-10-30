# The DeFi Walkaway Test — Results

Fork block **26,248,199** (2026-10-22 12:37:23 UTC) for every protocol. Method: [`SPEC.md`](SPEC.md).
Each row links to the full run log, where every claim is backed by a query, transaction, or trace.

**Status (2026-10-25):** 16 protocols done (Lido, Aave V3, Spark, Morpho, Sky, ether.fi, Ethena, Maple, Uniswap, Rocket Pool, Compound, Curve, Falcon, Kelp, Fluid, Pendle); Binance staked ETH paused; EigenCloud not started.
Protocols #6+ are beyond the top-5 rule (SPEC §7) and were added by hand in DefiLlama-ranking order (Morpho, Sky, ether.fi, Ethena, Maple, Uniswap, Rocket Pool, Compound, Curve, Falcon, Kelp, Fluid, Pendle), same method.

## Summary

| # | Protocol | Test address (SPEC §8) | Position | Exit at T0, all dependencies removed | What blocks it | Capital exposed |
|---|----------|------------------------|----------|--------------------------------------|----------------|-----------------|
| 1 | [Lido](runs/lido/2026-10-22-T0-all-removed.md) | `0xde80…b9e2` | 5,084.27 stETH | 🔴 **Blocked** | **D4:** a permissioned daily batch | 9,661,657 stETH (all of it) |
| 2 | [Aave V3](runs/aave/2026-10-22-T0-all-removed.md) | `0x462a…31d0` | 456.48 aEthweETH + 4,515.39 aEthwstETH, 5,762.76 WETH debt | ◐ **Partial exit**: 61.67 weETH (13.5% of the aEthweETH position) with own funds. Full exit possible (shown with capital), but **very hard to find without assistance** | The user's own debt caps withdrawals; no dependency on the paths used | None found on the paths used |
| 3 | [Binance staked ETH](runs/binance-staked-eth/2026-10-22-T0-all-removed.md) | `0x066e…76bc` | 16.96 wBETH (user has 0 ETH, never sent a tx) | ⏸ **Paused** after step 3b | — (so far: 0 burns and 0.012 wBETH minted on-chain in 7 days; 99.2% of supply in 5 EOAs) | — |
| 4 | EigenCloud | — | — | ⏸ **Not started** | Test address can't be picked with SPEC §8 as written: **no position token** (deposits are recorded as internal shares). DefiLlama: one product; "WETH" $5.72B (89.4%), stETH $0.54B (8.5%). Fallback rule pending (see SPEC open questions) | — |
| 5 | [Spark (SparkLend)](runs/spark/2026-10-22-T0-all-removed.md) | `0x50e8…cb42` | 403.29 spwstETH + 199.67 spweETH; debts: 155,818 DAI, 119,078 USDS, 138,109 USDT | ◐ **Partial exit**: all 403.29 wstETH + 5.29 weETH (2.65%) with own funds (the two deposits share one limit). Full exit possible (shown with ≈$412k of stablecoins), but **very hard to find without assistance** | The user's own debts cap withdrawals; no dependency on the paths used | None found on the paths used |
| 6 | [Morpho (Gauntlet USDC Prime vault)](runs/morpho/2026-10-22-T0-all-removed.md) | `0x1c42…8a49` | 123,530 gtusdcp | ✅ **Exits cleanly**: one `redeem` → 128,453 USDC (+4.0% vs shares) | Nothing. Liquidity limit only: the USDC comes from `0xbbbb…ffcb` (127.6M held vs 110.9M vault total at the fork block) | None found on the path used |
| 7 | [Sky (Savings USDS)](runs/sky/2026-10-22-T0-all-removed.md) | `0x03ba…2f96` | 1,844,122 sUSDS | ✅ **Exits cleanly**: one `redeem` → 2,053,783 USDS (+11.4% vs shares) | Nothing. The sUSDS contract holds ≈100% of what all shares are worth (4.83B USDS) | None found on the path used |
| 8 | [ether.fi (eETH)](runs/etherfi/2026-10-22-T0-all-removed.md) | `0xd26d…aacf` | 43.64 eETH | 🔴 **Blocked** | **D4:** batches fund the claims; anyone can execute one, but only data approved by **all 3 of 3 permissioned EOAs** works (any one stopping blocks it) | 2,267,690 eETH (all of it) |
| 9 | [Ethena (USDe)](runs/ethena/2026-10-22-T0-all-removed.md) | `0xa29e…4ff5` | 191,359 USDe | 🔴 **Blocked** | **D4:** redemption can only be submitted by holders of an access-control role (20 addresses that week); the USDe holder can't submit their own | 4,655,090,585 USDe (all of it) |
| 10 | [Maple (Syrup USDC)](runs/maple/2026-10-22-T0-all-removed.md) | `0x90eb…9c8c` | 336,381 syrupUSDC | 🔴 **Blocked** | **D4:** withdrawals are requests that only a "redeemer" can process ("WM:NOT_REDEEMER"); one address processed all 152 that week | 872,764,779 syrupUSDC (all of it) |
| 11 | [Uniswap (V3 positions)](runs/uniswap/2026-10-22-T0-all-removed.md) | `0xda94…8514` | 3 position NFTs (1 with liquidity) | 🟡 **Harder but possible**: full exit (3,666 PYUSD + 4,116 USDC; NFTs burned) | Nothing permissioned; the exit functions are unnamed and the amount had to be rebuilt from the position's event history | None found |
| 12 | [Rocket Pool (rETH)](runs/rocketpool/2026-10-22-T0-all-removed.md) | `0x85f3…d5ce` | 419.29 rETH | ✅ **Exits cleanly**: one `burn` → 492.36 ETH, sent by the holder | Nothing permissioned. Liquidity limit: only the ETH in the rETH contract (3,631 ETH ≈ 1.2% of supply at the fork block) | None found |
| 13 | [Compound (V3 WETH market)](runs/compound/2026-10-22-T0-all-removed.md) | `0xe8bd…be90` | 10.48 cWETHv3 | ✅ **Exits cleanly**: one `withdraw(WETH, balance)` → 10.48 WETH | Nothing permissioned. Liquidity: 26.7% of supplied WETH on hand | None found |
| 14 | [Curve (crvUSD/USDT pool)](runs/curve/2026-10-22-T0-all-removed.md) | `0x1e18…4604` | 0.00195 LP (dust; ~83% of LP sits in two contracts) | 🟡 **Harder but possible**: one call → USDT + crvUSD; same call works at 95–13,890 LP | Nothing permissioned; the exit function can't be named at T0 (learned from traces) | None found |
| 15 | [Falcon Finance (USDf)](runs/falcon/2026-10-22-T0-all-removed.md) | `0xd3db…417b` | 36,060 USDf (0 ETH, never sent a tx) | 🔴 **Blocked** | **No on-chain exit:** holders can't burn (permission); every USDf ever burned (1.95B) was sent by plain transfer to an operator EOA and burned by another EOA; nothing visible comes back on-chain | 1,727,683,714 USDf (all of it) |
| 16 | [Kelp (rsETH)](runs/kelp/2026-10-22-T0-all-removed.md) | `0xcbe6…1054` | 10.36 rsETH | 🔴 **Blocked** | **D4:** request → unlock → claim; only `0xcbcd…` can unlock, and only with data it has authorized (anyone can relay; changing one value fails for everyone) | 367,430 rsETH (all of it) |
| 17 | [Fluid (fwstETH)](runs/fluid/2026-10-22-T0-all-removed.md) | `0xb7b8…aa9a` | 0.00796 fwstETH | ✅ **Exits cleanly**: one `redeem` → 0.00827 wstETH | Nothing; liquidity source held 42,455 wstETH | None found (test position tiny; Fluid's collateral side not tested) |
| 18 | [Pendle (PT-reUSD-10DEC2026)](runs/pendle/2026-10-22-T0-all-removed.md) | `0xc1de…b98e` | 103,889.86 PT | 🟡 **Harder but possible, time-locked**: nothing until 10 Dec 2026, then 93,709 reUSD | No permission, **only time** (49 days); unnamed multi-step exit with traps | None found |

Removing the frontend, API, indexer, or default RPC (D1, D2, D3, D5) changes nothing in either run: neither T0 run used them.

## Totals (16 protocols)

| Result | Count | Protocols |
|--------|-------|-----------|
| 🔴 **Blocked** (a privileged actor is needed, D4) | **6** | Lido, ether.fi, Ethena, Maple, Falcon Finance, Kelp |
| ◐ **Partial exit** (user's own debt caps withdrawals; full exit with capital) | **2** | Aave V3\*, Spark\* |
| 🟡 **Harder but possible** (permissionless, but unnamed or state must be rebuilt) | **3 (+2)** | Uniswap, Curve, Pendle (time-locked until maturity); also Aave V3\*, Spark\* |
| ✅ **Exits cleanly** (one named call by the holder; liquidity permitting) | **5** | Morpho, Sky, Rocket Pool, Compound, Fluid |
| ⏸ Not finished | 2 | Binance staked ETH (paused), EigenCloud (no position token) |

\* **Aave V3 and Spark appear in two categories** (as in the talk): with the user's own funds, only the "free" part of the
position comes out (◐); a full exit is possible once the debt is repaid, but finding out why most of the position is locked
and how to repay was very hard without assistance (traces, bytecode searches, the user's own history, cause-and-effect
tests; for Spark, the repay path was only visible inside other users' smart-wallet transactions) (🟡).

**Six D4 designs:** Lido (only specific callers send the batch), ether.fi (anyone executes; 3-of-3 signers approve),
Ethena (redemptions submitted only by role holders), Maple (one "redeemer" processes requests), Falcon (no on-chain
redemption; operator wallets), Kelp (operator contract unlocks, authorized by signed data).

**Capital exposed to D4 at the fork block** (position token supply): Lido 9,661,657 stETH · ether.fi 2,267,690 eETH ·
Ethena 4,655,090,585 USDe · Maple 872,764,779 syrupUSDC · Falcon 1,727,683,714 USDf · Kelp 367,430 rsETH.

## Lido

**Exit path found at T0 (from other users' behavior):** hand in stETH at `0x889e…f9b1` → numbered claim (NFT) →
wait for a daily batch → redeem the claim for ETH, 1:1.

- **Blocked by D4:** ETH reaches the claims contract only in a **daily batch** (~12:22 UTC) that only a small set of
  callers can send. A random address sending the same data on the same state is rejected.
- **Proof:** on a fork one block before a real batch, the same claim fails before the batch, a random sender is rejected,
  the original sender's replay succeeds, and the claim then pays 1:1 (run log step 5).
- **Our user:** handed in all 5,084.27 stETH as 6 claims (max 1,000 stETH each, found by probing). Nothing could be
  redeemed without a batch, including after 7 days.
- **With the batch running:** median wait ~40h this week (16h – 6 days); the holder then redeems alone with just the claim id.
- **Fallback (not a pass):** selling on a trading route.
- **Capital exposed:** every stETH needs the batch to exit through the protocol: **9,661,657 stETH**; 4,204 stETH
  were already in claims waiting for a batch at the fork block.

## Aave V3 — ◐ Partial exit

**Result:** with only their own funds, the user gets **61.67 weETH (13.5% of the aEthweETH position)** out. A **full exit is
possible**: it was completed on the fork once the capital to repay the debt was provided. But finding out how, and why
most of the position was locked, was **very challenging without assistance**: it took traces, bytecode searches, the
user's own transaction history, and a cause-and-effect test (run log steps 4–7).

**Exit path found at T0:** `withdraw(asset, amount, recipient)` on `0x8787…a4e2`. It's the only function the fixed
word list could name, and it works in one step.

- **Our user** had more than the token they knew about: a second deposit (aEthwstETH) and a debt-named balance (WETH).
- **Partial exit with own funds:** 61.67 weETH (13.5% of the aEthweETH position) withdrawn. The rest is capped.
- **Shown to be the user's own debt:** the debt-named balance was minted while the user received ETH, the withdrawal
  logic reads it, and lowering it by 1 raised the cap by 0.95 weETH, with a control showing no change (run log steps 5–6).
  The cap also shrinks over time, because the debt grows by itself.
- **Full exit with capital (provided by the experimenter):** repay 5,762.76 ETH, then withdraw everything:
  456.48 weETH + 4,515.39 wstETH in the wallet, all Aave balances at 0 (step 7).
- **No privileged actor** on the repay or withdraw paths. Not tested: the helper contract the user repaid through,
  and who can upgrade or pause the (upgradeable) contracts.

## Spark (SparkLend) — ◐ Partial exit

**Exit path found at T0:** `withdraw(asset, amount, recipient)` on `0xc13e…e987`, named by the fixed list, one step, ~1:1.

- **Our user** had two deposits (403.29 spwstETH, 199.67 spweETH) and three debt-named balances (DAI, USDS, USDT).
- **The two deposits share one withdrawal limit:** either one can be fully withdrawn alone, but not both.
  Order A: all wstETH + 2.65% of weETH; order B: all weETH + 59% of wstETH. Which is better depends on prices,
  which aren't available at T0.
- **Shown to be the user's own debts:** minted by `0xc13e` while the user received the same amount of each stablecoin;
  read by the withdrawal logic; repaying 1,000 DAI raised the weETH cap from 0.001 to 0.47 (control: no change).
- **The repay path was only visible inside other users' smart-wallet transactions** (traces), never as a direct call.
- **Full exit with capital (provided):** repay ≈ $412k of stablecoins, withdraw everything: 403.29 wstETH + 199.67 weETH.
- **Spam reaches protocol contracts too:** the spweETH contract held a 100-billion-unit airdrop token; "which token does
  this contract hold" has to be matched against its supply.

## Morpho (Gauntlet USDC Prime vault) — ✅ Exits cleanly

- **The position contract isn't a proxy, and the fixed word list names its exit functions directly**
  (`withdraw(uint256,address,address)`, `redeem(uint256,address,address)`). Behavior (196 burns by 66 holders in 7 days)
  only confirmed it.
- **One transaction:** `redeem(all shares, user, user)` → 128,453 USDC for 123,530 shares (+4.0%). No debt, no limits.
- Trap: passing 2²⁵⁶−1 as "everything" reverts with an arithmetic panic; the exact share balance is needed.
- **Liquidity test:** the vault holds no USDC itself; it pulls it from `0xbbbb…ffcb`. Draining that contract on the fork
  made large redemptions fail while small ones still worked: a capital-type limit, not a permission. At the fork block
  it held more than the whole vault.
- Selection note: Morpho's largest assets are collateral with no token, so the test used the largest USDC vault
  (new §8 sub-rules).

## Sky (Savings USDS) — ✅ Exits cleanly

- Same shape as Morpho: sUSDS is a proxy whose logic exposes the four nameable functions (`deposit`, `mint`,
  `withdraw`, `redeem`); 1,697 burns by 148 holders in 7 days confirmed `redeem`/`withdraw` as the exit.
- **One transaction:** `redeem(all shares, user, user)` → 2,053,783 USDS for 1,844,122 sUSDS (+11.4%).
- The user had received their sUSDS by plain transfer (never deposited), so their own history gave no hint; the fixed
  list and other holders' behavior were enough.
- **Backing:** the sUSDS contract holds 4.83B USDS, ≈100% of what all 4.34B shares are worth; interest is minted during
  the call. Drain test: a capital-type limit, no permission.

## ether.fi (eETH) — 🔴 Blocked

**Exit path found at T0:** hand in eETH at the deposit contract (`0x397a1b28`, after an `approve`) → claim NFT from
`0x7d57…` → later redeem with `0xb13acedd(id)` → ETH. Same two-step shape as Lido.

- **What makes a claim payable:** a batch (~every 4h) sends ETH to the claims contract. **Anyone can execute a batch**
  (a random address did, on a fork), **but only data approved by 3 EOAs works**: modified data fails from any caller,
  and a random address can't submit a report (step 5).
- **Our user:** 43.64 eETH handed in → claim #83,769 → not redeemable, including after 7 days without a batch.
- **With batches running:** median wait ~14h this week (max ~56h).
- **Capital exposed:** 2,267,690 eETH (all of it); 1,855 eETH already waiting in claims.
- **Quorum: all 3 of 3.** In every approved report this week, and on a fork, 2 of 3 never made a batch valid (even a
  day later). **If any single submitter stops, withdrawals stop.**
- **The user's weETH** unwraps to eETH without any dependency, then hits the same block (second claim, #83,770).
- **vs Lido:** Lido restricts who can *send* the batch; ether.fi restricts who can *approve* it. Same dependency.

## Ethena (USDe) — 🔴 Blocked

- **Every USDe mint and burn that week went through one contract** (`0xe349…62d3`). Redemptions are **orders**: the
  holder is named inside the call, but someone else always sends the transaction.
- **Caller test (fork):** the same redemption works from its sender and from each of the other 19 senders that week, and
  fails for **the holder themself**, the recipient, and a random address: "AccessControl: … is missing role 0x44ac…".
- **Our user** (191,359 USDe, received by transfer) can't redeem; `burn` just destroys USDe. Only selling remains (fallback).
- **No queue, no claim:** unlike Lido and ether.fi, the exit itself can only be submitted by permissioned addresses.
- **T0 discovery cost:** the test wallet is very busy (122,478 txs): 206,815 transfer logs, 2,102 token contracts,
  ~18 minutes to find the one relevant token.

## Maple (Syrup USDC) — 🔴 Blocked

- **A request-then-process queue:** holders call `0x107703ab(shares, owner)` on the vault; shares wait in an escrow
  (`0x1bc4…`); **one address processed every request that week** (152 txs), paying ~1.19 USDC per share.
- **Caller test (fork):** the processor's tx works; **the requester themself** and a random address get
  "WM:NOT_REDEEMER". Sent for real by the processor, the requester received +100 USDC.
- **Our user:** request ✅ (336,381 shares into the escrow) → self-processing ❌ now and after 7 days → **0 USDC**.
- **Standard names, no standard exit:** the vault has `withdraw`/`redeem` (the functions that worked directly on Morpho
  and Sky), but here they answer "NOT_ENABLED" / "TOO_MANY_SHARES".

## Uniswap (V3 positions) — 🟡 Harder but possible

- **Position NFTs found by a log scan**; what each held came from tracing the user's own deposit txs.
- **Exit = two unnamed calls**, learned from other holders' traces: release (`0x0c49ccbe`) then collect (`0xfc6f7865`).
  The only nameable function is `burn(uint256)`.
- **The amount to release was rebuilt from the position's full event history** (adds minus removals), exactly what an
  indexer normally provides; a simulation confirmed it to the unit.
- **Our user:** two positions already empty; the third returned 3,665.69 PYUSD + 4,115.86 USDC; all 3 NFTs burned.
  No privileged actor anywhere.

## Rocket Pool (rETH) — ✅ Exits cleanly

- **One call, by the holder:** `burn(uint256)` on rETH (named by the fixed list) → ETH from the rETH contract, ~1.174 ETH
  per rETH. 44 holders did exactly this in the observed week. Our user: 419.29 rETH → 492.36 ETH.
- **Liquidity-limited:** a burn can only take the ETH the rETH contract holds (3,631 ETH at the fork block, ~1.2% of the
  309k rETH supply). The largest wallet holder could burn only ~47% of their rETH ("Insufficient ETH balance for
  exchange"). A capital-type limit, not a permission.
- **The staking contrast:** Lido and ether.fi pay out only after permissioned batches; Rocket Pool lets any holder exit in
  one call, as far as the ETH on hand goes.
- 8 phishing tokens imitating "Rocket Pool" sat in this single wallet's history.

## Compound (V3 WETH market) — ✅ Exits cleanly

- **One call, by the holder:** `withdraw(WETH, amount)` on cWETHv3 (named by the fixed list; arguments from another
  holder's trace). Our user: 10.48 cWETHv3 → 10.48 WETH. Every burn in the week was sent by the holder (directly or via
  the same helper the user had deposited with).
- **Liquidity:** 26.7% of supplied WETH was on hand; the largest holder couldn't withdraw everything at once.
- 5 phishing tokens imitating "Compound" in this wallet's history.

## Curve (crvUSD/USDT pool) — 🟡 Harder but possible

- **Exit = one call on the pool, by the holder:** `0x1a4d01d2(LP, 0, min)` for one token or `0x5b36389c(LP, min, min)` for
  both. **Neither is nameable at T0** (none of the 3,120 fixed signatures appears in the logic); both learned from 10
  holders' traces.
- **Our user** held dust (0.00195 LP → 0.001 USDT + 0.001 crvUSD); the same call was simulated for holders with 95, 2,412,
  and 13,890 LP, all ✅.
- **~83% of the LP sits in two contracts** (one named "… Gauge Deposit"); that extra layer wasn't tested.

## Falcon Finance (USDf) — 🔴 Blocked

- **No on-chain redemption in the token's whole history.** All 131 burns (1.95B USDf) were sent by **one EOA** burning its
  own balance with `burn(address,uint256)`; that EOA got its USDf from **another EOA**, which received **plain transfers from
  61 holders** in 90 days.
- **Nothing visible comes back:** the top senders received no USDC/USDT or other collateral on Ethereum within 3 days.
- **Our user** (36,060 USDf, received by transfer, 0 ETH) can't burn: the error carries their address and a 32-byte
  permission identifier.
- **vs Ethena:** Ethena's redemptions are on-chain but role-gated; Falcon's exit isn't on-chain at all, as far as T0 can see.

## Kelp (rsETH) — 🔴 Blocked

- **Three-step queue on an escrow:** request (`0xc5a67b01`, rsETH in) → **unlock** (burns rsETH, brings the asset in) →
  claim (`0xd3a86833`, asset out). 5 unlocks this week, by 2 senders through `0xcbcd…`.
- **Proof (fork):** the claim fails before an unlock and pays after; a random address can't call the unlock; it can
  **relay** the operator's tx, but changing one value fails for everyone ("GS026") → authorization is **signed data**.
- **Our user:** request ✅ (10.36 rsETH in), claim ❌ now and after 7 days → 0 rsETH, 0 stETH.

## Fluid (fwstETH) — ✅ Exits cleanly

- ERC-4626 vault, not a proxy; the fixed list names `redeem`/`withdraw`; holders exit in one call themselves.
- Our user: 0.00796 fwstETH → 0.00827 wstETH. The wstETH comes from a shared liquidity contract holding 42,455 wstETH.
- Caveat: the rule picked a small vault (most of Fluid's wstETH is collateral elsewhere); the test position was tiny.

## Pendle (PT-reUSD-10DEC2026) — 🟡 Harder but possible, time-locked

- **A time lock, not a permission:** redeeming PT alone pays **0 until 10 Dec 2026** (day 48: 0; day 49: full), then
  103,889.86 PT → 93,709.36 SY → 93,709.36 reUSD, all by the holder. Before maturity, every observed redemption paired PT with YT.
- **Unnamed, multi-step, with traps:** the PT contract has no nameable function; each step is "send tokens to a contract,
  then call it" (two txs for a plain wallet); a PT-only redeem before maturity **succeeds and pays nothing**; the final call
  needs an exact 5th argument. All found by trial on the fork and recorded as corrections.

## Findings across protocols

1. **Six D4 dependencies, six designs.** Lido and ether.fi fund withdrawals through batches only a few actors can
   produce (Lido: send; ether.fi: approve, 3 of 3). Ethena has no queue: the redemption itself can only be submitted by
   role holders. Maple queues requests that only one "redeemer" processes. Falcon has no on-chain redemption at all: holders
   send USDf to an operator wallet. Kelp unlocks claims only with data signed for an operator contract. Morpho, Sky, Rocket Pool, Compound, and Fluid exit in one call (liquidity permitting).
   **Three liquid staking tokens, two designs:** Lido and ether.fi need permissioned batches; Rocket Pool lets any
   holder burn for ETH directly.
   **A familiar interface isn't a permissionless exit:** Maple's vault has the same `withdraw`/`redeem` as Morpho and
   Sky, but they're disabled.
2. **A time lock is different from a permission.** Pendle's PT can't be redeemed alone before its maturity date, but
   from that date on the holder exits without anyone else. Nothing can block it; nothing can speed it up.
3. **A dependency is different from a capital limit.** Lido can't be exited by anyone, with any amount of money,
   without the permissioned batch. Aave V3 can be fully exited by anyone with the capital to repay, but our user,
   with their own funds, only gets a **partial exit**, and working that out was very hard without assistance.
4. **Knowing what to do takes expert work at T0.** With only a node, users have to:
   - find their positions in a log scan full of spam and address-poisoning tokens (77 of 78 contracts for the Lido user);
   - work without function names: the only nameable exit function across three protocols was `withdraw` (Aave, Spark);
   - learn the exit from **other users' behavior** (log analysis, call traces);
   - explain blocks with traces, bytecode searches, and cause-and-effect tests.

   The chain had all the information, but a normal user couldn't realistically assemble it without expert tooling or
   AI assistance.
5. **The user's node must be an archive node** with full log history, a complete tx index, and debug tracing.
6. **Small traps a frontend normally hides:** Lido's 1,000 stETH per-claim limit (found only by probing), and Aave's
   withdrawal cap that shrinks every second (a simulated amount can fail moments later).
7. **Hosted signature databases (T2) shortcut a lot:** in the Aave run, one leaked a revert reason instantly
   (not used at T0).

## Effort per run (raw; SPEC open questions)

| Protocol | Queries / execution | Analysis | Wall clock | Note |
|----------|---------------------|----------|------------|------|
| Lido | ~8 min | ~55 min | 3h44m | Includes building the method and scripts |
| Aave V3 | ~4 min | ~35 min | 34 min | Method and scripts reused |
| Spark | ~9 min | ~22 min | 63 min | Includes a ~10 min hung query |
| Morpho | ~2.5 min | ~13 min | 2 min (+ step 5 later) | Vault selection (setup) took longer than the run |
| Sky | ~2.5 min | ~11 min | 3 min | |
| ether.fi | ~9.5 min | ~26 min | 17 min (+ steps 6–7 later) | |
| Ethena | ~20 min | ~11 min | 24 min | Discovery for a very busy wallet dominated |
| Maple | ~1.5 min | ~10 min | 3 min | |
| Uniswap | ~4.5 min | ~11 min | 5.5 min | |
| Rocket Pool | ~2 min | ~10 min | 3.5 min | |
| Compound | ~1 min | ~8 min | 1.5 min | |
| Curve | ~30s | ~8 min | 2 min | |
| Falcon | ~2.5 min | ~10 min | ~9 min | |
| Kelp | ~5 min | ~14 min | ~20 min | |
| Fluid | ~1 min | ~6 min | ~3 min | |
| Pendle | ~4 min | ~15 min | ~12 min | Includes a fork restart after a wrong probe |
