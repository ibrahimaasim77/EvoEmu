# Graph Report - protein_optimizer  (2026-07-02)

## Corpus Check
- Corpus is ~35,854 words - fits in a single context window. You may not need a graph.

## Summary
- 548 nodes · 1297 edges · 32 communities (27 shown, 5 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 237 edges (avg confidence: 0.51)
- Token cost: 124,772 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_GA Analysis & Stage Reporting|GA Analysis & Stage Reporting]]
- [[_COMMUNITY_BioEmu Scoring Aggregation|BioEmu Scoring Aggregation]]
- [[_COMMUNITY_Budgeted Evolutionary Search|Budgeted Evolutionary Search]]
- [[_COMMUNITY_Trajectory GIF Maker|Trajectory GIF Maker]]
- [[_COMMUNITY_BioEmu Backend Abstraction|BioEmu Backend Abstraction]]
- [[_COMMUNITY_Genetic Algorithm Core Types|Genetic Algorithm Core Types]]
- [[_COMMUNITY_CLI Entry Point & BioEmu Wrapper|CLI Entry Point & BioEmu Wrapper]]
- [[_COMMUNITY_EvoEmu Frontend & Fit-to-Target Config|EvoEmu Frontend & Fit-to-Target Config]]
- [[_COMMUNITY_Genetic Algorithm Evolution Loop|Genetic Algorithm Evolution Loop]]
- [[_COMMUNITY_Optimization Pipeline Orchestration|Optimization Pipeline Orchestration]]
- [[_COMMUNITY_Conformational Landscape Scorer|Conformational Landscape Scorer]]
- [[_COMMUNITY_BioEmu GIF Maker|BioEmu GIF Maker]]
- [[_COMMUNITY_Evolutionary Search & Mutation Module|Evolutionary Search & Mutation Module]]
- [[_COMMUNITY_Composite Scoring Function|Composite Scoring Function]]
- [[_COMMUNITY_ESM-2 Mutation Proposer|ESM-2 Mutation Proposer]]
- [[_COMMUNITY_Mutation & Crossover Config|Mutation & Crossover Config]]
- [[_COMMUNITY_Optimization Tracker & Export|Optimization Tracker & Export]]
- [[_COMMUNITY_Mock BioEmu Backend & Examples|Mock BioEmu Backend & Examples]]
- [[_COMMUNITY_Random Mutator & Tests|Random Mutator & Tests]]
- [[_COMMUNITY_Wildtype Proximity Scorer|Wildtype Proximity Scorer]]
- [[_COMMUNITY_Base Mutator Sampling|Base Mutator Sampling]]
- [[_COMMUNITY_Component Scorer Base Class|Component Scorer Base Class]]
- [[_COMMUNITY_YAML Config Loading|YAML Config Loading]]
- [[_COMMUNITY_Design Principles (Rationale)|Design Principles (Rationale)]]
- [[_COMMUNITY_GA & Scoring Settings|GA & Scoring Settings]]
- [[_COMMUNITY_Frontend GA Process & Results UI|Frontend GA Process & Results UI]]
- [[_COMMUNITY_Practice Shell Script|Practice Shell Script]]
- [[_COMMUNITY_VM Setup Script|VM Setup Script]]
- [[_COMMUNITY_BioEmu Config Block|BioEmu Config Block]]
- [[_COMMUNITY_Project Package Metadata|Project Package Metadata]]
- [[_COMMUNITY_Conformational Landscape Target|Conformational Landscape Target]]

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
- `Fit to LLR panel (state A/B, p1/p2)` --semantically_similar_to--> `run_L5Y evolutionary search run`  [INFERRED] [semantically similar]
  frontend/index.html → shared_runs/run_L5Y/results.txt
- `Wildtype Recovery Mode` --semantically_similar_to--> `target_parameter / healthy_sequence (fit-to-target goal)`  [INFERRED] [semantically similar]
  README.md → config/evolutionary.yaml
- `TestWildtypePipeline` --uses--> `StageReporter`  [INFERRED]
  tests/test_wildtype.py → protein_optimizer/analysis.py
- `TestWildtypeProximityScorer` --uses--> `StageReporter`  [INFERRED]
  tests/test_wildtype.py → protein_optimizer/analysis.py
- `TestConformationalLandscapeScorer` --uses--> `ConformationSample`  [INFERRED]
  tests/test_scoring.py → protein_optimizer/bioemu.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **ESM-2 proposes mutations, BioEmu scores, GA searches, Pipeline orchestrates** — readme_esm2, readme_bioemu, readme_genetic_algorithm, readme_optimization_pipeline [EXTRACTED 1.00]
- **Fit-to-target goal-directed evolution across wildtype recovery, config, and observed run** — readme_wildtype_recovery_mode, config_evolutionary_target_parameter, shared_runs_run_l5y_results_run_l5y [INFERRED 0.85]
- **Frontend configuration to results/live-activity UI flow** — frontend_index_configuration_panel, frontend_index_ga_process_header, frontend_index_results_section, frontend_index_live_activity_log [EXTRACTED 1.00]

## Communities (32 total, 5 thin omitted)

### Community 0 - "GA Analysis & Stage Reporting"
Cohesion: 0.09
Nodes (20): GenerationSummary, MutationRecord, Called by GeneticAlgorithm after each generation is evaluated., Warmth reading at the end of one stage., Divides a GA run into N equal stages and reports how "warm" (close to     wildty, Return the last generation (inclusive) for each stage.         e.g. max_gen=100,, GA callback — called after each generation is evaluated., Full multi-stage summary as a printable string. (+12 more)

### Community 1 - "BioEmu Scoring Aggregation"
Cohesion: 0.10
Nodes (18): BioEmuOutput, Run inference on a batch of sequences and return aggregated outputs.          Th, Run inference for a single sequence. Return un-aggregated output., Compute ensemble-level summary statistics in-place and return the object., Aggregated structural output for one protein sequence.      `samples` holds the, CompactnessScorer, ConsistencyScorer, EnergyScorer (+10 more)

### Community 2 - "Budgeted Evolutionary Search"
Cohesion: 0.08
Nodes (20): BaseModel, BudgetedEvolutionarySearch, Higher = better in both modes. Maximise mode: the LLR itself.         Target mod, Execute the full search. Returns EvolutionarySearchResult., Extract a single LLR scalar from a BioEmuOutput.          Priority:           1., Generate `n` candidates via random amino acid substitutions (no HF download)., Generate `n` mutation candidates via ESM-2.          For each slot, picks a rand, Maximise mode: best LLR beats the reference.         Target mode: best LLR is cl (+12 more)

### Community 3 - "Trajectory GIF Maker"
Cohesion: 0.13
Nodes (31): _add_title_overlay(), assign_to_states(), _axis_limits(), compute_ss_mdtraj(), coords_to_fingerprint(), frame_rmsd_to_ref(), load_ca_trajectory(), main() (+23 more)

### Community 4 - "BioEmu Backend Abstraction"
Cohesion: 0.14
Nodes (18): ABC, Logging and Analysis Module  Responsibilities:   - Attach to GA as a callback to, BaseStructuralBackend, build_bioemu_backend(), BioEmu Interface Module  Abstracts all structural inference behind a single cont, Minimal contract that any structural inference engine must satisfy.      Impleme, Return the appropriate backend based on config.mock., LoggingConfig (+10 more)

### Community 5 - "Genetic Algorithm Core Types"
Cohesion: 0.12
Nodes (14): FitnessCallable, ConvergenceTracker, Random, Genetic Algorithm Module  A clean, biology-agnostic GA engine. It operates entir, Deterministic top-k selection. Useful for greedy benchmarking.     Repeats top s, Tracks whether the GA has stalled., Tournament selection: repeatedly sample k individuals, keep the best.      Produ, TopKSelector (+6 more)

### Community 6 - "CLI Entry Point & BioEmu Wrapper"
Cohesion: 0.12
Nodes (21): apply_overrides(), format_mutations(), main(), parse_args(), Protein Optimization — Entry Point  Default usage (runs evolutionary search with, Return the point mutations of `variant` vs. `original` as e.g. 'L5I, Q34K'., Namespace, BioEmuWrapper (+13 more)

### Community 7 - "EvoEmu Frontend & Fit-to-Target Config"
Cohesion: 0.09
Nodes (26): wildtype_sequence field (default.yaml), target_parameter / healthy_sequence (fit-to-target goal), trajectory_dir (results/trajectories), Protein Optimizer (backup title, no EvoEmu branding), Backup theme layering (futuristic/frosted-glass style overrides), Configuration Panel (sequence input, mode tabs), EvoEmu Branding/Header (index.html), Fit to LLR panel (state A/B, p1/p2) (+18 more)

### Community 8 - "Genetic Algorithm Evolution Loop"
Cohesion: 0.12
Nodes (10): GeneticAlgorithm, Call once per generation.         Returns True if the GA has converged (stale_co, Evolutionary optimiser for sequences.      The GA has no knowledge of biology. I, Execute the full GA loop.          Args:             initial_population: Startin, Produce the next generation from the current population + scores., Return the top elite_size sequences (always survive)., Build a population of exactly population_size from the seed.         If seed is, dummy_fitness() (+2 more)

### Community 9 - "Optimization Pipeline Orchestration"
Cohesion: 0.17
Nodes (7): ProteinOptimizationPipeline, Execute the full optimization. Returns OptimizationResult.          Steps:, Full evaluation pipeline for one generation's population:           sequences →, Seed population:           - The original sequence is always included (index 0), Orchestrates the full protein sequence optimization run.      Construction build, TestPipelineMock, TestWildtypePipeline

### Community 10 - "Conformational Landscape Scorer"
Cohesion: 0.16
Nodes (12): _clamp01(), ConformationalLandscapeScorer, _jensen_shannon_divergence(), _pairwise_drmsd(), ndarray, Compare a candidate ensemble against a target conformational landscape.      The, Return the target occupancy distribution, including the outlier bin., Pairwise distance RMSD between rows of two feature matrices. (+4 more)

### Community 11 - "BioEmu GIF Maker"
Cohesion: 0.17
Nodes (23): assign_to_states(), _axis_limits(), coords_to_fingerprint(), load_ca_coords(), main(), ndarray, Path, Upper-triangle of the Cα pairwise distance matrix, flattened to 1-D.      This i (+15 more)

### Community 12 - "Evolutionary Search & Mutation Module"
Cohesion: 0.13
Nodes (13): EvolutionarySearchResult, Evolutionary Search Pipeline  Implements the team's target algorithm:    1. Scor, Final result returned by BudgetedEvolutionarySearch.run()., Higher = better in both modes. Maximise mode: the LLR itself.         Target mod, CommonAncestorCrossover, ESMGuidedMutator, Random, Mutation and Crossover Module  Provides:   - BaseMutator: abstract contract for (+5 more)

### Community 13 - "Composite Scoring Function"
Cohesion: 0.15
Nodes (8): Weights for the composite fitness function., ScoringConfig, Weighted combination of component scorers → single fitness scalar.      Usage::, Score a single BioEmuOutput. Returns fitness in [0, 1]., Score a list of BioEmuOutputs. Returns List[float] in same order., Return both the aggregate fitness and per-component scores.         Useful for a, ScoringFunction, TestScoringFunction

### Community 14 - "ESM-2 Mutation Proposer"
Cohesion: 0.17
Nodes (11): ESM2Config, Controls ESM-2 mutation proposal behaviour., ESM2MutationProposer, MutationCandidate, ESM-2 Mutation Proposal Module  Wraps Meta's ESM-2 (via HuggingFace) as a biolog, Propose top-k substitutions for each target position.          Args:, Convenience wrapper for a single position., Build one masked sequence per position, batch-tokenise, run forward pass, (+3 more)

### Community 15 - "Mutation & Crossover Config"
Cohesion: 0.17
Nodes (8): MutationConfig, Controls how sequences are mutated during evolution., CrossoverOperator, Recombines two parent sequences to produce two offspring.      Supported strateg, Return two offspring. If crossover rate not triggered, return clones., Pair up parents sequentially, apply crossover, flatten results.         If popul, crossover_op(), TestCrossoverOperator

### Community 16 - "Optimization Tracker & Export"
Cohesion: 0.14
Nodes (7): OptimizationTracker, Path, Collects GA progress data and exports to disk.      Attach to a GeneticAlgorithm, Write final results to disk.          Returns:             dict mapping format n, Best-score per generation (useful for plotting)., Return a human-readable one-page report string., Write stage snapshots to JSON.

### Community 17 - "Mock BioEmu Backend & Examples"
Cohesion: 0.17
Nodes (13): MockBioEmuBackend, Deterministic synthetic backend for unit tests and GPU-free development.      Sc, BioEmuConfig, Controls BioEmu structural inference., custom_scorer_demo(), landscape_scorer_demo(), quick_start(), Example usage script — demonstrates the full Python API without going through th (+5 more)

### Community 18 - "Random Mutator & Tests"
Cohesion: 0.16
Nodes (8): build_mutator(), RandomMutator, Construct the appropriate mutator given the strategy in config.      Pass esm_pr, Baseline mutator: choose a random position, substitute a random AA.      Number, random_mutator(), Tests for mutation and crossover operators., TestBuildMutator, TestRandomMutator

### Community 19 - "Wildtype Proximity Scorer"
Cohesion: 0.18
Nodes (6): Directly append WildtypeProximityScorer into the scoring function and         re, Measures how close a sequence is to a known wildtype target.      Uses normalise, Number of positions that differ between two equal-length sequences., Fraction of identical positions. Clamped to shortest length., WildtypeProximityScorer, TestWildtypeProximityScorer

### Community 20 - "Base Mutator Sampling"
Cohesion: 0.18
Nodes (6): BaseMutator, Softmax-weighted sampling over MutationCandidate log-probs., Abstract mutation operator.      All mutators take a sequence string and return, Return a mutated copy of *sequence*., Batch mutation. Override for vectorised implementations., Return positions eligible for mutation.

### Community 21 - "Component Scorer Base Class"
Cohesion: 0.22
Nodes (5): ComponentScorer, A single scoring axis. Returns a float in [0, 1].      Subclass and implement `s, Add a custom component scorer and optionally renormalize all weights         so, Add a preconfigured component scorer instance.          Use this for scorers tha, Compute a score in [0, 1] from a BioEmuOutput. Higher = better.

### Community 22 - "YAML Config Loading"
Cohesion: 0.25
Nodes (5): Any, Path, Load from a YAML file. Missing keys fall back to dataclass defaults., Serialize to a plain dict (useful for logging)., from_yaml_config()

### Community 23 - "Design Principles (Rationale)"
Cohesion: 0.50
Nodes (4): BioEmu is a black box (rationale), Design Principles, GA is biology-agnostic (rationale), Mock-first testability (rationale)

### Community 24 - "GA & Scoring Settings"
Cohesion: 0.67
Nodes (3): GA Settings (config/default.yaml), Scoring Weights (config/default.yaml), GA Settings (config/evolutionary.yaml)

### Community 25 - "Frontend GA Process & Results UI"
Cohesion: 0.67
Nodes (3): GA Process Header (#gaHeader), Live Search Activity Log (#activity), Results section (#results)

## Knowledge Gaps
- **16 isolated node(s):** `practice.sh script`, `protein-optimizer`, `setup_vm.sh script`, `Conformational Landscape (target ensemble)`, `BioEmu Config (config/default.yaml)` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BioEmuOutput` connect `BioEmu Scoring Aggregation` to `GA Analysis & Stage Reporting`, `Budgeted Evolutionary Search`, `BioEmu Backend Abstraction`, `CLI Entry Point & BioEmu Wrapper`, `Optimization Pipeline Orchestration`, `Conformational Landscape Scorer`, `Evolutionary Search & Mutation Module`, `Composite Scoring Function`, `Mock BioEmu Backend & Examples`, `Wildtype Proximity Scorer`, `Component Scorer Base Class`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `ProteinOptimizationPipeline` connect `Optimization Pipeline Orchestration` to `GA Analysis & Stage Reporting`, `BioEmu Backend Abstraction`, `Genetic Algorithm Core Types`, `Genetic Algorithm Evolution Loop`, `Composite Scoring Function`, `ESM-2 Mutation Proposer`, `Mutation & Crossover Config`, `Optimization Tracker & Export`, `Mock BioEmu Backend & Examples`, `Wildtype Proximity Scorer`, `YAML Config Loading`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `OptimizationConfig` connect `BioEmu Backend Abstraction` to `GA Analysis & Stage Reporting`, `Budgeted Evolutionary Search`, `Genetic Algorithm Core Types`, `CLI Entry Point & BioEmu Wrapper`, `Genetic Algorithm Evolution Loop`, `Optimization Pipeline Orchestration`, `Evolutionary Search & Mutation Module`, `Mock BioEmu Backend & Examples`, `Wildtype Proximity Scorer`, `YAML Config Loading`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `BioEmuOutput` (e.g. with `BioEmuConfig` and `BudgetedEvolutionarySearch`) actually correct?**
  _`BioEmuOutput` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `ProteinOptimizationPipeline` (e.g. with `OptimizationTracker` and `StageReporter`) actually correct?**
  _`ProteinOptimizationPipeline` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `MutationConfig` (e.g. with `._from_dict()` and `BaseMutator`) actually correct?**
  _`MutationConfig` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `CrossoverOperator` (e.g. with `ConvergenceTracker` and `GenerationResult`) actually correct?**
  _`CrossoverOperator` has 16 INFERRED edges - model-reasoned connections that need verification._