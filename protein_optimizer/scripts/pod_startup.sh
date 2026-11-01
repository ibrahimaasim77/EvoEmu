#!/usr/bin/env bash
#
# Pod start command target. Runs on a Runpod pod AFTER the repo is cloned to
# /workspace/EvoE. It never restarts anything and never runs the KaiB search.
#
#   1. Verifies a GPU is really usable (aborts early if not).
#   2. Runs setup_vm.sh, streaming step markers + a heartbeat so a hang is visible.
#   3. Runs the real-model smoke test (which itself fails if CUDA is unavailable).
#   4. Leaves /workspace/SETUP_OK or /workspace/SETUP_FAILED for the next person/Claude.
#
set -uo pipefail

export HF_HOME=/workspace/hf              # ESM-3 + HF cache survive on the volume
cd "$(dirname "$0")/.."                   # -> protein_optimizer/
rm -f /workspace/SETUP_OK /workspace/SETUP_FAILED

echo "GPU-CHECK: $(nvidia-smi -L 2>&1 | head -1)"
if ! nvidia-smi -L >/dev/null 2>&1; then
    echo "FATAL: no usable GPU on this pod. Terminate it and create another; do NOT restart."
    echo "no GPU" > /workspace/SETUP_FAILED
    exit 1
fi

# Heartbeat: pip is silent for minutes while writing files; this shows whether it is alive.
( while sleep 30; do
    echo "HEARTBEAT: $(tail -n 1 /workspace/setup.log 2>/dev/null | tr '\r' '\n' | tail -n 1 | cut -c1-160) | cpu-load: $(cut -d' ' -f1 /proc/loadavg)"
  done ) &
HB=$!
trap 'kill $HB 2>/dev/null' EXIT

bash setup_vm.sh 2>&1 | tee /workspace/setup.log | grep --line-buffered -E '^===|ERROR|Traceback|Error|imports OK|Setup complete'
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    echo "SETUP FAILED — see /workspace/setup.log (last lines below)"
    tail -n 25 /workspace/setup.log
    echo "setup_vm.sh failed" > /workspace/SETUP_FAILED
    exit 1
fi

echo "--- SMOKE (real Dyna-1 on GPU) ---"
OUT="$(.venv/bin/python scripts/smoke_dyna1.py 2>&1)"; RC=$?
echo "$OUT" | tail -n 25
if [ $RC -ne 0 ] || ! echo "$OUT" | grep -q "SMOKE TEST OK"; then
    echo "smoke test failed" > /workspace/SETUP_FAILED
    echo "SETUP FAILED (smoke test)"
    exit 1
fi
echo "ok $(date -u +%FT%TZ)" > /workspace/SETUP_OK
echo "=== SETUP_OK — pod is ready. The KaiB search has NOT been run. ==="
