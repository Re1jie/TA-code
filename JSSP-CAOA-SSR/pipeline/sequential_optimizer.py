from algorithms.caoa import CAOA
from encoding.rov import generate_lref_per_batch
from encoding.rov import decode_rov_single
from scheduling.batching import create_job_batches
from scheduling.objective import evaluate_schedule_tardiness
from experiments.config import BATCH_SIZE, CAOA_CONFIG
import numpy as np
import pandas as pd

def run_sequential_optimization(df, batch_size=30):
    batches = create_job_batches(df, batch_size)
    print(f"Total Jobs: {df['Job_ID'].nunique()}")
    print(f"Total Batches terbentuk: {len(batches)}")
    print("-" * 50)
    
    # Inisialisasi status mesin (kapan mesin/pelabuhan siap melayani kapal baru)
    # Key: Machine_ID, Value: Waktu penyelesaian operasi terakhir (Completion Time)
    machine_ready_times = {machine_id: 0.0 for machine_id in df['Machine_ID'].unique()}
    
    all_optimized_schedules = []

    for batch_idx, job_ids_in_batch in enumerate(batches):
        # Ekstrak seluruh operasi (secara utuh) untuk Job di dalam batch ini
        batch_data = df[df['Job_ID'].isin(job_ids_in_batch)].copy()

        L_ref_batch = generate_lref_per_batch(batch_data)
        
        # Hitung dimensi pencarian (D) untuk batch ini
        D = len(L_ref_batch)

        print(f"Memproses Batch {batch_idx + 1}/{len(batches)} | Jumlah Job: {len(job_ids_in_batch)} | Dimensi (D): {D}")
        
        # === 1. BUAT FUNGSI OBJEKTIF (fobj) UNTUK BATCH INI ===
        # CAOA memanggil ini dengan vektor kontinu 1D (posisi 1 buaya)
        def fobj_wrapper(x_continuous_1d):
            # A. Translasi Kontinu ke Diskrit (ROV untuk 1 buaya)
            # Karena x_continuous_1d adalah 1D, argsort langsung dipakai
            pi = np.argsort(x_continuous_1d)
            S_sequence = decode_rov_single(x_continuous_1d, L_ref_batch)
            
            # B. Evaluasi Jadwal (Hitung Tardiness)
            fitness_value = evaluate_schedule_tardiness(S_sequence, batch_data, machine_ready_times)
            return fitness_value
            
        # === 2. PANGGIL CAOA ===
        # Sekarang CAOA dieksekusi dengan fobj_wrapper yang sudah mengerti ROV dan JSSP
        best_fitness, best_x_continuous, cg_curve = CAOA(
            dim=D, 
            fobj=fobj_wrapper,
            **CAOA_CONFIG
        )
        
        print(f"Batch {batch_idx + 1} Selesai. Best Tardiness: {best_fitness}")
        
        # === 3. DECODE GLOBAL BEST UNTUK UPDATE STATE MESIN ===
        # Translasi posisi kontinu terbaik kembali ke urutan S
        pi_best = np.argsort(best_x_continuous)
        best_S_sequence = decode_rov_single(best_x_continuous, L_ref_batch)
        
        # ... (Di sini Anda akan menggunakan best_S_sequence untuk menghitung ulang 
        # C_l,j final dan memperbarui machine_ready_times untuk batch berikutnya) ...
        
        updated_machine_times = machine_ready_times.copy() # Update logika ini nanti
        
        # --- TRANSFER STATE KE BATCH BERIKUTNYA ---
        machine_ready_times = updated_machine_times
        
    return machine_ready_times

# Contoh Eksekusi
df = pd.read_csv('./data/preprocessed_transformed_data.csv')
final_machine_states = run_sequential_optimization(df, batch_size=BATCH_SIZE)