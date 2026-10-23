# The DeFi Walkaway Test — Results

Fork block **26,248,199** (2026-10-22 12:37:23 UTC) for every protocol. Method: [`SPEC.md`](SPEC.md).
Each row links to the full run log, where every claim is backed by a query, transaction, or trace.

**Status:** 6 protocols done (Lido, Aave V3, Spark, Morpho, Sky, ether.fi); Binance staked ETH paused; EigenCloud not started.
Protocols #6+ are beyond the top-5 rule (SPEC §7) and were added by hand (Morpho, then Sky and ether.fi), same method.

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
| 8 | [ether.fi (eETH)](runs/etherfi/2026-10-22-T0-all-removed.md) | `0xd26d…aacf` | 43.64 eETH | 🔴 **Blocked** | **D4:** batches fund the claims; anyone can execute one, but only data approved by **3 permissioned EOAs** works | 2,267,690 eETH (all of it) |

Removing the frontend, API, indexer, or default RPC (D1, D2, D3, D5) changes nothing in either run: neither T0 run used them.

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
- **vs Lido:** Lido restricts who can *send* the batch; ether.fi restricts who can *approve* it. Same dependency.

## Findings across protocols

1. **Two withdrawal queues, two D4 dependencies.** Lido and ether.fi both fund withdrawals through batches that
   only a few permissioned actors can produce (Lido: send; ether.fi: approve). Morpho and Sky exit in one call.
2. **A dependency is different from a capital limit.** Lido can't be exited by anyone, with any amount of money,
   without the permissioned batch. Aave V3 can be fully exited by anyone with the capital to repay, but our user,
   with their own funds, only gets a **partial exit**, and working that out was very hard without assistance.
3. **Knowing what to do takes expert work at T0.** With only a node, users have to:
   - find their positions in a log scan full of spam and address-poisoning tokens (77 of 78 contracts for the Lido user);
   - work without function names: the only nameable exit function across three protocols was `withdraw` (Aave, Spark);
   - learn the exit from **other users' behavior** (log analysis, call traces);
   - explain blocks with traces, bytecode searches, and cause-and-effect tests.

   The chain had all the information, but a normal user couldn't realistically assemble it without expert tooling or
   AI assistance.
4. **The user's node must be an archive node** with full log history, a complete tx index, and debug tracing.
5. **Small traps a frontend normally hides:** Lido's 1,000 stETH per-claim limit (found only by probing), and Aave's
   withdrawal cap that shrinks every second (a simulated amount can fail moments later).
6. **Hosted signature databases (T2) shortcut a lot:** in the Aave run, one leaked a revert reason instantly
   (not used at T0).

## Effort per run (raw; SPEC open questions)

| Protocol | Queries / execution | Analysis | Wall clock | Note |
|----------|---------------------|----------|------------|------|
| Lido | ~8 min | ~55 min | 3h44m | Includes building the method and scripts |
| Aave V3 | ~4 min | ~35 min | 34 min | Method and scripts reused |
| Spark | ~9 min | ~22 min | 63 min | Includes a ~10 min hung query |
| Morpho | ~2.5 min | ~13 min | 2 min (+ step 5 later) | Vault selection (setup) took longer than the run |
| Sky | ~2.5 min | ~11 min | 3 min | |
| ether.fi | ~6.5 min | ~20 min | 17 min | |
