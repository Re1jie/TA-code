# =============================================================================
# FILE: fifo_baseline.py
# DESKRIPSI: Baseline Pembanding menggunakan aturan Greedy FCFS/FIFO. 
#            Metode ini mengabaikan CAOA dan mengurutkan kapal 100% berdasarkan waktu kedatangan.
# =============================================================================
import pandas as pd
import numpy as np
from scheduling.batching import create_job_batches
from scheduling.objective import evaluate_schedule_tardiness

def run_fifo_baseline(df, batch_size=30):
    batches = create_job_batches(df, batch_size)
    machine_ready_times = {machine_id: 0.0 for machine_id in df['Machine_ID'].unique()}
    cumulative_tardiness = 0.0

    for batch_idx, job_ids_in_batch in enumerate(batches):
        batch_data = df[df['Job_ID'].isin(job_ids_in_batch)].copy()

        # Prakomputasi kamus yang identik dengan pipeline CAOA
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
            job_lookup_dict[j_id]['max_op'] = max(job_lookup_dict[j_id]['max_op'], o_seq)

        # LOGIKA FIFO: Mengurutkan jadwal murni berdasarkan waktu tiba di data historis
        fifo_S_sequence = batch_data.sort_values(by='Arrival_Time')['Job_ID'].values
        
        # Mengevaluasi keterlambatan menggunakan mesin decoder JSSP yang sama
        batch_tardiness, updated_machine_times = evaluate_schedule_tardiness(
            fifo_S_sequence, 
            job_lookup_dict, 
            machine_ready_times
        )
        
        machine_ready_times = updated_machine_times
        cumulative_tardiness += batch_tardiness
        
        print(f"Batch {batch_idx + 1:<2} | Tardiness Batch Ini: {batch_tardiness:<10.2f} | Kumulatif: {cumulative_tardiness:.2f}")
        
    print(f"Total keterlambatan metode FIFO: {cumulative_tardiness:.2f} Jam")
    return cumulative_tardiness

if __name__ == "__main__":
    df = pd.read_csv('./data/preprocessed_transformed_data.csv')
    run_fifo_baseline(df, batch_size=15)