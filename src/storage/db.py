from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.storage.models import ValidationFinding


DEFAULT_DB = Path("data/intranew_validator.db")


def connect(db_path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            period TEXT,
            submitted_at TEXT,
            status TEXT,
            verifier TEXT,
            validator TEXT,
            detail_url TEXT,
            scraping_status TEXT,
            validation_status TEXT,
            risk_score INTEGER DEFAULT 0,
            recommendation TEXT,
            raw_html_path TEXT,
            raw_csv_paths TEXT,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(report_id) REFERENCES reports(report_id)
        );
        """
    )
    conn.commit()


def report_key(report: dict[str, Any]) -> str:
    explicit = str(report.get("report_id") or "").strip()
    if explicit:
        return explicit
    basis = "|".join(
        [
            str(report.get("company_name") or ""),
            str(report.get("period") or ""),
            str(report.get("submitted_at") or ""),
            str(report.get("detail_url") or ""),
        ]
    )
    import hashlib

    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def save_report(conn: sqlite3.Connection, report: dict[str, Any]) -> str:
    key = report_key(report)
    report["report_id"] = key
    conn.execute(
        """
        INSERT INTO reports (
            report_id, company_name, period, submitted_at, status, verifier, validator, detail_url,
            scraping_status, validation_status, risk_score, recommendation, raw_html_path, raw_csv_paths,
            payload_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(report_id) DO UPDATE SET
            company_name=excluded.company_name,
            period=excluded.period,
            submitted_at=excluded.submitted_at,
            status=excluded.status,
            verifier=excluded.verifier,
            validator=excluded.validator,
            detail_url=excluded.detail_url,
            scraping_status=excluded.scraping_status,
            validation_status=excluded.validation_status,
            risk_score=excluded.risk_score,
            recommendation=excluded.recommendation,
            raw_html_path=excluded.raw_html_path,
            raw_csv_paths=excluded.raw_csv_paths,
            payload_json=excluded.payload_json,
            updated_at=excluded.updated_at
        """,
        (
            key,
            report.get("company_name", ""),
            report.get("period", ""),
            report.get("submitted_at", ""),
            report.get("status", ""),
            report.get("verifier", ""),
            report.get("validator", ""),
            report.get("detail_url", ""),
            report.get("scraping_status", ""),
            report.get("validation_status", ""),
            int(report.get("risk_score") or 0),
            report.get("recommendation", ""),
            report.get("raw_html_path", ""),
            json.dumps(report.get("raw_csv_paths", []), ensure_ascii=False),
            json.dumps(report, ensure_ascii=False),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    return key


def list_reports(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT report_id, company_name, period, submitted_at, status, verifier, validator, detail_url,
               scraping_status, validation_status, risk_score, recommendation, updated_at
        FROM reports
        ORDER BY updated_at DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def load_report(conn: sqlite3.Connection, report_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT payload_json FROM reports WHERE report_id = ?", (report_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def save_findings(conn: sqlite3.Connection, report_id: str, findings: list[ValidationFinding], risk_score: int, recommendation: str) -> None:
    conn.execute("DELETE FROM findings WHERE report_id = ?", (report_id,))
    now = datetime.now().isoformat(timespec="seconds")
    conn.executemany(
        """
        INSERT INTO findings (report_id, rule_id, severity, status, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                report_id,
                finding.rule_id,
                finding.severity,
                finding.status,
                json.dumps(finding.to_dict(), ensure_ascii=False),
                now,
            )
            for finding in findings
        ],
    )
    validation_status = "validated" if findings else "validated_no_findings"
    conn.execute(
        """
        UPDATE reports
        SET validation_status = ?, risk_score = ?, recommendation = ?, updated_at = ?
        WHERE report_id = ?
        """,
        (validation_status, risk_score, recommendation, now, report_id),
    )
    conn.commit()


def load_findings(conn: sqlite3.Connection, report_id: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT payload_json FROM findings WHERE report_id = ? ORDER BY id", (report_id,)).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]

