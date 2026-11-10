#!/usr/bin/env python
"""
Analyse the cached BioEmu frames of the ADK run (read-only on the run's files).

  python scripts/analyze_cache.py --run /workspace/results/adk

Writes <run>/analysis/ :
  hist2d/<name>_pass.png      RMSD-to-state-1 vs RMSD-to-state-2 frame-count histogram (frames that pass the filter)
  hist2d/<name>_all.png       same for ALL frames (key variants only)
  overview_top3_worst3.png    WT + top 3 + worst 3 on shared axes
  topology/<name>_CA.pdb, xtc/<name>_CA.xtc, frames/<name>_frames.csv   (key variants; CA-only, core-aligned on state 1)
  diagnostics.txt             why frames fail the physical filter (also printed)
and <run>/analysis.zip.

RMSD used on the axes = the classifier's own metric: mobile-region CA RMSD after superposing the CORE onto the
reference. A frame is counted "state 1" when x <= y, so the dashed diagonal IS the classification boundary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protein_optimizer.adk_pipeline import (  # noqa: E402
    ADKPipelineConfig, align_on_core, core_mask, detect_mobile, mask_to_ranges,
)

AA3 = {'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C', 'GLN': 'Q', 'GLU': 'E', 'GLY': 'G',
       'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K', 'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S',
       'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V'}
AA1TO3 = {v: k for k, v in AA3.items()}


def parse_ca(pdb: Path) -> tuple[str, np.ndarray]:
    seq, ca = [], []
    for line in pdb.read_text().splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            seq.append(AA3.get(line[17:20], "X"))
            ca.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return "".join(seq), np.array(ca)


def load_frames(cache: Path, seq: str, n: int) -> np.ndarray:
    f = cache / f"{hashlib.sha1(seq.encode()).hexdigest()[:16]}_{n}.npz"
    if not f.exists():
        alts = sorted(cache.glob(f"{hashlib.sha1(seq.encode()).hexdigest()[:16]}_*.npz"))
        if not alts:
            raise FileNotFoundError(f"no cache file for sequence (wanted {f.name})")
        f = alts[-1]
    frames = np.load(f)["ca"].astype(float)
    if np.median(np.linalg.norm(np.diff(frames[0], axis=0), axis=1)) < 1.5:    # nm -> Angstrom
        frames = frames * 10.0
    return frames


def mobile_rmsd(frames, ref, core):
    a = align_on_core(frames, ref, core)
    mob = ~core
    return np.sqrt(((a[:, mob] - ref[mob]) ** 2).sum(-1).mean(-1)), a


def analyse(frames, ref1, ref2, core, cfg):
    d = np.linalg.norm(np.diff(frames, axis=1), axis=2)
    bad = (d < cfg.ca_ca_min) | (d > cfg.ca_ca_max)
    bonds_ok = ~bad.any(axis=1)
    x, a1 = mobile_rmsd(frames, ref1, core)
    y, _ = mobile_rmsd(frames, ref2, core)
    core_rmsd = np.sqrt(((a1[:, core] - ref1[core]) ** 2).sum(-1).mean(-1))
    core_ok = core_rmsd <= cfg.core_rmsd_max
    return dict(d=d, bad=bad, bonds_ok=bonds_ok, core_rmsd=core_rmsd, core_ok=core_ok,
                passed=bonds_ok & core_ok, x=x, y=y, state=np.where(x <= y, 1, 2), aligned=a1)


def hist_plot(ax, x, y, m1, m2, lim, title, vmax=None, cbar=True, fig=None):
    import matplotlib.pyplot as plt
    edges = np.arange(0, lim + 0.25, 0.25)
    H, xe, ye = np.histogram2d(x, y, bins=[edges, edges])
    H = np.ma.masked_where(H == 0, H)
    im = ax.pcolormesh(xe, ye, H.T, cmap="viridis", vmin=1, vmax=vmax or max(2, H.max() if H.count() else 2))
    ax.plot([0, lim], [0, lim], "--", color="gray", lw=0.8)
    ax.scatter([m1[0]], [m1[1]], s=140, facecolors="none", edgecolors="#c0392b", lw=2, zorder=5)
    ax.scatter([m2[0]], [m2[1]], s=140, facecolors="none", edgecolors="#2c5d8a", lw=2, zorder=5)
    ax.annotate("state 1 (open)", m1, xytext=(6, 8), textcoords="offset points", color="#c0392b", fontsize=8, weight="bold")
    ax.annotate("state 2 (closed)", m2, xytext=(-62, 8), textcoords="offset points", color="#2c5d8a", fontsize=8, weight="bold")
    ax.set_xlim(-0.5, lim); ax.set_ylim(-0.5, lim); ax.set_aspect("equal")
    ax.set_xlabel("RMSD to state 1 [Å]"); ax.set_ylabel("RMSD to state 2 [Å]"); ax.set_title(title, fontsize=10)
    if cbar and fig is not None:
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03).set_label("Frame count")
    return im


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="/workspace/results/adk")
    args = ap.parse_args()
    run = Path(args.run)
    out = run / "analysis"
    for sub in ("hist2d", "topology", "xtc", "frames"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cfg = ADKPipelineConfig()
    seq1, ref1 = parse_ca(run / "state1_4AKE_A.pdb")
    seq2, ref2 = parse_ca(run / "state2_1AKE_A.pdb")
    assert seq1 == seq2 and len(ref1) == len(ref2), "state structures differ"
    L = len(seq1)
    mob = detect_mobile(ref1, ref2)
    cfg.mobile_ranges = mask_to_ranges(mob)
    core = core_mask(L, cfg.mobile_ranges)

    wt = json.load(open(run / "wt_result.json"))
    rows = list(csv.DictReader(open(run / "ranked.csv")))
    variants = [("WT", wt["sequence"], bool(wt.get("resampled")))]
    variants += [(r["mutations"], r["sequence"], r["resampled"] == "True") for r in rows]
    key_names = ["WT"] + [r["mutations"] for r in rows[:3]] + [r["mutations"] for r in rows[-3:]]
    cache = run / "bioemu_cache"

    # state markers (where each reference sits on the two axes)
    m1 = (0.0, float(mobile_rmsd(ref1[None], ref2, core)[0][0]))
    m2 = (float(mobile_rmsd(ref2[None], ref1, core)[0][0]), 0.0)

    results, lines = {}, []
    P = lines.append
    P(f"run={run}  L={L}  mobile_ranges={cfg.mobile_ranges}  core={int(core.sum())} mobile={int((~core).sum())}")
    P(f"filter: every CA-CA in [{cfg.ca_ca_min}, {cfg.ca_ca_max}] A and core RMSD <= {cfg.core_rmsd_max} A")
    P(f"reference separation (mobile RMSD, core-aligned): state1->state2 {m1[1]:.2f} A, state2->state1 {m2[0]:.2f} A\n")
    for name, seq, resampled in variants:
        n = 1000 if resampled else 500
        try:
            fr = load_frames(cache, seq, n)
        except FileNotFoundError as exc:
            P(f"{name}: SKIPPED ({exc})")
            continue
        res = analyse(fr, ref1, ref2, core, cfg)
        res.update(seq=seq, frames=fr, n=len(fr))
        results[name] = res

    # ---------------- diagnostics ----------------
    for name in key_names:
        if name not in results:
            continue
        r = results[name]
        n = r["n"]
        pb, pc, pa = r["bonds_ok"].sum(), r["core_ok"].sum(), r["passed"].sum()
        P(f"=== {name}: {n} frames -> {pa} pass ({100 * pa / n:.1f}%)")
        P(f"    CA-CA test alone passes {pb} ({100 * pb / n:.1f}%) | core-RMSD test alone passes {pc} ({100 * pc / n:.1f}%)")
        P(f"    fail CA-CA only {int((~r['bonds_ok'] & r['core_ok']).sum())} | fail core only {int((r['bonds_ok'] & ~r['core_ok']).sum())} "
          f"| fail both {int((~r['bonds_ok'] & ~r['core_ok']).sum())}")
        d = r["d"]
        P(f"    CA-CA (A): min {d.min():.2f}  p1 {np.percentile(d, 1):.2f}  median {np.median(d):.2f}  p99 {np.percentile(d, 99):.2f}  max {d.max():.2f}")
        P(f"    bad bonds per frame: mean {r['bad'].sum(1).mean():.2f}, median {np.median(r['bad'].sum(1)):.0f}, frames with >=1 bad bond {100 * (~r['bonds_ok']).mean():.1f}%")
        cr = r["core_rmsd"]
        P(f"    core RMSD to state 1 (A): p5 {np.percentile(cr, 5):.2f}  p25 {np.percentile(cr, 25):.2f}  median {np.median(cr):.2f}  p75 {np.percentile(cr, 75):.2f}  p95 {np.percentile(cr, 95):.2f}")
        frac = r["bad"].mean(0)
        top = np.argsort(frac)[::-1][:8]
        P("    most-failing bonds: " + "; ".join(
            f"{seq1[i]}{i + 1}-{seq1[i + 1]}{i + 2} fails {100 * frac[i]:.0f}% (median d {np.median(d[:, i]):.2f})" for i in top if frac[i] > 0))
        sens = []
        for lo, hi, cl in [(3.3, 4.3, 5.0), (3.3, 4.3, 6.0), (3.3, 4.3, 8.0), (3.0, 4.6, 5.0), (3.0, 4.6, 8.0), (2.8, 5.0, 8.0)]:
            ok = ~((d < lo) | (d > hi)).any(1) & (cr <= cl)
            sens.append(f"[{lo}-{hi}A, core<={cl:g}A]: {100 * ok.mean():.0f}%")
        P("    pass rate if limits were loosened: " + " | ".join(sens))
        P("")
    # ---------------- plots ----------------
    allx = np.concatenate([results[k]["x"][results[k]["passed"]] for k in results if results[k]["passed"].any()] + [np.array([m2[0]])])
    ally = np.concatenate([results[k]["y"][results[k]["passed"]] for k in results if results[k]["passed"].any()] + [np.array([m1[1]])])
    lim = float(np.ceil(max(allx.max(), ally.max()) + 1))
    vmax = 1
    for k, r in results.items():
        ok = r["passed"]
        if ok.any():
            edges = np.arange(0, lim + 0.25, 0.25)
            vmax = max(vmax, np.histogram2d(r["x"][ok], r["y"][ok], bins=[edges, edges])[0].max())
    for name, r in results.items():
        ok = r["passed"]
        fig, ax = plt.subplots(figsize=(4.6, 4.2))
        hist_plot(ax, r["x"][ok], r["y"][ok], m1, m2, lim,
                  f"{name}: {int(ok.sum())} frames pass ({int((r['state'][ok] == 1).sum())} open / {int((r['state'][ok] == 2).sum())} closed)",
                  vmax=vmax, fig=fig)
        fig.tight_layout(); fig.savefig(out / "hist2d" / f"{name}_pass.png", dpi=200); plt.close(fig)
        if name in key_names:
            lim_all = float(np.ceil(max(r["x"].max(), r["y"].max(), m1[1], m2[0]) + 1))
            fig, ax = plt.subplots(figsize=(4.6, 4.2))
            hist_plot(ax, r["x"], r["y"], m1, m2, lim_all, f"{name}: ALL {r['n']} frames (before filter)", fig=fig)
            fig.tight_layout(); fig.savefig(out / "hist2d" / f"{name}_all.png", dpi=200); plt.close(fig)
    panel = [k for k in key_names if k in results]
    fig, axes = plt.subplots(2, 4, figsize=(17, 8.2))
    for ax, name in zip(axes.ravel(), panel):
        r = results[name]; ok = r["passed"]
        hist_plot(ax, r["x"][ok], r["y"][ok], m1, m2, lim, f"{name}  ({int((r['state'][ok] == 1).sum())} open / {int((r['state'][ok] == 2).sum())} closed)",
                  vmax=vmax, cbar=False)
    for ax in axes.ravel()[len(panel):]:
        ax.axis("off")
    fig.tight_layout(); fig.savefig(out / "overview_top3_worst3.png", dpi=170); plt.close(fig)

    # ---------------- topology + xtc (CA only) ----------------
    try:
        import mdtraj as md
        from mdtraj.core.element import carbon
        for name in key_names:
            if name not in results:
                continue
            r = results[name]
            top = md.Topology()
            chain = top.add_chain()
            for i, aa in enumerate(r["seq"]):
                res = top.add_residue(AA1TO3.get(aa, "UNK"), chain, resSeq=i + 1)
                top.add_atom("CA", carbon, res)
            traj = md.Trajectory(r["aligned"].astype(np.float32) / 10.0, top)       # A -> nm
            traj[0].save_pdb(str(out / "topology" / f"{name}_CA.pdb"))
            traj.save_xtc(str(out / "xtc" / f"{name}_CA.xtc"))
            with open(out / "frames" / f"{name}_frames.csv", "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["frame", "passes_filter", "ca_ca_ok", "n_bad_bonds", "core_rmsd_A", "state", "rmsd_state1_A", "rmsd_state2_A"])
                for i in range(r["n"]):
                    w.writerow([i, int(r["passed"][i]), int(r["bonds_ok"][i]), int(r["bad"][i].sum()),
                                f"{r['core_rmsd'][i]:.3f}", int(r["state"][i]), f"{r['x'][i]:.3f}", f"{r['y'][i]:.3f}"])
        P("topology/xtc written (CA-only, all frames, core-aligned on state 1; see frames/*.csv for the filter flag per frame)")
    except Exception as exc:                                                       # keep the diagnostics even if mdtraj is missing
        P(f"topology/xtc NOT written: {exc!r}")

    text = "\n".join(lines)
    (out / "diagnostics.txt").write_text(text)
    print(text)
    zp = run / "analysis.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(run))
    print(f"\nWROTE {zp} ({zp.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
