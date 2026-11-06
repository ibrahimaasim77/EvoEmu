#!/usr/bin/env bash
#
# Fully unattended run: setup -> KaiB search -> results -> self-stop.
# Launched by the Runpod pod start command AFTER the repo is cloned to /workspace/EvoE.
# Needs no laptop/Claude session once the pod is created.
#
#   1. pod_startup.sh (GPU check, setup_vm.sh, real-model smoke test). Abort if no SETUP_OK.
#   2. main.py on KaiB with real Dyna-1 + real BioEmu, capped by a hard timeout.
#   3. Results are written to /workspace/results/ AND printed to the container log.
#   4. Waits GRACE_MIN minutes (so results can be fetched), then stops the pod so it stops billing.
#
# Tunables (env vars on the pod, all optional):
#   POPULATION=20 ROUNDS=2 BIOEMU_SAMPLES=20 DIRECTION=up
#   MAX_RUN_MIN=180   hard cap on the search
#   GRACE_MIN=90      time the pod stays up after finishing before it stops itself
set -uo pipefail

POPULATION="${POPULATION:-20}"
ROUNDS="${ROUNDS:-2}"
BIOEMU_SAMPLES="${BIOEMU_SAMPLES:-20}"
DIRECTION="${DIRECTION:-up}"
MAX_RUN_MIN="${MAX_RUN_MIN:-180}"
GRACE_MIN="${GRACE_MIN:-90}"
KAIB="MSPRKTYILKLYVAGNTPNSVRALKTLKNILEVEFQGVYALKVIDVLKNPQLAEEDKILATPTLAKVLPLPVRRIIGDLSDREKVLIGLDLLYGELQDSDDF"

export HF_HOME=/workspace/hf
HERE="$(cd "$(dirname "$0")/.." && pwd)"     # protein_optimizer/
cd "$HERE"
mkdir -p /workspace/results

stop_pod() {
    echo "=== $(date -u +%FT%TZ) stopping pod to end billing (results are in /workspace/results and above in this log) ==="
    if command -v runpodctl >/dev/null 2>&1 && [ -n "${RUNPOD_POD_ID:-}" ]; then
        runpodctl stop pod "$RUNPOD_POD_ID" || runpodctl remove pod "$RUNPOD_POD_ID" || true
    else
        echo "runpodctl / RUNPOD_POD_ID unavailable - POD KEEPS BILLING, stop it manually"
    fi
}

echo "=== $(date -u +%FT%TZ) AUTO-RUN START (pop=$POPULATION rounds=$ROUNDS samples=$BIOEMU_SAMPLES dir=$DIRECTION) ==="

bash scripts/pod_startup.sh
if [ ! -f /workspace/SETUP_OK ]; then
    echo "=== AUTO-RUN ABORTED: setup did not pass ($(cat /workspace/SETUP_FAILED 2>/dev/null)). Not running the search. ==="
    echo "Pod left up for ${GRACE_MIN} min so logs can be read, then it stops itself."
    sleep "$((GRACE_MIN * 60))"; stop_pod; exit 1
fi

echo "=== $(date -u +%FT%TZ) SEARCH START ==="
timeout "$((MAX_RUN_MIN * 60))" .venv/bin/python main.py \
    --config config/evolutionary.yaml --sequence "$KAIB" \
    --set ga.population_size="$POPULATION" \
    --set ga.max_generations="$ROUNDS" \
    --set bioemu.num_samples="$BIOEMU_SAMPLES" \
    --set dyna1.direction="$DIRECTION" \
    2>&1 | tee /workspace/results/kaib_run.log
RC=${PIPESTATUS[0]}
echo "=== $(date -u +%FT%TZ) SEARCH END rc=$RC ==="

[ -d results ] && cp -r results/. /workspace/results/ 2>/dev/null
if [ "$RC" -eq 0 ]; then echo "ok" > /workspace/RUN_OK; else echo "rc=$RC" > /workspace/RUN_FAILED; fi

echo "=== FINAL RESULTS (from log) ==="
sed -n '/RESULTS/,$p' /workspace/results/kaib_run.log | head -60

echo "Pod stays up ${GRACE_MIN} min for retrieval, then stops itself."
sleep "$((GRACE_MIN * 60))"
stop_pod
