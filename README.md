# The DeFi Walkaway Test

Devcon 8 talk: *The DeFi Walkaway Test: Can Users Actually Leave?*

Remove the team, frontend, hosted indexer, privileged relayer, and default RPC. Can a user with only their address and
a node still find their position and exit? This repo holds the method, the scripts, and every run's raw data.

- **Method:** [`SPEC.md`](SPEC.md)
- **Results so far:** [`RESULTS.md`](RESULTS.md)

## Repository layout

```
SPEC.md                     test specification (rules, tiers, selection, evidence rules)
RESULTS.md                  cross-protocol summary
data/
  selection/                snapshots used to pick protocols, tokens, and test addresses (DefiLlama, Ethplorer)
  methodology/              fixed function-name list (signatures.json, SHA-256 in SPEC §9)
runs/<protocol>/
  <fork-date>-T0-all-removed.md    run log: every step, query, finding, timing
  data/step*/                      raw data for each step (logs, txs, traces, receipts)
scripts/                    the harness (standard JSON-RPC only)
logs/                       anvil logs (git-ignored: they contain the RPC URL)
```

Run logs are named after the **fork block's date** (2026-10-22), not the day they were run.

**Runs (16 done, 1 paused):** `runs/lido`, `aave`, `spark`, `morpho`, `sky`, `etherfi`, `ethena`, `maple`, `uniswap`,
`rocketpool`, `compound`, `curve`, `falcon`, `kelp`, `fluid`, `pendle`; paused: `binance-staked-eth`.
Large raw files: DefiLlama snapshots in `data/selection/` (up to 68 MB each) and per-run logs/traces in `runs/*/data/`;
the biggest raw log is gzip-compressed (`runs/ethena/data/step2/raw_logs.json.gz`).

## Scripts

| Script | What it does | Used in |
|--------|--------------|---------|
| `fork.sh <block> <address>` | Start an anvil fork pinned to a block, impersonating the test address | setup |
| `discover.py <address> <block> <outdir> --match SYMBOL [--reuse-logs]` | Every token contract the address ever sent/received (ERC-20/721/1155 events), with `name`/`symbol`/`balanceOf` (batched reads; `--reuse-logs` skips the log scan if saved) | step 2 |
| `selectors.py <code.hex> <out.json>` | Extract function selectors from bytecode; name them with basic signatures and the fixed list | step 3a |
| `wordlist.py` | Build the fixed signature list (pure Python Keccak, no packages) | methodology |
| `flows.py <token> <from> <to> <outdir>` | Every Transfer of a token in a block window, by recipient/sender, mints/burns, contract vs wallet | step 3b |
| `txgroups.py <logs.json> <outdir> <candidates…>` | Fetch every tx behind those transfers; group by `tx.to` + selector; pick 3 examples per group | step 3b |
| `tracetx.py <groups.json> <outdir>` | Trace the examples; what the sender sent and got back (ETH and tokens) | step 3b |
| `events.py <contract> <from> <to> <outdir>` | Every event a contract emitted in a window, by type, with senders; NFT mints/burns | step 3c (Lido, ether.fi, Kelp, Uniswap) |
| `rpcutil.py` | Plain JSON-RPC helpers for fork experiments (calls, sends, binary search); never decodes errors via hosted databases | steps 4–7 (Spark onward) |

Some steps (cause-and-effect tests, exits on the fork) were run as short inline scripts; their exact calls and
results are recorded in the run logs and `runs/<protocol>/data/`.

## Requirements

- [Foundry](https://getfoundry.sh) (`anvil`, `cast`) and Python 3 (standard library only).
- `ETH_RPC_URL`: an **archive** Ethereum RPC with `debug_traceTransaction` / `debug_traceCall` and wide `eth_getLogs`
  ranges (the runs used Alchemy Pay As You Go as a stand-in for a self-run node; SPEC §6).

## Rerunning a protocol

1. Start the fork: `scripts/fork.sh 26248199 <test address from SPEC §8>`
2. Follow the steps in that protocol's run log; each step lists the exact script call or RPC calls and the expected output.
