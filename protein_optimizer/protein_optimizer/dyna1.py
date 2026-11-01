"""
Dyna-1 Mutation Proposal Module

Uses Dyna-1 (WaymentSteeleLab/Dyna-1, ESM-3 variant, sequence-only mode) as the
sole mutation oracle.

Dyna-1 predicts, for every residue, the probability of µs–ms conformational
exchange (``p_exchange``). It has no amino-acid vocabulary head, so it cannot
"propose" mutations directly. Instead we run an in-silico saturation scan:

  1. For each target position, build the 19 single-point mutants.
  2. Score every mutant with Dyna-1 (mean p_exchange over the whole chain, or
     over ``target_positions`` if configured).
  3. Rank substitutions by the change vs. the parent, signed by ``direction``
     ("up" favours more dynamics, "down" favours more rigidity).
  4. Return the top-k as ``MutationCandidate`` objects whose ``log_prob`` is the
     signed delta, z-scored across the 19 substitutions and divided by ``temperature`` (so the mutator's softmax sampling
     prefers, but does not deterministically pick, the best substitution).

Setup (real mode):
  git clone https://github.com/WaymentSteeleLab/Dyna-1  <dyna1.repo_path>
  pip install -r <repo>/requirements.txt
  python -c "from huggingface_hub import snapshot_download as d; d('gelnesr/Dyna-1', allow_patterns=['dyna1.pt'], local_dir='<repo>/model/weights')"

Nothing here touches ESM-2: tokenisation uses ESM-3's sequence vocabulary directly.
"""

from __future__ import annotations

import hashlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .config import Dyna1Config

logger = logging.getLogger(__name__)

# Canonical single-letter amino acid alphabet (20 standard residues)
AMINO_ACIDS: List[str] = list("ACDEFGHIKLMNPQRSTVWY")

# ESM-3 sequence-track vocabulary (ids 0..32). Only the residue letters matter here.
_ESM3_SEQ_VOCAB: List[str] = [
    "<cls>", "<pad>", "<eos>", "<unk>",
    "L", "A", "G", "V", "S", "E", "R", "T", "I", "D", "P", "K", "Q", "N", "F", "Y",
    "M", "H", "W", "C", "X", "B", "U", "Z", "O", ".", "-", "<null_1>", "<mask>",
]
_TOKEN_ID: Dict[str, int] = {tok: i for i, tok in enumerate(_ESM3_SEQ_VOCAB)}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MutationCandidate:
    """A single ranked substitution at one sequence position."""

    position: int
    original_aa: str
    proposed_aa: str
    log_prob: float   # signed Δp_exchange / temperature (higher = more preferred)

    def __repr__(self) -> str:
        return (
            f"MutationCandidate(pos={self.position}, "
            f"{self.original_aa}→{self.proposed_aa}, "
            f"score={self.log_prob:.3f})"
        )


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------


class Dyna1MutationProposer:
    """
    Suggests substitutions by saturation-scanning with Dyna-1.

    Example::

        proposer = Dyna1MutationProposer(cfg.dyna1)
        candidates = proposer.propose(sequence="MKTLLLT...", positions=[5, 12])
        # candidates: Dict[int, List[MutationCandidate]]
    """

    def __init__(self, config: Dyna1Config) -> None:
        self.config = config
        self._model = None
        self._torch = None
        self._device = None
        self._loaded = False
        self._cache: Dict[str, float] = {}   # sequence → scalar dynamics score

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded or self.config.mock:
            return

        try:
            import torch
        except ImportError as exc:
            raise ImportError("torch is required for Dyna-1. pip install torch") from exc

        repo = Path(self.config.repo_path).expanduser().resolve()
        if not (repo / "model" / "model.py").exists():
            raise FileNotFoundError(
                f"Dyna-1 repo not found at {repo}. Clone "
                "https://github.com/WaymentSteeleLab/Dyna-1 there, or set "
                "dyna1.repo_path (or dyna1.mock=true)."
            )
        weights = (
            Path(self.config.weights_path).expanduser()
            if self.config.weights_path
            else repo / "model" / "weights" / "dyna1.pt"
        )
        if not weights.exists():
            found = sorted(
                str(f.relative_to(repo)) for f in (repo / "model").rglob("*") if f.is_file()
            )[:30]
            raise FileNotFoundError(
                f"Dyna-1 weights not found at {weights}. See the module docstring. "
                f"Files under {repo / 'model'}: {found}"
            )

        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))
        from model.model import ESM_model  # type: ignore  # Dyna-1 repo
        import utils as dyna1_utils        # type: ignore  # Dyna-1 repo

        logger.info("Loading Dyna-1 (ESM-3, sequence-only) from %s", repo)
        # Upstream pins the ESM-3 backbone to cuda-if-available at construction but
        # leaves the classifier head on CPU, so move the whole model explicitly.
        device = torch.device(self.config.device if torch.cuda.is_available() else "cpu")
        model = ESM_model(method="esm3")
        state = torch.load(weights, map_location="cpu")
        model.load_state_dict(state, strict=False)
        model = model.to(device).eval()
        self._device = device
        self._model = model
        self._prob_adjusted = dyna1_utils.prob_adjusted
        self._torch = torch
        logger.info("Dyna-1 ready on device: %s", self._device)
        self._loaded = True

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _reduce(self, p: np.ndarray) -> float:
        """Collapse a per-residue p_exchange vector to one scalar."""
        tp = self.config.target_positions
        if tp:
            idx = [i for i in tp if 0 <= i < len(p)]
            if idx:
                return float(p[idx].mean())
        return float(p.mean())

    def _mock_profile(self, seq: str) -> np.ndarray:
        """Deterministic pseudo-random per-residue p_exchange (no model needed)."""
        seed = int(hashlib.sha256(seq.encode()).hexdigest()[:8], 16)
        return np.random.default_rng(seed).uniform(0.0, 1.0, len(seq))

    def _real_profiles(self, seqs: List[str]) -> List[np.ndarray]:
        torch = self._torch
        out: List[np.ndarray] = []
        for start in range(0, len(seqs), self.config.batch_size):
            chunk = seqs[start : start + self.config.batch_size]
            tokens = torch.tensor(
                [[_TOKEN_ID[a] for a in s] for s in chunk], device=self._device
            )
            sequence_id = torch.ones_like(tokens, dtype=torch.bool)
            with torch.no_grad(), torch.autocast(
                device_type=self._device.type,
                dtype=torch.bfloat16,
                enabled=self.config.half_precision and self._device.type == "cuda",
            ):
                logits = self._model((tokens, None), sequence_id)
            p = self._prob_adjusted(logits.float()).detach().cpu().numpy()
            out.extend(p.reshape(len(chunk), -1))   # .squeeze() upstream drops dims
        return out

    def score_sequences(self, seqs: List[str]) -> List[float]:
        """Scalar dynamics score (reduced mean p_exchange) for each sequence."""
        self._ensure_loaded()
        todo = [s for s in dict.fromkeys(seqs) if s not in self._cache]
        if todo:
            profiles = (
                [self._mock_profile(s) for s in todo]
                if self.config.mock
                else self._real_profiles(todo)
            )
            for s, p in zip(todo, profiles):
                self._cache[s] = self._reduce(p)
        return [self._cache[s] for s in seqs]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def propose(
        self,
        sequence: str,
        positions: Optional[List[int]] = None,
    ) -> Dict[int, List[MutationCandidate]]:
        """
        Propose top-k substitutions for each target position (0-based).

        Returns:
            Mapping of position → ranked MutationCandidate list (best first).
        """
        if positions is None:
            positions = list(range(len(sequence)))

        sign = 1.0 if self.config.direction == "up" else -1.0

        # Build every mutant for every position up front so they share batches.
        subs_by_pos = {p: [aa for aa in AMINO_ACIDS if aa != sequence[p]] for p in positions}
        mutants_by_pos = {
            p: [sequence[:p] + aa + sequence[p + 1 :] for aa in subs]
            for p, subs in subs_by_pos.items()
        }
        flat = [sequence] + [m for ms in mutants_by_pos.values() for m in ms]
        flat_scores = dict(zip(flat, self.score_sequences(flat)))
        wt_score = flat_scores[sequence]

        results: Dict[int, List[MutationCandidate]] = {}
        for pos in positions:
            orig = sequence[pos]
            subs = subs_by_pos[pos]
            deltas = np.array([flat_scores[m] - wt_score for m in mutants_by_pos[pos]])
            # Z-score within the position so `temperature` is scale-free: whole-chain
            # mean p_exchange moves by only ~1/L per mutation, which a fixed
            # temperature would flatten into near-uniform sampling.
            scale = max(float(deltas.std()), 1e-9) * self.config.temperature
            ranked = sorted(
                (
                    MutationCandidate(
                        position=pos,
                        original_aa=orig,
                        proposed_aa=aa,
                        log_prob=sign * float(d) / scale,
                    )
                    for aa, d in zip(subs, deltas)
                ),
                key=lambda c: c.log_prob,
                reverse=True,
            )
            results[pos] = ranked[: self.config.top_k_candidates]
        return results

    def propose_single(self, sequence: str, position: int) -> List[MutationCandidate]:
        """Convenience wrapper for a single position."""
        return self.propose(sequence, [position])[position]

    def get_top_substitution(
        self, sequence: str, position: int, exclude_original: bool = True
    ) -> MutationCandidate:
        """Return the single best substitution at a position."""
        candidates = self.propose_single(sequence, position)
        if exclude_original:
            candidates = [c for c in candidates if c.proposed_aa != sequence[position]]
        if not candidates:
            raise ValueError(f"No valid candidates at position {position}.")
        return candidates[0]
