# Graph Report - protein_optimizer  (2026-07-23)

## Corpus Check
- 28 files · ~37,815 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 567 nodes · 1328 edges · 31 communities (23 shown, 8 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 232 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `67a7139e`
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
- [[_COMMUNITY_._from_dict|._from_dict]]
- [[_COMMUNITY_.__init__|.__init__]]
- [[_COMMUNITY_.crossover|.crossover]]
- [[_COMMUNITY_practice.sh|practice.sh]]
- [[_COMMUNITY_setup_vm.sh|setup_vm.sh]]
- [[_COMMUNITY_protein-optimizer|protein-optimizer]]

## God Nodes (most connected - your core abstractions)
1. `BioEmuOutput` - 51 edges
2. `ProteinOptimizationPipeline` - 45 edges
3. `MutationConfig` - 36 edges
4. `CrossoverOperator` - 36 edges
5. `OptimizationConfig` - 33 edges
6. `GAConfig` - 32 edges
7. `ScoringFunction` - 29 edges
8. `GenerationResult` - 28 edges
9. `StageReporter` - 27 edges
10. `ScoringConfig` - 26 edges

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

## Communities (31 total, 8 thin omitted)

### Community 0 - "server.py"
Cohesion: 0.10
Nodes (23): BaseModel, Connection, _connect(), create_run(), fail_run(), finalize_run(), get_run(), get_run_rounds() (+15 more)

### Community 1 - "Any"
Cohesion: 0.06
Nodes (31): GenerationSummary, MutationRecord, OptimizationTracker, Path, Logging and Analysis Module  Responsibilities:   - Attach to GA as a callback to, Collects GA progress data and exports to disk.      Attach to a GeneticAlgorithm, Called by GeneticAlgorithm after each generation is evaluated., Write final results to disk.          Returns:             dict mapping format n (+23 more)

### Community 2 - "_connect"
Cohesion: 0.07
Nodes (20): FitnessCallable, ConvergenceTracker, GeneticAlgorithm, Random, Deterministic top-k selection. Useful for greedy benchmarking.     Repeats top s, Tracks whether the GA has stalled., Call once per generation.         Returns True if the GA has converged (stale_co, Evolutionary optimiser for sequences.      The GA has no knowledge of biology. I (+12 more)

### Community 3 - "run_store.py"
Cohesion: 0.05
Nodes (37): 1. Set up the VM (one time), 2. Activate the environment (every new terminal), 3. Run it, 4. Practice sequences, 5. How long it takes, 6. Output — what you get and where, 7. Download files to your laptop, Add a custom scoring component (+29 more)

### Community 4 - "RunRequest"
Cohesion: 0.08
Nodes (21): apply_overrides(), format_mutations(), main(), parse_args(), Protein Optimization — Entry Point  Default usage (runs evolutionary search with, Return the point mutations of `variant` vs. `original` as e.g. 'L5I, Q34K'., Namespace, Write trajectory files for one BioEmuOutput.      Real BioEmu runs: writes BioEm (+13 more)

### Community 5 - "fold_sequence"
Cohesion: 0.13
Nodes (31): _add_title_overlay(), assign_to_states(), _axis_limits(), compute_ss_mdtraj(), coords_to_fingerprint(), frame_rmsd_to_ref(), load_ca_trajectory(), main() (+23 more)

### Community 6 - "Queue"
Cohesion: 0.15
Nodes (15): BioEmuOutput, Aggregated structural output for one protein sequence.      `samples` holds the, CompactnessScorer, ConsistencyScorer, EnergyScorer, Energy-based stability proxy.      Assumes energy_proxy is negative (lower = mor, Radius of gyration stability proxy.      A compact, consistent fold (low Rg with, Structural stability score from per-residue confidence (pLDDT proxy).      pLDDT (+7 more)

### Community 7 - "saved_trajectory"
Cohesion: 0.16
Nodes (7): ProteinOptimizationPipeline, Execute the full optimization. Returns OptimizationResult.          Steps:, Full evaluation pipeline for one generation's population:           sequences →, Seed population:           - The original sequence is always included (index 0), Orchestrates the full protein sequence optimization run.      Construction build, TestPipelineMock, TestWildtypePipeline

### Community 9 - "MutationConfig"
Cohesion: 0.16
Nodes (10): MutationConfig, Controls how sequences are mutated during evolution., build_mutator(), CrossoverOperator, Recombines two parent sequences to produce two offspring.      Supported strateg, Construct the appropriate mutator given the strategy in config.      Pass esm_pr, crossover_op(), Tests for mutation and crossover operators. (+2 more)

### Community 10 - "bioemu_gif_maker.py"
Cohesion: 0.17
Nodes (23): assign_to_states(), _axis_limits(), coords_to_fingerprint(), load_ca_coords(), main(), ndarray, Path, Upper-triangle of the Cα pairwise distance matrix, flattened to 1-D.      This i (+15 more)

### Community 11 - "OptimizationConfig"
Cohesion: 0.15
Nodes (15): ABC, BaseStructuralBackend, build_bioemu_backend(), BioEmu Interface Module  Abstracts all structural inference behind a single cont, Minimal contract that any structural inference engine must satisfy.      Impleme, Run inference for a single sequence. Return un-aggregated output., Return the appropriate backend based on config.mock., OptimizationConfig (+7 more)

### Community 12 - "ConformationalLandscapeScorer"
Cohesion: 0.15
Nodes (11): _clamp01(), ConformationalLandscapeScorer, _jensen_shannon_divergence(), _pairwise_drmsd(), ndarray, Compare a candidate ensemble against a target conformational landscape.      The, Return the target occupancy distribution, including the outlier bin., Pairwise distance RMSD between rows of two feature matrices. (+3 more)

### Community 13 - "ScoringFunction"
Cohesion: 0.15
Nodes (9): Weights for the composite fitness function., ScoringConfig, Weighted combination of component scorers → single fitness scalar.      Usage::, Score a single BioEmuOutput. Returns fitness in [0, 1]., Score a list of BioEmuOutputs. Returns List[float] in same order., Return both the aggregate fitness and per-component scores.         Useful for a, ScoringFunction, scoring_fn() (+1 more)

### Community 14 - "ESM2MutationProposer"
Cohesion: 0.17
Nodes (11): ESM2Config, Controls ESM-2 mutation proposal behaviour., ESM2MutationProposer, MutationCandidate, ESM-2 Mutation Proposal Module  Wraps Meta's ESM-2 (via HuggingFace) as a biolog, Propose top-k substitutions for each target position.          Args:, Convenience wrapper for a single position., Build one masked sequence per position, batch-tokenise, run forward pass, (+3 more)

### Community 15 - "WildtypeProximityScorer"
Cohesion: 0.17
Nodes (6): Directly append WildtypeProximityScorer into the scoring function and         re, Measures how close a sequence is to a known wildtype target.      Uses normalise, Number of positions that differ between two equal-length sequences., Fraction of identical positions. Clamped to shortest length., WildtypeProximityScorer, TestWildtypeProximityScorer

### Community 16 - "ConformationSample"
Cohesion: 0.20
Nodes (12): BioEmuWrapper, ConformationSample, ndarray, Path, Wraps the real BioEmu model (microsoft/bioemu v1.4+).      Uses bioemu.sample.ma, Load one BioEmu NPZ file and return one ConformationSample per frame.          B, Try common key names for coordinate arrays in BioEmu NPZ files., Parse Cα coordinates from a PDB file using Biopython. (+4 more)

### Community 17 - "MockBioEmuBackend"
Cohesion: 0.20
Nodes (12): MockBioEmuBackend, Deterministic synthetic backend for unit tests and GPU-free development.      Sc, BioEmuConfig, Controls BioEmu structural inference., custom_scorer_demo(), landscape_scorer_demo(), Example usage script — demonstrates the full Python API without going through th, Custom component: penalises sequences with very high average SASA     (over-expo (+4 more)

### Community 18 - "BaseMutator"
Cohesion: 0.17
Nodes (8): BaseMutator, ESMGuidedMutator, Softmax-weighted sampling over MutationCandidate log-probs., Abstract mutation operator.      All mutators take a sequence string and return, Return a mutated copy of *sequence*., Batch mutation. Override for vectorised implementations., Return positions eligible for mutation., Mutation operator that uses ESM-2 log-probabilities to bias substitutions     to

### Community 19 - "evolutionary_search.py"
Cohesion: 0.18
Nodes (9): EvolutionarySearchResult, Evolutionary Search Pipeline  Implements the team's target algorithm:    1. Scor, Final result returned by BudgetedEvolutionarySearch.run()., Higher = better in both modes. Maximise mode: the LLR itself.         Target mod, CommonAncestorCrossover, Crossover operator based on consensus positions across an elite pool.      Algor, Return {position: amino_acid} for every position where all sequences agree., Generate `n_offspring` sequences by fixing consensus positions and         recom (+1 more)

### Community 20 - "test_ga.py"
Cohesion: 0.24
Nodes (6): Unified configuration for the protein optimization framework.  All modules are d, Genetic Algorithm Module  A clean, biology-agnostic GA engine. It operates entir, Mutation and Crossover Module  Provides:   - BaseMutator: abstract contract for, crossover(), mutator(), Tests for GeneticAlgorithm and the full pipeline (mock mode).

### Community 21 - "RandomMutator"
Cohesion: 0.25
Nodes (4): RandomMutator, Baseline mutator: choose a random position, substitute a random AA.      Number, random_mutator(), TestRandomMutator

### Community 22 - "ComponentScorer"
Cohesion: 0.22
Nodes (5): ComponentScorer, A single scoring axis. Returns a float in [0, 1].      Subclass and implement `s, Add a custom component scorer and optionally renormalize all weights         so, Add a preconfigured component scorer instance.          Use this for scorers tha, Compute a score in [0, 1] from a BioEmuOutput. Higher = better.

## Knowledge Gaps
- **36 isolated node(s):** `practice.sh script`, `protein-optimizer`, `setup_vm.sh script`, `graphify`, `Table of Contents` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BioEmuOutput` connect `Queue` to `Any`, `RunRequest`, `saved_trajectory`, `OptimizationConfig`, `ConformationalLandscapeScorer`, `ScoringFunction`, `WildtypeProximityScorer`, `ConformationSample`, `MockBioEmuBackend`, `evolutionary_search.py`, `ComponentScorer`, `._aggregate`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `ProteinOptimizationPipeline` connect `saved_trajectory` to `Any`, `_connect`, `RunRequest`, `MutationConfig`, `OptimizationConfig`, `ScoringFunction`, `ESM2MutationProposer`, `WildtypeProximityScorer`, `MockBioEmuBackend`, `test_ga.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `OptimizationConfig` connect `OptimizationConfig` to `server.py`, `Any`, `_connect`, `RunRequest`, `saved_trajectory`, `WildtypeProximityScorer`, `MockBioEmuBackend`, `evolutionary_search.py`, `test_ga.py`, `._from_dict`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `BioEmuOutput` (e.g. with `BioEmuConfig` and `BudgetedEvolutionarySearch`) actually correct?**
  _`BioEmuOutput` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `ProteinOptimizationPipeline` (e.g. with `OptimizationTracker` and `StageReporter`) actually correct?**
  _`ProteinOptimizationPipeline` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `MutationConfig` (e.g. with `._from_dict()` and `BaseMutator`) actually correct?**
  _`MutationConfig` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `CrossoverOperator` (e.g. with `ConvergenceTracker` and `GenerationResult`) actually correct?**
  _`CrossoverOperator` has 16 INFERRED edges - model-reasoned connections that need verification._