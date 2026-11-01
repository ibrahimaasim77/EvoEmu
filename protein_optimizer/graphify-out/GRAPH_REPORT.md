# Graph Report - protein_optimizer  (2026-11-01)

## Corpus Check
- 31 files · ~39,557 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 597 nodes · 1274 edges · 34 communities (21 shown, 13 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 236 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `32883666`
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
- [[_COMMUNITY_CrossoverOperator|CrossoverOperator]]
- [[_COMMUNITY_test_dyna1.py|test_dyna1.py]]
- [[_COMMUNITY_practice.sh|practice.sh]]
- [[_COMMUNITY_setup_vm.sh|setup_vm.sh]]
- [[_COMMUNITY_protein-optimizer|protein-optimizer]]
- [[_COMMUNITY_Dyna1GuidedMutator|Dyna1GuidedMutator]]
- [[_COMMUNITY_test_ga.py|test_ga.py]]
- [[_COMMUNITY_dyna1_worker.py|dyna1_worker.py]]
- [[_COMMUNITY_stub_dyna1_worker.py|stub_dyna1_worker.py]]

## God Nodes (most connected - your core abstractions)
1. `BioEmuOutput` - 46 edges
2. `ProteinOptimizationPipeline` - 42 edges
3. `MutationConfig` - 36 edges
4. `Dyna1MutationProposer` - 36 edges
5. `CrossoverOperator` - 35 edges
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

## Communities (34 total, 13 thin omitted)

### Community 0 - "server.py"
Cohesion: 0.07
Nodes (20): BaseModel, BudgetedEvolutionarySearch, Higher = better in both modes. Maximise mode: the LLR itself.         Target mod, Execute the full search. Returns EvolutionarySearchResult., Extract a single LLR scalar from a BioEmuOutput.          Priority:           1., Generate `n` candidates via random amino acid substitutions (no model needed)., Generate `n` mutation candidates via Dyna-1.          For each slot, picks a ran, Maximise mode: best LLR beats the reference.         Target mode: best LLR is cl (+12 more)

### Community 1 - "Any"
Cohesion: 0.14
Nodes (15): Dyna1Config, Unified configuration for the protein optimization framework.  All modules are d, Controls Dyna-1 mutation proposal (saturation scan; see dyna1.py)., Dyna1MutationProposer, Dyna-1 Mutation Proposal Module  Uses Dyna-1 (WaymentSteeleLab/Dyna-1, ESM-3 var, Shut the worker down (also registered with atexit)., Suggests substitutions by saturation-scanning with Dyna-1.      Example::, Evolutionary Search Pipeline  Implements the team's target algorithm:    1. Scor (+7 more)

### Community 2 - "_connect"
Cohesion: 0.06
Nodes (30): FitnessCallable, GAConfig, Genetic algorithm hyper-parameters., ConvergenceTracker, GenerationResult, GeneticAlgorithm, Random, Deterministic top-k selection. Useful for greedy benchmarking.     Repeats top s (+22 more)

### Community 3 - "run_store.py"
Cohesion: 0.05
Nodes (37): 1. Set up the VM (one time), 2. Activate the environment (every new terminal), 3. Run it, 4. Practice sequences, 5. How long it takes, 6. Output — what you get and where, 7. Download files to your laptop, Add a custom scoring component (+29 more)

### Community 4 - "RunRequest"
Cohesion: 0.20
Nodes (8): EvolutionarySearchResult, Final result returned by BudgetedEvolutionarySearch.run()., Higher = better in both modes. Maximise mode: the LLR itself.         Target mod, CommonAncestorCrossover, Crossover operator based on consensus positions across an elite pool.      Algor, Return {position: amino_acid} for every position where all sequences agree., Generate `n_offspring` sequences by fixing consensus positions and         recom, Number of positions that are NOT conserved across the sequences.

### Community 5 - "fold_sequence"
Cohesion: 0.11
Nodes (29): _add_title_overlay(), assign_to_states(), _axis_limits(), compute_ss_mdtraj(), coords_to_fingerprint(), frame_rmsd_to_ref(), load_ca_trajectory(), main() (+21 more)

### Community 6 - "Queue"
Cohesion: 0.06
Nodes (25): LoggingConfig, Controls logging, checkpointing, and result export., GenerationSummary, MutationRecord, OptimizationTracker, Logging and Analysis Module  Responsibilities:   - Attach to GA as a callback to, Collects GA progress data and exports to disk.      Attach to a GeneticAlgorithm, Called by GeneticAlgorithm after each generation is evaluated. (+17 more)

### Community 7 - "saved_trajectory"
Cohesion: 0.06
Nodes (31): apply_overrides(), format_mutations(), main(), parse_args(), Protein Optimization — Entry Point  Default usage (runs evolutionary search with, Return the point mutations of `variant` vs. `original` as e.g. 'L5I, Q34K'., Namespace, OptimizationConfig (+23 more)

### Community 8 - "protein_optimizer (EvoEmu)"
Cohesion: 0.14
Nodes (21): assign_to_states(), _axis_limits(), coords_to_fingerprint(), load_ca_coords(), main(), Upper-triangle of the Cα pairwise distance matrix, flattened to 1-D.      This i, Greedy max-coverage prototype selection.      Picks the first prototype as index, Assign each sample to its nearest prototype and return the distances.      Retur (+13 more)

### Community 9 - "MutationConfig"
Cohesion: 0.17
Nodes (12): MutationConfig, Controls how sequences are mutated during evolution., build_mutator(), RandomMutator, Construct the appropriate mutator given the strategy in config.      Pass dyna1_, Baseline mutator: choose a random position, substitute a random AA.      Number, test_errors_propagate_instead_of_silent_random_fallback(), crossover_op() (+4 more)

### Community 10 - "bioemu_gif_maker.py"
Cohesion: 0.29
Nodes (11): Connection, _connect(), create_run(), fail_run(), finalize_run(), get_run(), get_run_rounds(), init_db() (+3 more)

### Community 11 - "OptimizationConfig"
Cohesion: 0.09
Nodes (23): ABC, BioEmuConfig, Controls BioEmu structural inference., BaseStructuralBackend, BioEmuWrapper, ConformationSample, MockBioEmuBackend, BioEmu Interface Module  Abstracts all structural inference behind a single cont (+15 more)

### Community 12 - "ConformationalLandscapeScorer"
Cohesion: 0.05
Nodes (44): Weights for the composite fitness function., ScoringConfig, protein_optimizer — Evolutionary protein sequence optimization framework.  Publi, OptimizationResult, Returned by ProteinOptimizationPipeline.run()., _clamp01(), CompactnessScorer, ComponentScorer (+36 more)

### Community 15 - "WildtypeProximityScorer"
Cohesion: 0.22
Nodes (5): Measures how close a sequence is to a known wildtype target.      Uses normalise, Number of positions that differ between two equal-length sequences., Fraction of identical positions. Clamped to shortest length., WildtypeProximityScorer, TestWildtypeProximityScorer

### Community 20 - "test_ga.py"
Cohesion: 0.13
Nodes (9): MutationCandidate, ndarray, Collapse a per-residue p_exchange vector to one scalar., Deterministic pseudo-random per-residue p_exchange (no model needed)., Scalar dynamics score (reduced mean p_exchange) for each sequence., Propose top-k substitutions for each target position (0-based).          Returns, Convenience wrapper for a single position., Return the single best substitution at a position. (+1 more)

### Community 25 - "CrossoverOperator"
Cohesion: 0.17
Nodes (5): CrossoverOperator, Recombines two parent sequences to produce two offspring.      Supported strateg, Return two offspring. If crossover rate not triggered, return clones., Pair up parents sequentially, apply crossover, flatten results.         If popul, TestCrossoverOperator

### Community 26 - "test_dyna1.py"
Cohesion: 0.29
Nodes (11): _fake_repo(), _proposer(), Dyna-1 proposer tests (mock mode — no model or weights required)., test_all_positions_scored_in_one_call_and_cached(), test_candidates_exclude_original_and_respect_top_k(), test_deterministic(), test_missing_worker_env_gives_actionable_error(), test_ranked_best_first_and_direction_flips_order() (+3 more)

### Community 30 - "Dyna1GuidedMutator"
Cohesion: 0.40
Nodes (3): Dyna1GuidedMutator, Random, Mutation operator that uses Dyna-1 saturation-scan scores to bias substitutions

### Community 31 - "test_ga.py"
Cohesion: 0.40
Nodes (3): crossover(), mutator(), Tests for GeneticAlgorithm and the full pipeline (mock mode).

### Community 32 - "dyna1_worker.py"
Cohesion: 0.67
Nodes (3): main(), Dyna-1 inference worker.  Runs inside Dyna-1's own virtualenv (its pinned numpy<, _send()

## Knowledge Gaps
- **36 isolated node(s):** `practice.sh script`, `protein-optimizer`, `setup_vm.sh script`, `graphify`, `Table of Contents` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BioEmuOutput` connect `ConformationalLandscapeScorer` to `server.py`, `Any`, `RunRequest`, `Queue`, `saved_trajectory`, `OptimizationConfig`, `WildtypeProximityScorer`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `Dyna1MutationProposer` connect `Any` to `server.py`, `_connect`, `RunRequest`, `saved_trajectory`, `MutationConfig`, `ConformationalLandscapeScorer`, `test_ga.py`, `CrossoverOperator`, `test_dyna1.py`, `Dyna1GuidedMutator`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `ProteinOptimizationPipeline` connect `saved_trajectory` to `Any`, `_connect`, `Queue`, `OptimizationConfig`, `ConformationalLandscapeScorer`, `WildtypeProximityScorer`, `CrossoverOperator`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `BioEmuOutput` (e.g. with `BudgetedEvolutionarySearch` and `EvolutionarySearchResult`) actually correct?**
  _`BioEmuOutput` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `ProteinOptimizationPipeline` (e.g. with `OptimizationConfig` and `Dyna1MutationProposer`) actually correct?**
  _`ProteinOptimizationPipeline` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `MutationConfig` (e.g. with `._from_dict()` and `BaseMutator`) actually correct?**
  _`MutationConfig` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Dyna1MutationProposer` (e.g. with `Dyna1Config` and `BudgetedEvolutionarySearch`) actually correct?**
  _`Dyna1MutationProposer` has 10 INFERRED edges - model-reasoned connections that need verification._