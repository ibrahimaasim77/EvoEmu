
"""Stage C: end-to-end directed evolution on T4 lysozyme with a STATE-based BioEmu score.
Start L99A (ground-state dominated) -> target = triple mutant L99A/G113A/R119P (excited-state dominated).
Fitness (injected via log_partition) = ln((n_ES+0.5)/(n_ground+0.5)) over BioEmu frames.
Arms: ThermoMPNN guard off / on (cutoff c, two poses 3DMV ground + 2LCB excited)."""
import sys, os, json, time, glob, tempfile, argparse, logging
import numpy as np
sys.path.insert(0, '/workspace/t4l_validation')
from msa_util import a3m_for
sys.path.insert(0, '/workspace/thermompnn_module_test/EvoEmu/protein_optimizer')
from protein_optimizer.config import OptimizationConfig, ThermoMPNNConfig
from protein_optimizer.bioemu import BaseStructuralBackend, BioEmuOutput, BioEmuWrapper
import protein_optimizer.evolutionary_search as es_mod
from protein_optimizer.evolutionary_search import BudgetedEvolutionarySearch
from protein_optimizer.thermompnn import ThermoMPNNWrapper, BaseThermoMPNNBackend, build_stability_filter

ap = argparse.ArgumentParser()
ap.add_argument('--samples', type=int, default=40); ap.add_argument('--pop', type=int, default=40)
ap.add_argument('--gens', type=int, default=4); ap.add_argument('--seeds', type=int, nargs='+', default=[0, 1, 2])
ap.add_argument('--arms', nargs='+', default=['off', 'on1.0']); ap.add_argument('--deadline', type=float, default=0, help='unix time; stop starting new runs after this')
ap.add_argument('--tag', default='stageC')
args = ap.parse_args()
logging.basicConfig(level=logging.WARNING)

D = '/workspace/t4l_validation'
seqs = json.load(open(D + '/sequences.json'))
L99A = seqs['L99A_ground']; TRIPLE = seqs['triple_excited']
NRES = 162

def read_models(pid):
    models, cur = [], None
    for l in open('%s/structures/%s.pdb' % (D, pid)):
        if l.startswith('MODEL'): cur = []
        elif l.startswith('ENDMDL'): models.append(np.array(cur)); cur = None
        elif l.startswith('ATOM') and l[21] == 'A' and l[12:16].strip() == 'CA' and l[16] in ' A':
            if cur is None and not models: cur = []
            if cur is not None: cur.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
    if cur: models.append(np.array(cur))
    return [m[:NRES] / 10.0 for m in models]
def kabsch(P, Q):
    Pc, Qc = P.mean(0), Q.mean(0)
    U, S, Vt = np.linalg.svd((P - Pc).T @ (Q - Qc)); d = np.sign(np.linalg.det(U @ Vt))
    return U @ np.diag([1, 1, d]) @ Vt, Pc, Qc
def fit(P, Q, idx):
    R, Pc, Qc = kabsch(P[idx], Q[idx]); return (P - Pc) @ R + Qc
def rmsd(P, Q, idx): return float(np.sqrt(((P[idx] - Q[idx]) ** 2).sum(1).mean()))
ground = read_models('3DMV')[0]; es = read_models('2LCB')[0]
allidx = np.arange(NRES); disp = np.sqrt(((fit(es, ground, allidx) - ground) ** 2).sum(1))
region = np.where(disp > disp.mean() + disp.std())[0]; core = np.setdiff1d(allidx, region); es_c = fit(es, ground, core)
def classify(frames):
    g, e = [], []
    for P in frames:
        Pf = fit(P, ground, core); g.append(rmsd(Pf, ground, region)); e.append(rmsd(Pf, es_c, region))
    return np.array(g), np.array(e)

STATS = {}
class StateLLRBackend(BaseStructuralBackend):
    def _run_inference(self, sequence):
        from bioemu.sample import main
        with tempfile.TemporaryDirectory() as td:
            main(sequence=a3m_for(sequence), num_samples=args.samples, output_dir=td, base_seed=0, filter_samples=False, batch_size_100=40)
            pos = np.concatenate([np.load(f)['pos'] for f in sorted(glob.glob(td + '/batch_*.npz'))])
        out = BioEmuOutput(sequence=sequence)
        for P in pos: out.samples.append(BioEmuWrapper._coords_to_sample(P * 10.0))
        cc = np.linalg.norm(np.diff(pos[:, :NRES], axis=1), axis=2)
        ok = ((cc > 0.33) & (cc < 0.43)).all(axis=1)
        if ok.sum() < 3:
            out.log_partition = -10.0; STATS[sequence] = (0, 0, int(ok.sum())); return out
        g, e = classify(pos[ok][:, :NRES]); nE = int((e < g).sum()); nG = int(len(g) - nE)
        out.log_partition = float(np.log((nE + 0.5) / (nG + 0.5))); STATS[sequence] = (nE, nG, int(ok.sum()))
        return out

# ThermoMPNN tables once (two poses of the L99A sequence)
class Cached(BaseThermoMPNNBackend):
    def __init__(self): self.t = {}
    def predict(self, pdb_path, sequence): return self.t[pdb_path]
poses = [D + '/structures/3DMV_m1.pdb', D + '/structures/2LCB_m1.pdb']
tcfg = ThermoMPNNConfig(enabled=True, repo_dir='/workspace/ThermoMPNN', python_executable='/workspace/ThermoMPNN/.venv/bin/python', chain='A', pdb_paths=poses)
cache = Cached(); wrap = ThermoMPNNWrapper(tcfg)
import pickle
PK = D + '/ssm_cache.pkl'
if os.path.exists(PK):
    cache.t = pickle.load(open(PK, 'rb'))
else:
    for p in poses:
        t0 = time.time(); cache.t[p] = wrap.predict(p, L99A); print('SSM %s %.0fs' % (os.path.basename(p), time.time() - t0), flush=True)
    pickle.dump(cache.t, open(PK, 'wb'))
for key, nm in (((112, 'A'), 'G113A'), ((118, 'P'), 'R119P')):
    print('POSE_DDG %s: ground(3DMV)=%.2f excited(2LCB)=%.2f' % (nm, cache.t[poses[0]].ddg[key], cache.t[poses[1]].ddg[key]), flush=True)
orig_build = es_mod.build_stability_filter
es_mod.build_stability_filter = lambda c_, ref, out, orig=orig_build: orig(c_, ref, out, backend=cache)

def muts(seq): return [(i + 1, L99A[i], seq[i]) for i in range(len(L99A)) if seq[i] != L99A[i]]
allres = {}
for seed in args.seeds:
    for arm in args.arms:
        if args.deadline and time.time() > args.deadline:
            print('DEADLINE reached, stopping before seed=%d arm=%s' % (seed, arm), flush=True); break
        oc = OptimizationConfig(); oc.original_sequence = L99A; oc.healthy_sequence = TRIPLE
        oc.mutation.strategy = 'random'; oc.mutation.allowed_positions = list(range(94, 125))   # residues 95-125
        oc.ga.population_size = args.pop; oc.ga.max_generations = args.gens; oc.ga.seed = seed
        oc.logging.output_dir = '%s/%s_out/%s_seed%d' % (D, args.tag, arm, seed)
        paths = [poses[1]] if arm.startswith('es') else poses   # 'esX' = target-state (excited) pose only; 'onX' = worst case over both poses
        oc.thermompnn = ThermoMPNNConfig(enabled=(arm != 'off'), pdb_paths=paths, ddg_cutoff=(float(arm[2:]) if arm != 'off' else 2.0), repo_dir='/workspace/ThermoMPNN')
        t0 = time.time(); STATS.clear()
        search = BudgetedEvolutionarySearch(oc, bioemu_backend=StateLLRBackend(oc.bioemu)); r = search.run()
        ranked = r.ranked(20)
        best = r.best_sequence
        rec = {'arm': arm, 'seed': seed, 'wall_s': time.time() - t0, 'reference_llr': r.reference_llr, 'target_llr': r.target_parameter,
               'best_llr': r.best_llr, 'gap_closed': (r.best_llr - r.reference_llr) / (r.target_parameter - r.reference_llr) if r.target_parameter != r.reference_llr else None,
               'closer_than_reference': bool(abs(r.best_llr - r.target_parameter) < abs(r.reference_llr - r.target_parameter)),
               'total_evaluated': r.total_evaluated, 'total_rejected': r.total_rejected, 'best_mutations_vs_L99A': muts(best),
               'best_ES_frac': (STATS[best][0] / max(1, STATS[best][0] + STATS[best][1])) if best in STATS else None,
               'top20_has_G113A': any(s[112] == 'A' for s, _ in ranked), 'top20_has_R119P': any(s[118] == 'P' for s, _ in ranked),
               'best_has_G113A': best[112] == 'A', 'best_has_R119P': best[118] == 'P',
               'top20': [(s, l, muts(s)) for s, l in ranked]}
        allres['%s_seed%d' % (arm, seed)] = rec
        json.dump(allres, open('%s/%s_results.json' % (D, args.tag), 'w'), indent=1)
        print('RUN arm=%s seed=%d wall=%.0fs ref=%.2f target=%.2f best=%.2f gap=%.2f evaluated=%d rejected=%d best_muts=%s' % (arm, seed, rec['wall_s'], rec['reference_llr'], rec['target_llr'], rec['best_llr'], rec['gap_closed'] or 0, rec['total_evaluated'], rec['total_rejected'], rec['best_mutations_vs_L99A']), flush=True)
print('DONE', flush=True)
