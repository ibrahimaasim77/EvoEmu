#!/usr/bin/env python
"""
ADK overnight run: Dyna-1 -> ThermoMPNN -> BioEmu -> MCMC.   (run with the BioEmu .venv python)

  python scripts/run_adk_overnight.py --hours 9 --out /workspace/results/adk
  python scripts/run_adk_overnight.py --mock --hours 0.01 --out /tmp/adk_mock   # wiring check, no GPU

States: 4AKE chain A = state 1 (open), 1AKE chain A = state 2 (closed). Objective: LLR=ln(n_open/n_closed)
driven to target 0 (50:50), ThermoMPNN ranking biased toward the closed state.
Everything is written under --out; stage outputs are cached so a re-run resumes.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protein_optimizer.adk_pipeline import (  # noqa: E402
    ADKPipelineConfig, MCMCSearch, MockTwoStateBackend, detect_mobile, evaluate_mutant,
    make_two_state_references, mask_to_ranges, rank_mutants, rank_positions_dyna1,
)
from protein_optimizer.config import BioEmuConfig, ThermoMPNNConfig  # noqa: E402
from protein_optimizer.thermompnn import (  # noqa: E402
    DdgTable, MockThermoMPNNBackend, build_thermompnn_backend,
)

log = logging.getLogger("adk")
AA3 = {'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C', 'GLN': 'Q', 'GLU': 'E', 'GLY': 'G',
       'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K', 'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S',
       'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V'}


def clean_pdb(src: Path, dst: Path, chain: str = "A") -> tuple[str, np.ndarray]:
    """ATOM-only, single chain, first altloc. Returns (sequence, CA coords in Angstrom)."""
    lines, seq, ca, seen = [], [], [], set()
    for l in src.read_text().splitlines():
        if not l.startswith("ATOM") or l[21] != chain or l[16] not in " A":
            continue
        lines.append(l)
        if l[12:16].strip() == "CA":
            key = l[22:27]
            if key not in seen:
                seen.add(key)
                seq.append(AA3.get(l[17:20], "X"))
                ca.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
    dst.write_text("\n".join(lines) + "\nEND\n")
    return "".join(seq), np.array(ca)


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def stage_dyna1(args, out: Path, pdbs: dict[str, Path], seq: str) -> np.ndarray:
    """Mean p_exchange per position over the two state PDBs (cached)."""
    cache = out / "dyna1_pex.csv"
    if cache.exists():
        return np.array([float(r["pex_mean"]) for r in csv.DictReader(open(cache))])
    pex = {}
    for name, pdb in pdbs.items():
        if args.mock:
            rng = np.random.default_rng(abs(hash(name)) % 2**31)
            pex[name] = rng.uniform(0, 1, len(seq))
            continue
        repo = Path(args.dyna1_repo).resolve()
        cmd = [str(repo / ".venv/bin/python"), "dyna1.py", "--pdb", str(pdb.resolve()), "--chain", "A",
               "--name", name, "--use_pdb_seq", "--save_dir", str(out.resolve())]
        log.info("Dyna-1: %s", " ".join(cmd))
        r = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"Dyna-1 failed on {name}:\n{r.stderr[-2000:]}")
        rows = list(csv.DictReader(open(out / f"{name}-Dyna1.csv")))
        got = "".join(x["residue"] for x in rows)
        if got != seq:
            raise RuntimeError(f"Dyna-1 residues for {name} do not match the pipeline sequence")
        pex[name] = np.array([float(x["p_exchange"]) for x in rows])
    names = list(pdbs)
    mean = (pex[names[0]] + pex[names[1]]) / 2
    write_csv(cache, ["position", "residue", f"pex_{names[0]}", f"pex_{names[1]}", "pex_mean"],
              [[i + 1, seq[i], pex[names[0]][i], pex[names[1]][i], mean[i]] for i in range(len(seq))])
    return mean


def stage_thermompnn(args, out: Path, pdbs: dict[str, Path], seq: str):
    names = list(pdbs)
    if args.mock:
        b = MockThermoMPNNBackend()
        return [b.predict(str(pdbs[n]), seq) for n in names]
    cfg = ThermoMPNNConfig(enabled=True, repo_dir=args.thermompnn_repo,
                           python_executable=str(Path(args.thermompnn_repo) / ".venv/bin/python"))
    backend = build_thermompnn_backend(cfg)
    return [backend.predict(str(pdbs[n].resolve()), seq) for n in names]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=9.0)
    ap.add_argument("--out", default="results/adk")
    ap.add_argument("--frames", type=int, default=500)
    ap.add_argument("--bioemu-batch-100", type=int, default=60)
    ap.add_argument("--dyna1-repo", default=str(ROOT / "Dyna-1"))
    ap.add_argument("--thermompnn-repo", default="/workspace/ThermoMPNN")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S",
                        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(out / "run.log")])

    # ---- inputs -----------------------------------------------------------------
    data = ROOT / "data" / "adk"
    seq1, ref1 = clean_pdb(data / "4AKE.pdb", out / "state1_4AKE_A.pdb")
    seq2, ref2 = clean_pdb(data / "1AKE.pdb", out / "state2_1AKE_A.pdb")
    if seq1 != seq2 or len(ref1) != len(ref2):
        raise SystemExit(f"4AKE/1AKE sequences differ: {len(seq1)} vs {len(seq2)}")
    pdbs = {"state1_4AKE": out / "state1_4AKE_A.pdb", "state2_1AKE": out / "state2_1AKE_A.pdb"}
    L = len(seq1)

    mobile = detect_mobile(ref1, ref2)
    ranges = mask_to_ranges(mobile)
    log.info("L=%d | mobile residues=%d | ranges=%s", L, int(mobile.sum()), ranges)
    if not 15 <= mobile.sum() <= L // 2:
        raise SystemExit(f"Implausible mobile region ({int(mobile.sum())} of {L}); refusing to run.")

    cfg = ADKPipelineConfig(frames=args.frames, mobile_ranges=ranges, bias_toward=2, target_llr=0.0,
                            out_dir=str(out), time_budget_s=1.0)

    # ---- stage 1: Dyna-1 --------------------------------------------------------
    pex = stage_dyna1(args, out, pdbs, seq1)
    order = rank_positions_dyna1(pex, pex)             # already the per-position mean
    write_csv(out / "positions_ranked.csv", ["rank", "position", "residue", "pex_mean"],
              [[r + 1, p + 1, seq1[p], pex[p]] for r, p in enumerate(order)])
    log.info("Top-%d Dyna-1 positions (1-based): %s", cfg.top_positions, [p + 1 for p in order[:cfg.top_positions]])

    # ---- stage 2: ThermoMPNN ----------------------------------------------------
    t1, t2 = stage_thermompnn(args, out, pdbs, seq1)
    allm = rank_mutants(t1, t2, order[:cfg.top_positions], cfg, top_n=10_000)
    write_csv(out / "mutants_all.csv", ["position", "wt", "mut", "ddg_state1", "ddg_state2", "ddg_mt", "worst"],
              [[m.position + 1, seq1[m.position], m.aa, m.ddg_1, m.ddg_2, m.ddg_mt, m.worst] for m in allm])
    top = allm[:cfg.top_mutants]
    log.info("%d guard-passing mutants; top %d -> BioEmu", len(allm), len(top))
    seeds = [seq1[:m.position] + m.aa + seq1[m.position + 1:] for m in top]

    # ---- stage 3/4: BioEmu + MCMC -----------------------------------------------
    if args.mock:
        r1, r2 = make_two_state_references(L, (L - 19, L), seed=1)
        ref1, ref2 = r1, r2
        cfg.mobile_ranges = [(L - 19, L)]
        backend = MockTwoStateBackend(SimpleNamespace(num_samples=cfg.frames, batch_size=1), ref1, ref2)
    else:
        from protein_optimizer.bioemu import build_bioemu_backend
        backend = build_bioemu_backend(BioEmuConfig(num_samples=cfg.frames, batch_size=args.bioemu_batch_100,
                                                    model_path="bioemu-v1.1", mock=False))

    # gate: the wild type must give physical frames and both states, else units/format are wrong
    wt = evaluate_mutant(backend, seq1, [], ref1, ref2, cfg, out / "pca")
    log.info("WT: frames=%d physical=%d open=%d closed=%d llr=%s", wt.n_frames, wt.n_physical,
             wt.n_state1, wt.n_state2, wt.llr)
    if wt.n_physical < 0.2 * wt.n_frames:
        raise SystemExit(f"Only {wt.n_physical}/{wt.n_frames} WT frames pass the physical filter -- "
                         "check units / residue order before burning GPU time.")
    json.dump(wt.__dict__, open(out / "wt_result.json", "w"), indent=1)

    cfg.time_budget_s = max(60.0, args.hours * 3600 - (time.time() - t0))
    pos_bias = np.log(np.clip(pex, 1e-3, None))
    search = MCMCSearch(cfg, backend, seq1, t1, t2, ref1, ref2, order, pos_bias=pos_bias, bias_weight=0.3)
    best = search.run(seeds)

    ranked = sorted((r for r in search.results.values() if r.valid), key=lambda r: abs(r.llr - (cfg.target_llr or 0)))
    write_csv(out / "ranked.csv", ["mutations", "n_open", "n_closed", "llr", "dg_kcal", "resampled", "sequence"],
              [["+".join(r.mutations), r.n_state1, r.n_state2, r.llr, r.dg, r.resampled, r.sequence] for r in ranked])
    (out / "SUMMARY.md").write_text(
        f"# ADK run summary\n\n- evaluated: {len(search.results)} sequences ({len(search.discarded)} discarded NaN)\n"
        f"- WT LLR (ln open/closed): {wt.llr:.3f}  (open={wt.n_state1}, closed={wt.n_state2})\n"
        f"- best: {'+'.join(best.mutations)}  LLR={best.llr:.3f}  dG={best.dg:.2f} kcal/mol\n"
        f"- mobile ranges: {ranges}\n- wall time: {(time.time() - t0) / 3600:.2f} h\n")
    (out / "ADK_DONE").write_text("ok\n")
    log.info("DONE best=%s llr=%.3f", "+".join(best.mutations), best.llr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
