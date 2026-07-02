"""
Run Store — SQLite persistence for optimization runs.

Records every server-triggered `BudgetedEvolutionarySearch` run (config, per-round
progress, and final result) so past runs can be browsed in the dashboard and their
convergence replayed as a chart. Read-only with respect to the optimization engine
itself: this module only observes and stores the progress events / result data that
`evolutionary_search.py` already produces.

Each function opens and closes its own short-lived connection — adequate for this
app's concurrency level (one background thread per run) without needing a shared
connection object or locking.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "runs.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                job_id TEXT PRIMARY KEY,
                created_at REAL,
                status TEXT,
                mode TEXT,
                sequence TEXT,
                config_json TEXT,
                reference_llr REAL,
                best_llr REAL,
                best_sequence TEXT,
                target_parameter REAL,
                improved INTEGER,
                rounds_run INTEGER,
                total_evaluated INTEGER,
                wall_time_s REAL,
                error TEXT,
                result_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                round INTEGER,
                total_rounds INTEGER,
                best_llr REAL,
                total_evaluated INTEGER,
                top20_json TEXT,
                created_at REAL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_run_rounds_job_id ON run_rounds(job_id)"
        )


def create_run(job_id: str, req: Dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO runs (job_id, created_at, status, mode, sequence, config_json)
            VALUES (?, ?, 'running', ?, ?, ?)
            """,
            (job_id, time.time(), req.get("mode"), req.get("sequence"), json.dumps(req)),
        )


def record_round(job_id: str, event: Dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO run_rounds (job_id, round, total_rounds, best_llr, total_evaluated, top20_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                event.get("round"),
                event.get("total_rounds"),
                event.get("best_llr"),
                event.get("total_evaluated"),
                json.dumps(event.get("top20", [])),
                time.time(),
            ),
        )


def finalize_run(job_id: str, result_data: Dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE runs SET
                status = 'done',
                reference_llr = ?,
                best_llr = ?,
                best_sequence = ?,
                target_parameter = ?,
                improved = ?,
                rounds_run = ?,
                total_evaluated = ?,
                wall_time_s = ?,
                result_json = ?
            WHERE job_id = ?
            """,
            (
                result_data.get("reference_llr"),
                result_data.get("best_llr"),
                result_data.get("best_sequence"),
                result_data.get("target_parameter"),
                1 if result_data.get("improved") else 0,
                result_data.get("rounds_run"),
                result_data.get("total_evaluated"),
                result_data.get("wall_time_s"),
                json.dumps(result_data),
                job_id,
            ),
        )


def fail_run(job_id: str, message: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE runs SET status = 'error', error = ? WHERE job_id = ?",
            (message, job_id),
        )


def list_runs(limit: int = 50) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT job_id, created_at, status, mode, sequence, reference_llr, best_llr,
                   improved, rounds_run, total_evaluated, wall_time_s, error
            FROM runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_run(job_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        run = dict(row)
        run["result"] = json.loads(run["result_json"]) if run.get("result_json") else None
        run["config"] = json.loads(run["config_json"]) if run.get("config_json") else None
        return run


def get_run_rounds(job_id: str) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT round, total_rounds, best_llr, total_evaluated, top20_json, created_at
            FROM run_rounds
            WHERE job_id = ?
            ORDER BY round ASC
            """,
            (job_id,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["top20"] = json.loads(d.pop("top20_json"))
            out.append(d)
        return out
