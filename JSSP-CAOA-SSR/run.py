import time
import numpy as np
import pandas as pd

# Import modul yang sudah Anda miliki
from jssp_model import JSSP_Tardiness_Env
from CAOA import CAOA

def run_solver(csv_path):
    print(f"=== MEMULAI SOLVER JSSP-CAOA ===")
    print(f"Reading Data from: {csv_path}")

    # 1. Inisialisasi Environment
    # Environment akan membaca CSV dan membangun struktur data Job/Operasi
    try:
        env = JSSP_Tardiness_Env(csv_path)
    except FileNotFoundError:
        print(f"ERROR: File tidak ditemukan di {csv_path}")
        return
    
    print(f"\n[Environment Info]")
    print(f"Total Jobs (Kapal) : {len(env.jobs_data)}")
    print(f"Total Mesin (Port) : {env.num_machines}")
    print(f"Total Operasi      : {env.num_ops}")
    print("-" * 50)

    # 2. Definisi Wrapper Fungsi Objektif
    # Fungsi ini menghubungkan output continuous dari CAOA dengan logic diskrit JSSP
    def objective_function(position_vector):
        return env.calculate_total_tardiness(position_vector)

    # 3. Konfigurasi Parameter CAOA
    # Anda bisa tuning parameter ini untuk hasil yang lebih baik
    N_POPULATION = 100       # Jumlah agen (buaya)
    MAX_ITERATION = 1000      # Jumlah iterasi
    DIMENSION = env.num_ops # Dimensi solusi = Jumlah total operasi
    LB = 0.0                # Batas bawah Random Keys
    UB = 1.0                # Batas atas Random Keys

    print(f"\n[Konfigurasi Optimasi]")
    print(f"Populasi         : {N_POPULATION}")
    print(f"Iterasi          : {MAX_ITERATION}")
    print(f"Dimensi Masalah  : {DIMENSION}")
    print(f"Target           : Minimasi Total Tardiness")
    print("-" * 50)

    # 4. Eksekusi CAOA
    print("\n>>> Menjalankan Algoritma CAOA...\n")
    
    best_score, best_pos, convergence_curve = CAOA(
        N=N_POPULATION,
        max_iter=MAX_ITERATION,
        lb=LB,
        ub=UB,
        dim=DIMENSION,
        fobj=objective_function,
        verbose_interval=10 # Update print setiap 10 iterasi
    )

    # 5. Hasil Akhir
    print("\n" + "="*50)
    print("HASIL AKHIR OPTIMASI")
    print("="*50)
    print(f"Minimum Total Tardiness Ditemukan : {best_score:.4f} Jam")
    
    # 6. Decoding Solusi Terbaik (Untuk melihat urutan kapal)
    # Kita urutkan posisi terbaik untuk mendapatkan urutan prioritas job
    best_priority_indices = np.argsort(best_pos)
    best_job_sequence = env.gene_to_job[best_priority_indices]
    
    print("\nUrutan Prioritas Penjadwalan (10 Operasi Pertama):")
    print(best_job_sequence[:10])
    
    # Opsional: Simpan kurva konvergensi ke CSV jika ingin di-plot nanti
    # np.savetxt("convergence_curve.csv", convergence_curve, delimiter=",")
    # print("\nData konvergensi disimpan ke 'convergence_curve.csv'")

if __name__ == "__main__":
    # Path ke file data Anda
    DATA_PATH = "Data/jssp_data.csv"
    
    run_solver(DATA_PATH)