import streamlit as st
import json
import re

def process_dynamic_text(text, bio):
    """Mengganti keyword dinamis (isian xxxx) dengan Regex yang sangat toleran terhadap typo/kutip/spasi"""
    
    # Ambil nilai dari memori biodata
    try:
        val_inv = float(bio.get('inv_lainnya', 0))
        val_kap = float(bio.get('kapasitas', 0))
        val_mk = float(bio.get('modal_kerja', 0))
        val_mdn = float(bio.get('inv_mesin_dn', 0))
        val_mimp = float(bio.get('inv_mesin_impor', 0))
    except (ValueError, TypeError):
        val_inv, val_kap, val_mk, val_mdn, val_mimp = 0, 0, 0, 0, 0
        
    # Format nominal menjadi ribuan dengan titik
    inv_lainnya_str = f"Rp {int(val_inv):,}".replace(",", ".")
    kapasitas_str = f"{int(val_kap):,}".replace(",", ".") + f" {bio.get('satuan', 'Ton/Tahun')}"
    mk_str = f"Rp {int(val_mk):,}".replace(",", ".")
    mdn_str = f"Rp {int(val_mdn):,}".replace(",", ".")
    mimp_str = f"Rp {int(val_mimp):,}".replace(",", ".")
    
    # --- 1. REPLACE KAPASITAS ---
    text = re.sub(r'"{0,2}isian kapasitas.*?biodata"{0,2}', kapasitas_str, text, flags=re.IGNORECASE)
    text = re.sub(r'"{0,2}isian kapasitas produksi"{0,2}', kapasitas_str, text, flags=re.IGNORECASE)
    text = re.sub(r'"{0,2}isian kapasitas"{0,2}', kapasitas_str, text, flags=re.IGNORECASE)
    
    # --- 2. REPLACE INVESTASI LAINNYA ---
    text = re.sub(r'"{0,2}isian investasi lainnya"{0,2}', inv_lainnya_str, text, flags=re.IGNORECASE)
    
    # --- 3. REPLACE MODAL KERJA ---
    text = re.sub(r'"{0,2}isian modal kerja"{0,2}', mk_str, text, flags=re.IGNORECASE)
    
    # --- 4. REPLACE MESIN DALAM NEGERI & IMPOR ---
    text = re.sub(r'"{0,2}isian investasi mesin dalam negeri"{0,2}', mdn_str, text, flags=re.IGNORECASE)
    text = re.sub(r'"{0,2}isian investasi mesin impor"{0,2}', mimp_str, text, flags=re.IGNORECASE)
    # (Fallback jika penulisan di excel kurang kata 'investasi')
    text = re.sub(r'"{0,2}isian mesin dalam negeri"{0,2}', mdn_str, text, flags=re.IGNORECASE)
    text = re.sub(r'"{0,2}isian mesin impor"{0,2}', mimp_str, text, flags=re.IGNORECASE)
        
    return text

def generate_return_text():
    bio = st.session_state.get("biodata", {})
    template = st.session_state.get("template", {"sections": []})
    
    # Fallback text jika biodata masih kosong
    nama_verifikator = bio.get('lead_verifikator') if bio.get('lead_verifikator') else '[Nama Verifikator]'
    kbli = bio.get('kbli') if bio.get('kbli') else '[KBLI]'
    nama_perusahaan = bio.get('nama_perusahaan') if bio.get('nama_perusahaan') else '[Nama Perusahaan]'

    text = f"Yth. Bapak/Ibu {nama_verifikator},\n\n"
    text += f"Berkenaan dengan permohonan Verifikasi Pemenuhan Standar Kegiatan Usaha KBLI {kbli} "
    text += f"yang diajukan oleh {nama_perusahaan}, dapat kami sampaikan kebutuhan perbaikan dokumen sebagai berikut:\n\n"
    
    ada_nok = False
    
    for sec in template.get("sections", []):
        sec_has_nok = False
        nok_items = []
        
        for item in sec["items"]:
            status = st.session_state.get(f"status_{item['id']}", "OK")
            if status == "NOK":
                sec_has_nok = True
                ada_nok = True
                raw_autotext = item["autotext"]
                dynamic_autotext = process_dynamic_text(raw_autotext, bio)
                nok_items.append(dynamic_autotext)
                
        note = st.session_state.get(f"note_{sec['id']}", "").strip()
        
        if sec_has_nok or note:
            text += f"{sec['name']}\n"
            for nok in nok_items:
                clean_nok = nok.lstrip('- ') 
                text += f"- {clean_nok}\n"
            if note:
                text += f"- Catatan Tambahan: {note}\n"
            text += "\n"
            
    if not ada_nok:
        text += "*(Tidak ada perbaikan dokumen. Seluruh dokumen telah sesuai).* \n"
        
    text += "Demikian disampaikan, atas perhatiannya diucapkan terima kasih."
    return text

def get_nok_summary():
    template = st.session_state.get("template", {"sections": []})
    total_items = 0
    total_nok = 0
    nok_list = []
    
    for sec in template.get("sections", []):
        for item in sec["items"]:
            total_items += 1
            if st.session_state.get(f"status_{item['id']}", "OK") == "NOK":
                total_nok += 1
                nok_list.append(f"{sec['name']} - {item['label']}")
                
    return total_items, total_nok, nok_list