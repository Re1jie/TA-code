import pandas as pd
import re
import os
import datetime

# --- KONFIGURASI INPUT & OUTPUT ---
INPUT_EXCEL_FILE = 'HITUNGAN EMPLOOI 2025 (FIX RILIS).xlsx'
OUTPUT_CSV_FILE = 'Jadwal_Kapal_Final_Fixed.csv'

def clean_ship_name(text):
    """Membersihkan nama kapal dengan penanganan spasi ganda."""
    if not isinstance(text, str): return None
    # Hapus spasi berlebih (misal: "KM  AWU" -> "KM AWU")
    text = re.sub(r'\s+', ' ', text).strip()
    
    match = re.search(r"(KM|KFC)\.?\s*([A-Z\s\.]+)", text, re.IGNORECASE)
    if match:
        name = match.group(2).strip()
        name = name.replace('.', '')
        name = re.sub(r"\s+VOYAGE.*", "", name, flags=re.IGNORECASE)
        return f"KM {name}"
        
    if "VOYAGE" not in text and len(text) > 3 and text.isupper():
         return f"KM {text.strip()}"
    return None

def extract_voyage_id(text):
    if not isinstance(text, str): return None
    match = re.search(r"VOYAGE\s*([\w\.\s\(\)]+)", text, re.IGNORECASE)
    if match:
        raw_voy = match.group(1).strip()
        simple_id = re.search(r"(\d{1,2})[\._](\d{4})", raw_voy)
        if simple_id:
            return f"VOY_{simple_id.group(1).zfill(2)}_{simple_id.group(2)}"
        return f"VOY_{raw_voy.replace(' ', '_').replace('.', '_')}"
    return None

def normalize_date_time(date_val, time_val):
    """Menggabungkan Tanggal dan Jam dengan validasi ketat."""
    if pd.isna(date_val) or pd.isna(time_val):
        return None

    try:
        # 1. Parse Tanggal
        date_obj = pd.to_datetime(date_val, errors='coerce')
        if pd.isna(date_obj): return None
        date_str = date_obj.strftime('%Y-%m-%d')

        # 2. Parse Jam
        t_str = str(time_val).strip()
        time_str = "00:00:00" # Default

        if isinstance(time_val, (datetime.time, datetime.datetime, pd.Timestamp)):
            time_str = time_val.strftime('%H:%M:%S')
        else:
            # Ganti titik dengan titik dua (12.00 -> 12:00)
            t_str = t_str.replace('.', ':')
            # Cek pola HH:MM
            time_match = re.search(r'(\d{1,2})[:](\d{2})', t_str)
            if time_match:
                h, m = time_match.groups()
                time_str = f"{int(h):02d}:{int(m):02d}:00"
            elif t_str.isdigit():
                 time_str = f"{int(t_str):02d}:00:00"
        
        return f"{date_str} {time_str}"
    except:
        return None

def process_single_sheet(df, sheet_name):
    data_rows = []
    current_ship = None
    current_voyage = None
    
    # Infer ship name initial
    if '-' in sheet_name:
        current_ship = f"KM {sheet_name.split('-')[-1].strip()}"
    elif sheet_name.upper() not in ['SHEET1', 'REKAP']:
         current_ship = f"KM {sheet_name.strip()}"

    i = 0
    while i < len(df):
        row_values = df.iloc[i].dropna().astype(str).tolist()
        row_str = " ".join(row_values)
        
        # 1. Metadata Detection
        new_ship = clean_ship_name(row_str)
        if new_ship and len(new_ship) > 4: current_ship = new_ship
        new_voyage = extract_voyage_id(row_str)
        if new_voyage: current_voyage = new_voyage
        
        # 2. Header Detection
        if "PELABUHAN" in row_str.upper() and "NO" in row_str.upper():
            col_map = {}
            header_row = df.iloc[i]
            
            # Helper cari kolom di baris header utama
            def get_col_idx(keyword, row_series):
                for idx, val in row_series.items():
                    if isinstance(val, str) and keyword in val.upper(): return idx
                return None
            
            col_map['no'] = get_col_idx("NO", header_row)
            col_map['port'] = get_col_idx("PELABUHAN", header_row)
            col_map['svc_time'] = get_col_idx("JAM LABUH", header_row) or get_col_idx("LABUH", header_row)
            
            # --- LOGIKA STRICT ETA MAPPING ---
            eta_root_idx = get_col_idx("ETA", header_row)
            has_subheader = False
            
            if i + 1 < len(df):
                subheader_row = df.iloc[i+1]
                subheader_str = " ".join(subheader_row.dropna().astype(str).tolist()).upper()
                
                if "HARI" in subheader_str or "TANGGAL" in subheader_str:
                    has_subheader = True
                    
                    if eta_root_idx is not None:
                        # Kita harus mencari Tanggal dan Jam milik ETA saja.
                        # ETA (Arrival) selalu duluan sebelum ETD (Departure).
                        # Jadi kita cari kolom Tanggal & Jam PERTAMA setelah kolom ETA Header.
                        
                        start_pos = df.columns.get_loc(eta_root_idx)
                        found_date = False
                        found_time = False
                        
                        # Loop hanya 5 kolom ke depan dari posisi ETA
                        for offset in range(5): 
                            if start_pos + offset >= len(df.columns): break
                            
                            curr_col = df.columns[start_pos + offset]
                            val = str(subheader_row[curr_col]).upper()
                            
                            # Ambil Tanggal pertama yang ketemu
                            if "TANGGAL" in val and not found_date:
                                col_map['eta_date'] = curr_col
                                found_date = True
                            
                            # Ambil Jam pertama yang ketemu (STOP setelah ini agar tidak ambil Jam ETD)
                            if "JAM" in val and not found_time:
                                col_map['eta_time'] = curr_col
                                found_time = True
                            
                            # Jika sudah ketemu sepasang, berhenti loop. 
                            # Ini mencegah terambilnya kolom ETD.
                            if found_date and found_time:
                                break

            # 3. Data Extraction Loop
            if col_map.get('no') is not None and col_map.get('port') is not None:
                data_start_idx = i + 2 if has_subheader else i + 1
                
                j = data_start_idx
                while j < len(df):
                    data_row = df.iloc[j]
                    
                    try:
                        no_val = data_row[col_map['no']]
                        if pd.isna(no_val) or str(no_val).strip() == '': break 
                        leg_seq = int(float(no_val))
                    except: break 
                    
                    port_name = data_row[col_map['port']]
                    if pd.isna(port_name): 
                        j += 1; continue
                    
                    svc_time = 0.0
                    if col_map['svc_time'] is not None:
                        try:
                            val = data_row[col_map['svc_time']]
                            svc_time = float(val) if pd.notna(val) else 0.0
                        except: pass
                    
                    # Ambil ETA
                    eta_planned = None
                    if 'eta_date' in col_map and 'eta_time' in col_map:
                        d = data_row[col_map['eta_date']]
                        t = data_row[col_map['eta_time']]
                        eta_planned = normalize_date_time(d, t)

                    if current_ship and current_voyage:
                        data_rows.append({
                            'Ship_Name': current_ship,
                            'Voyage_ID': current_voyage,
                            'Leg_Sequence': leg_seq,
                            'Port_Name': str(port_name).upper().strip(),
                            'ETA_Planned': eta_planned,
                            'Service_Time_Hours': svc_time
                        })
                    
                    j += 1
                i = j - 1 
        i += 1
        
    return data_rows

def main_pipeline():
    print(f"Membaca file Excel: {INPUT_EXCEL_FILE}...")
    if not os.path.exists(INPUT_EXCEL_FILE):
        print("Error: File tidak ditemukan.")
        return

    try:
        xls = pd.read_excel(INPUT_EXCEL_FILE, sheet_name=None, header=None)
    except Exception as e:
        print(f"Error membuka file Excel: {e}")
        return

    all_data = []
    for sheet_name, df in xls.items():
        # Skip sheet rekap/kosong
        if sheet_name.upper() == 'REKAP' or 'SHEET' in sheet_name.upper(): continue
        
        print(f"Memproses Sheet: {sheet_name}")
        rows = process_single_sheet(df, sheet_name)
        if rows: all_data.extend(rows)

    if not all_data:
        print("Tidak ada data yang ditemukan.")
        return

    final_df = pd.DataFrame(all_data)
    
    # Logic Next Port
    print("Menghitung Next Port...")
    def set_next_port(group):
        group['Next_Port'] = group['Port_Name'].shift(-1)
        return group

    final_df = final_df.groupby(['Ship_Name', 'Voyage_ID'], group_keys=False).apply(set_next_port)
    final_df = final_df.sort_values(by=['Ship_Name', 'Voyage_ID', 'Leg_Sequence'])
    
    columns_order = ['Ship_Name', 'Voyage_ID', 'Leg_Sequence', 'Port_Name', 'ETA_Planned', 'Service_Time_Hours', 'Next_Port']
    final_df = final_df[columns_order]

    final_df.to_csv(OUTPUT_CSV_FILE, index=False)
    print(f"\nSukses! Data telah diekspor ke: {OUTPUT_CSV_FILE}")
    print("\nPreview 5 Data Teratas (Cek ETA vs ETD):")
    print(final_df.head(5).to_string())
    print("\nPreview 5 Data Terbawah (Cek Leg Terakhir):")
    print(final_df.tail(5).to_string())

if __name__ == "__main__":
    main_pipeline()