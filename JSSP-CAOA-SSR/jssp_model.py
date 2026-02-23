import numpy as np
import pandas as pd

# --- 2. JSSP ENVIRONMENT (MODEL MATEMATIKA) ---
class JSSP_Tardiness_Env:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.num_ops = len(self.df)
        self.num_machines = self.df['Machine_ID'].max()
        
        # Pre-process ke Dictionary untuk kecepatan akses
        self.jobs_data = {}
        for j_id, group in self.df.groupby('Job_ID'):
            self.jobs_data[j_id] = group.sort_values('Operation_Seq').to_dict('records')
            
        # Mapping Decoding (Random Keys)
        self.gene_to_job = []
        for j_id in sorted(self.jobs_data.keys()):
            self.gene_to_job.extend([j_id] * len(self.jobs_data[j_id]))
        self.gene_to_job = np.array(self.gene_to_job)

    def calculate_total_tardiness(self, position_vector):
        # 1. DECODING
        priority_indices = np.argsort(position_vector)
        job_sequence = self.gene_to_job[priority_indices]
        
        # 2. STATE INITIALIZATION
        # machine_free_time: Kapan dermaga kosong?
        machine_free_time = {m: 0.0 for m in range(1, self.num_machines + 5)}
        # job_next_avail_time: Kapan kapal siap (setelah perjalanan dari port sebelumnya)?
        job_next_avail_time = {j: 0.0 for j in self.jobs_data.keys()}
        # Pointer operasi
        job_op_idx = {j: 0 for j in self.jobs_data.keys()}
        
        total_tardiness = 0.0
        
        # 3. SIMULATION LOOP
        for job_id in job_sequence:
            # Ambil data operasi
            op_idx = job_op_idx[job_id]
            op_data = self.jobs_data[job_id][op_idx]
            
            m_id = int(op_data['Machine_ID'])
            p_time = op_data['Proc_Time']
            arr_time = op_data['Arrival_Time']
            due_date = op_data['Due_Date']
            travel_time = op_data['Travel_Time']
            
            # Kapan kapal BISA sandar?
            # Syarat 1: Kapal sudah tiba (Arrival Time or Selesai dari prev port)
            ready_time = max(job_next_avail_time[job_id], arr_time)
            
            # Syarat 2: Dermaga Kosong (Machine Free)
            # Inilah model ANTREAN (Congestion)
            start_time = max(machine_free_time[m_id], ready_time)
            
            # Kapan selesai bongkar muat?
            finish_time = start_time + p_time
            
            # Hitung Dosa (Tardiness)
            tardiness = max(0.0, finish_time - due_date)
            total_tardiness += tardiness
            
            # UPDATE STATE
            machine_free_time[m_id] = finish_time
            
            # Kapal SELALU butuh waktu tempuh ke pelabuhan berikutnya,
            # tidak peduli dia telat atau tidak.
            arrival_at_next_port = finish_time + travel_time
            job_next_avail_time[job_id] = arrival_at_next_port
            
            job_op_idx[job_id] += 1
            
        return total_tardiness