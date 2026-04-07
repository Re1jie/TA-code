import pandas as pd
from utils.tidal_builder import build_sparse_tidal_lookup
from pipeline.sequential_optimizer import run_sequential_optimization

print("1. Pra-Komputasi Matriks Pasang Surut...")
aturan_pasang_surut = './data/tidal_rules.csv'
folder_elevasi = './data/tidal'
global_tidal_matrix = build_sparse_tidal_lookup(aturan_pasang_surut, folder_elevasi)

print("2. Memuat Data Jadwal Final...")
df_final = pd.read_csv('./data/preprocessed_transformed_data_FINAL.csv')

print("3. Memulai Pipeline Optimasi Sekuensial...")
# Eksekusi dengan mengirimkan DataFrame utuh dan Matriks W
# Sesuaikan batch_size dengan eksperimen Anda
jadwal_optimal_final = run_sequential_optimization(df_final, global_tidal_matrix, batch_size=30)

print("4. Menyimpan Hasil Akhir...")
jadwal_optimal_final.to_csv('./data/Jadwal_Optimum_CAOA_Tidal.csv', index=False)
print("SELESAI. File tersimpan di ./data/Jadwal_Optimum_CAOA_Tidal.csv")