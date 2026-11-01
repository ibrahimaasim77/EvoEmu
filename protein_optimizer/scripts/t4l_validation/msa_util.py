
import os, hashlib
D = '/workspace/t4l_validation'
def base_a3m():
    return open(D + '/msa_L99A.a3m').read()
def a3m_for(seq):
    """Fixed MSA (fetched once for L99A) with the query row replaced by seq -> no per-candidate server calls."""
    os.makedirs(D + '/a3m', exist_ok=True)
    path = '%s/a3m/%s.a3m' % (D, hashlib.sha1(seq.encode()).hexdigest()[:16])
    if not os.path.exists(path):
        lines = base_a3m().split('\n')
        qi = next(i for i, l in enumerate(lines) if l and not l.startswith('>'))
        assert len(lines[qi]) == len(seq), (len(lines[qi]), len(seq))
        lines[qi] = seq
        open(path, 'w').write('\n'.join(lines))
    return path
