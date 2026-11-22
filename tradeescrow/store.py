"""SQLite persistence for the simulated permissioned ledger.

This is an ordinary SQLite database used as a *mock* permissioned ledger. It is
not a distributed consensus network. The event journal is hash-chained so that
post-hoc edits are detectable (tamper-evident demonstration, not tamper-proof).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS principals(
  principal_id TEXT PRIMARY KEY, role TEXT NOT NULL, entity_id TEXT NOT NULL, display TEXT);
CREATE TABLE IF NOT EXISTS parties(
  party_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS watchlist(
  entry_id INTEGER PRIMARY KEY AUTOINCREMENT, party_id TEXT NOT NULL, reason_code TEXT NOT NULL,
  added_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS dispositions(
  party_id TEXT NOT NULL, reason_code TEXT NOT NULL, review_reference TEXT NOT NULL,
  decided_at TEXT NOT NULL, PRIMARY KEY(party_id, reason_code));
CREATE TABLE IF NOT EXISTS trades(
  trade_id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS escrows(
  escrow_id TEXT PRIMARY KEY, trade_id TEXT UNIQUE NOT NULL, state TEXT NOT NULL,
  locked_minor INTEGER NOT NULL CHECK(locked_minor >= 0), version INTEGER NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS accounts(
  account_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, instrument TEXT NOT NULL,
  balance_minor INTEGER NOT NULL CHECK(balance_minor >= 0));
CREATE TABLE IF NOT EXISTS postings(
  posting_id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL, instrument TEXT NOT NULL,
  debit_account TEXT NOT NULL, credit_account TEXT NOT NULL,
  amount_minor INTEGER NOT NULL CHECK(amount_minor > 0), ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents(
  doc_id TEXT PRIMARY KEY, trade_id TEXT NOT NULL, doc_type TEXT NOT NULL, revision INTEGER NOT NULL,
  submitted_by TEXT NOT NULL, submitted_at TEXT NOT NULL, content TEXT NOT NULL, digest TEXT NOT NULL,
  UNIQUE(trade_id, doc_type, revision));
CREATE TABLE IF NOT EXISTS attestations(
  attestation_id TEXT PRIMARY KEY, seq INTEGER NOT NULL, trade_id TEXT NOT NULL, type TEXT NOT NULL,
  checkpoint TEXT, subject_id TEXT, issuer_id TEXT NOT NULL, issuer_role TEXT NOT NULL,
  result TEXT NOT NULL, issued_at TEXT NOT NULL, expires_at TEXT, revision INTEGER NOT NULL,
  input_digest TEXT, reason_code TEXT, details TEXT, revoked INTEGER NOT NULL DEFAULT 0,
  review_reference TEXT);
CREATE TABLE IF NOT EXISTS holds(
  hold_id TEXT PRIMARY KEY, raised_seq INTEGER NOT NULL, escrow_id TEXT NOT NULL,
  status TEXT NOT NULL, reason_code TEXT NOT NULL, party_ids TEXT NOT NULL DEFAULT '[]',
  source TEXT NOT NULL, raised_by TEXT NOT NULL, raised_at TEXT NOT NULL, resolved_by TEXT,
  resolved_at TEXT, decision TEXT, review_reference TEXT);
CREATE TABLE IF NOT EXISTS events(
  seq INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, trade_id TEXT, escrow_id TEXT,
  ts TEXT NOT NULL, actor_id TEXT NOT NULL, actor_role TEXT NOT NULL, actor_kind TEXT NOT NULL,
  operation TEXT NOT NULL, outcome TEXT NOT NULL, prior_state TEXT, new_state TEXT,
  reason_code TEXT, related_attestation_ids TEXT NOT NULL, amount_minor INTEGER,
  details TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS commands(command_id TEXT PRIMARY KEY, result TEXT NOT NULL);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Serialised write transaction: guard evaluation, postings and event append
    commit together or not at all."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
