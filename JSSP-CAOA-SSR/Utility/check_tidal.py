import pandas as pd
import re
import os
import glob

def check_timestamp_format(ts):
    """
    Fungsi ketat untuk mengecek format yyyy-mm-dd hh:mm:ss
    """
    if pd.isna(ts):
        return False
    ts = str(ts).strip()
    # Regex untuk memastikan tidak ada karakter ekstra di luar format
    return bool(re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', ts))

def process_tidal_csv(file_path):
    df = pd.read_csv(file_path)
    file_name = os.path.basename(file_path)
    
    print(f"{"="*50}\nMemproses File: {file_name}\n{"="*50}")
    
    # 1. Verifikasi Format Timestamp
    df['is_valid_format'] = df['timestamp'].apply(check_timestamp_format)
    invalid_rows = df[~df['is_valid_format']]
    
    print(f"Total baris: {len(df)}")
    print(f"Baris dengan format waktu INVALID: {len(invalid_rows)}")
    
    if len(invalid_rows) > 0:
        print("CONTOH BARIS INVALID (Mungkin OCR menggabungkan kolom/salah baca):")
        # Menampilkan 5 sampel error teratas
        print(invalid_rows[['timestamp', 'tidal_elevation']].head())
        print("-" * 50)
    
    # 2. Parsing Waktu untuk Perhitungan Bulanan
    # errors='coerce' akan mengubah format yang hancur menjadi NaT
    df['datetime'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Kita hanya menghitung rekapitulasi bulan/hari dari data yang waktunya bisa dipahami
    valid_df = df.dropna(subset=['datetime']).copy()
    valid_df['year_month'] = valid_df['datetime'].dt.to_period('M')
    valid_df['date'] = valid_df['datetime'].dt.date
    
    summary = []
    
    # 3. Ekstraksi Data per Bulan
    for ym, group in valid_df.groupby('year_month'):
        # Pastikan data berurutan secara temporal
        group = group.sort_values('datetime')
        
        # Hitung unik hari yang terekam di bulan tersebut
        days_count = group['date'].nunique()
        
        # Ambil 3 sampel atas dan 3 sampel bawah
        first_3 = group['tidal_elevation'].head(3).tolist()
        last_3 = group['tidal_elevation'].tail(3).tolist()
        
        summary.append({
            'Bulan': str(ym),
            'Jml_Hari_Terparsing': days_count,
            '3_Elevasi_Awal': first_3,
            '3_Elevasi_Akhir': last_3
        })
        
    summary_df = pd.DataFrame(summary)
    print("\nRingkasan Ekstraksi Bulanan:")
    print(summary_df.to_string(index=False))
    print("\n")
    return summary_df, invalid_rows

# ==========================================
# EKSEKUSI PIPELINE UNTUK SEMUA 17 FILE CSV
# ==========================================
if __name__ == "__main__":
    # Ganti path ini dengan folder tempat 17 file CSV kamu berada
    # contoh: folder_path = "data_pasang_surut/*.csv"
    folder_path = "./JSSP-CAOA-SSR/Data/Tidal/*.csv" 
    
    all_files = glob.glob(folder_path)
    
    if not all_files:
        print("Tidak ada file CSV ditemukan di direktori tersebut.")
    else:
        for file in all_files:
            process_tidal_csv(file)