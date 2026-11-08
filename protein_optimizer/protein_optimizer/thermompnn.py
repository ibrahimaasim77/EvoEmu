"""
ThermoMPNN stability guard.

Scores every point substitution of the reference sequence against one or more
backbones (poses) with ThermoMPNN (Dieckhaus et al., PNAS 2024) and builds a
blocklist of mutations predicted not to fold. The evolutionary search drops
candidates containing a blocklisted mutation *before* spending BioEmu time.

Conventions
-----------
  - ΔΔG in kcal/mol, positive = destabilizing (ThermoMPNN's convention).
  - Positions are 0-based indices into the reference sequence, matching
    ThermoMPNN's own CSV output and ``MutationConfig.allowed_positions``.
  - A mutation is blocked when its ΔΔG exceeds ``ddg_cutoff`` on ANY backbone
    (the worst case across poses is what counts).

ThermoMPNN only models single point mutations, so a multi-mutant candidate is
rejected if any one of its mutations is blocklisted; epistasis is ignored.
"""

from __future__ import annotations

import csv
import hashlib
import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .config import ThermoMPNNConfig

logger = logging.getLogger(__name__)

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"

Mutation = Tuple[int, str]   # (0-based position, mutant amino acid)


# ---------------------------------------------------------------------------
# ΔΔG table for one backbone
# ---------------------------------------------------------------------------


@dataclass
class DdgTable:
    """Predicted ΔΔG for every substitution on a single backbone."""

    name: str
    wildtype: str                              # sequence as seen in the structure
    ddg: Dict[Mutation, float] = field(default_factory=dict)

    def get(self, position: int, aa: str) -> Optional[float]:
        return self.ddg.get((position, aa))


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------


class BaseThermoMPNNBackend(ABC):
    """Produces a DdgTable for a PDB. Mirrors the BioEmu backend pattern."""

    @abstractmethod
    def predict(self, pdb_path: str, sequence: str) -> DdgTable:
        """Score all 19 substitutions at every position of ``sequence``."""


class MockThermoMPNNBackend(BaseThermoMPNNBackend):
    """
    Deterministic synthetic ΔΔG values for tests / GPU-free development.

    Values come from a hash of (structure, position, mutation), spread over
    roughly -1..+4 kcal/mol so a +2 cutoff blocks a realistic minority.
    """

    def predict(self, pdb_path: str, sequence: str) -> DdgTable:
        name = Path(pdb_path).stem
        table = DdgTable(name=name, wildtype=sequence)
        for pos, wt in enumerate(sequence):
            for aa in AMINO_ACIDS:
                if aa == wt:
                    continue
                digest = hashlib.sha256(f"{name}:{pos}:{aa}".encode()).digest()
                u = int.from_bytes(digest[:4], "big") / 2**32
                table.ddg[(pos, aa)] = -1.0 + 5.0 * u
        return table


class ThermoMPNNWrapper(BaseThermoMPNNBackend):
    """
    Runs the Kuhlman-Lab/ThermoMPNN ``analysis/custom_inference.py`` script in a
    subprocess (so its dependencies stay out of this environment) and parses
    the site-saturation CSV it writes.
    """

    def __init__(self, config: ThermoMPNNConfig) -> None:
        if not config.repo_dir:
            raise ValueError(
                "thermompnn.repo_dir must point to a Kuhlman-Lab/ThermoMPNN "
                "checkout (or set thermompnn.mock=true)."
            )
        self.config = config
        self._script = Path(config.repo_dir).expanduser() / "analysis" / "custom_inference.py"
        if not self._script.is_file():
            raise FileNotFoundError(f"ThermoMPNN inference script not found: {self._script}")

    def predict(self, pdb_path: str, sequence: str) -> DdgTable:
        pdb = Path(pdb_path).expanduser().resolve()
        if not pdb.is_file():
            raise FileNotFoundError(f"PDB not found: {pdb}")
        with tempfile.TemporaryDirectory() as out_dir:
            cmd = [
                self.config.python_executable, str(self._script),
                "--pdb", str(pdb), "--chain", self.config.chain,
                "--out_dir", out_dir,
            ]
            if self.config.model_path:
                cmd += ["--model_path", str(Path(self.config.model_path).expanduser())]
            logger.info("Running ThermoMPNN on %s ...", pdb.name)
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self._script.parent))
            if proc.returncode != 0:
                raise RuntimeError(
                    f"ThermoMPNN failed on {pdb.name} (exit {proc.returncode}):\n"
                    f"{proc.stderr[-2000:]}"
                )
            csv_path = Path(out_dir) / f"ThermoMPNN_inference_{pdb.stem}.csv"
            if not csv_path.is_file():
                raise RuntimeError(f"ThermoMPNN produced no output CSV at {csv_path}")
            return parse_thermompnn_csv(csv_path, pdb.stem, sequence)


def parse_thermompnn_csv(path: str | Path, name: str, sequence: str) -> DdgTable:
    """
    Parse a ThermoMPNN custom_inference CSV (columns ddG_pred, position,
    wildtype, mutation) into a DdgTable.

    The structure's wild-type residues must match ``sequence`` at every scored
    position; a mismatch means the PDB and the pipeline sequence disagree on
    numbering/identity, and every downstream lookup would be wrong.
    """
    table = DdgTable(name=name, wildtype=sequence)
    seen_wt: Dict[int, str] = {}
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    # ThermoMPNN's position column may be 0- or 1-based depending on version: pick the offset that
    # makes the CSV's wild-type residues agree with the sequence.
    def _agree(off: int) -> int:
        return sum(1 for r in rows if 0 <= int(r["position"]) - off < len(sequence)
                   and sequence[int(r["position"]) - off] == r["wildtype"])
    offset = max((0, 1), key=_agree)
    if True:
        for row in rows:
            pos = int(row["position"]) - offset
            wt, mut = row["wildtype"], row["mutation"]
            if pos >= len(sequence) or sequence[pos] != wt:
                raise ValueError(
                    f"{name}: structure has {wt} at 0-based position {pos} but the "
                    f"pipeline sequence has "
                    f"{sequence[pos] if pos < len(sequence) else '<out of range>'}. "
                    "The PDB must match original_sequence residue-for-residue."
                )
            seen_wt[pos] = wt
            if mut in AMINO_ACIDS:
                table.ddg[(pos, mut)] = float(row["ddG_pred"])
    if not table.ddg:
        raise ValueError(f"{name}: no ΔΔG rows parsed from {path}")
    return table


# ---------------------------------------------------------------------------
# Dyna-1 positions
# ---------------------------------------------------------------------------


def read_dyna1_positions(path: str | Path, threshold: float) -> Set[int]:
    """
    Read per-residue Dyna-1 scores (CSV/TSV, ``residue_number,score``, 1-based,
    optional header) and return the 0-based positions scoring >= threshold.
    """
    flagged: Set[int] = set()
    with open(path, newline="") as fh:
        for line in fh:
            parts = line.replace("\t", ",").strip().split(",")
            if len(parts) < 2:
                continue
            try:
                resnum, score = int(parts[0]), float(parts[1])
            except ValueError:
                continue   # header or comment
            if score >= threshold:
                flagged.add(resnum - 1)
    return flagged


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


class StabilityFilter:
    """Blocklist built from one or more DdgTables; screens candidate sequences."""

    def __init__(
        self,
        reference: str,
        tables: Sequence[DdgTable],
        ddg_cutoff: float,
        dyna1_positions: Optional[Iterable[int]] = None,
    ) -> None:
        if not tables:
            raise ValueError("StabilityFilter needs at least one DdgTable.")
        self.reference = reference
        self.tables = list(tables)
        self.cutoff = ddg_cutoff
        self.dyna1_positions: Set[int] = set(dyna1_positions or [])

        # Worst-case (max) ΔΔG across backbones for every mutation.
        self.worst_ddg: Dict[Mutation, float] = {}
        for key in self.tables[0].ddg:
            values = [t.ddg[key] for t in self.tables if key in t.ddg]
            self.worst_ddg[key] = max(values)
        self.blocked: Dict[Mutation, float] = {
            k: v for k, v in self.worst_ddg.items() if v > ddg_cutoff
        }

    def offending_mutations(self, candidate: str) -> List[Mutation]:
        """Blocklisted point mutations a candidate carries vs the reference."""
        if len(candidate) != len(self.reference):
            return []   # not a pure-substitution variant; cannot be checked
        return [
            (i, aa)
            for i, (ref_aa, aa) in enumerate(zip(self.reference, candidate))
            if ref_aa != aa and (i, aa) in self.blocked
        ]

    def filter(self, candidates: Sequence[str]) -> Tuple[List[str], Dict[str, List[Mutation]]]:
        """Split candidates into (kept, {rejected: offending mutations})."""
        kept: List[str] = []
        rejected: Dict[str, List[Mutation]] = {}
        for seq in candidates:
            bad = self.offending_mutations(seq)
            if bad:
                rejected[seq] = bad
            else:
                kept.append(seq)
        return kept, rejected

    def write_report(self, path: str | Path) -> None:
        """One row per substitution: ΔΔG on each backbone, worst case, verdict."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        names = [t.name for t in self.tables]
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(
                ["position", "wildtype", "mutant"]
                + [f"ddg_{n}" for n in names]
                + ["worst_ddg", "blocked", "dyna1_flagged"]
            )
            for (pos, aa) in sorted(self.worst_ddg):
                w.writerow(
                    [pos + 1, self.reference[pos], aa]
                    + [
                        f"{t.ddg[(pos, aa)]:.3f}" if (pos, aa) in t.ddg else ""
                        for t in self.tables
                    ]
                    + [
                        f"{self.worst_ddg[(pos, aa)]:.3f}",
                        int((pos, aa) in self.blocked),
                        int(pos in self.dyna1_positions),
                    ]
                )

    def summary(self) -> str:
        total = len(self.worst_ddg)
        return (
            f"{len(self.blocked)}/{total} substitutions blocked "
            f"(ΔΔG > {self.cutoff:+.2f} kcal/mol on any of {len(self.tables)} backbone(s))"
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_thermompnn_backend(config: ThermoMPNNConfig) -> BaseThermoMPNNBackend:
    if config.mock:
        logger.warning("ThermoMPNN running in MOCK mode — ΔΔG values are synthetic.")
        return MockThermoMPNNBackend()
    return ThermoMPNNWrapper(config)


def build_stability_filter(
    config: ThermoMPNNConfig,
    reference: str,
    output_dir: str = "results",
    backend: Optional[BaseThermoMPNNBackend] = None,
) -> Optional[StabilityFilter]:
    """Build the filter from config, or None when the guard is disabled."""
    if not config.enabled:
        return None
    if not config.pdb_paths:
        raise ValueError("thermompnn.enabled is true but thermompnn.pdb_paths is empty.")
    backend = backend or build_thermompnn_backend(config)
    tables = [backend.predict(p, reference) for p in config.pdb_paths]

    dyna1: Set[int] = set()
    if config.dyna1_scores_path:
        dyna1 = read_dyna1_positions(config.dyna1_scores_path, config.dyna1_threshold)
        logger.info("Dyna-1: %d high-score positions flagged", len(dyna1))

    flt = StabilityFilter(reference, tables, config.ddg_cutoff, dyna1)
    report = config.report_path or str(Path(output_dir) / "thermompnn_report.csv")
    flt.write_report(report)
    logger.info("ThermoMPNN guard: %s | report: %s", flt.summary(), report)
    return flt
