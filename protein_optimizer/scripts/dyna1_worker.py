"""
Dyna-1 inference worker.

Runs inside Dyna-1's own virtualenv (its pinned numpy<2 / biotite / transformers stack
conflicts with BioEmu's numpy>=2 / jax stack, so the two never share a process).
`protein_optimizer.dyna1.Dyna1MutationProposer` spawns this and talks JSON lines:

    worker -> parent : {"ready": true, "device": "cuda"}            (once, after load)
    parent -> worker : {"seqs": ["MKT...", ...]}
    worker -> parent : {"profiles": [[p_exchange per residue], ...]}  or {"error": "..."}

stdout is reserved for the protocol; anything the libraries print goes to stderr.
"""

import argparse
import json
import os
import sys

# Keep a private handle on the real stdout, then point sys.stdout at stderr so stray
# prints from torch / esm can never corrupt the JSON stream.
_PROTO = sys.stdout
sys.stdout = sys.stderr

# ESM-3 sequence-track vocabulary (ids 0..32); same ordering as ESM-2's.
_VOCAB = [
    "<cls>", "<pad>", "<eos>", "<unk>",
    "L", "A", "G", "V", "S", "E", "R", "T", "I", "D", "P", "K", "Q", "N", "F", "Y",
    "M", "H", "W", "C", "X", "B", "U", "Z", "O", ".", "-", "<null_1>", "<mask>",
]
_TOKEN_ID = {tok: i for i, tok in enumerate(_VOCAB)}


def _send(obj) -> None:
    _PROTO.write(json.dumps(obj) + "\n")
    _PROTO.flush()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="path to the cloned Dyna-1 repo")
    ap.add_argument("--weights", required=True, help="path to dyna1.pt")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--half", action="store_true", help="bf16 autocast on CUDA")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    os.chdir(repo)
    sys.path.insert(0, repo)

    import torch
    from model.model import ESM_model
    import utils as dyna1_utils

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    # Upstream pins the ESM-3 backbone to cuda-if-available but leaves the classifier
    # head on CPU, so move the whole model explicitly.
    model = ESM_model(method="esm3")
    model.load_state_dict(torch.load(args.weights, map_location="cpu"), strict=False)
    model = model.to(device).eval()

    _send({"ready": True, "device": str(device)})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            seqs = json.loads(line)["seqs"]
            tokens = torch.tensor([[_TOKEN_ID[a] for a in s] for s in seqs], device=device)
            sequence_id = torch.ones_like(tokens, dtype=torch.bool)
            with torch.no_grad(), torch.autocast(
                device_type=device.type,
                dtype=torch.bfloat16,
                enabled=args.half and device.type == "cuda",
            ):
                logits = model((tokens, None), sequence_id)   # sequence-only mode
            p = dyna1_utils.prob_adjusted(logits.float()).detach().cpu().numpy()
            _send({"profiles": p.reshape(len(seqs), -1).tolist()})
        except Exception as exc:   # report, keep serving
            _send({"error": f"{type(exc).__name__}: {exc}"})


if __name__ == "__main__":
    main()
