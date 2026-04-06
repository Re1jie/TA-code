# =============================================================================
# FILE: sequential_optimizer.py
# DESKRIPSI: Pipeline pengoptimalan batch-sekuensial. Merakit O(1) Dictionary
#            dan mengelola transfer memori state pelabuhan (Ripple Effect).
# =============================================================================
import numpy as np
import pandas as pd
from algorithms.caoa import CAOA
from encoding.rov import generate_lref_per_batch, decode_rov_single
from scheduling.batching import create_job_batches
from scheduling.objective import evaluate_schedule_tardiness
from experiments.config import BATCH_SIZE, CAOA_CONFIG

def run_sequential_optimization(df, batch_size=30):
    batches = create_job_batches(df, batch_size)
    print(f"Total Jobs: {df['Job_ID'].nunique()}")
    print(f"Total Batches terbentuk: {len(batches)}")
    print("-" * 50)
    
    # Memori Global State: Menyimpan waktu kapan setiap pelabuhan siap melayani kapal baru
    machine_ready_times = {machine_id: 0.0 for machine_id in df['Machine_ID'].unique()}
    
    for batch_idx, job_ids_in_batch in enumerate(batches):
        batch_data = df[df['Job_ID'].isin(job_ids_in_batch)].copy()

        # Inisialisasi arsitektur translasi (DNA kromosom) untuk batch ini
        L_ref_batch = generate_lref_per_batch(batch_data)
        D = len(L_ref_batch) # Dimensi yang dinamis

        # === PRAKOMPUTASI: PEMBUATAN KAMUS O(1) LOOKUP ===
        # Mengubah Pandas DataFrame yang lambat menjadi nested dict murni agar
        # proses pemanggilan data di dalam jutaan iterasi JSSP berjalan instan.
        job_lookup_dict = {}
        for _, row in batch_data.iterrows():
            j_id = int(row['Job_ID'])
            o_seq = int(row['Operation_Seq'])
            
            if j_id not in job_lookup_dict:
                job_lookup_dict[j_id] = {'max_op': 0}
                
            job_lookup_dict[j_id][o_seq] = {
                'machine': int(row['Machine_ID']),
                'proc_time': float(row['Proc_Time']),
                'arrival': float(row['Arrival_Time']),
                'travel': float(row['Travel_Time']),
                'due_date': float(row['Due_Date'])
            }
            # Lacak total operasi untuk mengetahui pemicu perhitungan Tardiness
            job_lookup_dict[j_id]['max_op'] = max(job_lookup_dict[j_id]['max_op'], o_seq)

        print(f"Memproses Batch {batch_idx + 1}/{len(batches)} | Jumlah Job: {len(job_ids_in_batch)} | Dimensi (D): {D}")
        
        # === BUNGKUSAN FUNGSI OBJEKTIF (WRAPPER) ===
        def fobj_wrapper(x_continuous_1d):
            # Mengubah array probabilitas menjadi jadwal fisik
            S_sequence = decode_rov_single(x_continuous_1d, L_ref_batch)
            # Mengevaluasi simulasi jadwal dengan meneruskan memori machine_ready_times
            fitness_value, _ = evaluate_schedule_tardiness(S_sequence, job_lookup_dict, machine_ready_times)
            return fitness_value
            
        # Panggil algoritma pengoptimalan CAOA
        best_fitness, best_x_continuous, cg_curve = CAOA(
            dim=D, 
            fobj=fobj_wrapper,
            **CAOA_CONFIG
        )
        print(f"Batch {batch_idx + 1} Selesai. Best Tardiness: {best_fitness}")
        
        # === DEKODE DAN PENGUNCIAN GLOBAL BEST ===
        # Eksekusi ulang solusi terbaik untuk mengamankan status akhir pelabuhannya
        best_S_sequence = decode_rov_single(best_x_continuous, L_ref_batch)
        final_tardiness, updated_machine_times = evaluate_schedule_tardiness(
            best_S_sequence, 
            job_lookup_dict, 
            machine_ready_times
        )
        
        # TRANSFER STATE ANTAR-BATCH: Mengunci efek riak ke batch selanjutnya
        machine_ready_times = updated_machine_times
        
    return machine_ready_times

if __name__ == "__main__":
    df = pd.read_csv('./data/preprocessed_transformed_data.csv')
    final_machine_states = run_sequential_optimization(df, batch_size=BATCH_SIZE)