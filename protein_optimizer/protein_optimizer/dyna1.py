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

Setup (real mode): `bash setup_vm.sh` clones Dyna-1 to ./Dyna-1, builds its own virtualenv
(Dyna-1/.venv — its numpy<2 stack conflicts with BioEmu's), and downloads the weights.
Inference runs in a long-lived worker process (scripts/dyna1_worker.py) inside that
virtualenv; this module only speaks JSON lines to it, so it needs no torch.

Nothing here touches ESM-2: the worker tokenises with ESM-3's own sequence vocabulary.
"""

from __future__ import annotations

import atexit
import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .config import Dyna1Config

logger = logging.getLogger(__name__)

# Canonical single-letter amino acid alphabet (20 standard residues)
AMINO_ACIDS: List[str] = list("ACDEFGHIKLMNPQRSTVWY")

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
        self._proc: Optional[subprocess.Popen] = None
        self._loaded = False
        self._cache: Dict[str, float] = {}   # sequence → scalar dynamics score

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded or self.config.mock:
            return

        cfg = self.config
        repo = Path(cfg.repo_path).expanduser().resolve()
        if not (repo / "model" / "model.py").exists():
            raise FileNotFoundError(
                f"Dyna-1 repo not found at {repo}. Run setup_vm.sh, or clone "
                "https://github.com/WaymentSteeleLab/Dyna-1 there and set "
                "dyna1.repo_path (or dyna1.mock=true)."
            )
        weights = (
            Path(cfg.weights_path).expanduser()
            if cfg.weights_path
            else repo / "model" / "weights" / "dyna1.pt"
        )
        if not weights.exists():
            found = sorted(
                str(f.relative_to(repo)) for f in (repo / "model").rglob("*") if f.is_file()
            )[:30]
            raise FileNotFoundError(
                f"Dyna-1 weights not found at {weights}. Files under {repo / 'model'}: {found}"
            )
        python = Path(cfg.python_path).expanduser() if cfg.python_path else repo / ".venv" / "bin" / "python"
        if not python.exists():
            raise FileNotFoundError(
                f"Dyna-1 virtualenv python not found at {python}. Run setup_vm.sh "
                "(it builds Dyna-1/.venv) or set dyna1.python_path."
            )
        worker = (
            Path(cfg.worker_script)
            if cfg.worker_script
            else Path(__file__).resolve().parents[1] / "scripts" / "dyna1_worker.py"
        )

        cmd = [str(python), str(worker), "--repo", str(repo), "--weights", str(weights),
               "--device", cfg.device]
        if cfg.half_precision:
            cmd.append("--half")
        logger.info("Starting Dyna-1 worker: %s", " ".join(cmd))
        # stderr is inherited so model-load logs and tracebacks show up in our output.
        self._proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
        )
        atexit.register(self.close)
        ready = self._read_message()
        if not ready.get("ready"):
            raise RuntimeError(f"Dyna-1 worker failed to start: {ready}")
        logger.info("Dyna-1 ready on device: %s", ready.get("device"))
        self._loaded = True

    def _read_message(self) -> dict:
        assert self._proc is not None and self._proc.stdout is not None
        line = self._proc.stdout.readline()
        if not line:
            code = self._proc.poll()
            raise RuntimeError(
                f"Dyna-1 worker exited unexpectedly (code {code}); see its traceback above."
            )
        return json.loads(line)

    def close(self) -> None:
        """Shut the worker down (also registered with atexit)."""
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None
        self._loaded = False

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
        assert self._proc is not None and self._proc.stdin is not None
        out: List[np.ndarray] = []
        for start in range(0, len(seqs), self.config.batch_size):
            chunk = seqs[start : start + self.config.batch_size]
            self._proc.stdin.write(json.dumps({"seqs": chunk}) + "\n")
            self._proc.stdin.flush()
            reply = self._read_message()
            if "error" in reply:
                raise RuntimeError(f"Dyna-1 worker error: {reply['error']}")
            out.extend(np.asarray(p, dtype=float) for p in reply["profiles"])
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
