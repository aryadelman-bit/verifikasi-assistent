from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

from src.insight.recommendation import calculate_risk_score, decision_recommendation, severity_counts
from src.storage.models import ValidationFinding, ValidationResult

RuleFn = Callable[[dict[str, Any], dict[str, Any]], list[ValidationFinding]]


def load_yaml(path: str | Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return default or {}
    with file_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


class ValidationEngine:
    def __init__(
        self,
        thresholds: dict[str, Any] | None = None,
        rule_config: dict[str, Any] | None = None,
        mappings: list[dict[str, Any]] | None = None,
    ) -> None:
        self.thresholds = thresholds or {}
        self.rule_config = rule_config or {}
        self.mappings = mappings or []
        self._rules: dict[str, RuleFn] = {}

    def register(self, name: str, fn: RuleFn) -> None:
        self._rules[name] = fn

    def register_default_rules(self) -> None:
        from src.validation import (
            rules_capacity,
            rules_completeness,
            rules_energy_water,
            rules_identity,
            rules_indi,
            rules_investment,
            rules_labor,
            rules_machine,
            rules_material,
            rules_production_inventory,
            rules_waste,
        )

        self.register("completeness", rules_completeness.run)
        self.register("identity", rules_identity.run)
        self.register("capacity", rules_capacity.run)
        self.register("production_inventory", rules_production_inventory.run)
        self.register("material", rules_material.run)
        self.register("energy_water", rules_energy_water.run)
        self.register("labor", rules_labor.run)
        self.register("investment", rules_investment.run)
        self.register("machine", rules_machine.run)
        self.register("waste", rules_waste.run)
        self.register("indi", rules_indi.run)

    def validate(
        self,
        report: dict[str, Any],
        previous_report: dict[str, Any] | None = None,
    ) -> ValidationResult:
        if not self._rules:
            self.register_default_rules()

        enabled = self.rule_config.get("enabled_rules", {})
        context = {
            "thresholds": self.thresholds,
            "previous_report": previous_report or {},
            "mappings": self.mappings,
            "rule_config": self.rule_config,
        }

        findings: list[ValidationFinding] = []
        for name, fn in self._rules.items():
            if enabled and enabled.get(name, True) is False:
                continue
            try:
                findings.extend(fn(report, context))
            except Exception as exc:  # pragma: no cover - defensive audit trail.
                findings.append(
                    ValidationFinding(
                        rule_id=f"{name.upper()}_ENGINE_ERROR",
                        nama_rule=f"Rule {name} gagal dijalankan",
                        kategori_data="Sistem",
                        severity="MEDIUM",
                        status="WARNING",
                        deskripsi_temuan="Rule tidak dapat dijalankan karena struktur data tidak sesuai.",
                        nilai_terdeteksi=str(exc),
                        dasar_perhitungan="Exception saat menjalankan validation engine.",
                        rekomendasi_tindak_lanjut="Periksa raw data dan sesuaikan parser/rule jika struktur website berubah.",
                        pertanyaan_klarifikasi_ke_perusahaan="",
                    )
                )

        weights = self.rule_config.get("risk_weights", {})
        score = calculate_risk_score(findings, weights)
        return ValidationResult(
            findings=findings,
            risk_score=score,
            recommendation=decision_recommendation(findings, score),
            severity_counts=severity_counts(findings),
        )
