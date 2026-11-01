
"""Stage B: does BioEmu populate the known ground vs excited states of T4 lysozyme?
usage: python stageB.py N_SAMPLES SEED [SEED ...]"""
import sys, os, json, glob, time
import numpy as np
sys.path.insert(0, '/workspace/t4l_validation')
from msa_util import a3m_for
D = '/workspace/t4l_validation'
N = int(sys.argv[1]); SEEDS = [int(s) for s in sys.argv[2:]] or [0]
seqs = json.load(open(D + '/sequences.json'))
L99A = seqs['L99A_ground']
full = {'wt_star': L99A[:98] + 'L' + L99A[99:], 'L99A': L99A, 'triple': seqs['triple_excited']}
assert len(set(len(v) for v in full.values())) == 1
NRES = 162   # residues resolved in every reference structure

def read_models(pid):
    models, cur = [], None
    for l in open('%s/structures/%s.pdb' % (D, pid)):
        if l.startswith('MODEL'): cur = []
        elif l.startswith('ENDMDL'):
            models.append(np.array(cur)); cur = None
        elif l.startswith('ATOM') and l[21] == 'A' and l[12:16].strip() == 'CA' and l[16] in ' A':
            if cur is None and not models: cur = []   # single-model file
            if cur is not None: cur.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
    if cur: models.append(np.array(cur))
    return [m[:NRES] / 10.0 for m in models]   # nm

def kabsch(P, Q):
    Pc, Qc = P.mean(0), Q.mean(0)
    U, S, Vt = np.linalg.svd((P - Pc).T @ (Q - Qc)); d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return R, Pc, Qc
def fit(P, Q, idx):   # transform P onto Q using residues idx
    R, Pc, Qc = kabsch(P[idx], Q[idx]); return (P - Pc) @ R + Qc
def rmsd(P, Q, idx): return float(np.sqrt(((P[idx] - Q[idx]) ** 2).sum(1).mean()))

ground = read_models('3DMV')[0]
es_models = read_models('2LCB'); es = es_models[0]
allidx = np.arange(NRES)
es_on_g = fit(es, ground, allidx)
disp = np.sqrt(((es_on_g - ground) ** 2).sum(1))
region = np.where(disp > disp.mean() + disp.std())[0]
core = np.setdiff1d(allidx, region)
es_c = fit(es, ground, core)
sep = rmsd(es_c, ground, region)
print('REGION n=%d residues (1-based) %s ... %s | core n=%d | ground-vs-ES region RMSD after core fit = %.2f A' % (len(region), region[:3] + 1, region[-3:] + 1, len(core), sep * 10), flush=True)

def classify(frames):
    g, e = [], []
    for P in frames:
        Pf = fit(P, ground, core)
        g.append(rmsd(Pf, ground, region)); e.append(rmsd(Pf, es_c, region))
    g, e = np.array(g), np.array(e)
    return g, e

def summarize(g, e):
    return {'n': int(len(g)), 'frac_ES_like': float((e < g).mean()), 'mean_rmsd_to_ground_A': float(g.mean() * 10),
            'mean_rmsd_to_ES_A': float(e.mean() * 10), 'frac_within_half_sep_of_ES': float((e < 0.5 * sep).mean()),
            'frac_within_half_sep_of_ground': float((g < 0.5 * sep).mean())}

results = {'region_residues_1based': [int(i) + 1 for i in region], 'separation_A': sep * 10, 'controls': {}, 'runs': {}}
# controls: experimental structures must classify correctly
for name, pid in (('X-ray ground 3DMV', '3DMV'), ('X-ray WT* 1L63', '1L63'), ('NMR ES L99A 2LCB (all models)', '2LCB'), ('NMR ES triple 2LC9 (all models)', '2LC9')):
    ms = read_models(pid); g, e = classify(ms)
    results['controls'][name] = summarize(g, e)
    print('CONTROL %-34s %s' % (name, json.dumps(results['controls'][name])), flush=True)

def gen(tag, seq, seed):
    out = '%s/bioemu_%s_seed%d_n%d' % (D, tag, seed, N)
    if not glob.glob(out + '/batch_*.npz'):
        from bioemu.sample import main
        t = time.time()
        main(sequence=a3m_for(seq), num_samples=N, output_dir=out, base_seed=seed, filter_samples=False, batch_size_100=40)
        print('GEN %s seed=%d n=%d %.0fs' % (tag, seed, N, time.time() - t), flush=True)
    return np.concatenate([np.load(f)['pos'] for f in sorted(glob.glob(out + '/batch_*.npz'))])

for seed in SEEDS:
    for tag, seq in full.items():
        pos = gen(tag, seq, seed)[:, :NRES, :]
        cc = np.linalg.norm(np.diff(pos, axis=1), axis=2)
        ok = ((cc > 0.33) & (cc < 0.43)).all(axis=1)
        g, e = classify(pos[ok])
        s = summarize(g, e); s['frac_physical'] = float(ok.mean())
        results['runs']['%s_seed%d' % (tag, seed)] = s
        print('RUN %-8s seed=%d %s' % (tag, seed, json.dumps(s)), flush=True)
        json.dump(results, open(D + '/stageB_results.json', 'w'), indent=1)
agg = {}
for tag in full:
    f = [results['runs']['%s_seed%d' % (tag, s)]['frac_ES_like'] for s in SEEDS]
    agg[tag] = {'mean_frac_ES_like': float(np.mean(f)), 'sd': float(np.std(f)), 'per_seed': f}
results['aggregate'] = agg
json.dump(results, open(D + '/stageB_results.json', 'w'), indent=1)
print('AGG', json.dumps(agg), flush=True)
print('DONE', flush=True)
