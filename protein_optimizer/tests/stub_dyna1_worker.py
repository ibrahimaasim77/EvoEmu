"""Stand-in for scripts/dyna1_worker.py: same JSON-lines protocol, fake deterministic scores."""

import argparse
import hashlib
import json
import sys

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--repo")
ap.add_argument("--weights")
ap.add_argument("--device")
ap.add_argument("--half", action="store_true")
ap.parse_args()

print(json.dumps({"ready": True, "device": "stub"}), flush=True)
for line in sys.stdin:
    seqs = json.loads(line)["seqs"]
    if any("Z" in s for s in seqs):
        print(json.dumps({"error": "ValueError: bad residue"}), flush=True)
        continue
    profiles = [
        np.random.default_rng(int(hashlib.sha256(s.encode()).hexdigest()[:8], 16))
        .uniform(0, 1, len(s)).tolist()
        for s in seqs
    ]
    print(json.dumps({"profiles": profiles}), flush=True)
