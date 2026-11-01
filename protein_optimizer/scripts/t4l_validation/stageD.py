
"""Stage D diagnostic: is the missing excited state a BioEmu property or an artifact of the fixed-MSA setup?
usage: python stageD.py MSA(fixed|server) MODEL N TAG"""
import sys, os, json, glob, time
import numpy as np
sys.path.insert(0, '/workspace/t4l_validation')
from msa_util import a3m_for
MSA, MODEL, N, TAG = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
D = '/workspace/t4l_validation'; NRES = 162
seqs = json.load(open(D + '/sequences.json')); L99A = seqs['L99A_ground']
full = {'L99A': L99A, 'triple': seqs['triple_excited']}
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
sep = rmsd(es_c, ground, region) * 10
from bioemu.sample import main
out_all = {}
for tag, seq in full.items():
    out = '%s/bioemuD_%s_%s_%s_n%d' % (D, TAG, tag, MODEL, N)
    if not glob.glob(out + '/batch_*.npz'):
        t = time.time()
        kw = dict(sequence=(a3m_for(seq) if MSA == 'fixed' else seq), num_samples=N, output_dir=out, base_seed=0, filter_samples=False, batch_size_100=40, model_name=MODEL)
        main(**kw); print('GEN %s %s %s %.0fs' % (TAG, tag, MODEL, time.time() - t), flush=True)
    pos = np.concatenate([np.load(f)['pos'] for f in sorted(glob.glob(out + '/batch_*.npz'))])[:, :NRES]
    cc = np.linalg.norm(np.diff(pos, axis=1), axis=2); ok = ((cc > 0.33) & (cc < 0.43)).all(axis=1)
    g, e = [], []
    for P in pos[ok]:
        Pf = fit(P, ground, core); g.append(rmsd(Pf, ground, region) * 10); e.append(rmsd(Pf, es_c, region) * 10)
    g, e = np.array(g), np.array(e)
    r = {'n': int(ok.sum()), 'frac_ES_like': float((e < g).mean()), 'frac_e_lt_3A': float((e < 3.0).mean()), 'min_e_A': float(e.min()),
         'p05_e_A': float(np.percentile(e, 5)), 'median_e_A': float(np.median(e)), 'median_g_A': float(np.median(g)),
         'p95_g_A': float(np.percentile(g, 95)), 'separation_A': sep}
    out_all[tag] = r; print('RESULT %s %s %s %s' % (TAG, MODEL, tag, json.dumps(r)), flush=True)
json.dump(out_all, open('%s/stageD_%s_results.json' % (D, TAG), 'w'), indent=1)
print('DONE', flush=True)
