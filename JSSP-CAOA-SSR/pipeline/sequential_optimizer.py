# =============================================================================
# FILE: sequential_optimizer.py
# DESKRIPSI: Pipeline pengoptimalan batch-sekuensial. Merakit O(1) Dictionary
#            dan mengelola transfer memori state pelabuhan (Ripple Effect).
# =============================================================================
import numpy as np
import pandas as pd
from algorithms.caoa import CAOA
from scheduling.batching import create_job_batches
from utils.jssp_model import JSSP_Tardiness_Env
from experiments.config import CAOA_CONFIG

def run_sequential_optimization(df, global_tidal_matrix, batch_size=30):
    batches = create_job_batches(df, batch_size)
    print(f"Total Jobs: {df['job_id'].nunique()}")
    print(f"Total Batches terbentuk: {len(batches)}")
    print("-" * 50)
    
    # 1. Inisialisasi Memori Global (Ripple Effect State)
    # Memastikan tidak ada KeyError, default ke 0.0
    all_machines = df['m_id'].unique()
    machine_ready_times = {m_id: 0.0 for m_id in all_machines}
    
    all_schedule_results = []
    
    for batch_idx, job_ids_in_batch in enumerate(batches):
        batch_data = df[df['job_id'].isin(job_ids_in_batch)].copy()

        # 2. Inisialisasi Environment HANYA untuk Batch Ini
        env = JSSP_Tardiness_Env(batch_data, global_tidal_matrix)
        D = env.num_ops # Dimensi dinamis = jumlah total operasi dalam batch
        
        # 3. Wrapper untuk fungsi objektif CAOA
        def fobj_wrapper(x_continuous_1d):
            # Pass array kontinu dan status antrean pelabuhan terbaru
            return env.calculate_total_tardiness(x_continuous_1d, machine_ready_times)
            
        # 4. Panggil algoritma pengoptimalan CAOA
        print(f"Mengoptimasi Batch {batch_idx + 1}/{len(batches)}...")
        best_fitness, best_x_continuous, cg_curve = CAOA(
            dim=D, 
            fobj=fobj_wrapper,
            **CAOA_CONFIG
        )
        print(f"Batch {batch_idx + 1} Selesai. Keterlambatan Total: {best_fitness:.2f} jam")
        
        # 5. Ekstraksi Jadwal Terbaik & Transfer State
        batch_schedule_df, updated_machine_times = env.extract_optimized_schedule(
            best_x_continuous, 
            machine_ready_times
        )
        
        # Gabungkan data jadwal ke master list
        all_schedule_results.append(batch_schedule_df)
        
        # KUNCI UTAMA: Update memori global dengan waktu terbaru agar batch selanjutnya mengantre
        machine_ready_times = updated_machine_times
        
    print("=" * 50)
    print("Seluruh Batch Berhasil Dioptimasi.")
    
    # Menggabungkan seluruh batch menjadi 1 DataFrame final
    final_master_schedule = pd.concat(all_schedule_results, ignore_index=True)
    return final_master_schedule