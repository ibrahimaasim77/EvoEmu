# T4 lysozyme validation of the ThermoMPNN guard and the BioEmu state signal

Scripts run on a RunPod A40 on 2026-11-01 (BioEmu 1.4.1, ThermoMPNN default checkpoint). Paths inside the
scripts are the pod's (`/workspace/...`); adjust before reuse.

| Script | What it does |
|---|---|
| `stageA.py` | ThermoMPNN on 1L63 vs 304 measured T4L ddG (FireProt HF set); guard-cutoff calibration |
| `stageB.py` | BioEmu ground vs excited-state populations for WT*, L99A, L99A/G113A/R119P (structure-RMSD metric on residues 105-116) |
| `stageC.py` | End-to-end search L99A -> triple mutant with fitness ln(p_ES/p_ground) injected via `log_partition`; guard arms `off`, `onX` (worst case over 3DMV + 2LCB poses), `esX` (excited pose only) |
| `stageD.py` | Diagnostic: server MSA vs fixed MSA, BioEmu v1.1 vs v1.2 |
| `msa_util.py`, `fetch_msa.py` | One MSA fetched for L99A, query row swapped per candidate (no per-candidate calls to the public ColabFold server) |
| `runner3.sh` | Job queue used on the pod |

Structures: 1L63 (WT*), 3DMV (L99A ground), 2LCB (L99A excited, NMR), 2LC9 (triple excited, NMR), from RCSB.

## Results

**Stage A (ThermoMPNN vs experiment, n=304 unique T4L mutations):** Pearson 0.69, Spearman 0.75, RMSE 1.42 kcal/mol,
AUC 0.91 (exp >= 1) and 0.90 (exp >= 2).

| cutoff (kcal/mol) | blocked (measured set) | recall of exp >= 2 | false-block of exp < 1 |
|---|---|---|---|
| 0.5 | 67% | 99% | 37% |
| 1.0 | 49% | 90% | 15% |
| 1.5 | 29% | 64% | 5.4% |
| 2.0 | 16% | 40% | 2.7% |
| 3.0 | 2% | 6% | 0% |

**Pose dependence:** R119P is +2.43 on the ground pose and +0.05 on the excited pose; G113A is -0.04 and -0.54.
A worst-case-over-poses guard blocks R119P, a mutation that favours the excited state.

**Stage B/D (BioEmu, 250 samples per sequence):** fraction of frames closer to the excited than the ground state
in residues 105-116 (reference separation 6.2 A). Controls classify correctly (X-ray ground 0%, NMR excited 100%).

| setup | WT* | L99A | triple |
|---|---|---|---|
| v1.1, fixed MSA (stage B) | 0.4% | 0.4% | 0.0% |
| v1.1, ColabFold server MSA | - | 0.4% | 0.0% |
| v1.2, fixed MSA | - | 0.9% | 1.3% |

No frame came within 3 A of the excited-state reference in any setup. The state signal needed for the end-to-end
test was absent, so the fitness in stage C was flat (reference LLR = target LLR = -3.50, gap closed 0 in all runs).

**Stage C (seed 0 only, 16 samples/candidate, population 20 x 3 generations, residues 95-125):**
guard off evaluated 28 candidates; both guard arms rejected 14 of 33 proposals and evaluated 19. The remaining stage C
runs and stage B seeds 1-2 were cancelled once the flat fitness was clear.

## Other findings
- With BioEmu 1.4.1 the npz output has only `pos`, `node_orientations`, `sequence` (no `log_weights`), so the repo's
  real-BioEmu "LLR" falls back to the mean pairwise C-alpha distance, a compactness proxy.
- BioEmu sends each new sequence to the public ColabFold MSA server unless an `.a3m` path is passed.
- BioEmu's embedding step reserves ~33 GB of GPU memory per process unless `TF_FORCE_GPU_ALLOW_GROWTH=true`.
- Throughput on an A40: ~1.3 s/sample for 164 residues, plus ~20-30 s per new sequence for the embedding.
