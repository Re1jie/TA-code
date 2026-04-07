import pandas as pd
from utils.tidal_builder import build_sparse_tidal_lookup
from pipeline.sequential_optimizer import run_sequential_optimization
from experiments.config import VOYAGE_DATA,VOYAGE_P1,VOYAGE_P2,VOYAGE_P3,TIDAL_DATA,TIDAL_RULES,PORT_DATA,BATCH_SIZE
from utils.preproc_pipeline import jssp_transform, preprocess_jssp_data, merge_tidal_rules

print("MULAI")

print("Pra-Pemrosesan Data")
jssp_transform(VOYAGE_DATA, VOYAGE_P1)
preprocess_jssp_data(VOYAGE_P1, VOYAGE_P2)
merge_tidal_rules(VOYAGE_P2, TIDAL_RULES, VOYAGE_P3)

print("Pra-Komputasi Matriks Pasang Surut...")
global_tidal_matrix = build_sparse_tidal_lookup(TIDAL_RULES, TIDAL_DATA)

print("Memulai Pipeline Optimasi Sekuensial")
df_voy = pd.read_csv(VOYAGE_P3)
df_port = pd.read_csv(PORT_DATA)
jadwal_optimal_final = run_sequential_optimization(df_voy, global_tidal_matrix, df_port, batch_size=BATCH_SIZE)

print("Menyimpan Hasil Akhir...")
jadwal_optimal_final.to_csv('./data/Jadwal_Optimum_CAOA_Tidal.csv', index=False)

print("SELESAI")