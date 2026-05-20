import streamlit as st
import pandas as pd
import json
import os
from utils.helpers import (
    init_session_state, reset_data, load_css, 
    load_saved_verifications, save_current_progress, load_verification_to_session
)
from utils.generator import generate_return_text, get_nok_summary, process_dynamic_text
from utils.export_docx import create_docx
from utils.export_pdf import create_pdf

st.set_page_config(page_title="Checksheet Verifikasi IMHLP", layout="wide", page_icon="📝")

init_session_state()
load_css()

def parse_excel_to_template(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        jenis_col = [c for c in df.columns if 'Jenis' in str(c)][0]
        item_col = [c for c in df.columns if 'Item' in str(c)][0]
        text_col = [c for c in df.columns if 'Text' in str(c) or 'Autotext' in str(c)][0]
        
        df[jenis_col] = df[jenis_col].ffill()
        
        sections = []
        current_section = None
        sec_counter = 1
        item_counter = 1
        
        for index, row in df.iterrows():
            jenis = str(row[jenis_col]).strip()
            item_label = str(row[item_col]).strip()
            autotext = str(row[text_col]).strip()
            
            if pd.isna(row[item_col]) or item_label == 'nan' or item_label == "":
                continue
                
            if current_section is None or current_section["name"] != jenis:
                current_section = {"id": f"sec_{sec_counter}", "name": jenis, "items": []}
                sections.append(current_section)
                sec_counter += 1
                
            current_section["items"].append({
                "id": f"item_{sec_counter}_{item_counter}",
                "label": item_label,
                "autotext": autotext
            })
            item_counter += 1
            
        return {"sections": sections}
    except Exception as e:
        st.error(f"Gagal membaca format file. Error: {e}")
        return None

if "template" not in st.session_state:
    try:
        with open("data/template_checksheet.json", "r", encoding="utf-8") as f:
            st.session_state["template"] = json.load(f)
    except FileNotFoundError:
        st.session_state["template"] = {"sections": []}

# --- SIDEBAR (HANYA UNTUK PENGATURAN & RIWAYAT) ---
logo_path = os.path.join("assets", "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)

st.sidebar.title("⚙️ Pengaturan Panel")

st.sidebar.markdown("### 🗂️ Riwayat Verifikasi")
saved_db = load_saved_verifications()

if saved_db:
    options = ["-- Pilih Perusahaan --"] + [
        f"{k} - {v['biodata'].get('nama_perusahaan', 'Tanpa Nama')}" for k, v in saved_db.items()
    ]
    selected_history = st.sidebar.selectbox("Lanjutkan Verifikasi:", options)
    
    if selected_history != "-- Pilih Perusahaan --":
        if st.sidebar.button("📂 Muat Data"):
            id_rek = selected_history.split(" - ")[0]
            load_verification_to_session(saved_db[id_rek])
            st.sidebar.success(f"Data ID Rekomendasi: {id_rek} berhasil dimuat!")
            st.rerun()

if st.sidebar.button("💾 Simpan Progress Saat Ini"):
    success, msg = save_current_progress()
    if success:
        st.sidebar.success(msg)
    else:
        st.sidebar.error(msg)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 Pengaturan Template")
uploaded_file = st.sidebar.file_uploader("Upload Excel/CSV Template", type=['xlsx', 'csv'])

if uploaded_file is not None:
    if st.sidebar.button("Gunakan Template Ini"):
        new_template = parse_excel_to_template(uploaded_file)
        if new_template:
            st.session_state["template"] = new_template
            os.makedirs("data", exist_ok=True)
            with open("data/template_checksheet.json", "w", encoding="utf-8") as f:
                json.dump(new_template, f, indent=4, ensure_ascii=False)
            st.sidebar.success("Template berhasil diperbarui!")
            st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Form (Mulai Baru)"):
    reset_data()

# Fungsi pembantu format angka
def input_dengan_format(label, key, is_currency=False):
    val = st.number_input(label, value=float(st.session_state["biodata"].get(key, 0)), step=1000000.0)
    st.session_state["biodata"][key] = val
    formatted_val = f"{int(val):,}".replace(",", ".")
    if is_currency:
        st.caption(f"**Format: Rp {formatted_val}**")
    else:
        st.caption(f"**Format: {formatted_val}**")
    return val


# ================= LAYAR UTAMA (TABS NAVIGATION) =================
st.title("Verifikasi Standar Kegiatan Usaha IMHLP")

tab1, tab2, tab3 = st.tabs(["📋 1. Biodata Umum", "✅ 2. Checksheet Verifikasi", "📄 3. Summary & Export"])

# --- TAB 1: BIODATA UMUM ---
with tab1:
    with st.form("form_biodata"):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["biodata"]["id_rekomendasi"] = st.text_input("ID Rekomendasi (Wajib untuk Save Progress)", st.session_state["biodata"].get("id_rekomendasi", ""))
            st.session_state["biodata"]["nama_perusahaan"] = st.text_input("Nama Perusahaan", st.session_state["biodata"].get("nama_perusahaan", ""))
            st.session_state["biodata"]["lead_verifikator"] = st.text_input("Lead Verifikator", st.session_state["biodata"].get("lead_verifikator", ""))
            st.session_state["biodata"]["kbli"] = st.text_input("KBLI", st.session_state["biodata"].get("kbli", ""))
        with col2:
            st.session_state["biodata"]["jenis_produksi"] = st.text_input("Jenis Produksi", st.session_state["biodata"].get("jenis_produksi", ""))
            st.session_state["biodata"]["satuan"] = st.text_input("Satuan Produksi", st.session_state["biodata"].get("satuan", "Ton/Tahun"))
            input_dengan_format("Kapasitas Produksi", "kapasitas", is_currency=False)
            
        st.subheader("Tabel Nilai Investasi (Rp)")
        i_col1, i_col2, i_col3 = st.columns(3)
        with i_col1:
            input_dengan_format("Investasi Tanah", "inv_tanah", is_currency=True)
            input_dengan_format("Investasi Bangunan", "inv_bangunan", is_currency=True)
        with i_col2:
            input_dengan_format("Mesin Dalam Negeri", "inv_mesin_dn", is_currency=True)
            input_dengan_format("Mesin Impor", "inv_mesin_impor", is_currency=True)
        with i_col3:
            input_dengan_format("Investasi Lainnya", "inv_lainnya", is_currency=True)
            input_dengan_format("Modal Kerja", "modal_kerja", is_currency=True)
            
        submitted = st.form_submit_button("Update Form Biodata")
        if submitted:
            st.success("Biodata direkam. Jangan lupa klik 'Simpan Progress' di sidebar sebelum menutup web.")

# --- TAB 2: CHECKSHEET VERIFIKASI ---
with tab2:
    template = st.session_state.get("template", {"sections": []})
    
    if not template["sections"]:
        st.warning("Belum ada template checksheet. Silakan upload file Excel di sidebar kiri.")
    else:
        total_items, total_nok, _ = get_nok_summary()
        if total_items > 0:
            progress = ((total_items - total_nok) / total_items)
            st.progress(progress, text=f"Progress Kesesuaian: {total_items - total_nok} dari {total_items} Item OK")
        
        for sec in template["sections"]:
            with st.expander(sec["name"], expanded=False):
                for item in sec["items"]:
                    # Ubah urutan rendering kolom agar status widget bisa ditangkap instan
                    col_teks, col_aksi = st.columns([3, 1])
                    
                    with col_aksi:
                        current_val = st.session_state.get(f"status_{item['id']}", "OK")
                        status = st.selectbox(
                            "Hasil",
                            options=["OK", "NOK"],
                            index=0 if current_val == "OK" else 1,
                            key=f"widget_{item['id']}"
                        )
                        # Simpan state secara instan
                        st.session_state[f"status_{item['id']}"] = status
                        
                    with col_teks:
                        st.markdown(f"**{item['label']}**")
                    
                    # Munculkan autotext langsung di bawahnya tanpa perlu refresh jika NOK
                    if status == "NOK":
                        dynamic_text = process_dynamic_text(item['autotext'], st.session_state.get("biodata", {}))
                        st.info(f"📝 *Autotext: {dynamic_text}*")
                        
                st.divider()
                st.session_state[f"note_{sec['id']}"] = st.text_area(
                    "Tambahan Catatan Verifikator (Opsional)",
                    value=st.session_state.get(f"note_{sec['id']}", ""),
                    key=f"widget_note_{sec['id']}"
                )

# --- TAB 3: SUMMARY & EXPORT ---
with tab3:
    total_items, total_nok, nok_list = get_nok_summary()
    
    col_sum1, col_sum2 = st.columns(2)
    col_sum1.metric("Total Item Diverifikasi", total_items)
    col_sum2.metric("Total Item NOK (Perlu Perbaikan)", total_nok, delta_color="inverse")
    
    st.divider()
    st.subheader("Teks Pengembalian (Auto-generated)")
    
    final_text = generate_return_text()
    st.code(final_text, language="markdown")
    
    st.markdown("### 📥 Export Dokumen")
    e_col1, e_col2 = st.columns(2)
    with e_col1:
        docx_file = create_docx()
        st.download_button(label="📄 Download DOCX", data=docx_file, file_name=f"Hasil_{st.session_state['biodata']['nama_perusahaan']}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with e_col2:
        pdf_file = create_pdf()
        st.download_button(label="📕 Download PDF", data=pdf_file, file_name=f"Hasil_{st.session_state['biodata']['nama_perusahaan']}.pdf", mime="application/pdf")