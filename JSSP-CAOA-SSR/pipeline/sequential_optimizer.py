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

# UPDATE: Tambahkan parameter port_data_df
def run_sequential_optimization(df, global_tidal_matrix, port_data_df, batch_size=30):
    batches = create_job_batches(df, batch_size)
    print(f"Total Jobs: {df['job_id'].nunique()}")
    print(f"Total Batches terbentuk: {len(batches)}")
    print("-" * 50)
    
    # KUNCI: Biarkan bernilai None di awal.
    # Batch 1 akan secara otomatis membangun struktur antrean array sesuai kapasitas pelabuhan.
    machine_ready_times = None 
    
    all_schedule_results = []
    
    for batch_idx, job_ids_in_batch in enumerate(batches):
        batch_data = df[df['job_id'].isin(job_ids_in_batch)].copy()

        # UPDATE: Suntikkan port_data_df ke environment
        env = JSSP_Tardiness_Env(batch_data, global_tidal_matrix, port_data_df)
        D = env.num_ops 
        
        def fobj_wrapper(x_continuous_1d):
            return env.calculate_total_tardiness(x_continuous_1d, machine_ready_times)
            
        print(f"Mengoptimasi Batch {batch_idx + 1}/{len(batches)}...")
        best_fitness, best_x_continuous, cg_curve = CAOA(
            dim=D, fobj=fobj_wrapper, **CAOA_CONFIG
        )
        print(f"Batch {batch_idx + 1} Selesai. Keterlambatan Total: {best_fitness:.2f} jam")
        
        batch_schedule_df, updated_machine_times = env.extract_optimized_schedule(
            best_x_continuous, machine_ready_times
        )
        
        all_schedule_results.append(batch_schedule_df)
        
        # RIPPLE EFFECT TRANSFER
        machine_ready_times = updated_machine_times
        
    print("=" * 50)
    print("Seluruh Batch Berhasil Dioptimasi.")
    
    final_master_schedule = pd.concat(all_schedule_results, ignore_index=True)
    return final_master_schedule