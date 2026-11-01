"""Tests for the ThermoMPNN stability guard (mock backend, no GPU needed)."""

import csv

import pytest

from protein_optimizer.config import OptimizationConfig, ThermoMPNNConfig
from protein_optimizer.evolutionary_search import BudgetedEvolutionarySearch
from protein_optimizer.thermompnn import (
    DdgTable,
    MockThermoMPNNBackend,
    StabilityFilter,
    build_stability_filter,
    parse_thermompnn_csv,
    read_dyna1_positions,
)

SEQ = "MKTLLILAVLCLGFAQASG"


def _table(name, ddg):
    return DdgTable(name=name, wildtype=SEQ, ddg=dict(ddg))


class TestStabilityFilter:
    def test_blocks_above_cutoff_on_either_backbone(self):
        t1 = _table("pose1", {(0, "A"): 0.5, (1, "A"): 3.0, (2, "A"): 0.1})
        t2 = _table("pose2", {(0, "A"): 2.5, (1, "A"): 0.2, (2, "A"): 0.3})
        flt = StabilityFilter(SEQ, [t1, t2], ddg_cutoff=2.0)
        # (0,A) only bad on pose2, (1,A) only bad on pose1, (2,A) fine on both
        assert set(flt.blocked) == {(0, "A"), (1, "A")}
        assert flt.worst_ddg[(0, "A")] == 2.5

    def test_cutoff_is_strict_greater_than(self):
        flt = StabilityFilter(SEQ, [_table("p", {(0, "A"): 2.0})], ddg_cutoff=2.0)
        assert not flt.blocked

    def test_filter_rejects_candidates_with_blocked_mutation(self):
        flt = StabilityFilter(SEQ, [_table("p", {(0, "A"): 5.0, (1, "A"): 0.0})], 2.0)
        ok = "M" + "A" + SEQ[2:]            # position 1 -> A (fine)
        bad = "A" + SEQ[1:]                 # position 0 -> A (blocked)
        multi = "A" + "A" + SEQ[2:]         # carries the blocked one too
        kept, rejected = flt.filter([ok, bad, multi])
        assert kept == [ok]
        assert set(rejected) == {bad, multi}
        assert rejected[bad] == [(0, "A")]

    def test_length_mismatch_passes_through(self):
        flt = StabilityFilter(SEQ, [_table("p", {(0, "A"): 9.0})], 2.0)
        assert flt.offending_mutations(SEQ + "A") == []

    def test_requires_a_table(self):
        with pytest.raises(ValueError):
            StabilityFilter(SEQ, [], 2.0)

    def test_report_written(self, tmp_path):
        t1 = _table("pose1", {(0, "A"): 3.0})
        t2 = _table("pose2", {(0, "A"): 1.0})
        flt = StabilityFilter(SEQ, [t1, t2], 2.0, dyna1_positions={0})
        out = tmp_path / "r.csv"
        flt.write_report(out)
        rows = list(csv.DictReader(open(out)))
        assert rows[0]["position"] == "1" and rows[0]["mutant"] == "A"
        assert rows[0]["blocked"] == "1" and rows[0]["dyna1_flagged"] == "1"
        assert float(rows[0]["worst_ddg"]) == 3.0


class TestMockBackend:
    def test_deterministic_and_complete(self):
        b = MockThermoMPNNBackend()
        a, c = b.predict("pose1.pdb", SEQ), b.predict("pose1.pdb", SEQ)
        assert a.ddg == c.ddg
        assert len(a.ddg) == len(SEQ) * 19

    def test_poses_differ(self):
        b = MockThermoMPNNBackend()
        assert b.predict("pose1.pdb", SEQ).ddg != b.predict("pose2.pdb", SEQ).ddg


class TestParsing:
    def _write(self, path, rows):
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["", "Model", "Dataset", "ddG_pred", "position", "wildtype", "mutation", "pdb", "chain"])
            for i, (pos, wt, mut, ddg) in enumerate(rows):
                w.writerow([i, "ThermoMPNN", "x", ddg, pos, wt, mut, "x", "A"])

    def test_parse_ok(self, tmp_path):
        p = tmp_path / "o.csv"
        self._write(p, [(0, "M", "A", 1.5), (1, "K", "A", -0.5)])
        t = parse_thermompnn_csv(p, "x", SEQ)
        assert t.get(0, "A") == 1.5 and t.get(1, "A") == -0.5

    def test_wildtype_mismatch_raises(self, tmp_path):
        p = tmp_path / "o.csv"
        self._write(p, [(0, "W", "A", 1.0)])
        with pytest.raises(ValueError, match="match original_sequence"):
            parse_thermompnn_csv(p, "x", SEQ)

    def test_dyna1_reader(self, tmp_path):
        p = tmp_path / "d.csv"
        p.write_text("residue,score\n1,0.9\n2,0.1\n5,0.5\n")
        assert read_dyna1_positions(p, 0.5) == {0, 4}


class TestBuildAndSearch:
    def test_disabled_returns_none(self):
        assert build_stability_filter(ThermoMPNNConfig(), SEQ) is None

    def test_enabled_requires_pdbs(self):
        with pytest.raises(ValueError):
            build_stability_filter(ThermoMPNNConfig(enabled=True, mock=True), SEQ)

    def test_search_never_scores_blocked_mutations(self, tmp_path):
        cfg = OptimizationConfig()
        cfg.original_sequence = SEQ
        cfg.bioemu.mock = True
        cfg.mutation.strategy = "random"
        cfg.ga.population_size = 30
        cfg.ga.max_generations = 2
        cfg.logging.output_dir = str(tmp_path)
        cfg.thermompnn = ThermoMPNNConfig(
            enabled=True, mock=True, pdb_paths=["pose1.pdb", "pose2.pdb"], ddg_cutoff=1.0
        )
        search = BudgetedEvolutionarySearch(cfg)
        result = search.run()
        flt = search._stability_filter
        assert result.total_rejected > 0
        assert (tmp_path / "thermompnn_report.csv").is_file()
        for seq in result.all_scores:
            assert flt.offending_mutations(seq) == []
