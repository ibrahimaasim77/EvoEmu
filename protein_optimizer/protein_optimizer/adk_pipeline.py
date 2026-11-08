"""
Dyna-1 -> ThermoMPNN -> BioEmu -> MCMC pipeline (two-state proteins, e.g. ADK).

Stages
------
1. ``rank_positions_dyna1``  mean of the two per-state p(exchange) values; top-K positions.
2. ``rank_mutants``          all 19 substitutions at those positions scored on BOTH backbones.
                             Hard guard: worst-case ddG must be <= cutoff. Rank by
                             ddg_mt = ddg_state1 - ddg_state2 (negative favours state 1).
                             Cysteine substitutions excluded (assay artifact).
3. ``evaluate_mutant``       BioEmu ensemble -> physical-frame filter -> state counts -> LLR/dG.
                             Frames are filtered ONLY on CA-CA bond lengths and core RMSD
                             (never Rg or distance to a reference), so the open/closed split
                             is not biased. Under-sampled states are re-sampled once with
                             2x frames before a mutant is declared NaN (dropped for good).
4. ``MCMCSearch``            Metropolis chain seeded by the best stage-3 mutants. Proposals
                             are restricted to the Dyna-1 position pool, which widens when
                             the chain stalls. The stability guard uses the worst SINGLE
                             mutation ddG (not a sum), so epistasis cannot hide a bad one.

Units: coordinates in Angstrom, ddG in kcal/mol (positive = destabilizing).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from .bioemu import BaseStructuralBackend, BioEmuOutput, ConformationSample
from .thermompnn import AMINO_ACIDS, DdgTable

logger = logging.getLogger(__name__)

RT_KCAL = 0.001987204 * 300.0   # kcal/mol at 300 K


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class ADKPipelineConfig:
    top_positions: int = 10
    top_mutants: int = 20
    ddg_cutoff: float = 2.0                 # worst-case ddG guard (kcal/mol)
    bias_toward: int = 1                    # 1 or 2: which state ddg_mt should favour
    exclude_cysteine: bool = True
    # BioEmu sampling / frame filter
    frames: int = 500
    min_state_frames: int = 5               # below this in a state -> resample once at 2x
    ca_ca_min: float = 3.3                  # Angstrom (0.33 nm)
    ca_ca_max: float = 4.3
    core_rmsd_max: float = 5.0
    # 1-based inclusive residue ranges that MOVE between states. Everything else is "core".
    # ADK (1AKE numbering) NMP ~30-59, LID ~122-159 -- CONFIRM against the chosen PDB pair.
    mobile_ranges: List[Tuple[int, int]] = field(default_factory=list)
    # MCMC
    mcmc_temperature: float = 0.5           # in fitness units (|LLR| distance)
    esm_weight: float = 1.0
    ddg_weight: float = 0.5                 # penalty per kcal/mol of worst ddG above 0
    stall_steps: int = 15                   # steps with no accepted move before pool widens
    pool_growth: int = 5
    time_budget_s: float = 8 * 3600
    target_llr: Optional[float] = None      # None = maximise LLR
    seed: int = 0
    out_dir: str = "results/adk"


# ---------------------------------------------------------------------------
# Stage 1: Dyna-1 positions
# ---------------------------------------------------------------------------


def rank_positions_dyna1(pex_state1: Sequence[float], pex_state2: Sequence[float]) -> List[int]:
    """0-based positions sorted by mean p(exchange), highest first."""
    a, b = np.asarray(pex_state1, float), np.asarray(pex_state2, float)
    if a.shape != b.shape:
        raise ValueError("Dyna-1 outputs for the two states must have equal length.")
    mean = (a + b) / 2.0
    return [int(i) for i in np.argsort(-mean, kind="stable")]


# ---------------------------------------------------------------------------
# Stage 2: ThermoMPNN mutant ranking
# ---------------------------------------------------------------------------


@dataclass
class RankedMutant:
    position: int            # 0-based
    aa: str
    ddg_1: float
    ddg_2: float
    ddg_mt: float            # ddg_1 - ddg_2

    @property
    def worst(self) -> float:
        return max(self.ddg_1, self.ddg_2)


def rank_mutants(
    table_1: DdgTable,
    table_2: DdgTable,
    positions: Sequence[int],
    cfg: ADKPipelineConfig,
    top_n: Optional[int] = None,
) -> List[RankedMutant]:
    wt = table_1.wildtype
    out: List[RankedMutant] = []
    for pos in positions:
        for aa in AMINO_ACIDS:
            if aa == wt[pos] or (cfg.exclude_cysteine and aa == "C"):
                continue
            d1, d2 = table_1.get(pos, aa), table_2.get(pos, aa)
            if d1 is None or d2 is None:
                continue
            m = RankedMutant(pos, aa, d1, d2, d1 - d2)
            if m.worst <= cfg.ddg_cutoff:
                out.append(m)
    out.sort(key=lambda m: m.ddg_mt, reverse=(cfg.bias_toward == 2))
    return out[: (top_n if top_n is not None else cfg.top_mutants)]


# ---------------------------------------------------------------------------
# Stage 3: frames -> states -> LLR
# ---------------------------------------------------------------------------


def core_mask(length: int, mobile_ranges: Sequence[Tuple[int, int]]) -> np.ndarray:
    mask = np.ones(length, dtype=bool)
    for lo, hi in mobile_ranges:
        mask[lo - 1:hi] = False
    return mask


def _kabsch(mobile: np.ndarray, ref: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rotation R and centroids so that (x - cm) @ R + cr superposes mobile onto ref."""
    cm, cr = mobile.mean(0), ref.mean(0)
    H = (mobile - cm).T @ (ref - cr)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1.0, 1.0, d])
    return U @ D @ Vt, cm, cr


def align_on_core(frames: np.ndarray, ref: np.ndarray, core: np.ndarray) -> np.ndarray:
    """Superpose each (L,3) frame onto ``ref`` using core residues only."""
    out = np.empty_like(frames)
    for i, f in enumerate(frames):
        R, cm, cr = _kabsch(f[core], ref[core])
        out[i] = (f - cm) @ R + cr
    return out


def physical_frame_mask(frames: np.ndarray, ref: np.ndarray, core: np.ndarray, cfg: ADKPipelineConfig) -> np.ndarray:
    """True for frames passing BOTH criteria: all CA-CA in range, core RMSD <= limit."""
    d = np.linalg.norm(np.diff(frames, axis=1), axis=2)                   # (N, L-1)
    bonds_ok = np.all((d >= cfg.ca_ca_min) & (d <= cfg.ca_ca_max), axis=1)
    aligned = align_on_core(frames, ref, core)
    rmsd = np.sqrt(((aligned[:, core] - ref[core]) ** 2).sum(-1).mean(-1))
    return bonds_ok & (rmsd <= cfg.core_rmsd_max)


def classify_states(frames: np.ndarray, ref1: np.ndarray, ref2: np.ndarray, core: np.ndarray) -> np.ndarray:
    """1 or 2 per frame: nearer reference by RMSD over the MOBILE residues after core alignment.
    (Used only for counting, after the physical filter -- never for filtering.)"""
    mobile = ~core
    if not mobile.any():
        raise ValueError("mobile_ranges is empty: cannot tell the two states apart.")
    a1 = align_on_core(frames, ref1, core)
    a2 = align_on_core(frames, ref2, core)
    r1 = np.sqrt(((a1[:, mobile] - ref1[mobile]) ** 2).sum(-1).mean(-1))
    r2 = np.sqrt(((a2[:, mobile] - ref2[mobile]) ** 2).sum(-1).mean(-1))
    return np.where(r1 <= r2, 1, 2)


@dataclass
class MutantResult:
    sequence: str
    mutations: List[str]
    n_frames: int = 0
    n_physical: int = 0
    n_state1: int = 0
    n_state2: int = 0
    resampled: bool = False
    llr: float = float("nan")      # ln(n1/n2)
    dg: float = float("nan")       # RT ln(n1/n2), kcal/mol, state1 -> state2
    pca_png: Optional[str] = None

    @property
    def valid(self) -> bool:
        return not math.isnan(self.llr)


def _coords(output: BioEmuOutput) -> np.ndarray:
    arr = [s.ca_coords for s in output.samples if s.ca_coords is not None]
    if not arr:
        raise ValueError("BioEmu output has no CA coordinates; cannot filter/classify frames.")
    return np.stack(arr)


def save_pca_png(frames: np.ndarray, states: np.ndarray, ref1: np.ndarray, ref2: np.ndarray,
                 core: np.ndarray, path: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    aligned = align_on_core(frames, ref1, core).reshape(len(frames), -1)
    refs = align_on_core(np.stack([ref1, ref2]), ref1, core).reshape(2, -1)
    mean = aligned.mean(0)
    _, _, Vt = np.linalg.svd(aligned - mean, full_matrices=False)
    pcs = Vt[:2]
    xy, rxy = (aligned - mean) @ pcs.T, (refs - mean) @ pcs.T
    fig, ax = plt.subplots(figsize=(5, 4), dpi=130)
    for s, c in ((1, "#2b6cb0"), (2, "#dd6b20")):
        sel = states == s
        ax.scatter(xy[sel, 0], xy[sel, 1], s=6, alpha=0.5, c=c, label=f"state {s} (n={int(sel.sum())})")
    ax.scatter(rxy[:, 0], rxy[:, 1], marker="*", s=160, c="k", label="references")
    ax.set(xlabel="PC1", ylabel="PC2", title=title)
    ax.legend(fontsize=7)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def evaluate_mutant(
    backend: BaseStructuralBackend,
    sequence: str,
    mutations: List[str],
    ref1: np.ndarray,
    ref2: np.ndarray,
    cfg: ADKPipelineConfig,
    png_dir: Optional[Path] = None,
) -> MutantResult:
    core = core_mask(len(sequence), cfg.mobile_ranges)
    res = MutantResult(sequence=sequence, mutations=mutations)

    def sample(n: int) -> Tuple[np.ndarray, np.ndarray]:
        backend.config.num_samples = n
        frames = _coords(backend.infer_batch([sequence])[0])
        keep = physical_frame_mask(frames, ref1, core, cfg)
        frames = frames[keep]
        return frames, (classify_states(frames, ref1, ref2, core) if len(frames) else np.array([], int))

    frames, states = sample(cfg.frames)
    res.n_frames = cfg.frames
    n1, n2 = int((states == 1).sum()), int((states == 2).sum())
    if min(n1, n2) < cfg.min_state_frames:           # under-sampled: one 2x re-sample
        more_f, more_s = sample(cfg.frames * 2)
        frames, states = more_f, more_s
        res.resampled, res.n_frames = True, cfg.frames * 2
        n1, n2 = int((states == 1).sum()), int((states == 2).sum())
    res.n_physical, res.n_state1, res.n_state2 = len(frames), n1, n2
    if n1 > 0 and n2 > 0 and min(n1, n2) >= 1:
        res.llr = math.log(n1 / n2)
        res.dg = RT_KCAL * res.llr
    if png_dir is not None and len(frames) > 2:
        p = Path(png_dir) / f"{'_'.join(mutations) or 'wt'}.png"
        save_pca_png(frames, states, ref1, ref2, core, p, f"{'+'.join(mutations) or 'WT'}  n1={n1} n2={n2}")
        res.pca_png = str(p)
    return res


# ---------------------------------------------------------------------------
# Stage 4: MCMC
# ---------------------------------------------------------------------------


def mutation_labels(reference: str, seq: str) -> List[str]:
    return [f"{a}{i + 1}{b}" for i, (a, b) in enumerate(zip(reference, seq)) if a != b]


class MCMCSearch:
    """
    Metropolis chain over sequences. ``esm_logp(seq) -> (L, 20) array`` gives ESM-2 log
    probabilities in AMINO_ACIDS order (pass None for a uniform proposal). The proposal is a
    product of experts: esm_weight * logp - ddg_weight * max(worst_ddg, 0).
    """

    def __init__(
        self,
        cfg: ADKPipelineConfig,
        backend: BaseStructuralBackend,
        reference: str,
        table_1: DdgTable,
        table_2: DdgTable,
        ref1: np.ndarray,
        ref2: np.ndarray,
        position_order: Sequence[int],
        esm_logp: Optional[Callable[[str], np.ndarray]] = None,
    ) -> None:
        self.cfg, self.backend, self.reference = cfg, backend, reference
        self.t1, self.t2, self.ref1, self.ref2 = table_1, table_2, ref1, ref2
        self.order = list(position_order)
        self.pool_size = cfg.top_positions
        self.esm_logp = esm_logp
        self.rng = np.random.default_rng(cfg.seed)
        self.results: Dict[str, MutantResult] = {}
        self.discarded: Set[str] = set()
        self.out = Path(cfg.out_dir)
        self.history: List[dict] = []

    # -- fitness: higher is better ------------------------------------------------
    def fitness(self, llr: float) -> float:
        return llr if self.cfg.target_llr is None else -abs(llr - self.cfg.target_llr)

    def _worst(self, pos: int, aa: str) -> float:
        return max(self.t1.get(pos, aa) or 0.0, self.t2.get(pos, aa) or 0.0)

    def _evaluate(self, seq: str) -> MutantResult:
        if seq in self.results:
            return self.results[seq]
        res = evaluate_mutant(self.backend, seq, mutation_labels(self.reference, seq),
                              self.ref1, self.ref2, self.cfg, self.out / "pca")
        self.results[seq] = res
        if not res.valid:
            self.discarded.add(seq)
            logger.info("Discarded %s (state counts %d/%d)", res.mutations, res.n_state1, res.n_state2)
        return res

    def _propose(self, seq: str) -> Optional[str]:
        pool = self.order[: self.pool_size]
        logp = self.esm_logp(seq) if self.esm_logp else None
        cands, weights = [], []
        for pos in pool:
            for j, aa in enumerate(AMINO_ACIDS):
                if aa == seq[pos] or (self.cfg.exclude_cysteine and aa == "C"):
                    continue
                if self._worst(pos, aa) > self.cfg.ddg_cutoff:        # hard stability guard
                    continue
                new = seq[:pos] + aa + seq[pos + 1:]
                if new in self.discarded:
                    continue
                score = self.cfg.esm_weight * (float(logp[pos, j]) if logp is not None else 0.0)
                score -= self.cfg.ddg_weight * max(self._worst(pos, aa), 0.0)
                cands.append(new)
                weights.append(score)
        if not cands:
            return None
        w = np.exp(np.array(weights) - max(weights))
        return cands[int(self.rng.choice(len(cands), p=w / w.sum()))]

    def run(self, seeds: Sequence[str]) -> MutantResult:
        start = time.time()
        for s in seeds:                                  # generation 0: ThermoMPNN top mutants
            self._evaluate(s)
        valid = [r for r in self.results.values() if r.valid]
        if not valid:
            raise RuntimeError("No seed mutant produced both states; check frames / mobile_ranges / references.")
        cur = max(valid, key=lambda r: self.fitness(r.llr))
        best, stall, step = cur, 0, 0
        while time.time() - start < self.cfg.time_budget_s:
            step += 1
            prop = self._propose(cur.sequence)
            if prop is None:
                self._grow_pool(); continue
            res = self._evaluate(prop)
            accepted = False
            if res.valid:
                delta = self.fitness(res.llr) - self.fitness(cur.llr)
                accepted = delta >= 0 or self.rng.random() < math.exp(delta / self.cfg.mcmc_temperature)
            if accepted:
                cur, stall = res, 0
                if self.fitness(res.llr) > self.fitness(best.llr):
                    best = res
            else:
                stall += 1
                if stall >= self.cfg.stall_steps:
                    self._grow_pool(); stall = 0
            self.history.append({"step": step, "mutations": res.mutations, "llr": res.llr,
                                 "accepted": accepted, "pool": self.pool_size,
                                 "n1": res.n_state1, "n2": res.n_state2})
            self._checkpoint(best)
        return best

    def _grow_pool(self) -> None:
        new = min(self.pool_size + self.cfg.pool_growth, len(self.order))
        if new != self.pool_size:
            logger.info("Chain stalled: widening Dyna-1 pool %d -> %d", self.pool_size, new)
            self.pool_size = new

    def _checkpoint(self, best: MutantResult) -> None:
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "checkpoint.json").write_text(json.dumps({
            "best": asdict(best), "pool_size": self.pool_size,
            "discarded": sorted(self.discarded), "history": self.history,
            "results": {s: asdict(r) for s, r in self.results.items()},
        }, indent=1))


# ---------------------------------------------------------------------------
# Mock two-state backend (tests / proof of concept; NOT real physics)
# ---------------------------------------------------------------------------


def make_two_state_references(length: int, mobile: Tuple[int, int], seed: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    """Synthetic chain (3.8 A bonds) and a copy whose mobile tail is hinged about its first residue.
    ``mobile`` is 1-based inclusive and must end at the C-terminus (keeps all bonds intact)."""
    assert mobile[1] == length, "mock hinge requires the mobile segment to be the C-terminal tail"
    rng = np.random.default_rng(seed)
    steps = rng.normal(size=(length - 1, 3))
    steps = 3.8 * steps / np.linalg.norm(steps, axis=1, keepdims=True)
    ref1 = np.vstack([np.zeros(3), np.cumsum(steps, axis=0)])
    pivot = ref1[mobile[0] - 1]
    th = math.radians(70)
    R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    ref2 = ref1.copy()
    ref2[mobile[0] - 1:] = (ref1[mobile[0] - 1:] - pivot) @ R.T + pivot
    return ref1, ref2


class MockTwoStateBackend(BaseStructuralBackend):
    """Samples frames from the two references with a sequence-hash-determined state-2 fraction."""

    def __init__(self, config, ref1: np.ndarray, ref2: np.ndarray, bad_frame_frac: float = 0.05) -> None:
        super().__init__(config)
        self.ref1, self.ref2, self.bad = ref1, ref2, bad_frame_frac

    @staticmethod
    def p_state2(sequence: str) -> float:
        u = int.from_bytes(hashlib.sha256(sequence.encode()).digest()[:4], "big") / 2**32
        return 0.0 if u < 0.1 else 0.01 + 0.6 * u * u  # ~10% never reach state 2; some are rare

    def _run_inference(self, sequence: str) -> BioEmuOutput:
        seed = int.from_bytes(hashlib.sha256(sequence.encode()).digest()[4:8], "big") + self.config.num_samples
        rng = np.random.default_rng(seed)
        p2, out = self.p_state2(sequence), BioEmuOutput(sequence=sequence)
        for _ in range(self.config.num_samples):
            xyz = (self.ref2 if rng.random() < p2 else self.ref1) + rng.normal(scale=0.08, size=self.ref1.shape)
            if rng.random() < self.bad:                 # unphysical frame: broken backbone
                xyz[len(xyz) // 2:] += 15.0
            out.samples.append(ConformationSample(ca_coords=xyz))
        return out
