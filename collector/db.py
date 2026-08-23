from __future__ import annotations
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS collection_runs(run_id TEXT PRIMARY KEY, slot TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT, status TEXT NOT NULL, total_rooms INTEGER DEFAULT 0, successful_rooms INTEGER DEFAULT 0, failed_rooms INTEGER DEFAULT 0, coverage REAL DEFAULT 0, error_counts TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS room_registry(room_id TEXT PRIMARY KEY, private_device_id TEXT, campus TEXT NOT NULL, building TEXT NOT NULL, floor TEXT, room TEXT NOT NULL, discovered_at TEXT NOT NULL, last_confirmed_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS snapshots(room_id TEXT NOT NULL, slot TEXT NOT NULL, sampled_at TEXT NOT NULL, balance_value REAL, balance_unit TEXT, price REAL, quality TEXT NOT NULL, run_id TEXT NOT NULL, PRIMARY KEY(room_id, slot));
CREATE TABLE IF NOT EXISTS derived_consumption(room_id TEXT NOT NULL, start_slot TEXT NOT NULL, end_slot TEXT NOT NULL, estimated_consumption REAL, source TEXT NOT NULL, quality TEXT NOT NULL, PRIMARY KEY(room_id, start_slot, end_slot));
CREATE TABLE IF NOT EXISTS publication_runs(version TEXT PRIMARY KEY, generated_at TEXT NOT NULL, coverage REAL NOT NULL, target_repo TEXT, commit_sha TEXT, status TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_snapshots_room_sampled ON snapshots(room_id, sampled_at);
CREATE INDEX IF NOT EXISTS idx_registry_building ON room_registry(campus, building);
"""

def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db(path: Path | str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES (1, datetime('now'))")

def upsert_snapshot(conn, row: dict) -> None:
    conn.execute("""INSERT INTO snapshots(room_id,slot,sampled_at,balance_value,balance_unit,price,quality,run_id)
    VALUES(:room_id,:slot,:sampled_at,:balance_value,:balance_unit,:price,:quality,:run_id)
    ON CONFLICT(room_id,slot) DO UPDATE SET sampled_at=excluded.sampled_at,balance_value=excluded.balance_value,balance_unit=excluded.balance_unit,price=excluded.price,quality=excluded.quality,run_id=excluded.run_id""", row)
