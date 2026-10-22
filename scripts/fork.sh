#!/usr/bin/env bash
# Start a local mainnet fork pinned to a block, impersonating the test address.
# Usage: scripts/fork.sh <block> <address> [port]
set -euo pipefail

BLOCK="${1:?block number required}"
ADDR="${2:?test address required}"
PORT="${3:-8545}"
: "${ETH_RPC_URL:?ETH_RPC_URL must be set (upstream archive RPC)}"

mkdir -p logs
LOG="logs/anvil-${BLOCK}.log"

anvil --fork-url "$ETH_RPC_URL" --fork-block-number "$BLOCK" --port "$PORT" \
  >"$LOG" 2>&1 &
echo $! > logs/anvil.pid

# wait for anvil to come up
for _ in $(seq 1 30); do
  cast chain-id --rpc-url "http://127.0.0.1:$PORT" >/dev/null 2>&1 && break
  sleep 1
done

cast rpc anvil_impersonateAccount "$ADDR" --rpc-url "http://127.0.0.1:$PORT" >/dev/null
echo "anvil up on :$PORT (pid $(cat logs/anvil.pid)), fork block $BLOCK, impersonating $ADDR"
echo "log: $LOG"
