# KaiB-RS reference structures

Reference models for the KaiB benchmark (KaiB from Rhodobacter sphaeroides, 90-residue native sequence).

## Source
- Paper: Wayment-Steele et al., "The conformational landscape of fold-switcher KaiB is tuned to the circadian
  rhythm timescale", PNAS 2024.
- Data: Zenodo record https://doi.org/10.5281/zenodo.11448117, file `conf_landscape_kaibrs_data.zip`
  (md5 920d917f04237705366df4a59ddb9696). The zip is NOT included here; download it from Zenodo.
  Check the Zenodo record for its license before redistributing anything else from it.
- These three files come from `Zenodo/05_AF_models_CS_predictions/models_used_from_afcluster_norelax/` in that zip,
  unmodified.

## Files in structures/
| File | State (as named in the Zenodo record) |
|---|---|
| KAIBRS_114_1_TE_like_Ground.pdb | Ground (TE-like) |
| KAIBRS_061_1_FS_state.pdb | FS (fold-switched) |
| KAIBRS_128_1_putative_enigma_Ground.pdb | putative Enigma (register-shifted) |

## Numbering
Each model has 92 residues: a 2-residue "GA" tag followed by the 90-residue native sequence
(BMRB entry 52018). Native residue n is model residue n + 2.

Native sequence (90 residues):
MGRRLVLYVAGQTPKSLAAISNLRRICEENLPGQYEVEVIDLKQNPRLAKEHSIVAIPTLVRELPVPIRKIIGDLSDKEQVLVNLKMDME

## Measured populations at 20 C (paper, Supplementary Data 1)
Ground 75.3%, FS 16%, Enigma 6.2%, PD (partially disordered) 2.5%.
dG relative to Ground, kcal/mol: FS +0.90, Enigma +1.45, PD +1.97.
