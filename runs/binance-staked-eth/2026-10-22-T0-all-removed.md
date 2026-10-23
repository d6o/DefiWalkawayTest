# Run: Binance staked ETH (wBETH) — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Binance staked ETH (wBETH, Ethereum) |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0x066eb6929f18a72093c5afc9eba6dd476df876bc` (see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`), same block as every protocol (SPEC §6) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (Pay As You Go), standard JSON-RPC only |
| Operators | Diego + Claude |
| Started | 2026-10-23T02:26:27Z |

## Ground rules

- We play a user who has their **address** and knows they hold **wBETH** from **Binance staked ETH** (SPEC §1).
  They don't know any contract addresses or how to exit.
- Every address and function we use must come from **an earlier step's output** or from **basic knowledge**
  (SPEC §9). Function names only via the fixed list. Evidence rules: SPEC §10.

**Contamination disclosure:** both operators know what Binance and wBETH are. Picking the address (setup) used DefiLlama
and Ethplorer. Each step notes what knowledge it used.

## Setup notes (selection, SPEC §8)

- DefiLlama: one product on Ethereum, one asset (ETH, $8.72B at 2026-10-22 00:00 UTC). Receipt token: **wBETH**
  `0xa2E3…E2e1` ("Wrapped Binance Beacon ETH", totalSupply **3,175,326.49** at the fork block).
- **Concentration (Ethplorer list):** the top holder has **50.1%** of the supply, the **top 5 hold 99.2%**,
  the top 10 hold 99.6%. The 100th holder has 16.96 wBETH.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 02:26:27Z → 02:26:28Z (~1s).

| Query | Result |
|-------|--------|
| chainId / block | 1 / 26,248,199 |
| ETH balance | **0** |
| Nonce (txs sent) | **0** |
| Code | none (plain EOA) |

**Finding:** the user has **never sent a transaction** and has **no ETH for gas**. Any exit needs some ETH first.
That's a funds limit (SPEC §4), not a dependency, but a real barrier.

### Step 2: find every token contract the address touched, then find "wBETH"
**Time:** 02:26:28Z → 02:26:35Z (7s, `scripts/discover.py --match wBETH`), plus checking who sent the tokens (~2 min).
**Raw data:** `data/step2/raw_logs.json`, `contracts.json`, `contracts.md`.

| Contract | name() | symbol() | In | Out | Balance @ fork |
|----------|--------|----------|----|-----|----------------|
| `0xa2e3356610840701bdf5611a53974510ae27e2e1` | Wrapped Binance Beacon ETH | **wBETH** (exact match) | 2 | 0 | **16.9578** |
| `0xb64ef51c888972c908cfacf59b47c1afbc0ab8ac` | StorjToken | STORJ | 1 | 0 | 172.8155 |

**How the tokens arrived** (all three were plain ERC-20 `transfer()` calls, `0xa9059cbb`, sent by the token sender itself):

| Token | Block | Amount | Sender (EOA) | Sender's tx count (nonce) |
|-------|-------|--------|--------------|---------------------------|
| STORJ | 25,103,206 | (dust) | `0xdfd5293d8e347dfe59e90efd55b2956a1343963d` | **15,641,071** |
| wBETH | 25,103,260 | 0.19973 | `0x28c6c06298d514db089934071355e5743bf21d60` | **18,819,855** |
| wBETH | 25,103,306 | 16.75805569 | `0xdfd5293d8e347dfe59e90efd55b2956a1343963d` | 15,641,071 |

`0x28c6…1d60` is also the **#3 wBETH holder** in the Ethplorer list (40,341 wBETH).

**Contamination note:** Claude recognizes the two sender addresses from memory. Not used.

**Findings:**
1. **No spam, no look-alikes:** 2 contracts in total; one exact "wBETH" match with 16.9578.
2. **The user never minted wBETH.** It was sent to them by two EOAs that have each sent **15–19 million transactions**
   (very high-volume operators), within ~100 blocks of each other.
3. With no transactions of their own, the user's history gives **no hint** of how wBETH is created or redeemed.
EOF
