import pandas as pd
import json
import os
import math

def konversi_csv_ke_json():
    # Pastikan file CSV Anda bernama 'source_template.csv' di folder utama
    file_path = "source_template.csv"
    output_path = "data/template_checksheet.json"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} tidak ditemukan!")
        return
        
    # Membaca CSV (dengan asumsi baris pertama adalah judul kolom: Jenis, Item, Text...)
    # Ganti 'skiprows' jika header aslinya tidak berada di baris pertama
    df = pd.read_csv(file_path)
    
    # Kita asumsikan kolom index 1 = Jenis, index 2 = Item, index 3 = Autotext
    # Forward fill kolom 'Jenis' agar baris kosong di bawahnya terisi nama section yang sama
    df.iloc[:, 1] = df.iloc[:, 1].ffill()
    
    sections = []
    current_section = None
    sec_counter = 1
    item_counter = 1
    
    for index, row in df.iterrows():
        jenis = str(row.iloc[1]).strip()
        item_label = str(row.iloc[2]).strip()
        autotext = str(row.iloc[3]).strip()
        
        # Abaikan baris kosong atau tidak valid
        if pd.isna(row.iloc[2]) or item_label == 'nan' or item_label == "":
            continue
            
        # Jika ketemu "Jenis" baru, buat section baru
        if current_section is None or current_section["name"] != jenis:
            current_section = {
                "id": f"sec_{sec_counter}",
                "name": jenis,
                "items": []
            }
            sections.append(current_section)
            sec_counter += 1
            
        # Tambahkan item ke dalam section
        current_section["items"].append({
            "id": f"item_{sec_counter}_{item_counter}",
            "label": item_label,
            "autotext": autotext
        })
        item_counter += 1

    final_json = {"sections": sections}
    
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)
        
    print(f"Berhasil! JSON template telah dibuat dengan {len(sections)} Kategori/Lampiran.")

if __name__ == "__main__":
    konversi_csv_ke_json()