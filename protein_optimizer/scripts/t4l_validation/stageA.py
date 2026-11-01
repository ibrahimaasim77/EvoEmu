
"""Stage A: ThermoMPNN vs experimental T4 lysozyme ddG, and guard-cutoff calibration."""
import sys, csv, json, time
import numpy as np
sys.path.insert(0, '/workspace/thermompnn_module_test/EvoEmu/protein_optimizer')
from protein_optimizer.config import ThermoMPNNConfig
from protein_optimizer.thermompnn import ThermoMPNNWrapper

D = '/workspace/t4l_validation'
seqs = json.load(open(D + '/sequences.json'))
wt = seqs['wt_star']                      # 1L63, 162 resolved residues, T4L numbering 1..162
cfg = ThermoMPNNConfig(enabled=True, repo_dir='/workspace/ThermoMPNN',
                       python_executable='/workspace/ThermoMPNN/.venv/bin/python', chain='A')
t0 = time.time()
tab = ThermoMPNNWrapper(cfg).predict(D + '/structures/1L63_m1.pdb', wt)
print('SSM done %.0fs, n=%d' % (time.time() - t0, len(tab.ddg)), flush=True)

rows = list(csv.DictReader(open('/workspace/ThermoMPNN/data_all/testing/fireprot_HF.csv')))
t4 = [r for r in rows if r['uniprot_id'] == 'P00720']
agg, skipped = {}, 0
for r in t4:
    pos, w, m = int(r['position']), r['wild_type'], r['mutation']
    if pos > len(wt) or wt[pos - 1] != w or (pos - 1, m) not in tab.ddg:
        skipped += 1; continue
    agg.setdefault((pos, m), []).append(float(r['ddG']))
keys = sorted(agg)
exp = np.array([np.mean(agg[k]) for k in keys])
pred = np.array([tab.ddg[(k[0] - 1, k[1])] for k in keys])
print('T4L rows=%d usable_unique=%d skipped=%d' % (len(t4), len(keys), skipped), flush=True)

def ranks(x):
    o = np.argsort(x, kind='mergesort'); r = np.empty(len(x)); r[o] = np.arange(len(x))
    for v in np.unique(x):
        idx = np.where(x == v)[0]; r[idx] = r[idx].mean()
    return r
def auc(score, label):
    r = ranks(score); n1 = label.sum(); n0 = len(label) - n1
    return float((r[label == 1].sum() - n1 * (n1 - 1) / 2) / (n1 * n0))
res = {'n': len(keys),
       'pearson': float(np.corrcoef(exp, pred)[0, 1]),
       'spearman': float(np.corrcoef(ranks(exp), ranks(pred))[0, 1]),
       'rmse': float(np.sqrt(((exp - pred) ** 2).mean())),
       'auc_exp_ge_1': auc(pred, (exp >= 1).astype(int)),
       'auc_exp_ge_2': auc(pred, (exp >= 2).astype(int)),
       'frac_exp_ge_2': float((exp >= 2).mean()), 'frac_exp_lt_1': float((exp < 1).mean())}
cal = []
for c in (0.5, 1.0, 1.5, 2.0, 3.0):
    blocked = pred > c
    cal.append({'cutoff': c,
                'block_rate_measured': float(blocked.mean()),
                'recall_exp_ge_2': float(blocked[exp >= 2].mean()),
                'false_block_exp_lt_1': float(blocked[exp < 1].mean()),
                'false_block_exp_lt_0': float(blocked[exp < 0].mean()) if (exp < 0).any() else None,
                'precision': float((exp[blocked] >= 1).mean()) if blocked.any() else None})
res['calibration'] = cal
# whole-SSM block rates (all 19 substitutions x 162 positions) for context
allv = np.array(list(tab.ddg.values()))
res['ssm_block_rate'] = {str(c): float((allv > c).mean()) for c in (0.5, 1.0, 1.5, 2.0, 3.0)}
json.dump(res, open(D + '/stageA_results.json', 'w'), indent=1)
with open(D + '/stageA_predictions.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['position', 'wt', 'mut', 'exp_ddG', 'pred_ddG'])
    for k, e, p in zip(keys, exp, pred): w.writerow([k[0], wt[k[0] - 1], k[1], '%.3f' % e, '%.3f' % p])
print(json.dumps(res, indent=1), flush=True)
print('DONE', flush=True)
