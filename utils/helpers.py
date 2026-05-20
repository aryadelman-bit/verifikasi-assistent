import streamlit as st
import json
import os
from datetime import datetime

# Lokasi penyimpanan history verifikasi
DB_FILE = "data/verifications.json"

def init_session_state():
    if "biodata" not in st.session_state:
        st.session_state["biodata"] = {
            "id_rekomendasi": "", "nama_perusahaan": "", "lead_verifikator": "",
            "kbli": "", "jenis_produksi": "", "kapasitas": 0, "satuan": "Ton/Tahun",
            "inv_tanah": 0, "inv_bangunan": 0, "inv_mesin_dn": 0,
            "inv_mesin_impor": 0, "inv_lainnya": 0, "modal_kerja": 0
        }

def reset_data():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def load_css():
    st.markdown("""
        <style>
            .css-1d391kg { background-color: #f4f6f9; }
            .stButton>button { background-color: #1b3a57; color: white; border-radius: 5px; }
            .stButton>button:hover { background-color: #27527a; color: white; }
            .stExpander { background-color: white; border-radius: 8px; border: 1px solid #e0e0e0; }
            h1, h2, h3 { color: #1b3a57; }
        </style>
    """, unsafe_allow_html=True)

def load_saved_verifications():
    """Membaca data seluruh perusahaan yang pernah disimpan"""
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_current_progress():
    """Menyimpan progress aplikasi ke dalam file DB lokal"""
    bio = st.session_state.get("biodata", {})
    id_rek = bio.get("id_rekomendasi", "").strip()
    
    if not id_rek:
        return False, "⚠️ Gagal! ID Rekomendasi pada Biodata Umum tidak boleh kosong."
        
    db = load_saved_verifications()
    
    # Kumpulkan status OK/NOK dan catatan tambahan dari session_state
    status_data = {}
    note_data = {}
    
    for key, value in st.session_state.items():
        if key.startswith("status_"):
            status_data[key] = value
        elif key.startswith("note_"):
            note_data[key] = value

    # Simpan/update progress perusahaan ini
    db[id_rek] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "biodata": bio,
        "status_data": status_data,
        "note_data": note_data
    }

    os.makedirs("data", exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)
    
    return True, f"✅ Progress '{bio.get('nama_perusahaan')}' berhasil disimpan!"

def load_verification_to_session(data_dict):
    """Memuat data tersimpan kembali ke dalam tampilan checksheet"""
    st.session_state["biodata"] = data_dict.get("biodata", {})
    
    for k, v in data_dict.get("status_data", {}).items():
        # Set nilai logika
        st.session_state[k] = v
        # SINKRONISASI PENTING: Paksa widget UI Streamlit agar mengikuti nilai logika ini
        widget_key = k.replace("status_", "widget_")
        st.session_state[widget_key] = v
        
    for k, v in data_dict.get("note_data", {}).items():
        st.session_state[k] = v
        # Sinkronisasi textarea catatan
        widget_key = k.replace("note_", "widget_note_")
        st.session_state[widget_key] = v