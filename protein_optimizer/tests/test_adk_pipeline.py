"""Proof-of-concept tests for the Dyna-1 -> ThermoMPNN -> BioEmu -> MCMC pipeline (mock backends)."""

import math
from types import SimpleNamespace

import numpy as np

from protein_optimizer.adk_pipeline import (
    ADKPipelineConfig, MCMCSearch, MockTwoStateBackend, core_mask, evaluate_mutant,
    make_two_state_references, physical_frame_mask, rank_mutants, rank_positions_dyna1,
)
from protein_optimizer.thermompnn import MockThermoMPNNBackend

L = 60
SEQ = "ACDEFGHIKLMNPQRSTVWY" * 3
CFG = dict(mobile_ranges=[(41, 60)], frames=200, top_positions=10, time_budget_s=3, stall_steps=5)


def _setup(tmp_path, **over):
    cfg = ADKPipelineConfig(out_dir=str(tmp_path), **{**CFG, **over})
    ref1, ref2 = make_two_state_references(L, (41, 60))
    backend = MockTwoStateBackend(SimpleNamespace(num_samples=cfg.frames, batch_size=1), ref1, ref2)
    b = MockThermoMPNNBackend()
    return cfg, ref1, ref2, backend, b.predict("state1.pdb", SEQ), b.predict("state2.pdb", SEQ)


def test_dyna1_ranking_uses_mean_of_states():
    assert rank_positions_dyna1([0.9, 0.1, 0.5], [0.1, 0.1, 0.9])[:2] == [2, 0]


def test_rank_mutants_guard_cysteine_and_order(tmp_path):
    cfg, *_ , t1, t2 = _setup(tmp_path)
    ranked = rank_mutants(t1, t2, range(L), cfg, top_n=50)
    assert ranked and all(m.aa != "C" and m.worst <= cfg.ddg_cutoff for m in ranked)
    mts = [m.ddg_mt for m in ranked]
    assert mts == sorted(mts)                      # bias toward state 1: most negative first
    cfg.bias_toward = 2
    flipped = [m.ddg_mt for m in rank_mutants(t1, t2, range(L), cfg, 50)]
    assert flipped == sorted(flipped, reverse=True) and flipped[0] > mts[0]   # bias_toward=2 flips the order


def test_frame_filter_drops_broken_backbone(tmp_path):
    cfg, ref1, ref2, backend, *_ = _setup(tmp_path, frames=400)
    backend.bad = 0.2
    out = backend.infer_batch([SEQ])[0]
    frames = np.stack([s.ca_coords for s in out.samples])
    keep = physical_frame_mask(frames, ref1, core_mask(L, cfg.mobile_ranges), cfg)
    assert 0.65 < keep.mean() < 0.95               # ~20% broken frames removed, rest kept


def test_state_never_reached_gives_nan(tmp_path):
    cfg, ref1, ref2, backend, *_ = _setup(tmp_path)
    never = next(s for s in (SEQ[:-1] + a for a in "ACDEFGHIKLMNPQRSTVWY") if backend.p_state2(s) == 0.0)
    res = evaluate_mutant(backend, never, ["x"], ref1, ref2, cfg)
    assert res.resampled and res.n_state2 < cfg.min_state_frames and math.isnan(res.llr)


def test_rare_state_is_resampled_not_dropped(tmp_path):
    cfg, ref1, ref2, backend, *_ = _setup(tmp_path, frames=100, min_state_frames=5)
    aas = "ACDEFGHIKLMNPQRSTVWY"
    rare = next(SEQ[:i] + a + SEQ[i + 1:] for i in range(L) for a in aas
                if 0.0 < backend.p_state2(SEQ[:i] + a + SEQ[i + 1:]) < 0.02)
    res = evaluate_mutant(backend, rare, ["x"], ref1, ref2, cfg)
    assert res.resampled and res.n_frames == 200       # re-sampled once at 2x, not dropped on first pass


def test_mcmc_end_to_end_writes_checkpoint_and_pngs(tmp_path):
    cfg, ref1, ref2, backend, t1, t2 = _setup(tmp_path)
    order = list(range(L))
    seeds = [SEQ[:m.position] + m.aa + SEQ[m.position + 1:] for m in rank_mutants(t1, t2, order[:10], cfg)]
    search = MCMCSearch(cfg, backend, SEQ, t1, t2, ref1, ref2, order)
    best = search.run(seeds)
    assert best.valid and (tmp_path / "checkpoint.json").exists()
    assert list((tmp_path / "pca").glob("*.png"))
    assert all(r.sequence not in search.discarded for r in search.results.values() if r.valid)
