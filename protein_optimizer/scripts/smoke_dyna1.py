"""Real-model smoke test for the Dyna-1 proposer (needs the repo + weights from setup_vm.sh).

    python scripts/smoke_dyna1.py [SEQUENCE]
"""

import logging
import sys
import time

from protein_optimizer.config import Dyna1Config
from protein_optimizer.dyna1 import Dyna1MutationProposer

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")

SEQ = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "MKTLLILAVLCLGFAQASGNIERPIDGFHGDLQSLIKAMFESRHITAYIEQLEELRQRQTAATGGMRQ"
)

proposer = Dyna1MutationProposer(Dyna1Config())
t0 = time.time()
out = proposer.propose(SEQ, [5, 20, 40])
print(f"\nscanned 3 positions ({3 * 19} mutants) in {time.time() - t0:.1f}s")
for pos, cands in out.items():
    print(f"pos {pos} ({SEQ[pos]}):", cands)
wt = proposer.score_sequences([SEQ])[0]
print(f"parent mean p_exchange = {wt:.4f}")
spread = {c.proposed_aa for cs in out.values() for c in cs}
assert len(spread) > 1, "all positions proposed the same residue — suspicious"
print("SMOKE TEST OK")
