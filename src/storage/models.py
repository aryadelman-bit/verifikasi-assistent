from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


SEVERITIES = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")
STATUSES = ("PASS", "WARNING", "FAIL", "NOT_APPLICABLE")


@dataclass(slots=True)
class ValidationFinding:
    rule_id: str
    nama_rule: str
    kategori_data: str
    severity: str
    status: str
    deskripsi_temuan: str
    nilai_terdeteksi: str = ""
    dasar_perhitungan: str = ""
    rekomendasi_tindak_lanjut: str = ""
    pertanyaan_klarifikasi_ke_perusahaan: str = ""

    def __post_init__(self) -> None:
        self.severity = self.severity.upper()
        self.status = self.status.upper()
        if self.severity not in SEVERITIES:
            raise ValueError(f"Unknown severity: {self.severity}")
        if self.status not in STATUSES:
            raise ValueError(f"Unknown status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CompanyReport:
    company_name: str
    period: str = ""
    submitted_at: str = ""
    status: str = ""
    verifier: str = ""
    validator: str = ""
    detail_url: str = ""
    report_id: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    identity: dict[str, Any] = field(default_factory=dict)
    general: dict[str, Any] = field(default_factory=dict)
    sections: dict[str, Any] = field(default_factory=dict)
    raw_html_path: str = ""
    raw_csv_paths: list[str] = field(default_factory=list)
    parser_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationResult:
    findings: list[ValidationFinding]
    risk_score: int
    recommendation: str
    severity_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings": [finding.to_dict() for finding in self.findings],
            "risk_score": self.risk_score,
            "recommendation": self.recommendation,
            "severity_counts": self.severity_counts,
        }

