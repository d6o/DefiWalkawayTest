# Run: Lido — T0, all dependencies removed

| Field | Value |
|-------|-------|
| Protocol (experimenter only) | Lido |
| Scenario | D1–D5 all removed |
| Tier | **T0**: our node plus the chain only |
| Test address | `0xde804e46f67ebeecbe4c0a54efe33143cb7ab9e2` (see SPEC §8) |
| Fork | anvil, mainnet block 26,248,199 (`scripts/fork.sh`) |
| Node stand-in | anvil fork on top of an Alchemy archive RPC (free tier) |
| Operators | Diego + Claude |
| Started | 2026-10-22T12:41:06Z |

## Ground rules

- We play a user who has their **address** and knows they staked with **Lido** and got **stETH** (SPEC §1).
  They don't know any contract addresses or how to exit.
- Every address and function we use must come from **an earlier step's output** or from **general Ethereum standards** (ERC-20/721, EIPs, JSON-RPC).
  Nothing from protocol knowledge.
- Every step is logged with what we tried, what we found, and the time.

**Contamination disclosure:** both operators already know Lido. Picking the address (setup) used the stETH
address. Each step below notes what knowledge it used, so a reviewer can check it.

## Steps

### Step 1: what the node tells us about the address directly
**Time:** 12:41:06Z → 12:41:08Z (~2s)
**Knowledge used:** standard JSON-RPC only (`eth_getBalance`, `eth_getTransactionCount`, `eth_getCode`).

| Query | Result |
|-------|--------|
| chainId / block | 1 / 26,248,199 (2026-10-22T12:37:23Z) |
| ETH balance | 406.1339 ETH |
| Nonce (txs sent) | 36 |
| Code | none (plain EOA) |

**Finding:** the node tells us the address has sent **36 transactions**, but not **which** ones, and
nothing about which tokens or positions it holds. Standard Ethereum nodes have no
"transactions by address" or "tokens by address" lookup. Those come from indexers, which are removed here.

### Step 2: find every token contract the address touched, then find "stETH"
**Time:** scan 13:00:03Z → 13:01:12Z (69s, `scripts/discover.py`), then manual checks of the results (~5 min).
**Knowledge used:** standard event signatures only (ERC-20/721 `Transfer`, ERC-1155 `TransferSingle`/`TransferBatch`),
standard ERC-20 view functions (`name`, `symbol`, `decimals`, `balanceOf`), and the token symbol the user knows ("stETH").

**Method:**
1. `eth_getLogs` from block 0 to the fork block, for transfers **to** and **from** the address (logs via Alchemy, capped at the fork block).
2. For **every** contract that appeared: read `name()`, `symbol()`, `decimals()`, `balanceOf(user)` on the fork.
3. Mark contracts whose symbol is exactly "stETH" or contains it. **Nothing is filtered out.**

**Raw data:** `data/step2/raw_logs.json` (all logs), `data/step2/contracts.json` and `data/step2/contracts.md` (all 78 contracts).

**Logs found:** 45 transfers in, 83 transfers out, 9 ERC-1155 transfers in, 0 ERC-1155 out.

**All 78 contracts, grouped:**

| Group | Count | What it is | Rows in `contracts.md` |
|-------|-------|------------|------------------------|
| Exact symbol match "stETH" | **1** | `0xae7ab96520de3a18e5e111b5eaab095312d7fe84`, "Liquid staked Ether 2.0", balance **5,084.27** | 1 |
| Symbol contains "steth" | 2 | ERC-1155 spam NFTs advertising phishing sites (coinsteth.net, stethaward.net) | 2, 3 |
| ETH look-alikes with fake "outgoing" transfers | 29 | Tokens named ETH / ЕТН (Cyrillic) / EꓔH etc. that emit Transfer events **from** the user. All 83 outgoing logs come from these (see below) | 21–25, 28–32, 34–36, 41–43, 49–58, 64–66 |
| Other spam / phishing airdrops | 43 | "Visit X.com to claim rewards", fake airdrops, random meme tokens, look-alikes received | rest |
| Known-looking tokens with dust | 3 | WETH (0.0000001, sent by a spam contract), USDT (0.01), HEX (1,895) | 40, 63, 71 |

**Checks on the results:**
- **All 83 "outgoing" transfers are fake.** They're in 83 different transactions, and **none was sent by the user**.
  A token contract can emit a `Transfer` event naming any address as the sender. This is address poisoning:
  look-alike entries planted in the user's history so they copy the wrong address later.
- **How the stETH arrived:** one incoming transfer, a **mint** (from `0x0`) of 5,000 stETH at block 24,396,338 (2026-02-06),
  in tx `0x5d78c885…f1383`. That transaction was **sent by the user**, sent **5,000 ETH** directly to the same
  stETH contract, and succeeded. So the user put 5,000 ETH into this contract and got 5,000 stETH back.
- No other contract in the list mentions Lido or stETH in its name besides the 2 spam NFTs.

**Findings:**
1. At T0, finding the position took **one log scan plus one call per contract** (~70s) on a stand-in node with no range limit.
2. **Spam outnumbers the real position 77 to 1.** Of the 78 contracts, only one is a real position.
3. **The symbol alone wasn't enough, but it got close:** 1 exact match and 2 spam partial matches.
   For this address, no fake contract copied the symbol "stETH" exactly.
4. **The strongest T0 proof the contract is real comes from the user's own history:** they sent 5,000 ETH to this
   contract in a transaction they signed, and it minted their tokens. That doesn't depend on names, symbols, or any indexer.
5. **Logs can't be trusted on their own.** "Outgoing" transfers can be faked, so any discovery method has to check who sent the transaction.

**Position found:** 5,084.27 stETH at `0xae7ab96520de3a18e5e111b5eaab095312d7fe84`.
Whether this is the **only** Lido position (e.g. other forms the protocol uses) isn't known yet from the user's side.

### Step 3a.1: is the stETH contract a proxy, and where does its logic live?
**Time:** 13:14:49Z → 13:15:00Z (~11s of queries) plus reading the results (~2 min).
**Knowledge used:** standard proxy storage slots (EIP-1967, EIP-1822, legacy OpenZeppelin), EVM opcodes, the standard
ERC-20 `name()` selector, and the node's `debug_traceCall` with `callTracer`.
`debug_traceCall` isn't part of the official JSON-RPC spec, but self-run clients (Geth, Reth, Erigon) and anvil support it.

**Bytecode** (`data/step3/steth_code.hex`, disassembly in `data/step3/steth_code.asm`):
- 1,035 bytes: 1 `DELEGATECALL`, 1 `CALL`, 3 `SLOAD`. Small code with a `DELEGATECALL` looks like a proxy.
- **All standard proxy slots are empty** (EIP-1967 implementation / beacon / admin, EIP-1822, legacy OZ).
  So it's a proxy, but not a standard kind.

**Trace of `name()`** (`data/step3/trace_name.json`):
```
CALL         user  -> 0xae7ab965…7fe84 (stETH)               name()
  CALL         stETH -> 0xb8ffc3cd…88dc                       0xbe00bbd8(key1, key2) → returns 0x028271e3…cdb0
    DELEGATECALL 0xb8ffc3cd… -> 0x2b33cf28…4425              (that contract is itself a proxy)
  DELEGATECALL stETH -> 0x028271e3…cdb0                       name()
```
- On **every call**, stETH asks another contract (`0xb8ffc3cd6e7cf5a098a1c92f48009765b24088dc`) which logic to use,
  passing two 32-byte keys:
  - `key1 = 0xf1f3eb40f5bc1ad1344716ced8b8a0431d840b5783aea1fd01786bc26f35ac0f`
  - `key2 = 0x3ca7c3e38968823ccb4c78ea688df41356f182ae1d159e4ee608d30d68cef320`
  The keys are hashes and we can't tell what they mean from the chain. The lookup function `0xbe00bbd8` is unnamed for now.
- That contract answers **`0x028271e30a695c0527a0c50ca30603fed004cdb0`** (23,855 bytes), and stETH runs that code.
- The lookup contract is itself a proxy (898 bytes) running code at `0x2b33cf282f867a7ff693a66e11b0fcc5552e4425` (12,028 bytes).

**Findings:**
1. **The stETH logic lives at `0x028271e3…cdb0`.** That's the code we need to read to find an exit.
2. **Standard proxy checks missed it. A trace found it in one call.** At T0, tracing is more reliable than checking known slots.
3. **The logic can be swapped:** whoever controls the lookup contract can change which code stETH runs.
   The exit path depends on that staying the same. Who controls it isn't known yet from the user's side.

### Step 3a.2: list the logic contract's functions and try to name them
**Time:** 14:12:55Z → 14:12:56Z (~1s, `scripts/selectors.py`) plus reading the results (~3 min).
**Knowledge used:** EVM opcodes, basic ERC-20/721/1155 signatures, and the fixed list (SPEC §9, 3,120 signatures).

**Method:** parse the bytecode and record **every** 4-byte constant (`PUSH4`). Flag the ones the function dispatcher
compares against (`EQ`), since those are the contract's functions. Then match them against basic signatures and the fixed list.

**Raw data:** `data/step3/selectors_impl.json` (logic contract), `data/step3/selectors_proxy.json` (proxy).

**Logic contract `0x028271e3…cdb0` (23,855 bytes):**

| | Count |
|-|-------|
| All `PUSH4` constants | 114 |
| Used by the dispatcher (functions) | 87, of which `0xffffffff` is almost certainly a bit mask, not a function, so **86 functions** |
| Named by basic knowledge | **9**: the ERC-20 core (`name`, `symbol`, `decimals`, `totalSupply`, `balanceOf`, `transfer`, `transferFrom`, `approve`, `allowance`) |
| Named by the fixed list | **0** |
| **Unnamed** | **77** |
| Other `PUSH4` constants (not functions) | 27. One is `0xbe00bbd8`, the same lookup call we saw in the step 3a.1 trace |

**Proxy `0xae7ab965…7fE84` (1,035 bytes):** 5 functions of its own, all unnamed (`0x4555d5c9`, `0x48a0c8dd`, `0x5c60da1b`,
`0x80afdea8`, `0xd4aae0c4`). Two of them (`0x80afdea8`, `0xd4aae0c4`) also exist in the logic contract.

**Clue from the user's own history:** the user's 5,000 ETH deposit (tx `0x5d78c885…f1383`) called **`0xa1903eab`** with
one argument that looks like an address (`0x11d00000000000000000000000000000000011d0`). That selector is one of the 77 unnamed functions.
So **even the function the user used to get in can't be named** with the fixed list.

**Contamination note:** Claude recognizes some of these selectors from memory. Naming them that way would break
SPEC §9, so they stay unnamed in this run.

**Findings:**
1. **At T0, 77 of the 86 functions can't be named.** Only the ERC-20 basics are recognizable.
2. **None of the 20 verbs matched** with any common argument types. The exit function, whatever it is, has a name or
   arguments outside the fixed list, or it lives in another contract.
3. **The user can see what they called to get in (`0xa1903eab`), but not what to call to get out.**
4. Next we need behavior, not names: what other users call, and which calls send value back.

### Step 3b, part 1: where do stETH holders send their stETH?
**Time:** 14:22:13Z → 14:23:01Z (48s, `scripts/flows.py`) plus reading the results (~5 min).
**Knowledge used:** the standard `Transfer` event, `eth_getLogs` filtered by the emitting contract, `eth_getCode`.
**Window:** the 7 days before the fork: blocks 26,197,800 → 26,248,199 (2026-10-15 12:05Z → 2026-10-22 12:37Z).

**Method:** get every `Transfer` log **emitted by the stETH contract** in the window. Only the contract itself can emit these,
so they can't be faked like in step 2. Group them by recipient and by sender, and check every address for code.

**Raw data:** `data/step3b/raw_transfer_logs.json` (all 14,102 logs), `data/step3b/flows.json`,
`data/step3b/recipients.md` (all 2,799 recipients), `data/step3b/senders.md` (all 2,404 senders).

**Totals:**

| | |
|-|-|
| Transfer logs / distinct txs | 14,102 / 7,942 |
| stETH moved | 421,315 |
| Recipients | 2,799 (388 contracts, 2,109 wallets, 302 wallets with EIP-7702 delegation) |
| Share of stETH sent to contracts | **80.9%** |
| Mints (from `0x0`) | 1,352 transfers, 54,088 stETH, to 855 addresses |
| **Burns (to `0x0`)** | **0** |

**Top contract recipients by distinct senders** (how many independent users send stETH there):

| # | Contract | Code (B) | Senders | Transfers | stETH | % |
|---|----------|----------|---------|-----------|-------|---|
| 1 | `0x889edc2edab5f40e902b864ad4d7ade8e412f9b1` | 2,497 | **425** | 616 | 63,592 | 15.09% |
| 2 | `0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0` | 6,492 | 195 | 746 | 56,624 | 13.44% |
| 3 | `0x9008d19f58aabd9ed0d60971565aa8510560ab41` | 16,165 | 167 | 425 | 5,412 | 1.28% |
| 4 | `0x74de5d4fcbf63e00296fd95d33236b9794016631` | 1,163 | 86 | 109 | 60 | 0.01% |
| 5 | `0x0cef320d0c5793ade37964e2661a033771e53cd5` | 21,478 | 69 | 341 | 6,867 | 1.63% |

**Top contract recipients by amount:**

| # | Contract | Code (B) | Senders | Transfers | stETH | % |
|---|----------|----------|---------|-----------|-------|---|
| 1 | `0xe76c52750019b80b43e36df30bf4060eb73f573a` | 2,497 | 2 | 16 | 76,174 | **18.08%** |
| 2 | `0x889edc2edab5f40e902b864ad4d7ade8e412f9b1` | 2,497 | 425 | 616 | 63,592 | 15.09% |
| 3 | `0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0` | 6,492 | 195 | 746 | 56,624 | 13.44% |
| 4 | `0x51c72848c68a965f66fa7a88855f9f7784502a7f` | 20,805 | 11 | 171 | 19,571 | 4.65% |
| 5 | `0x53bcdcc18f3bada2cd749a72b28d55eb7abb3dd2` | 9,343 | 2 | 39 | 15,290 | 3.63% |

**Checks:**
- `0x889e…f9b1` and `0xe76c…573a` run **identical code** (same code hash `0x9bc25fa4…2100`).
  Two deployments of the same contract: one used by hundreds of senders, one by 2 senders moving large amounts.
- `0x889e…f9b1` has **by far the most independent senders** (425, more than twice the next one).

**Contamination note:** Claude recognizes several of these addresses from memory. That isn't used; the rankings and
the candidate list below come only from the numbers above.

**Findings:**
1. **No burns at all in 7 days**, but 1,352 mints. Looking for `Transfer` to `0x0` (the usual sign that tokens were
   redeemed) finds nothing here. Either nobody exited this way, or exits don't show up as standard burn events.
2. **Most stETH (80.9%) goes to contracts.** The question is which of them give ETH back.
3. **One contract stands out by usage:** `0x889e…f9b1`, with 425 independent senders and 15% of the volume.

**Candidates for part 2** (rule: top 5 by distinct senders ∪ top 5 by amount, 8 contracts):
`0x889e…f9b1`, `0x7f39…2ca0`, `0x9008…ab41`, `0x74de…6631`, `0x0cef…3cd5`, `0xe76c…573a`, `0x51c7…7a7f`, `0x53bc…3dd2`.

### Step 3b, part 2 prep: can we trace past transactions?
**Time:** ~14:30Z (~2 min).
**Sample tx:** `0xcfedd172e8e43de4dc82ddd2d6a194218936eb97fe402c7ff9dc9015afd5c87b` (a transfer into `0x889e…f9b1` from the window).

| Method | Where | Result | Time |
|--------|-------|--------|------|
| `debug_traceTransaction` + `callTracer` | fork (anvil) | ✅ works | ~1.6s |
| `debug_traceTransaction` + `callTracer` | Alchemy | ✅ works, **byte-identical** to the fork's output | ~1.5s |
| `trace_transaction` (Parity-style) | Alchemy | ✅ works | ~1.2s |

The fork forwards traces of past transactions to Alchemy (seen in the anvil log), so both give the same answer.

**Decision:** use `debug_traceTransaction` with `callTracer`. Self-run Geth, Reth, Erigon, and Nethermind all support it;
`trace_transaction` isn't available in Geth. Tracing past transactions needs a node that keeps historical state (archive).

**Finding:** following native ETH needs **traces**, because ETH transfers don't emit events.
That adds a requirement to the user's node: archive state plus tracing enabled.

### Step 3b, part 2, phase 1: what did users call when their stETH moved into a candidate?
**Time:** 14:39:58Z → 14:40:30Z (33s, `scripts/txgroups.py`) plus reading the results (~5 min).
**Knowledge used:** `eth_getTransactionByHash` (batched); calldata layout (4-byte selector + 32-byte words).

**Method:** for **every** stETH transfer into one of the 8 candidates, fetch the transaction and record the sender, `to`,
selector, ETH sent, calldata length, and whether the stETH sender is the transaction sender (user moved their own stETH).
Group by `to` + selector; pick 3 examples per group (first / middle / last by block).

**Raw data:** `data/step3b/phase1/txs.json` (all 2,213 txs with full calldata), `data/step3b/phase1/groups.json`,
`data/step3b/phase1/groups.md` (all 285 groups).

**Totals:** 2,213 transactions, 926 senders, **285 groups**, 474 examples by the 3-per-group rule.

**Groups where the user called a candidate directly** (9 groups, 943 txs = 43% of all, 27 examples):

| tx.to | Selector | Txs | Senders | Moved own stETH | Sent ETH | Calldata words |
|-------|----------|-----|---------|-----------------|----------|----------------|
| `0x889e…f9b1` | `0xacf41e4d` | 281 | 256 | 281 | 0 | 9 (279), 10 (2) |
| `0x7f39…2ca0` | `0xea598cb0` | 169 | 131 | 169 | 0 | 1 |
| `0x889e…f9b1` | `0xd6681042` | 117 | 115 | 117 | 0 | 4 |
| `0x889e…f9b1` | `0x7951b76f` | 32 | 29 | **0** | 0 | 9 (31), 12 (1) |
| `0x0cef…3cd5` | `0x1fff991f` | 26 | 19 | 13 | 6 | 43–671, varies |
| `0x9008…ab41` | `0x13d79a0b` | 271 | **13** | 0 | 0 | 63–1,517, varies |
| `0x7f39…2ca0` | *(no calldata)* | 8 | 5 | 0 | **8** | 0 |
| `0x53bc…3dd2` | `0x627888cb` | 28 | 1 | 0 | 0 | 1 |
| `0x53bc…3dd2` | `0x5e70c733` | 11 | 1 | 0 | 0 | 2 |

**Why the tail is so long:** 216 of the 285 groups have a **single sender**. Most of them share a selector across many
*different* contracts, each used by one person:

| Selector | Different contracts | Txs | Contracts with 1 sender |
|----------|---------------------|-----|-------------------------|
| `0xe9ae5c53` | 42 | 46 | 42 |
| `0x9265bb9d` | 38 | 39 | 37 |
| `0x6a761202` | 15 | 21 | 15 |
| `0x1cff79cd` | 8 | 10 | 8 |

The same function on dozens of one-user contracts looks like **personal smart-contract wallets**: the user calls their own
wallet, and the real action is nested inside. Grouping by the outer call can't show what those users did; only a trace can.

**Contamination note:** Claude recognizes some of these selectors from memory, including one (`0xd6681042`) that was
printed earlier in this session, before the contaminated exit map was deleted. None of that is used here.

**Findings:**
1. **Users mostly call a few contracts directly.** 9 groups cover 43% of all transactions, with short, fixed-length
   calldata (1, 2, 4, 9 words). That's what simple, user-facing functions look like.
2. **`0x889e…f9b1` has three direct functions** used by hundreds of people. Two move the sender's own stETH
   (`0xacf41e4d`, `0xd6681042`). The third (`0x7951b76f`) moves stETH that **isn't** the sender's.
3. **Some groups look like professional actors**, not users: `0x9008…ab41`/`0x13d79a0b` has 271 txs from only 13 senders,
   with very long, varying calldata.
4. **Smart-contract wallets hide the real call.** For those users, the outer transaction doesn't show what they did.

### Step 3b, part 2, phase 2: trace the direct groups — what does the user get back?
**Time:** 14:48:50Z → 14:48:57Z (27 traces in 6.4s, `scripts/tracetx.py --direct-only`) plus reading the results (~5 min).
**Knowledge used:** `debug_traceTransaction` (`callTracer`, `withLog`), standard `Transfer` events (3 topics = ERC-20, 4 topics = ERC-721).

**Raw data:** `data/step3b/phase2/traces/*.json` (all 27 full traces), `data/step3b/phase2/summaries.json`.

| tx.to / selector | What the user sent | What the user got back (same tx) | ETH back |
|------------------|--------------------|----------------------------------|----------|
| `0x889e…f9b1` / `0xacf41e4d` | stETH (0.000005 – 2.04) | **a newly minted ERC-721 NFT from `0x889e…f9b1`** (ids 138,796 → 139,407) | 0 |
| `0x889e…f9b1` / `0xd6681042` | stETH (0.0013 – 0.024) | **a newly minted ERC-721 NFT from `0x889e…f9b1`** (ids 138,810 → 139,410) | 0 |
| `0x889e…f9b1` / `0x7951b76f` | `0x7f39…2ca0` tokens (0.59 – 178) | **a newly minted ERC-721 NFT from `0x889e…f9b1`** (ids 138,797 → 139,377) | 0 |
| `0x7f39…2ca0` / `0xea598cb0` | stETH | `0x7f39…2ca0` ERC-20 tokens at **~0.802 per stETH** (0.802315 → 0.802022 over the week) | 0 |
| `0x7f39…2ca0` / *(plain ETH)* | ETH | `0x7f39…2ca0` ERC-20 tokens (~0.80 per ETH) | 0 |
| `0x0cef…3cd5` / `0x1fff991f` | varies | varies: `0x7f39` tokens → **3.0 ETH**; ETH → stETH; stETH → WETH (1:0.9999) | 1 of 3 |
| `0x9008…ab41` / `0x13d79a0b` | nothing | nothing; the sender moves other people's tokens | 0 |
| `0x53bc…3dd2` / `0x627888cb`, `0x5e70c733` | nothing | nothing; the sender moves tokens held elsewhere | 0 |

All 27 traces succeeded. Every example within a group behaved the same way, so no group needs more examples (rule from phase 1).

**Reading it (chain only):**
- **`0x889e…f9b1` takes stETH (or `0x7f39` tokens) and gives the user an NFT, with no ETH in the same tx.**
  The NFT ids go up steadily over the week. *Hypothesis (not yet shown):* a two-step exit, where the NFT is later
  redeemed for ETH. See phase 2b for what the chain does and doesn't show.
- **`0x7f39…2ca0` swaps stETH for another token** at a ratio that moves slowly. It also accepts ETH directly.
  The user gets a different token, **not ETH**, so this isn't an exit by itself. But `0x889e` also accepts this token.
- **`0x0cef…3cd5` behaves like a trading router:** different inputs and outputs each time, sometimes ETH.
  That's the secondary-market **fallback** (SPEC §4), not the protocol's own exit.
- **`0x9008…ab41` and `0x53bc…3dd2` are operated by a few professional senders** who move other people's tokens.
  They aren't something a regular user calls to exit.

**Findings:**
1. **The strongest exit candidate is `0x889e…f9b1`:** hundreds of users hand in stETH and get back an NFT.
2. **No direct path returns ETH in the same transaction** except trading routes. So the protocol's own exit, if it's
   `0x889e`, takes at least two transactions, and something has to happen in between.
3. **Next we have to follow the NFT:** when, how, and by whom it gets redeemed for ETH.

### Step 3b, part 2, phase 2b: is the NFT tied to the deposit? (what the chain shows)
**Time:** ~14:55Z (~3 min).
**Knowledge used:** event layout (topics + 32-byte data words). Nothing else.

**Correction:** phase 2 first described the NFT as a "receipt". The data then only showed that an NFT was minted to the
user in the same tx they sent stETH. That wording was an interpretation and has been replaced by a hypothesis.

**Method:** in each of the 9 `0x889e` example traces, decode the contract's own event (`topic0 = 0xf0cb471f…`), the only
event `0x889e` emits besides the NFT `Transfer`.

| Field | Content | Evidence |
|-------|---------|----------|
| `topic1` | **NFT id** | `0x21e2c` = 138,796, `0x21f8e` = 139,150, … equal to the NFT minted in the same tx, in all 9 examples |
| `topic2`, `topic3` | **The user** (same address twice in all examples) | Always the tx sender |
| `data[0]` | **stETH amount handed in**, exact to the wei | e.g. 2,040,000,000,000,000,000 in → 2,040,000,000,000,000,000 recorded |
| `data[1]` | Same amount in a second unit, ≈ 0.802 × `data[0]` | Same ratio as the `0x7f39` wrapper (phase 2) |

When the user hands in `0x7f39` tokens (`0x7951b76f`), `data[0]` is the **stETH equivalent** (178.34 tokens → 222.29),
and `data[1]` is the token amount (minus 1 wei). So the contract converts every deposit into one stETH amount.

**What the chain shows:** `0x889e` keeps an on-chain record linking **NFT id ↔ user ↔ exact stETH amount**.
That's a numbered claim tied to a specific deposit.

**What it doesn't show yet:** that the claim can be exchanged for ETH, when, or under what conditions.
That needs the redemptions (next step).

### Step 3c: everything `0x889e…f9b1` recorded in the window
**Time:** 15:18:16Z → 15:18:31Z (15s, `scripts/events.py`) plus analysis (~10 min).
**Knowledge used:** `eth_getLogs` by contract address (any event), `eth_getTransactionByHash`, standard ERC-721 `Transfer`.

**Raw data:** `data/step3c/raw_logs.json` (all 2,580 logs), `data/step3c/txs.json` (all 1,144 txs), `data/step3c/events.json`.

**Event types emitted by `0x889e` (all 5):**

| topic0 | Topics / data words | Logs | Txs | Senders | Main calls (tx.to / selector) |
|--------|---------------------|------|-----|---------|-------------------------------|
| `0xddf252ad` (ERC-721 `Transfer`) | 4 / 0 | 1,283 | 1,136 | 728 | mixed |
| `0x6ad26c5e` | 4 / 1 | **665** | 546 | **484** | `0x889e`/`0xe3afe0a3` (456), `0x889e`/`0xf8444436` (26), others |
| `0xf0cb471f` (deposit record, phase 2b) | 4 / 2 | 616 | 588 | 451 | `0x889e`/`0xacf41e4d`, `0xd6681042`, `0x7951b76f`, others |
| `0x197874c7` | 3 / 3 | **8** | 8 | 6 | `0x1cff79cd` on 6 different contracts |
| `0x6bd5c950` | 1 / 2 | **8** | 8 | 6 | same 8 txs as above |

**NFT transfers:** 616 mints (ids 138,796 → 139,411), **665 burns** (ids 1,283 → 139,310), 2 transfers between addresses.
`0x6ad26c5e` occurs exactly 665 times, once per burn, so it records something about each burned claim.

**The 8-times-a-week events: one batch per day, in id order**

| Date (UTC) | Block | Sender | `0x197874c7` ids | stETH amount | Second unit | `0x6bd5c950` data |
|------------|-------|--------|------------------|--------------|-------------|-------------------|
| 10-15 12:21 | 26,197,882 | `0x4d3ad7e8…` | 138,692 → 138,787 | 16,645.91 | 13,356.09 | [138,692, 138,796] |
| 10-16 12:23 | 26,205,073 | `0x2ae828f1…` | 138,788 → 138,823 | 4,612.82 | 3,700.94 | [138,788, 138,890] |
| 10-17 12:22 | 26,212,244 | `0x2ae828f1…` | 138,824 → 138,919 | 18,285.66 | 14,670.51 | [138,824, 138,983] |
| 10-18 12:21 | 26,219,417 | `0xc1025896…` | 138,920 → 138,991 | 1,891.88 | 1,517.74 | [138,920, 139,070] |
| 10-19 12:23 | 26,226,596 | `0x82a821e8…` | 138,992 → 139,094 | 5,948.08 | 4,771.59 | [138,992, 139,157] |
| 10-20 12:22 | 26,233,767 | `0x82a821e8…` | 139,095 → 139,196 | 10,174.49 | 8,161.53 | [139,095, 139,251] |
| 10-21 12:21 | 26,240,942 | `0x7abc999c…` | 139,197 → 139,265 | 12,381.90 | 9,931.67 | [139,197, 139,329] |
| 10-22 12:23 | 26,248,129 | `0x565f04cb…` | 139,266 → 139,310 | 6,230.07 | 4,996.96 | [139,266, 139,408] |

- **Every day at ~12:21–12:23 UTC**, one tx covers a range of claim ids. Each range starts right after the previous one ends:
  claims are processed **in order, in daily batches**.
- The stETH amount and the second unit keep the same ~0.802 ratio seen in phase 2b. The 3rd data word is a timestamp on that day.
- `0x6bd5c950`'s second value is higher than the batch's last id: the newest claims that existed at that moment.
  So **not every waiting claim is included**; each batch stops short of the newest ones.
- The batch tx is sent by **6 different addresses**, always through a contract function `0x1cff79cd` (6 different contracts).
  These are the same contracts that moved large amounts of stETH into `0xe76c…573a` (step 3b, phase 1).

**Claims are only burned after they're in a batch:**
- The highest burned id (**139,310**) is exactly the end of the last batch (10-22: 139,266 → **139,310**). No claim above it was burned.
- 343 claims were minted **and** burned within the window. Time from mint to burn: **min 16.3h, median 39.6h, max 146.3h.**
- 322 burned claims were minted **before** the window, the oldest being id **1,283**. Very old claims are still being redeemed.
- 273 claims minted in the window aren't burned yet. Ids above 139,310 haven't been processed by any batch.

**Contamination note:** `0xe3afe0a3` and `0xf8444436` were printed earlier in this session (during the deleted map's
verification). Claude recognizes them. Not used here; the analysis relies only on counts, ids, and timing.

**Findings:**
1. **Claims are processed in daily batches, in id order, and burned only after.** The data is consistent with:
   hand in stETH → get a numbered claim → wait for a daily batch to include it → redeem (burn).
2. **The wait is 16h to 6 days**, median ~40h, in this week.
3. **The batches come from a handful of senders through special contracts**, once a day, at the same time.
   Whether *anyone* could send that batch, or only those actors, is the key question for D4.
4. Still not shown: that burning a claim pays **ETH** to the holder. Next: trace the redemptions and a daily batch.

### Step 3d: trace redemptions and daily batches; who is allowed to send the batch?
**Time:** ~15:25Z → ~15:40Z (traces + `eth_call` tests, ~15 min including analysis).
**Knowledge used:** `debug_traceTransaction`, `eth_call` against historical state with a chosen `from`, ABI layout of
dynamic arrays (offset / length / items), standard `Error(string)` revert format.

**Raw data:** `data/step3c/trace_selection.json`, `data/step3c/traces/*.json` (7 traces), `data/step3c/permission_tests.json`.
**Examples (first / middle / last rule):** 3 redemptions via `0x889e`/`0xe3afe0a3`, 1 via `0x889e`/`0xf8444436`, 3 of the 8 daily batches.

**Redemptions: claim → ETH, 1:1** (4 of 4)

| Tx | Function | Claim | Deposited (stETH) | Paid (ETH) | Ratio |
|----|----------|-------|-------------------|------------|-------|
| `0x918aef2f…` | `0xe3afe0a3` | 138,530 | 37.000000 | 37.000000 | 1.000000 |
| `0x5a654d23…` | `0xe3afe0a3` | 135,941 | 0.001378 | 0.001378 | 1.000000 |
| `0xb2ec7bbb…` | `0xe3afe0a3` | 136,395 | 0.202871 | 0.202871 | 1.000000 |
| `0xd7174abf…` | `0xf8444436` | 138,751 | 0.655140 | 0.655140 | 1.000000 |

- In every case: the claim holder calls `0x889e`, **`0x889e` sends ETH to the holder**, the NFT is burned, and
  `0x6ad26c5e` records (claim id, holder, holder, ETH paid).
- Deposited amounts come from each claim's own deposit record (`0xf0cb471f`, looked up by claim id as `topic1`).
- **Two ways to redeem:**
  - `0xf8444436`: calldata is **just the claim id** (1 word).
  - `0xe3afe0a3`: **two lists**: claim ids, plus **one extra number per claim** (1,247 / 1,222 / 1,226). The number grows by
    ~1 per day between older and newer claims, so it's probably the index of the daily batch that covered the claim.
    A user taking this route has to work that number out.

**Daily batch: where the ETH comes from** (batch `0xec75ab44…`, 10-15):
```
CALL  EOA 0x4d3a…3f86 -> its contract 0xd524…6bdb     0x1cff79cd   (1,476 bytes calldata)
  CALL  0xd524… -> 0x852d…3cee                        0x11a78d23   (proxy → logic 0xe4f0…9136)
    CALL  0x852d… -> 0xfddf…2999 (twice), 0x889e…f9b1 (0x96992fed), 0x23ed…cddf (0xd68bcf5c), 0x5db4…ad6c
      ...  0x388c…9297 -> stETH   ETH 28.2710      (0x4ad509b2)
      ...  0xb9d7…293f -> stETH   ETH 5,952.8896   (0x78ffcfe2)
      ...  stETH -> 0x889e…f9b1   ETH 16,645.9094  (0xb6013cef)   ← exactly that batch's stETH amount
```
**ETH reaches the claims contract only inside the daily batch,** sent by the stETH contract.

**Is the batch permissioned?** Same calldata, same state (block before the batch), only the caller changed:

| Call | Original caller | Random address `0x1234…5678` |
|------|-----------------|------------------------------|
| EOA → its contract (`0x1cff79cd`) | ✅ success (3/3) | ❌ revert, error `0x1db3b859` (3/3) |
| that contract → `0x852d…3cee` (`0x11a78d23`) | ✅ success (3/3) | ❌ revert, error `0x23dada53` (3/3) |

Only the caller changed, so the revert is a **check on who is calling**. 6 different senders were allowed this week.
Who decides that list can't be seen yet from the user's side.

**Balances of `0x889e` at the fork block:** **29,692.83 ETH** and **4,204.19 stETH**.
That's consistent with ETH already set aside for processed-but-unredeemed claims, and stETH from claims still waiting for a batch.

**Contamination note:** `0x852d…3cee` appeared earlier in this session (during the deleted map's verification) and Claude
knows what it is. Not used; everything above comes from traces, event data, and the caller test.

**Findings:**
1. **The protocol's exit works and pays 1:1:** hand in stETH → numbered claim (NFT) → wait for a daily batch → redeem for ETH.
   Redeeming is something the holder does alone, with just the claim id (`0xf8444436`).
2. **Claims only get ETH through a daily batch that only a small, permissioned set of actors can send.**
   A random caller is rejected, with the same data and the same state. **This is the D4 dependency, found at T0.**
3. **If those actors stop:** claims already processed (ids ≤ 139,310) can still be redeemed, since the ETH is already in
   `0x889e`. New claims stay unprocessed; the stETH sits in `0x889e` and the holder can't get ETH for it.
4. **At T0, the user has to discover** the two-step design, the daily schedule, and the simple redemption function
   **entirely from other users' behavior.** Names, ABIs, and docs weren't available, and none of the 20 verbs matched.

### Step 4: run the exit for our user on the fork
**Time:** 16:12:24Z → 16:15:21Z (~3 min).
**Knowledge used:** calldata observed from other users (step 3b), standard ERC-20 `approve`/`allowance`, ABI encoding
of `(uint256[], address)`, `eth_call` to test before sending, anvil time travel (`evm_increaseTime`, `anvil_mine`).
**Fork snapshot before this step:** `0x0` (`data/step4/snapshot.txt`), so this step can be rolled back.

**4.1 Work out the call.** The `0xd6681042` calldata from 117 real txs always has the same layout:

| Word | Value | Meaning |
|------|-------|---------|
| 0 | 64 | Offset to a dynamic array |
| 1 | sender's address | Owner of the claim NFT |
| 2 | 1 | Array length |
| 3 | amount | stETH to hand in |

So the arguments are **`(uint256[] amounts, address owner)`**. The largest single amount handed in that week was exactly **1,000.0 stETH**.

**4.2 Approve.** Allowance to `0x889e` was 0. `approve(0x889e, 5,084.27 stETH)`: tx `0x9883610a…`, success, 65,388 gas.

**4.3 Find the limits by testing (`eth_call`, nothing sent):**

| Amount in one claim | Result |
|---------------------|--------|
| 5,084.27 stETH (all) | ❌ custom error `0x8ebfb78d(amount)` |
| 1,000 stETH | ✅ |
| 1,000 stETH + 1 wei | ❌ `0x8ebfb78d(amount)` |
| 100 wei | ✅ |
| 99 wei | ❌ custom error `0xb89b87c8` |

**Limits: max 1,000 stETH and min 100 wei per claim.** Found only by probing; nothing on-chain says so in readable form.

**4.4 Hand in everything in one tx:** amounts `[1000, 1000, 1000, 1000, 1000, 84.270077436142030282]`.
- tx `0x7aca87d33db4e42178ccc5ebddc5e91d13c3cb3739e6f4e7a980e9029b993b9b`, block 26,248,201, success, **802,075 gas**.
- **6 claims minted to the user: ids 139,412 → 139,417.** Deposit records total 5,084.27 stETH.
- User afterwards: **6 wei stETH left** (rounding dust), 6 claim NFTs. Receipt: `data/step4/handin_receipt.json`, ids: `data/step4/claims.json`.

**4.5 Try to redeem with no batch (D4 removed):**

| When | Call | Result |
|------|------|--------|
| Right after hand-in | redeem 139,412 and 139,417 (`0xf8444436`) | ❌ custom error `0x4ae50228(claim id)` |
| A processed claim that isn't ours (139,310) | `0xf8444436` | ❌ a **different** error, `0xf0e0cc2d(claim id)` |
| **7 days later, no batch sent** | redeem 139,412 and 139,417 | ❌ same `0x4ae50228(claim id)` |

- Time travel: `evm_increaseTime` 7 days, then mining blocks. Block time reached **2026-10-29 16:13Z**. The mining request timed
  out after ~9,800 of the 50,400 blocks; the block **timestamp** still moved the full 7 days.
- `0x4ae50228` carries our claim id and doesn't change with time, while a processed claim gives a different error
  (`0xf0e0cc2d`, likely an ownership check). Combined with step 3c (burns never exceed the last batch), the reading is:
  **`0x4ae50228` = this claim hasn't been processed by a batch.**
- User ETH after all of this: 406.13 ETH (only gas spent). **No ETH recovered.**

**Result for this scenario (T0, all dependencies removed): 🔴 Blocked.**
The user found the position, worked out the exit from other users' behavior, and handed in all 5,084.27 stETH, but
**can't get ETH without the permissioned daily batch**. Waiting doesn't help. The user ends holding 6 claims that only a
privileged actor can unlock. The trading-router route seen in step 3b (stETH/`0x7f39` → ETH) remains the **fallback** (SPEC §4).

### Step 5: proof that the daily batch is the only missing piece
**Time:** 16:23:53Z → 16:25:03Z (~1 min of execution).
**Setup:** a second fork at **block 26,248,128**, one block before the real 10-22 batch (`0x234e3a63…`, which covered
claims 139,266 → 139,310). Our own claims can't be used: a real batch only covers claims that existed before it, and
building a new valid batch isn't realistic. So we use a claim the real batch covered.
**Claim:** **139,267**, owned by plain wallet `0xa79b28eb847e729638b23b6734837dd86b1edeee` (rule: first wallet-owned claim in
the batch range, `data/step5/claim_choice.json`). `ownerOf(139267)` on the fork confirms the owner.

| # | Action (same claim, same starting state) | Result |
|---|------------------------------------------|--------|
| A | Owner redeems 139,267 (`0xf8444436`), before any batch | ❌ `0x4ae50228`, "not processed" (same error as our own claims in step 4) |
| B | **Random address** sends the real batch tx (same calldata, same timestamp) | ❌ **mined and reverted** (status 0) |
| B' | Owner redeems 139,267 again | ❌ `0x4ae50228`, unchanged |
| C | **Original sender** `0x565f04cb…` replays the real batch tx (timestamp +1s) | ✅ success, 1,793,394 gas. Emits the batch event: **ids 139,266 → 139,310, 6,230.07 stETH**, identical to the real one |
| D | Owner redeems 139,267 | ✅ **paid 0.125068516331512031 ETH**, NFT burned |
| D' | Owner of 139,311 (just above the batch range) tries to redeem | ❌ `0x4ae50228`, still not processed |

- Deposited for claim 139,267: **0.125068516331512030 stETH** → paid **0.125068516331512031 ETH** (1:1; 1 wei rounding).
- Owner's ETH: 0.013316 → 0.138374 (+0.125058 = payout minus 0.0000105 ETH gas).
- Receipts: `data/step5/batch_replay_receipt.json`, `data/step5/redeem_receipt.json`.

**Conclusion of the proof:** with everything else identical, the claim is **redeemable if and only if the permissioned
batch runs.** A random address can't send it (B); the original sender can (C); right after, the claim pays 1:1 (D), and
claims outside the batch stay locked (D').

---

## Result: Lido, T0

| Scenario | Result | Why |
|----------|--------|-----|
| **D4 removed** (privileged batch senders stop) | 🔴 **Blocked** | Steps 4–5: claims can't be redeemed without the permissioned daily batch; waiting doesn't help |
| D4 present | ✅ Exits (1:1, two steps) | Step 5: once a batch covers the claim, the holder redeems alone with just the claim id. This week's wait: median ~40h, max ~6 days |
| D1 frontend / D2 company API / D3 indexer / D5 default RPC removed | Same outcome as above | The whole T0 run never used any of them. The only blocking dependency found is D4 |

**Capital exposed to D4 at the fork block** (directly measured so far): claims waiting for a batch held **4,204.19 stETH**
in `0x889e`. Every stETH holder (our user: 5,084.27 stETH) needs a batch to exit through the protocol.

**What the user had to work out alone at T0:** where their position is (log scan + spam filtering), that the stETH
contract is a proxy, that no function names could be recovered, which contract and function other users use to exit,
the call layout, the 1,000 stETH / 100 wei limits (by probing), and the two-step design.

**Fallback (SPEC §4, not a pass):** selling on the trading route seen in step 3b.
