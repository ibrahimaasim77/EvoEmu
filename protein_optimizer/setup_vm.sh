#!/usr/bin/env bash
#
# One-shot BioEmu + protein_optimizer setup for a GPU rental VM
# (Lambda Labs / RunPod / Vast.ai — Ubuntu with NVIDIA drivers preinstalled).
#
# Usage (from inside the repo on the VM):
#     bash setup_vm.sh
#
# It creates a Python venv, installs BioEmu + project deps, and runs a tiny
# mock smoke test. No conda needed — we skip BioEmu's optional sidechain step
# (the code passes filter_samples=False).
#
set -euo pipefail

echo "=== 1/6  Checking GPU ==="
if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found. This needs a GPU VM with NVIDIA drivers." >&2
    exit 1
fi
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

echo "=== 2/6  Checking Python (need 3.10+) ==="
PY=python3
$PY -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required, found %s" % sys.version' \
    || { echo "ERROR: Python 3.10+ required." >&2; exit 1; }
$PY --version

echo "=== 3/6  Creating virtual environment (.venv) ==="
if [ ! -d .venv ]; then
    $PY -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip wheel

echo "=== 4/6  Installing BioEmu + dependencies ==="
# BioEmu core (MSA tooling is bundled; no separate install needed).
pip install "bioemu[cuda]"
# Project dependencies.
pip install torch transformers numpy pyyaml biopython

echo "=== 5/6  Installing Dyna-1 (mutation oracle, in its OWN virtualenv) ==="
# Dyna-1 pins numpy<2 / biotite==0.41.2 / transformers<4.47, which conflict with BioEmu's
# numpy>=2 / jax stack. So it gets Dyna-1/.venv and runs as a worker process
# (scripts/dyna1_worker.py); the two never share an interpreter.
if [ ! -d Dyna-1 ]; then
    git clone --depth 1 https://github.com/WaymentSteeleLab/Dyna-1 Dyna-1
fi
# Reuse the base interpreter's torch if it has one (runpod/pytorch images do) — saves ~5 GB.
BASE_PY="$(python -c 'import sys; print(sys.base_prefix)')/bin/python3"
SITE_FLAG=""
if "$BASE_PY" -c "import torch" 2>/dev/null; then SITE_FLAG="--system-site-packages"; fi
if [ ! -x Dyna-1/.venv/bin/python ]; then
    "$BASE_PY" -m venv $SITE_FLAG Dyna-1/.venv
fi
D1_PIP="Dyna-1/.venv/bin/pip"
$D1_PIP install --upgrade pip wheel
# Skip the torch family pins (they would replace the CUDA torch we already have).
grep -viE '^\s*(torch|torchaudio|torchvision|torchtext)\b' Dyna-1/requirements.txt \
    > .dyna1-requirements.txt
$D1_PIP install -r .dyna1-requirements.txt
rm -f .dyna1-requirements.txt
if ! Dyna-1/.venv/bin/python -c "import torch" 2>/dev/null; then $D1_PIP install torch; fi
# Weights live at the HuggingFace repo root (the upstream README's weights/ path is outdated).
Dyna-1/.venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("gelnesr/Dyna-1", allow_patterns=["dyna1.pt"], local_dir="Dyna-1/model/weights")
PY
# Fail setup loudly if the model code can't be imported in its own env.
(cd Dyna-1 && .venv/bin/python -c "from model.model import ESM_model; print('Dyna-1 imports OK')")
# NOTE: on first load Dyna-1 downloads the open ESM-3 base model (esm3_sm_open_v1) from
# HuggingFace. If that repo is gated for you, accept its license on huggingface.co and run
# `huggingface-cli login` (or set HF_TOKEN) first.

echo "=== 6/6  Mock smoke test (no GPU work, verifies wiring) ==="
python main.py --config config/evolutionary.yaml --mock \
    --set ga.population_size=6 --set ga.max_generations=1 --set dyna1.device=cpu

cat <<'EOF'

============================================================
 Setup complete.

 To run a REAL BioEmu job with your partner's mutation:

   source .venv/bin/activate
   python main.py --config config/evolutionary.yaml \
       --sequence <THE_MUTATION_SEQUENCE> \
       --set bioemu.num_samples=100

 The output prints the reference LLR, the best LLR found,
 and the LLR change. Trajectory files (.xtc/.pdb) are saved
 under results/trajectories/.

 NOTE: 100 samples x many candidates is slow. For a first
 real test, shrink the search:
       --set ga.population_size=20 --set ga.max_generations=2

 HuggingFace: model weights download once with NO token needed
 (the "set a HF_TOKEN" warning is already suppressed). After the
 first run has cached the weights, you can go fully offline with:
       export HF_HUB_OFFLINE=1
============================================================
EOF
