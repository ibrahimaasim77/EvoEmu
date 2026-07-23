# Graph Report - protein_optimizer  (2026-07-02)

## Corpus Check
- 26 files · ~37,507 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 31 nodes · 46 edges · 8 communities (5 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `828de619`
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

## God Nodes (most connected - your core abstractions)
1. `_connect()` - 10 edges
2. `create_run()` - 3 edges
3. `record_round()` - 3 edges
4. `finalize_run()` - 3 edges
5. `list_runs()` - 3 edges
6. `get_run()` - 3 edges
7. `get_run_rounds()` - 3 edges
8. `RunRequest` - 3 edges
9. `start_run()` - 3 edges
10. `fold_sequence()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `create_run()` --calls--> `_connect()`  [EXTRACTED]
  protein_optimizer/run_store.py → protein_optimizer/run_store.py  _Bridges community 2 → community 3_
- `finalize_run()` --calls--> `_connect()`  [EXTRACTED]
  protein_optimizer/run_store.py → protein_optimizer/run_store.py  _Bridges community 2 → community 1_
- `create_run()` --references--> `Any`  [EXTRACTED]
  protein_optimizer/run_store.py →   _Bridges community 3 → community 1_
- `start_run()` --calls--> `Queue`  [EXTRACTED]
  server.py →   _Bridges community 4 → community 6_

## Import Cycles
- None detected.

## Communities (8 total, 3 thin omitted)

### Community 1 - "Any"
Cohesion: 0.40
Nodes (5): Any, finalize_run(), get_run(), get_run_rounds(), list_runs()

### Community 2 - "_connect"
Cohesion: 0.50
Nodes (4): Connection, _connect(), fail_run(), init_db()

### Community 3 - "run_store.py"
Cohesion: 0.50
Nodes (3): create_run(), Run Store — SQLite persistence for optimization runs.  Records every server-trig, record_round()

### Community 4 - "RunRequest"
Cohesion: 0.67
Nodes (3): BaseModel, RunRequest, start_run()

### Community 5 - "fold_sequence"
Cohesion: 0.67
Nodes (3): Request, fold_sequence(), Proxy ESMFold structure prediction through the ESM Atlas public API.

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `fold_sequence()` connect `fold_sequence` to `server.py`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `_connect()` connect `_connect` to `Any`, `run_store.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `RunRequest` connect `RunRequest` to `server.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **What connects `Run Store — SQLite persistence for optimization runs.  Records every server-trig`, `Protein Optimizer — Web Server  Usage:     pip install fastapi uvicorn     pytho`, `Serve a pre-converted multi-frame PDB of a saved BioEmu run (real .xtc     ensem` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._