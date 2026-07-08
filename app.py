from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import yaml

from src.browser.navigator import IntraNewNavigator
from src.browser.session import DEFAULT_URL, BrowserSessionManager
from src.export.excel_exporter import export_report_excel
from src.export.html_report import export_html_report
from src.insight.narrative import (
    findings_table,
    generate_copy_note,
    generate_findings_narrative,
    generate_overall_validator_recommendation,
    generate_section_recommendation,
    generate_summary,
    section_recommendations_table,
)
from src.storage import db
from src.storage.models import ValidationFinding, ValidationResult
from src.validation.engine import ValidationEngine, load_yaml


ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "intranew_validator.db"
THRESHOLD_PATH = CONFIG_DIR / "thresholds.yaml"
RULE_CONFIG_PATH = CONFIG_DIR / "validation_rules.yaml"
MAPPING_PATH = CONFIG_DIR / "kbli_hs_mapping.csv"
BROWSER_MANAGER_VERSION = 2


def app_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def load_mappings() -> list[dict[str, Any]]:
    if not MAPPING_PATH.exists():
        return []
    return pd.read_csv(MAPPING_PATH).fillna("").to_dict(orient="records")


def get_conn():
    return db.connect(DB_PATH)


def make_engine() -> ValidationEngine:
    return ValidationEngine(
        thresholds=load_yaml(THRESHOLD_PATH, {}),
        rule_config=load_yaml(RULE_CONFIG_PATH, {}),
        mappings=load_mappings(),
    )


def validate_report(report_id: str) -> ValidationResult:
    conn = get_conn()
    report = db.load_report(conn, report_id)
    if report is None:
        raise ValueError("Report tidak ditemukan di database.")
    result = make_engine().validate(report)
    db.save_findings(conn, report_id, result.findings, result.risk_score, result.recommendation)
    report["risk_score"] = result.risk_score
    report["recommendation"] = result.recommendation
    report["validation_status"] = "validated"
    db.save_report(conn, report)
    return result


def result_from_db(report_id: str, report_row: dict[str, Any] | None = None) -> ValidationResult:
    conn = get_conn()
    finding_dicts = db.load_findings(conn, report_id)
    findings = [ValidationFinding(**item) for item in finding_dicts]
    score = int((report_row or {}).get("risk_score") or 0)
    recommendation = (report_row or {}).get("recommendation") or "Belum divalidasi"
    counts = {severity: 0 for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]}
    for finding in findings:
        if finding.status in {"WARNING", "FAIL"}:
            counts[finding.severity] += 1
    return ValidationResult(findings=findings, risk_score=score, recommendation=recommendation, severity_counts=counts)


def risk_label(score: int) -> str:
    if score <= 20:
        return "Risiko rendah"
    if score <= 40:
        return "Catatan ringan"
    if score <= 60:
        return "Perlu klarifikasi"
    if score <= 80:
        return "Anomali berat"
    return "Sangat berisiko"


def add_sample_data() -> None:
    sample = {
        "company_name": "PT Contoh Validasi Pangan",
        "period": "Triwulan I 2026",
        "submitted_at": "2026-04-15",
        "status": "Diproses",
        "verifier": "Verifikator Contoh",
        "validator": "Validator Contoh",
        "detail_url": "",
        "scraping_status": "sample",
        "identity": {"bidang_usaha": "Industri makanan", "NIB": "1234567890123"},
        "general": {
            "status_berproduksi": "Buka/berproduksi",
            "nama_penanda_tangan": "Budi Santoso",
            "jabatan_penanda_tangan": "Direktur",
            "link_surat_pernyataan": "",
        },
        "sections": {
            "kapasitas": [
                {
                    "produk": "Olahan daging sapi",
                    "KBLI": "10130",
                    "Kode HS": "16025000",
                    "kapasitas_terpasang_standar_kg": "100.000",
                    "kapasitas_produksi_standar_kg": "100.000",
                }
            ],
            "produksi_penjualan": [
                {
                    "produk": "Olahan daging sapi",
                    "KBLI": "10130",
                    "Kode HS": "16025000",
                    "jumlah_dalam_kilogram": "150.000",
                    "nilai_produksi": "Rp. 4.500.000.000",
                }
            ],
            "bahan_baku": [
                {"nama_bahan_baku": "Daging sapi", "jumlah_dalam_kilogram": "5", "nilai_total": "Rp500.000.000"},
                {"nama_bahan_baku": "Daging ayam", "jumlah_dalam_kilogram": "20", "nilai_total": "Rp1.000.000.000"},
            ],
            "air_energi": [{"penggunaan_listrik_kwh": "0", "nilai_listrik": "0", "bahan_bakar_mmbtu": "0"}],
            "tenaga_kerja": [{"total_pekerja": "0"}],
            "persediaan": [{"persediaan_awal": "0", "persediaan_akhir": "0"}],
            "limbah_cair": [{"cod_inlet": "100", "cod_outlet": "180", "debit_limbah_cair_inlet": "20"}],
            "mesin": [{"nama_mesin": "Mixer", "tahun_pembuatan": "2020", "tahun_perolehan": "2019", "negara_pembuat": ""}],
            "indi_4_0": [
                {
                    "pertanyaan": "Strategi digital",
                    "jawaban": "Belum ada strategi tetapi sudah memiliki ERP, server internal, database, dan analisis data.",
                }
            ],
        },
    }
    conn = get_conn()
    report_id = db.save_report(conn, sample)
    validate_report(report_id)


def browser_sidebar() -> None:
    if st.session_state.get("browser_manager_version") != BROWSER_MANAGER_VERSION:
        old_manager = st.session_state.pop("browser_manager", None)
        if old_manager:
            try:
                old_manager.close()
            except Exception:
                pass
        st.session_state["browser_status"] = {"connected": False}
        st.session_state["browser_manager_version"] = BROWSER_MANAGER_VERSION

    st.sidebar.subheader("Browser/Login")
    status = st.session_state.get("browser_status", {"connected": False})
    st.sidebar.write("Status:", "Tersambung" if status.get("connected") else "Belum tersambung")
    if status.get("current_url"):
        st.sidebar.caption(status["current_url"])

    mode_label = st.sidebar.radio(
        "Mode browser",
        ["Launch browser baru dengan persistent profile", "Connect ke Chrome/Edge external"],
        index=0,
    )
    mode = "persistent" if mode_label.startswith("Launch") else "cdp"
    profile_dir = st.sidebar.text_input("Folder profil lokal", str(ROOT / "browser_profiles" / "intranew"))
    cdp_endpoint = st.sidebar.text_input("CDP endpoint", "http://127.0.0.1:9222")

    if st.sidebar.button("Buka IntraNEW", use_container_width=True):
        try:
            manager = BrowserSessionManager(mode=mode, user_data_dir=profile_dir, cdp_endpoint=cdp_endpoint)
            st.session_state["browser_manager"] = manager
            st.session_state["browser_status"] = manager.open(DEFAULT_URL)
            st.sidebar.success("Browser dibuka. Silakan login manual di jendela browser.")
        except Exception as exc:
            st.session_state.pop("browser_manager", None)
            st.sidebar.error(f"Gagal membuka browser: {exc}")

    if st.sidebar.button("Saya sudah login", use_container_width=True):
        manager = st.session_state.get("browser_manager")
        if manager:
            st.session_state["browser_status"] = manager.status()
            st.session_state["login_ready"] = True
            st.sidebar.success("Siap membaca halaman IntraNEW.")
        else:
            st.sidebar.warning("Buka atau connect browser terlebih dahulu.")

    if st.sidebar.button("Refresh session", use_container_width=True):
        manager = st.session_state.get("browser_manager")
        if manager:
            try:
                manager.refresh()
                st.session_state["browser_status"] = manager.status()
                st.sidebar.success("Session di-refresh.")
            except Exception as exc:
                st.sidebar.error(f"Gagal refresh session: {exc}")

    if st.sidebar.button("Ambil daftar laporan", use_container_width=True):
        manager = st.session_state.get("browser_manager")
        if not manager:
            st.sidebar.warning("Browser belum tersambung.")
        else:
            try:
                navigator = IntraNewNavigator(manager, ROOT / "data" / "raw_html", ROOT / "data" / "raw_csv")
                reports, raw_path = navigator.fetch_processed_reports()
                conn = get_conn()
                for report in reports:
                    report["raw_html_path"] = str(raw_path)
                    db.save_report(conn, report)
                st.sidebar.success(f"{len(reports)} laporan terbaca.")
            except Exception as exc:
                st.sidebar.error(f"Gagal mengambil daftar laporan: {exc}")

    st.sidebar.caption('Chrome/Edge external: jalankan `chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\intranew-profile"` lalu pilih mode CDP.')


def load_report_table() -> pd.DataFrame:
    rows = db.list_reports(get_conn())
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "risk_score" in df:
        df["risk_label"] = df["risk_score"].fillna(0).astype(int).map(risk_label)
    return df


def reports_page() -> None:
    st.header("Daftar Laporan Diproses")
    df = load_report_table()
    if df.empty:
        st.info("Belum ada laporan di database lokal. Ambil dari IntraNEW atau muat data contoh untuk mencoba rules.")
        if st.button("Muat data contoh", type="primary"):
            add_sample_data()
            st.rerun()
        return

    company_filter = st.sidebar.text_input("Filter perusahaan")
    period_filter = st.sidebar.text_input("Filter periode")
    filtered = df.copy()
    if company_filter:
        filtered = filtered[filtered["company_name"].str.contains(company_filter, case=False, na=False)]
    if period_filter:
        filtered = filtered[filtered["period"].str.contains(period_filter, case=False, na=False)]

    display_cols = [
        "company_name",
        "period",
        "submitted_at",
        "status",
        "verifier",
        "validator",
        "detail_url",
        "scraping_status",
        "validation_status",
        "risk_score",
        "risk_label",
    ]
    st.dataframe(filtered[[col for col in display_cols if col in filtered.columns]], use_container_width=True, hide_index=True)

    selected = st.selectbox(
        "Pilih laporan",
        filtered["report_id"].tolist(),
        format_func=lambda rid: filtered.loc[filtered["report_id"] == rid, "company_name"].iloc[0],
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Ambil detail terpilih", use_container_width=True):
            manager = st.session_state.get("browser_manager")
            if not manager:
                st.warning("Browser belum tersambung.")
            else:
                try:
                    report = db.load_report(get_conn(), selected)
                    detail = IntraNewNavigator(manager, ROOT / "data" / "raw_html", ROOT / "data" / "raw_csv").scrape_detail(report)
                    db.save_report(get_conn(), detail)
                    st.success("Detail perusahaan tersimpan.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal mengambil detail perusahaan: {exc}")
    with col2:
        if st.button("Ambil semua detail", use_container_width=True):
            manager = st.session_state.get("browser_manager")
            if not manager:
                st.warning("Browser belum tersambung.")
            else:
                try:
                    navigator = IntraNewNavigator(manager, ROOT / "data" / "raw_html", ROOT / "data" / "raw_csv")
                    progress = st.progress(0)
                    for index, report_id in enumerate(filtered["report_id"].tolist(), start=1):
                        report = db.load_report(get_conn(), report_id)
                        if report:
                            db.save_report(get_conn(), navigator.scrape_detail(report))
                        progress.progress(index / len(filtered))
                    st.success("Detail semua laporan yang difilter sudah diambil.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal mengambil semua detail: {exc}")
    with col3:
        if st.button("Jalankan validasi", type="primary", use_container_width=True):
            result = validate_report(selected)
            st.success(f"Validasi selesai. Risk score {result.risk_score}/100.")
            st.rerun()
    with col4:
        if st.button("Validasi semua", use_container_width=True):
            for report_id in filtered["report_id"].tolist():
                validate_report(report_id)
            st.success("Validasi semua laporan selesai.")
            st.rerun()


def plot_small_charts(report: dict[str, Any]) -> None:
    sections = report.get("sections") or {}
    production = pd.DataFrame(sections.get("produksi_penjualan") or [])
    capacity = pd.DataFrame(sections.get("kapasitas") or [])
    material = pd.DataFrame(sections.get("bahan_baku") or [])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("Produksi vs kapasitas")
        if not production.empty or not capacity.empty:
            prod_count = len(production)
            cap_count = len(capacity)
            st.bar_chart(pd.DataFrame({"jumlah_baris": [prod_count, cap_count]}, index=["produksi", "kapasitas"]))
        else:
            st.write("Belum ada data.")
    with col2:
        st.caption("Komposisi bahan baku")
        if not material.empty:
            name_col = next((col for col in material.columns if "nama" in col.lower() or "bahan" in col.lower()), material.columns[0])
            st.bar_chart(material[name_col].value_counts().head(10))
        else:
            st.write("Belum ada data.")
    with col3:
        st.caption("Intensitas energi/air")
        energy_rows = len(sections.get("air_energi") or []) + len(sections.get("energi") or []) + len(sections.get("air") or [])
        st.bar_chart(pd.DataFrame({"jumlah_baris": [energy_rows]}, index=["air/energi"]))


def detail_page() -> None:
    st.header("Detail Validasi")
    df = load_report_table()
    if df.empty:
        st.info("Belum ada laporan.")
        return
    selected = st.selectbox(
        "Pilih perusahaan",
        df["report_id"].tolist(),
        format_func=lambda rid: f"{df.loc[df['report_id'] == rid, 'company_name'].iloc[0]} - {df.loc[df['report_id'] == rid, 'period'].iloc[0]}",
    )
    row = df[df["report_id"] == selected].iloc[0].to_dict()
    report = db.load_report(get_conn(), selected) or {}
    result = result_from_db(selected, row)

    st.subheader(report.get("company_name", "Perusahaan"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk score", f"{result.risk_score}/100", risk_label(result.risk_score))
    col2.metric("Rekomendasi", result.recommendation)
    col3.metric("Total temuan", len([f for f in result.findings if f.status in {"WARNING", "FAIL"}]))
    col4.metric("Critical/High", result.severity_counts.get("CRITICAL", 0) + result.severity_counts.get("HIGH", 0))

    if st.button("Jalankan ulang validasi", type="primary"):
        result = validate_report(selected)
        st.rerun()

    plot_small_charts(report)

    tab_names = [
        "Ringkasan",
        "Identitas dan Perizinan",
        "Investasi",
        "Kapasitas",
        "Produksi & Penjualan",
        "Bahan Baku",
        "Bahan Penolong",
        "Tenaga Kerja",
        "Air & Energi",
        "Pengeluaran",
        "Rencana Produksi",
        "Mesin",
        "Persediaan",
        "Limbah",
        "INDI 4.0",
        "Raw Data",
        "Catatan Validator",
    ]
    tabs = st.tabs(tab_names)
    sections = report.get("sections") or {}
    tab_map = {
        "Investasi": ["investasi"],
        "Kapasitas": ["kapasitas"],
        "Produksi & Penjualan": ["produksi_penjualan"],
        "Bahan Baku": ["bahan_baku"],
        "Bahan Penolong": ["bahan_penolong"],
        "Tenaga Kerja": ["tenaga_kerja", "prakerin"],
        "Air & Energi": ["air_energi", "air", "energi"],
        "Pengeluaran": ["pengeluaran"],
        "Rencana Produksi": ["rencana_produksi"],
        "Mesin": ["mesin"],
        "Persediaan": ["persediaan"],
        "Limbah": ["limbah_padat", "limbah_b3", "limbah_cair"],
        "INDI 4.0": ["indi_4_0"],
    }

    with tabs[0]:
        st.text(generate_summary(report, result))
        st.subheader("Rekomendasi per bagian")
        st.dataframe(pd.DataFrame(section_recommendations_table(result.findings)), use_container_width=True, hide_index=True)
        st.subheader("Tabel validasi")
        st.dataframe(pd.DataFrame(findings_table(result.findings)), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.text_area(
            "Rekomendasi bagian",
            generate_section_recommendation("Identitas dan Perizinan", result.findings),
            height=190,
            key=f"rec_identitas_{selected}",
        )
        st.write("Identitas")
        st.json(report.get("identity") or {})
        st.write("Data umum")
        st.json(report.get("general") or {})

    for tab, name in zip(tabs[2:15], tab_names[2:15]):
        with tab:
            st.text_area(
                "Rekomendasi bagian",
                generate_section_recommendation(name, result.findings),
                height=190,
                key=f"rec_{selected}_{name}",
            )
            keys = tab_map.get(name, [])
            shown = False
            for key in keys:
                rows = sections.get(key) or []
                if rows:
                    st.write(key.replace("_", " ").title())
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    shown = True
            if not shown:
                st.info("Belum ada data terstruktur pada bagian ini.")

    with tabs[15]:
        st.write("Raw HTML:", report.get("raw_html_path") or "-")
        st.write("Raw CSV:")
        for path in report.get("raw_csv_paths", []) or []:
            st.write(path)
        if report.get("parser_warnings"):
            st.warning("\n".join(report["parser_warnings"]))
    with tabs[16]:
        st.text_area(
            "Rekomendasi keseluruhan",
            generate_overall_validator_recommendation(result),
            height=260,
            key=f"overall_rec_{selected}",
        )
        st.text_area("Insight temuan utama", generate_findings_narrative(result), height=300, key=f"main_insight_{selected}")
        note = generate_copy_note(result)
        st.text_area("Catatan yang siap ditempel ke IntraNEW", note, height=160, key=f"copy_note_{selected}")
        col1, col2 = st.columns(2)
        if col1.button("Export Excel", use_container_width=True):
            path = export_report_excel(
                report,
                result.findings,
                result,
                DATA_DIR / "exports" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{selected}.xlsx",
            )
            st.success(f"Excel dibuat: {path}")
        if col2.button("Export HTML", use_container_width=True):
            path = export_html_report(
                report,
                result,
                DATA_DIR / "exports" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{selected}.html",
            )
            st.success(f"HTML dibuat: {path}")


def settings_page() -> None:
    st.header("Pengaturan Rules")
    thresholds = load_yaml(THRESHOLD_PATH, {})
    rows = [{"threshold": key, "value": value} for key, value in thresholds.items()]
    edited = st.data_editor(pd.DataFrame(rows), num_rows="dynamic", use_container_width=True)
    if st.button("Simpan threshold", type="primary"):
        new_thresholds: dict[str, Any] = {}
        for _, row in edited.iterrows():
            key = str(row.get("threshold", "")).strip()
            value = row.get("value")
            if not key:
                continue
            try:
                value = float(value)
                if value.is_integer():
                    value = int(value)
            except (TypeError, ValueError):
                value = str(value)
            new_thresholds[key] = value
        THRESHOLD_PATH.write_text(yaml.safe_dump(new_thresholds, allow_unicode=True, sort_keys=False), encoding="utf-8")
        st.success("Threshold tersimpan.")

    st.subheader("Mapping KBLI/HS")
    if MAPPING_PATH.exists():
        mapping_df = pd.read_csv(MAPPING_PATH).fillna("")
    else:
        mapping_df = pd.DataFrame(columns=["kbli", "keyword", "expected_hs_prefix", "description"])
    edited_mapping = st.data_editor(mapping_df, num_rows="dynamic", use_container_width=True)
    if st.button("Simpan mapping KBLI/HS"):
        edited_mapping.to_csv(MAPPING_PATH, index=False)
        st.success("Mapping tersimpan.")


def main() -> None:
    st.set_page_config(page_title="IntraNEW Validator", layout="wide")
    st.title("IntraNEW Validator")
    st.caption("Aplikasi lokal untuk membantu validasi pelaporan perusahaan. Password tidak disimpan dan data tidak dikirim ke layanan eksternal.")
    DATA_DIR.mkdir(exist_ok=True)
    browser_sidebar()
    page = st.sidebar.radio("Halaman", ["Daftar Laporan", "Detail Validasi", "Pengaturan Rules"])
    if page == "Daftar Laporan":
        reports_page()
    elif page == "Detail Validasi":
        detail_page()
    else:
        settings_page()


if __name__ == "__main__":
    main()
