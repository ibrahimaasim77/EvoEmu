"""Dyna-1 proposer tests (mock mode — no model or weights required)."""

from protein_optimizer.config import Dyna1Config
from protein_optimizer.dyna1 import AMINO_ACIDS, Dyna1MutationProposer

SEQ = "MKTLLILAVLCLGFAQASGNIERPIDGFHG"


def _proposer(**kw):
    return Dyna1MutationProposer(Dyna1Config(mock=True, **kw))


def test_candidates_exclude_original_and_respect_top_k():
    out = _proposer(top_k_candidates=4).propose(SEQ, [3, 10])
    for pos, cands in out.items():
        assert len(cands) == 4
        assert all(c.proposed_aa != SEQ[pos] and c.proposed_aa in AMINO_ACIDS for c in cands)


def test_ranked_best_first_and_direction_flips_order():
    up = _proposer(top_k_candidates=19, direction="up").propose_single(SEQ, 5)
    down = _proposer(top_k_candidates=19, direction="down").propose_single(SEQ, 5)
    assert [c.log_prob for c in up] == sorted([c.log_prob for c in up], reverse=True)
    assert up[0].proposed_aa == down[-1].proposed_aa


def test_deterministic():
    a = _proposer().propose_single(SEQ, 7)
    b = _proposer().propose_single(SEQ, 7)
    assert [c.proposed_aa for c in a] == [c.proposed_aa for c in b]


def test_errors_propagate_instead_of_silent_random_fallback(tmp_path):
    import random

    import pytest

    from protein_optimizer.config import MutationConfig
    from protein_optimizer.mutation import build_mutator

    broken = Dyna1MutationProposer(Dyna1Config(repo_path=str(tmp_path / "missing")))
    mutator = build_mutator(
        MutationConfig(strategy="dyna1_guided"), random.Random(0), dyna1_proposer=broken
    )
    with pytest.raises(FileNotFoundError):
        mutator.mutate(SEQ)


def test_all_positions_scored_in_one_call_and_cached():
    proposer = _proposer()
    calls = []
    original = proposer._mock_profile
    proposer._mock_profile = lambda s: calls.append(s) or original(s)
    proposer.propose(SEQ, [2, 9, 15])
    assert len(calls) == len(set(calls)) == 1 + 3 * 19      # parent + 19 mutants/position
    proposer.propose(SEQ, [2, 9, 15])
    assert len(calls) == 1 + 3 * 19                         # second pass fully cached
