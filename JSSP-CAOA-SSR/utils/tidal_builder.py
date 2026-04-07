import pandas as pd
import numpy as np
import os

def build_sparse_tidal_lookup(rules_csv_path, tidal_data_folder, anchor_date_str='2025-01-01 00:00:00'):
    """
    Membangun Matriks W (Lookup Table) eksklusif secara otomatis menggunakan Numpy Vectorization.
    """
    print("Membangun Tidal Lookup Table...")

    # 1. Baca aturan konstrain (Hanya memproses yang ada aturannya)
    rules_df = pd.read_csv(rules_csv_path)
    anchor_date = pd.to_datetime(anchor_date_str)
    
    global_tidal_lookup = {}
    
    # Kelompokkan aturan berdasarkan Pelabuhan agar kita hanya membaca file CSV pelabuhan 1 kali
    rules_by_port = rules_df.groupby('port_name')
    
    for port, group in rules_by_port:
        file_path = os.path.join(tidal_data_folder, f"{port}.csv")
        
        if not os.path.exists(file_path):
            print(f"[WARNING] File elevasi tidak ditemukan untuk pelabuhan: {port}")
            continue
            
        # 2. Baca data elevasi pasang surut aktual
        tidal_df = pd.read_csv(file_path)
        
        # Perbaikan Anomali 24:00:00 (Sesuai skrip check_tidal.py)
        tidal_df['timestamp_str'] = tidal_df['timestamp'].astype(str).str.replace('24:00:00', '23:59:59', regex=False)
        tidal_df['datetime'] = pd.to_datetime(tidal_df['timestamp_str'], errors='coerce')
        
        # Buang baris yang gagal di-parsing
        tidal_df = tidal_df.dropna(subset=['datetime'])
        
        # 3. Transformasi ke Indeks Waktu (t)
        # Menghitung selisih jam dari anchor date (1 Januari 2025)
        tidal_df['t'] = ((tidal_df['datetime'] - anchor_date).dt.total_seconds() / 3600).apply(np.floor).astype(int)
        
        # Filter hanya t >= 0 (Abaikan data sebelum 1 Jan 2025 jika ada)
        tidal_df = tidal_df[tidal_df['t'] >= 0]
        
        if len(tidal_df) == 0:
            continue
            
        max_t = tidal_df['t'].max()
        
        # 4. Inisialisasi Array Elevasi dengan NaN
        # Ukuran array disesuaikan dengan nilai t maksimum (misal 8760 jam)
        elevations = np.full(max_t + 1, np.nan)
        
        # Masukkan elevasi aktual ke indeks t yang sesuai
        # Hal ini secara otomatis menangani jika ada "waktu yang hilang / lompat"
        valid_t_indices = tidal_df['t'].values
        valid_h_values = tidal_df['tidal_elevation'].values
        elevations[valid_t_indices] = valid_h_values
        
        global_tidal_lookup[port] = {}
        
        # 5. Eksekusi Vektorisasi untuk setiap Kapal di pelabuhan ini
        for _, row in group.iterrows():
            ship_name = row['ship_name']
            e_min = row['E_min']
            e_max = row['E_max']
            
            # KOMPUTASI INTI: Evaluasi Boolean secara instan untuk seluruh tahun
            # Peringatan: Numpy akan menganggap (NaN >= e_min) sebagai False
            # Ini sangat aman! Jika data hilang, kapal tidak diizinkan sandar.
            is_valid_array = (elevations >= e_min) & (elevations <= e_max)
            
            # Simpan array hasil evaluasi ke dalam struktur Sparse Dictionary
            global_tidal_lookup[port][ship_name] = is_valid_array
            
    print("Tidal Lookup Table berhasil dibangun!")
    return global_tidal_lookup