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


# --- real (non-mock) path, exercised against a stub worker speaking the same protocol ---

STUB = str(__import__("pathlib").Path(__file__).parent / "stub_dyna1_worker.py")


def _fake_repo(tmp_path):
    (tmp_path / "model" / "weights").mkdir(parents=True)
    (tmp_path / "model" / "model.py").write_text("")
    (tmp_path / "model" / "weights" / "dyna1.pt").write_text("")
    return tmp_path


def _worker_proposer(tmp_path, **kw):
    import sys

    cfg = Dyna1Config(
        repo_path=str(_fake_repo(tmp_path)),
        python_path=sys.executable,
        worker_script=STUB,
        batch_size=7,
        **kw,
    )
    return Dyna1MutationProposer(cfg)


def test_worker_protocol_end_to_end(tmp_path):
    proposer = _worker_proposer(tmp_path)
    try:
        out = proposer.propose(SEQ, [3, 11])
        assert set(out) == {3, 11}
        assert all(len(c) == 5 for c in out.values())
        # batch_size=7 forces several round-trips (39 sequences) — all must come back aligned
        assert len(proposer._cache) == 1 + 2 * 19
    finally:
        proposer.close()


def test_worker_error_is_raised_not_swallowed(tmp_path):
    import pytest

    proposer = _worker_proposer(tmp_path)
    try:
        with pytest.raises(RuntimeError, match="bad residue"):
            proposer.score_sequences(["MKZ"])
    finally:
        proposer.close()


def test_missing_worker_env_gives_actionable_error(tmp_path):
    import pytest

    cfg = Dyna1Config(repo_path=str(_fake_repo(tmp_path)))   # no Dyna-1/.venv in the fake repo
    with pytest.raises(FileNotFoundError, match="setup_vm.sh"):
        Dyna1MutationProposer(cfg).propose(SEQ, [1])
