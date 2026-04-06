import pandas as pd
import re
import os
import glob

def check_timestamp_format(ts):
    if pd.isna(ts):
        return False
    ts = str(ts).strip()
    # Regex ini mengizinkan angka 24 di bagian jam (karena \d{2}),
    # jadi format stringnya akan dianggap valid oleh fungsi ini.
    return bool(re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', ts))

def process_tidal_csv(file_path):
    df = pd.read_csv(file_path)
    file_name = os.path.basename(file_path)
    
    print(f"{'='*50}\nMemproses File: {file_name}\n{'='*50}")
    
    # 1. Verifikasi Format Timestamp (Secara String)
    df['is_valid_format'] = df['timestamp'].apply(check_timestamp_format)
    invalid_rows = df[~df['is_valid_format']]
    
    print(f"Total baris awal: {len(df)}")
    print(f"Baris dengan format string INVALID: {len(invalid_rows)}")
    
    if len(invalid_rows) > 0:
        print("CONTOH BARIS INVALID:")
        print(invalid_rows[['timestamp', 'tidal_elevation']].head())
        print("-" * 50)
    
    # ==========================================================
    # 2. HACK UNTUK JAM 24:00:00
    # Ubah 24:00:00 menjadi 23:59:59 agar pandas tidak membuangnya,
    # dan agar data tetap tercatat sebagai data terakhir di hari/bulan yang sama.
    # ==========================================================
    # Pastikan timestamp dalam bentuk string
    df['timestamp_str'] = df['timestamp'].astype(str)
    # Replace jam 24 dengan 23:59:59
    df['timestamp_str'] = df['timestamp_str'].str.replace('24:00:00', '23:59:59', regex=False)
    
    # Sekarang lakukan parsing dengan datetime
    df['datetime'] = pd.to_datetime(df['timestamp_str'], errors='coerce')

    anomali_waktu = df[df['datetime'].isna()]
    if len(anomali_waktu) > 0:
        print("\n[PERINGATAN KRITIS] Ditemukan Data Cacat Logika Waktu:")
        # Tampilkan index asli CSV agar kamu tahu persis baris ke berapa yang harus diperbaiki
        print(anomali_waktu[['timestamp', 'tidal_elevation']])
        print("-" * 50)
    
    # Cek berapa banyak data yang HILANG karena gagal konversi ke datetime
    valid_df = df.dropna(subset=['datetime']).copy()
    print(f"Total baris yang berhasil menjadi datetime: {len(valid_df)} (Hilang: {len(df) - len(valid_df)})\n")
    
    # Setelah kamu memiliki valid_df
    valid_df = valid_df.sort_values('datetime').reset_index(drop=True)
    
    # Hitung selisih waktu antar baris
    valid_df['time_diff'] = valid_df['datetime'].diff()
    
    # Karena kita mengubah 24:00:00 menjadi 23:59:59, 
    # selisih wajar maksimum antar baris adalah 1 jam lebih 1 detik (1h 0m 1s).
    # Jika selisihnya lebih dari 65 menit, artinya ADA BARIS YANG HILANG.
    missing_gaps = valid_df[valid_df['time_diff'] > pd.Timedelta(minutes=65)]
    
    if len(missing_gaps) > 0:
        print("\n[PERINGATAN KRITIS] DATA LOMPAT / BARIS HILANG SECARA FISIK:")
        for idx in missing_gaps.index:
            waktu_sebelum = valid_df.loc[idx-1, 'timestamp']
            waktu_setelah = valid_df.loc[idx, 'timestamp']
            selisih_jam = valid_df.loc[idx, 'time_diff']
            print(f"-> Lompat dari {waktu_sebelum} langsung ke {waktu_setelah} (Selisih: {selisih_jam})")
        print("-" * 50)

    duplikat_waktu = valid_df[valid_df.duplicated(subset=['datetime'], keep=False)]
    
    if len(duplikat_waktu) > 0:
        print(f"\n[BAHAYA] Ditemukan {len(duplikat_waktu)} baris dengan timestamp ganda/bentrok:")
        # Menampilkan index asli dari CSV agar kamu bisa langsung mencari barisnya
        print(duplikat_waktu[['timestamp', 'tidal_elevation']])
        print("-" * 50)

    valid_df['year_month'] = valid_df['datetime'].dt.to_period('M')
    valid_df['date'] = valid_df['datetime'].dt.date
    
    summary = []
    
    # 3. Ekstraksi Data per Bulan
    for ym, group in valid_df.groupby('year_month'):
        # Pastikan data berurutan secara temporal
        group = group.sort_values('datetime')
        
        days_count = group['date'].nunique()
        total_jam = len(group)
        
        # Ambil 3 sampel atas dan 3 sampel bawah
        first_3 = group['tidal_elevation'].head(3).tolist()
        last_3 = group['tidal_elevation'].tail(3).tolist()
        
        summary.append({
            'Bulan': str(ym),
            'Jml_Hari': days_count,
            'Total_Jam': total_jam,
            '3_Elevasi_Awal': first_3,
            '3_Elevasi_Akhir': last_3
        })
        
    summary_df = pd.DataFrame(summary)
    print("Ringkasan Ekstraksi Bulanan:")
    print(summary_df.to_string(index=False))
    print("\n")
    return summary_df, invalid_rows

# ==========================================
# EKSEKUSI PIPELINE UNTUK SEMUA 17 FILE CSV
# ==========================================
if __name__ == "__main__":
    folder_path = "./JSSP-CAOA-SSR/Data/Tidal/WAINGAPU.csv"
    all_files = glob.glob(folder_path)
    
    if not all_files:
        print("Tidak ada file CSV ditemukan di direktori tersebut.")
    else:
        for file in all_files:
            process_tidal_csv(file)