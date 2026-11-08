# protein_optimizer (EvoEmu)

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Runpod setup runbook (read before touching any pod)

**Standing orders from the project owner:**
1. **Understand what the project needs BEFORE creating anything.** Read this section, check `setup_vm.sh`, and verify prices/stock with live reads. Do not create a pod to "see what happens".
2. **Get setup fully correct first.** A pod counts as set up only when `/workspace/SETUP_OK` exists (see Gates).
3. **Do NOT run the KaiB search (or any BioEmu search) until setup is verified AND the owner says go.** Setup and running are separate steps.
4. Tell the owner the hourly price before creating a pod; stop/terminate pods you created when work pauses.

### What the project needs (facts, with how we know)
| Need | Detail | Source |
|---|---|---|
| Two Python environments | `.venv` (BioEmu, numpy>=2, jax) and `Dyna-1/.venv` (numpy<2, biotite==0.41.2, transformers<4.47). They cannot share an interpreter. | Hit on a real pod: biotite's wheel crashes under numpy 2 |
| Dyna-1 worker | `scripts/dyna1_worker.py` runs in `Dyna-1/.venv`; the main process talks JSON-lines to it. | Implemented + tested with a stub |
| Dyna-1 weights | `dyna1.pt` (0.76 GB) at the **root** of HF repo `gelnesr/Dyna-1`. Its README's `weights/` path is wrong. | HF API listing |
| ESM-3 base model | `esm3_sm_open_v1`, downloaded on first Dyna-1 load; worked with **no HF token** on 2026-11-01. Size not measured (a few GB). | Real pod run |
| BioEmu checkpoints | ~0.13 GB each (HF `microsoft/bioemu`), fetched on first use | HF API listing |
| GPU | >=24 GB, CUDA 13.x host. The image's torch is cu128 and runs fine on 13.x hosts. Dyna-1 refuses to run on CPU by design. | Real pod runs |
| Disk | Used successfully: container disk 40 GB + `/workspace` volume 40 GB. BioEmu's venv (torch+jax+tf-cpu) is multi-GB; exact size unmeasured. | Working pod |
| Image | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` (Python 3.12, system torch 2.8 reused by Dyna-1's venv) | Seen on owner's pod; worked |
| Env gotcha | Runpod exports `HF_HUB_ENABLE_HF_TRANSFER=1`; the worker disables it if the package is missing. `NVIDIA_VISIBLE_DEVICES=void` is NORMAL on these pods — not a sign of a lost GPU. | Observed |

### Choosing the pod (decide from live reads, not memory)
- Read live stock/price: `get-capacity` (use `cudaVersions` ["13.0","13.2"]; 12.8 was always out) and `list-gpu-types`. Quote the price before creating.
- **Prefer community RTX 4090** (finished BioEmu install in ~3.5 min; $0.34/hr when seen). It sells out between the read and the create — retry the read, then try the next option.
- **Avoid secure-cloud L4 for now:** two separate L4 pods hung (0% CPU for 12+ min) during BioEmu's pip install phase, cause unknown. If one is the only option, expect a possible hang.
- Pin `gpu.minCudaVersion` to a version that has stock (13.0 or 13.2). Ports: `8888/http`, `startJupyter: true`. No SSH unless asked.
- Mounts: persistent `/workspace`, 40 GB. Container disk 40 GB.
- **Never restart a pod to apply a change.** On community pods, restarts have preceded lost GPUs and "not enough free GPUs on the host" errors. Edit in place, or terminate and create a fresh pod. Don't `update-pod` + `restart`.
- A stopped community pod often cannot be started again (host GPU taken). Stopping = assume it is gone; keep nothing irreplaceable only on the pod (code is in git, weights re-download).

### Pod start command (use exactly this; the logic lives in the repo script)
```json
{"entrypoint": ["/bin/bash","-c"],
 "cmd": ["cd /workspace && ( if [ -d EvoE/.git ]; then git -C EvoE pull -q; else git clone -q -b dyna1-mutation-oracle https://github.com/ibrahimaasim77/EvoEmu.git EvoE; fi ) && ( bash /workspace/EvoE/protein_optimizer/scripts/pod_startup.sh & ) ; exec /start.sh"]}
```
`pod_startup.sh` checks the GPU, runs `setup_vm.sh` with step markers + a 30 s heartbeat, runs the real-model smoke test, and writes `/workspace/SETUP_OK` or `/workspace/SETUP_FAILED`.

### Gates — all must pass before anyone says "setup is done"
1. Log shows `GPU-CHECK: GPU 0: <name>` (not an error).
2. Log shows `=== 1/6` … `=== 6/6`, `Dyna-1 imports OK`, `Setup complete`.
3. Smoke test prints `SMOKE TEST OK` with Dyna-1 `ready on device: cuda` (NOT `cpu`).
4. `/workspace/SETUP_OK` exists. (Read via the pod's logs: `=== SETUP_OK — pod is ready ===`.)
5. **Still not run:** BioEmu on the GPU. After gates 1–4, ask the owner before the first small BioEmu check, then before any search.

### Monitoring without a shell
The Runpod tools cannot exec in a pod. Read progress with `stream-pod-logs` (`source: container`, a `since` timestamp that is in the PAST — a future `since` returns nothing). A 30 s `HEARTBEAT` line with `cpu-load` near 0 for >10 min means a hang: terminate and recreate rather than restart.

### Known failures and what they mean
| Symptom | Meaning / action |
|---|---|
| `numpy.core.multiarray failed to import` | Dyna-1 deps leaked into the BioEmu env — keep them in `Dyna-1/.venv` |
| `hf_transfer ... not available` | Worker handles it; if seen elsewhere set `HF_HUB_ENABLE_HF_TRANSFER=0` |
| `CUDA requested but unavailable` | Worker's deliberate fail-loud; pod has no usable GPU — terminate/recreate, don't restart |
| `FileNotFoundError ... weights` | Weights not at `Dyna-1/model/weights/dyna1.pt`; error lists what is there |
| `There are no longer any instances available` | Capacity, not input — re-read stock and try the next option |
| `not enough free GPUs on the host` (on start) | Stopped pod's host is full — the pod is effectively lost |
