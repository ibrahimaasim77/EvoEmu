
import json, sys
sys.path.insert(0, '/workspace/t4l_validation')
from bioemu.get_embeds import _get_a3m_string
D = '/workspace/t4l_validation'
seq = json.load(open(D + '/sequences.json'))['L99A_ground']
a3m = _get_a3m_string(seq, None, None)
open(D + '/msa_L99A.a3m', 'w').write(a3m)
n = sum(1 for l in a3m.split('\n') if l.startswith('>'))
print('MSA rows', n, 'query len', len(a3m.split('\n')[1]), flush=True)
