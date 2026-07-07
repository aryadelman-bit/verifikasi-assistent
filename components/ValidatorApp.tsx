"use client";

import { AlertTriangle, CheckCircle2, Clipboard, Download, FileText, Scale, Upload, XCircle } from "lucide-react";
import { useMemo, useState } from "react";
import { extractPdfText } from "@/lib/pdfText";
import { parsePriceLimits } from "@/lib/priceLimits";
import { parseReportFromText, SECTION_LABELS } from "@/lib/reportParser";
import { buildValidatorNote, validateReport } from "@/lib/validator";
import { formatNumber, formatRupiah } from "@/lib/number";
import type { Finding, ParsedReport, PriceLimitMap, ReportSectionKey, SectionSummary, ValidationResult } from "@/lib/types";

const SECTION_KEYS = Object.keys(SECTION_LABELS) as ReportSectionKey[];

const severityRank: Record<string, number> = {
  CRITICAL: 5,
  HIGH: 4,
  MEDIUM: 3,
  LOW: 2,
  INFO: 1
};

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function FilePicker({
  label,
  fileName,
  onFile
}: {
  label: string;
  fileName: string;
  onFile: (file: File) => void;
}) {
  return (
    <label className="uploadBox">
      <span className="uploadIcon">
        <Upload size={18} />
      </span>
      <span>
        <strong>{label}</strong>
        <small>{fileName || "Pilih PDF"}</small>
      </span>
      <input
        type="file"
        accept="application/pdf,.pdf"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFile(file);
        }}
      />
    </label>
  );
}

function RecommendationBadge({ recommendation }: { recommendation: string }) {
  const severe = /jangan|perbaikan/i.test(recommendation);
  const warning = /klarifikasi|catatan/i.test(recommendation);
  return (
    <span className={cx("badge", severe ? "badgeDanger" : warning ? "badgeWarn" : "badgeOk")}>
      {severe ? <XCircle size={15} /> : warning ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}
      {recommendation}
    </span>
  );
}

function FindingTable({ findings }: { findings: Finding[] }) {
  if (!findings.length) return <p className="empty">Tidak ada temuan pada bagian ini.</p>;
  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Rule</th>
            <th>Temuan</th>
            <th>Data</th>
            <th>Rekomendasi</th>
          </tr>
        </thead>
        <tbody>
          {findings
            .slice()
            .sort((a, b) => severityRank[b.severity] - severityRank[a.severity])
            .map((finding) => (
              <tr key={`${finding.ruleId}-${finding.section}-${finding.detectedValue}`}>
                <td>
                  <span className={cx("severity", `sev${finding.severity}`)}>{finding.severity}</span>
                </td>
                <td>{finding.rule}</td>
                <td>{finding.finding}</td>
                <td>{finding.detectedValue || "-"}</td>
                <td>{finding.recommendation}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function SectionPanel({
  section,
  report,
  result
}: {
  section: SectionSummary;
  report: ParsedReport;
  result: ValidationResult;
}) {
  const findings = result.findings.filter((finding) => finding.section === section.label);
  return (
    <section className="sectionPanel">
      <div className="sectionHeader">
        <div>
          <h2>{section.label}</h2>
          <RecommendationBadge recommendation={section.recommendation} />
        </div>
        <div className="miniScore">
          <span>{section.score}</span>
          <small>/100</small>
        </div>
      </div>
      <div className="sectionGrid">
        <div className="sectionCard">
          <h3>Catatan Bagian</h3>
          {section.topFindings.length ? (
            <ul className="noteList">
              {section.topFindings.map((finding) => (
                <li key={`${finding.ruleId}-${finding.detectedValue}`}>
                  <strong>{finding.severity}</strong> {finding.finding}
                  {finding.detectedValue ? <span> Data: {finding.detectedValue}</span> : null}
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty">Tidak ada catatan utama berdasarkan rule yang berjalan.</p>
          )}
        </div>
        <div className="sectionCard">
          <h3>Raw Section</h3>
          <pre>{report.sectionsText[section.key] || "Bagian tidak ditemukan pada PDF."}</pre>
        </div>
      </div>
      <FindingTable findings={findings} />
    </section>
  );
}

function DataPreview({ report }: { report: ParsedReport }) {
  const totalProduction = report.production.reduce((total, row) => total + row.productionKg, 0);
  const totalMaterial = report.materials.reduce((total, row) => total + row.domesticKg + row.importKg, 0);
  const totalProductionValue = report.production.reduce((total, row) => total + row.productionValue, 0);
  return (
    <div className="metricGrid">
      <div className="metric">
        <small>Perusahaan</small>
        <strong>{report.companyName}</strong>
      </div>
      <div className="metric">
        <small>Produksi</small>
        <strong>{formatNumber(totalProduction)} kg</strong>
      </div>
      <div className="metric">
        <small>Nilai Produksi</small>
        <strong>{formatRupiah(totalProductionValue)}</strong>
      </div>
      <div className="metric">
        <small>Bahan Baku</small>
        <strong>{formatNumber(totalMaterial)} kg</strong>
      </div>
      <div className="metric">
        <small>Kapasitas</small>
        <strong>{report.capacity.length} baris</strong>
      </div>
      <div className="metric">
        <small>Limbah Cair</small>
        <strong>{formatNumber(report.liquidWaste.outletDebit, 2)} m3/detik</strong>
      </div>
    </div>
  );
}

export function ValidatorApp() {
  const [reportFileName, setReportFileName] = useState("");
  const [limitFileName, setLimitFileName] = useState("");
  const [reportText, setReportText] = useState("");
  const [limitText, setLimitText] = useState("");
  const [activeKey, setActiveKey] = useState<ReportSectionKey>("identity");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const priceLimits: PriceLimitMap = useMemo(() => (limitText ? parsePriceLimits(limitText) : {}), [limitText]);
  const report = useMemo(() => (reportText ? parseReportFromText(reportText, reportFileName) : null), [reportText, reportFileName]);
  const result = useMemo(() => (report ? validateReport(report, priceLimits) : null), [report, priceLimits]);
  const validatorNote = useMemo(() => (result ? buildValidatorNote(result) : ""), [result]);

  async function loadPdf(file: File, target: "report" | "limit") {
    setError("");
    setBusy(`Membaca ${file.name}`);
    try {
      const text = await extractPdfText(file);
      if (target === "report") {
        setReportFileName(file.name);
        setReportText(text);
      } else {
        setLimitFileName(file.name);
        setLimitText(text);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF tidak dapat dibaca.");
    } finally {
      setBusy("");
    }
  }

  function exportHtml() {
    if (!report || !result) return;
    const findingsRows = result.findings
      .slice()
      .sort((a, b) => severityRank[b.severity] - severityRank[a.severity])
      .map(
        (finding) => `
          <tr>
            <td>${escapeHtml(finding.section)}</td>
            <td>${escapeHtml(finding.severity)}</td>
            <td>${escapeHtml(finding.rule)}</td>
            <td>${escapeHtml(finding.finding)}</td>
            <td>${escapeHtml(finding.detectedValue || "-")}</td>
            <td>${escapeHtml(finding.recommendation)}</td>
          </tr>`
      )
      .join("");
    const html = `<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8" />
  <title>Hasil Validasi ${escapeHtml(report.companyName)}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #182235; }
    h1 { margin-bottom: 4px; }
    .muted { color: #637083; }
    .summary { border: 1px solid #d8dee9; padding: 16px; border-radius: 8px; margin: 18px 0; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { border: 1px solid #d8dee9; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f1f4f9; }
    pre { white-space: pre-wrap; background: #f8fafc; border: 1px solid #d8dee9; padding: 12px; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>${escapeHtml(report.companyName)}</h1>
  <p class="muted">${escapeHtml(report.general["Periode Laporan"] || report.fileName)}</p>
  <div class="summary">
    <strong>Rekomendasi:</strong> ${escapeHtml(result.recommendation)}<br />
    <strong>Risk score:</strong> ${result.riskScore}/100
  </div>
  <h2>Catatan Validator</h2>
  <pre>${escapeHtml(validatorNote)}</pre>
  <h2>Tabel Temuan</h2>
  <table>
    <thead>
      <tr>
        <th>Bagian</th>
        <th>Severity</th>
        <th>Rule</th>
        <th>Temuan</th>
        <th>Data</th>
        <th>Rekomendasi</th>
      </tr>
    </thead>
    <tbody>${findingsRows || `<tr><td colspan="6">Tidak ada temuan.</td></tr>`}</tbody>
  </table>
</body>
</html>`;
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `validasi-${report.companyName.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.html`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const selectedSection = result?.sectionSummaries.find((section) => section.key === activeKey);
  const topFindings = result?.findings.slice().sort((a, b) => severityRank[b.severity] - severityRank[a.severity]).slice(0, 6) ?? [];

  return (
    <main className="appShell">
      <aside className="sidebar">
        <div className="brand">
          <Scale size={24} />
          <div>
            <h1>Validator PDF</h1>
            <span>IntraNEW/SIINas</span>
          </div>
        </div>
        <FilePicker label="Laporan PDF" fileName={reportFileName} onFile={(file) => loadPdf(file, "report")} />
        <FilePicker label="Batas Harga KBLI" fileName={limitFileName} onFile={(file) => loadPdf(file, "limit")} />
        <div className="statusBox">
          <small>Status</small>
          <strong>{busy || (report ? "Siap divalidasi" : "Menunggu PDF")}</strong>
          <span>{Object.keys(priceLimits).length} batas KBLI terbaca</span>
        </div>
        {error ? <div className="errorBox">{error}</div> : null}
        {result ? (
          <nav className="sectionNav">
            {result.sectionSummaries.map((section) => (
              <button
                key={section.key}
                className={cx(activeKey === section.key && "active")}
                onClick={() => setActiveKey(section.key)}
              >
                <span>{section.label}</span>
                <b>{section.score}</b>
              </button>
            ))}
          </nav>
        ) : null}
      </aside>

      <section className="content">
        {!report || !result ? (
          <div className="emptyState">
            <FileText size={44} />
            <h2>Unggah laporan PDF dan batas harga KBLI</h2>
            <p>Aplikasi akan membaca PDF di browser, menilai kewajaran sampai bagian Pengelolaan Limbah Cair, lalu membuat catatan per bagian dan rekomendasi keseluruhan.</p>
          </div>
        ) : (
          <>
            <header className="reportHeader">
              <div>
                <h2>{report.companyName}</h2>
                <p>{report.general["Periode Laporan"] || report.fileName}</p>
              </div>
              <div className="scoreCard">
                <small>Risk score</small>
                <strong>{result.riskScore}/100</strong>
                <RecommendationBadge recommendation={result.recommendation} />
              </div>
            </header>

            <DataPreview report={report} />

            {report.parserWarnings.length ? (
              <div className="warningStrip">
                <AlertTriangle size={18} />
                <span>{report.parserWarnings.join(" ")}</span>
              </div>
            ) : null}

            <div className="twoCol">
              <section className="panel">
                <h2>Temuan Prioritas</h2>
                <FindingTable findings={topFindings} />
              </section>
              <section className="panel">
                <div className="panelTitle">
                  <h2>Catatan Validator</h2>
                  <div className="buttonRow">
                    <button className="iconButton" onClick={() => navigator.clipboard.writeText(validatorNote)} title="Salin catatan">
                      <Clipboard size={16} />
                    </button>
                    <button className="iconButton" onClick={exportHtml} title="Export HTML">
                      <Download size={16} />
                    </button>
                  </div>
                </div>
                <textarea readOnly value={validatorNote} />
              </section>
            </div>

            {selectedSection ? <SectionPanel section={selectedSection} report={report} result={result} /> : null}
          </>
        )}
      </section>
    </main>
  );
}
