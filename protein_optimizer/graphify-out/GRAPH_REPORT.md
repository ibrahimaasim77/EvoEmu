# Graph Report - protein_optimizer  (2026-10-31)

## Corpus Check
- 28 files · ~38,599 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 581 nodes · 1246 edges · 28 communities (16 shown, 12 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 236 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d63d094`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_server.py|server.py]]
- [[_COMMUNITY_Any|Any]]
- [[_COMMUNITY__connect|_connect]]
- [[_COMMUNITY_run_store.py|run_store.py]]
- [[_COMMUNITY_RunRequest|RunRequest]]
- [[_COMMUNITY_fold_sequence|fold_sequence]]
- [[_COMMUNITY_Queue|Queue]]
- [[_COMMUNITY_saved_trajectory|saved_trajectory]]
- [[_COMMUNITY_protein_optimizer (EvoEmu)|protein_optimizer (EvoEmu)]]
- [[_COMMUNITY_MutationConfig|MutationConfig]]
- [[_COMMUNITY_bioemu_gif_maker.py|bioemu_gif_maker.py]]
- [[_COMMUNITY_OptimizationConfig|OptimizationConfig]]
- [[_COMMUNITY_ConformationalLandscapeScorer|ConformationalLandscapeScorer]]
- [[_COMMUNITY_ScoringFunction|ScoringFunction]]
- [[_COMMUNITY_ESM2MutationProposer|ESM2MutationProposer]]
- [[_COMMUNITY_WildtypeProximityScorer|WildtypeProximityScorer]]
- [[_COMMUNITY_ConformationSample|ConformationSample]]
- [[_COMMUNITY_MockBioEmuBackend|MockBioEmuBackend]]
- [[_COMMUNITY_BaseMutator|BaseMutator]]
- [[_COMMUNITY_evolutionary_search.py|evolutionary_search.py]]
- [[_COMMUNITY_test_ga.py|test_ga.py]]
- [[_COMMUNITY_RandomMutator|RandomMutator]]
- [[_COMMUNITY_ComponentScorer|ComponentScorer]]
- [[_COMMUNITY_._aggregate|._aggregate]]
- [[_COMMUNITY_practice.sh|practice.sh]]
- [[_COMMUNITY_setup_vm.sh|setup_vm.sh]]
- [[_COMMUNITY_protein-optimizer|protein-optimizer]]

## God Nodes (most connected - your core abstractions)
1. `BioEmuOutput` - 46 edges
2. `ProteinOptimizationPipeline` - 42 edges
3. `MutationConfig` - 36 edges
4. `CrossoverOperator` - 35 edges
5. `Dyna1MutationProposer` - 31 edges
6. `OptimizationConfig` - 30 edges
7. `GAConfig` - 27 edges
8. `ScoringFunction` - 27 edges
9. `StageReporter` - 26 edges
10. `GenerationResult` - 25 edges

## Surprising Connections (you probably didn't know these)
- `TestWildtypePipeline` --uses--> `StageReporter`  [INFERRED]
  tests/test_wildtype.py → protein_optimizer/analysis.py
- `TestWildtypeProximityScorer` --uses--> `StageReporter`  [INFERRED]
  tests/test_wildtype.py → protein_optimizer/analysis.py
- `TestConformationalLandscapeScorer` --uses--> `ConformationSample`  [INFERRED]
  tests/test_scoring.py → protein_optimizer/bioemu.py
- `TestIndividualScorers` --uses--> `ConformationSample`  [INFERRED]
  tests/test_scoring.py → protein_optimizer/bioemu.py
- `TestScoringFunction` --uses--> `ConformationSample`  [INFERRED]
  tests/test_scoring.py → protein_optimizer/bioemu.py

## Import Cycles
- None detected.

## Communities (28 total, 12 thin omitted)

### Community 0 - "server.py"
Cohesion: 0.13
Nodes (11): BaseModel, Queue, Request, fold_sequence(), _queue_get(), Protein Optimizer — Web Server  Usage:     pip install fastapi uvicorn     pytho, Proxy ESMFold structure prediction through the ESM Atlas public API., Serve a pre-converted multi-frame PDB of a saved BioEmu run (real .xtc     ensem (+3 more)

### Community 1 - "Any"
Cohesion: 0.11
Nodes (8): LoggingConfig, Controls logging, checkpointing, and result export., OptimizationTracker, Collects GA progress data and exports to disk.      Attach to a GeneticAlgorithm, Called by GeneticAlgorithm after each generation is evaluated., Write final results to disk.          Returns:             dict mapping format n, Best-score per generation (useful for plotting)., Return a human-readable one-page report string.

### Community 2 - "_connect"
Cohesion: 0.06
Nodes (36): FitnessCallable, GAConfig, Genetic algorithm hyper-parameters., ConvergenceTracker, GenerationResult, GeneticAlgorithm, Random, Genetic Algorithm Module  A clean, biology-agnostic GA engine. It operates entir (+28 more)

### Community 3 - "run_store.py"
Cohesion: 0.05
Nodes (37): 1. Set up the VM (one time), 2. Activate the environment (every new terminal), 3. Run it, 4. Practice sequences, 5. How long it takes, 6. Output — what you get and where, 7. Download files to your laptop, Add a custom scoring component (+29 more)

### Community 4 - "RunRequest"
Cohesion: 0.05
Nodes (34): apply_overrides(), format_mutations(), main(), parse_args(), Protein Optimization — Entry Point  Default usage (runs evolutionary search with, Return the point mutations of `variant` vs. `original` as e.g. 'L5I, Q34K'., Namespace, BudgetedEvolutionarySearch (+26 more)

### Community 5 - "fold_sequence"
Cohesion: 0.11
Nodes (29): _add_title_overlay(), assign_to_states(), _axis_limits(), compute_ss_mdtraj(), coords_to_fingerprint(), frame_rmsd_to_ref(), load_ca_trajectory(), main() (+21 more)

### Community 6 - "Queue"
Cohesion: 0.12
Nodes (11): Divides a GA run into N equal stages and reports how "warm" (close to     wildty, Return the last generation (inclusive) for each stage.         e.g. max_gen=100,, GA callback — called after each generation is evaluated., Full multi-stage summary as a printable string., Write stage snapshots to JSON., Return (label, icon_bar) for a given sequence identity value., StageReporter, warmth_label() (+3 more)

### Community 7 - "saved_trajectory"
Cohesion: 0.11
Nodes (16): OptimizationConfig, Any, Path, Root configuration object.      Usage::          cfg = OptimizationConfig.from_y, Load from a YAML file. Missing keys fall back to dataclass defaults., Serialize to a plain dict (useful for logging)., ProteinOptimizationPipeline, Execute the full optimization. Returns OptimizationResult.          Steps: (+8 more)

### Community 8 - "protein_optimizer (EvoEmu)"
Cohesion: 0.14
Nodes (21): assign_to_states(), _axis_limits(), coords_to_fingerprint(), load_ca_coords(), main(), Upper-triangle of the Cα pairwise distance matrix, flattened to 1-D.      This i, Greedy max-coverage prototype selection.      Picks the first prototype as index, Assign each sample to its nearest prototype and return the distances.      Retur (+13 more)

### Community 9 - "MutationConfig"
Cohesion: 0.09
Nodes (20): MutationConfig, Controls how sequences are mutated during evolution., build_mutator(), CrossoverOperator, Random, RandomMutator, Mutation and Crossover Module  Provides:   - BaseMutator: abstract contract for, Recombines two parent sequences to produce two offspring.      Supported strateg (+12 more)

### Community 10 - "bioemu_gif_maker.py"
Cohesion: 0.29
Nodes (11): Connection, _connect(), create_run(), fail_run(), finalize_run(), get_run(), get_run_rounds(), init_db() (+3 more)

### Community 11 - "OptimizationConfig"
Cohesion: 0.07
Nodes (30): ABC, BioEmuConfig, Controls BioEmu structural inference., OptimizationResult, Orchestration Layer — ProteinOptimizationPipeline  The single entry point that w, Returned by ProteinOptimizationPipeline.run()., BaseStructuralBackend, BioEmuWrapper (+22 more)

### Community 12 - "ConformationalLandscapeScorer"
Cohesion: 0.05
Nodes (43): Weights for the composite fitness function., ScoringConfig, protein_optimizer — Evolutionary protein sequence optimization framework.  Publi, _clamp01(), CompactnessScorer, ComponentScorer, ConformationalLandscapeScorer, ConsistencyScorer (+35 more)

### Community 15 - "WildtypeProximityScorer"
Cohesion: 0.17
Nodes (6): Directly append WildtypeProximityScorer into the scoring function and         re, Measures how close a sequence is to a known wildtype target.      Uses normalise, Number of positions that differ between two equal-length sequences., Fraction of identical positions. Clamped to shortest length., WildtypeProximityScorer, TestWildtypeProximityScorer

### Community 20 - "test_ga.py"
Cohesion: 0.10
Nodes (22): Dyna1Config, Unified configuration for the protein optimization framework.  All modules are d, Controls Dyna-1 mutation proposal (saturation scan; see dyna1.py)., Dyna1MutationProposer, MutationCandidate, ndarray, Dyna-1 Mutation Proposal Module  Uses Dyna-1 (WaymentSteeleLab/Dyna-1, ESM-3 var, Collapse a per-residue p_exchange vector to one scalar. (+14 more)

## Knowledge Gaps
- **36 isolated node(s):** `practice.sh script`, `protein-optimizer`, `setup_vm.sh script`, `graphify`, `Table of Contents` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BioEmuOutput` connect `ConformationalLandscapeScorer` to `RunRequest`, `Queue`, `saved_trajectory`, `OptimizationConfig`, `WildtypeProximityScorer`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `ProteinOptimizationPipeline` connect `saved_trajectory` to `Any`, `_connect`, `Queue`, `MutationConfig`, `OptimizationConfig`, `ConformationalLandscapeScorer`, `WildtypeProximityScorer`, `test_ga.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `Dyna1MutationProposer` connect `test_ga.py` to `_connect`, `RunRequest`, `saved_trajectory`, `MutationConfig`, `OptimizationConfig`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `BioEmuOutput` (e.g. with `BudgetedEvolutionarySearch` and `EvolutionarySearchResult`) actually correct?**
  _`BioEmuOutput` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `ProteinOptimizationPipeline` (e.g. with `OptimizationConfig` and `Dyna1MutationProposer`) actually correct?**
  _`ProteinOptimizationPipeline` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `MutationConfig` (e.g. with `._from_dict()` and `BaseMutator`) actually correct?**
  _`MutationConfig` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `CrossoverOperator` (e.g. with `ConvergenceTracker` and `GenerationResult`) actually correct?**
  _`CrossoverOperator` has 16 INFERRED edges - model-reasoned connections that need verification._