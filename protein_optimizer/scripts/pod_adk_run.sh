#!/usr/bin/env bash
#
# Unattended ADK run for a Runpod pod. Start command clones the repo to /workspace/EvoE and runs
# this in the background. Idempotent: everything cached on /workspace (a network volume) is reused.
#
#   1. pod_startup.sh   -> GPU check, setup_vm.sh (BioEmu .venv + Dyna-1/.venv + weights), smoke test
#   2. ThermoMPNN       -> /workspace/ThermoMPNN with its own venv (weights ship in the repo)
#   3. run_adk_overnight.py (HOURS budget) -> Dyna-1 -> ThermoMPNN -> BioEmu -> MCMC
#   4. best-effort self-stop of the pod when finished (billing ends)
#
# Markers: /workspace/ADK_SETUP_FAILED (reason inside), /workspace/results/adk/ADK_DONE, /workspace/adk_run.log
set -uo pipefail
HOURS="${ADK_HOURS:-9}"
OUT=/workspace/results/adk
LOG=/workspace/adk_run.log
export HF_HOME=/workspace/hf
cd "$(dirname "$0")/.."            # protein_optimizer/
rm -f /workspace/ADK_SETUP_FAILED

fail() { echo "ADK FAILED: $1"; echo "$1" > /workspace/ADK_SETUP_FAILED; selfstop; exit 1; }
selfstop() {
  # best effort; the monitor can also stop the pod from outside
  if [ -n "${RUNPOD_POD_ID:-}" ]; then
    if command -v runpodctl >/dev/null 2>&1; then runpodctl stop pod "$RUNPOD_POD_ID" >/dev/null 2>&1 && echo "selfstop: requested via runpodctl" && return; fi
    [ -n "${RUNPOD_API_KEY:-}" ] && curl -s -X POST -H "Authorization: Bearer $RUNPOD_API_KEY" \
        "https://rest.runpod.io/v1/pods/$RUNPOD_POD_ID/stop" >/dev/null && echo "selfstop: requested via REST"
  fi
}

echo "=== ADK 1/3: base setup (BioEmu + Dyna-1) ==="
bash scripts/pod_startup.sh || fail "pod_startup.sh failed: $(cat /workspace/SETUP_FAILED 2>/dev/null)"
[ -f /workspace/SETUP_OK ] || fail "SETUP_OK missing after pod_startup.sh"

echo "=== ADK 2/3: ThermoMPNN ==="
TM=/workspace/ThermoMPNN
[ -d "$TM/.git" ] || git clone -q --depth 1 https://github.com/Kuhlman-Lab/ThermoMPNN "$TM" || fail "ThermoMPNN clone"
if [ ! -x "$TM/.venv/bin/python" ]; then
  # reuse the image's CUDA torch; add ThermoMPNN's light deps
  python3 -m venv --system-site-packages "$TM/.venv" || fail "ThermoMPNN venv"
  "$TM/.venv/bin/pip" install -q pytorch-lightning omegaconf pandas tqdm wandb biopython joblib \
      || fail "ThermoMPNN pip install"
fi
.venv/bin/pip install -q matplotlib || fail "matplotlib install"
mkdir -p "$OUT"
(cd "$TM/analysis" && "$TM/.venv/bin/python" custom_inference.py --pdb "$PWD/../examples/pdbs/$(ls "$TM/examples/pdbs" 2>/dev/null | head -1)" \
    --chain A --out_dir "$OUT/tm_smoke" >/dev/null 2>"$OUT/tm_smoke.err") \
  || echo "ThermoMPNN example smoke failed (will surface in the real run): $(tail -n 3 "$OUT/tm_smoke.err" 2>/dev/null)"

echo "=== ADK 3/3: run (budget ${HOURS} h) ==="
( while sleep 600; do echo "HEARTBEAT $(date -u +%T) $(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader) | $(tail -n 1 "$OUT/run.log" 2>/dev/null | cut -c1-140)"; done ) &
HB=$!
PYTHONPATH=. .venv/bin/python scripts/run_adk_overnight.py --hours "$HOURS" --out "$OUT" \
    --dyna1-repo "$PWD/Dyna-1" --thermompnn-repo "$TM" 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}
kill $HB 2>/dev/null
if [ "$RC" -ne 0 ]; then echo "run_adk_overnight.py exited $RC" > /workspace/ADK_SETUP_FAILED; echo "ADK FAILED (rc=$RC)"; fi
[ -f "$OUT/ADK_DONE" ] && echo "=== ADK_DONE ==="
selfstop
