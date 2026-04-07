import numpy as np
import pandas as pd
import math

# --- 1. FUNGSI VALIDATOR PASANG SURUT (DISEMPURNAKAN) ---
def get_valid_arrival_and_departure(earliest_ready, proc_time, buffer_time, port_name, ship_name, tidal_lookup):
    """
    Memisahkan pengecekan Manuver Kedatangan dan Keberangkatan.
    Merepresentasikan idle-time di pelabuhan jika kapal selesai saat air surut.
    """
    # Safety Net: Mencegah OverflowError jika sudah terlanjur inf dari operasi sebelumnya
    if math.isinf(earliest_ready):
        return float('inf'), float('inf')

    # BYPASS 1: Pelabuhan bebas hambatan & Kapal bebas syarat
    if port_name not in tidal_lookup or ship_name not in tidal_lookup[port_name]:
        return earliest_ready, earliest_ready + proc_time
        
    validity_array = tidal_lookup[port_name][ship_name]
    max_t = len(validity_array) - 1
    b_time = int(buffer_time)
    
    # --- TAHAP 1: CARI JENDELA KEDATANGAN YANG AMAN ---
    t_arr = int(math.ceil(earliest_ready))
    while True:
        if t_arr > max_t:
            return earliest_ready, earliest_ready + proc_time
            
        # Cegah negative index (kasus ekstrim kapal datang di t=0 dengan buffer)
        start_idx = max(0, t_arr - b_time)
        
        if all(validity_array[hour] for hour in range(start_idx, t_arr + 1)):
            break
        t_arr += 1
        
    # --- TAHAP 2: CARI JENDELA KEBERANGKATAN YANG AMAN ---
    # Kapal paling cepat selesai di t_arr + proc_time
    t_dep = math.ceil(t_arr + proc_time)
    while True:
        if t_dep + b_time > max_t:
            return earliest_ready, earliest_ready + proc_time
            
        if all(validity_array[hour] for hour in range(int(t_dep), int(t_dep + b_time) + 1)):
            break # Ditemukan waktu keberangkatan aman
        t_dep += 1
        
    return float(t_arr), float(t_dep)


# --- 2. JSSP ENVIRONMENT (MODEL MATEMATIKA) ---
class JSSP_Tardiness_Env:
    # 1. UPDATE INIT: Menerima port_data_df
    def __init__(self, data_source, tidal_matrix, port_data_df):
        if isinstance(data_source, str):
            self.df = pd.read_csv(data_source)
        else:
            self.df = data_source.copy()
            
        self.tidal_matrix = tidal_matrix
        self.num_ops = len(self.df)
        self.num_machines = self.df['m_id'].max()
        
        # --- INTEGRASI DINAMIS PARALLEL MACHINE (total_berths) ---
        # Bersihkan string untuk mencegah gagal matching (hapus spasi, uppercase)
        port_data_df['port_name_clean'] = port_data_df['port_name'].astype(str).str.replace(' ', '').str.upper()
        self.df['port_name_clean'] = self.df['port_name'].astype(str).str.replace(' ', '').str.upper()
        
        # Inisialisasi default 1 dermaga untuk semua Machine ID
        self.port_capacities = {m_id: 1 for m_id in range(1, self.num_machines + 5)}
        
        # Petakan m_id ke jumlah total_berths berdasarkan port_name
        unique_ports = self.df[['m_id', 'port_name_clean']].drop_duplicates()
        for _, row in unique_ports.iterrows():
            m_id = int(row['m_id'])
            p_name = row['port_name_clean']
            matched_port = port_data_df[port_data_df['port_name_clean'] == p_name]
            
            if not matched_port.empty:
                # Ambil nilai total_berths dan jadikan integer
                self.port_capacities[m_id] = int(matched_port['total_berths'].values[0])
        # ---------------------------------------------------------
        
        self.jobs_data = {}
        for j_id, group in self.df.groupby('job_id'):
            self.jobs_data[j_id] = group.sort_values('op_seq').to_dict('records')
            
        self.gene_to_job = []
        for j_id in sorted(self.jobs_data.keys()):
            self.gene_to_job.extend([j_id] * len(self.jobs_data[j_id]))
        self.gene_to_job = np.array(self.gene_to_job)

    # 2. UPDATE EVALUATOR: Memilih dermaga paralel
    def calculate_total_tardiness(self, position_vector, initial_machine_times=None):
        priority_indices = np.argsort(position_vector)
        job_sequence = self.gene_to_job[priority_indices]
        
        # Inisialisasi Antrean Parallel Machine (Bentuk Array/List)
        if initial_machine_times is None:
            machine_free_time = {m: [0.0] * self.port_capacities[m] for m in self.port_capacities}
        else:
            machine_free_time = {m: list(times) for m, times in initial_machine_times.items()}
            
        job_next_avail_time = {j: 0.0 for j in self.jobs_data.keys()}
        job_op_idx = {j: 0 for j in self.jobs_data.keys()}
        
        total_tardiness = 0.0
        
        for job_id in job_sequence:
            op_idx = job_op_idx[job_id]
            op_data = self.jobs_data[job_id][op_idx]
            
            m_id = int(op_data['m_id'])
            p_time = op_data['proc_time']
            arr_time = op_data['arrival_time']
            due_date = op_data['due_date']
            travel_time = op_data['travel_time']
            
            port_name = op_data['port_name']
            ship_name = op_data['ship_name']
            buffer_time = op_data['buffer_time']
            
            # PARALLEL MACHINE LOGIC: Cari dermaga yang kosong paling awal
            earliest_available_dock_time = min(machine_free_time[m_id])
            earliest_dock_index = machine_free_time[m_id].index(earliest_available_dock_time)
            
            ready_time = max(job_next_avail_time[job_id], arr_time)
            earliest_start_time = max(earliest_available_dock_time, ready_time)
            
            start_time, finish_time = get_valid_arrival_and_departure(
                earliest_ready=earliest_start_time, proc_time=p_time, buffer_time=buffer_time,
                port_name=port_name, ship_name=ship_name, tidal_lookup=self.tidal_matrix
            )
            
            if start_time == float('inf'):
                return 1e9 # DEATH PENALTY
            
            tardiness = max(0.0, finish_time - due_date)
            total_tardiness += tardiness
            
            # HANYA UPDATE DERMAGA YANG DIGUNAKAN KAPAL INI
            machine_free_time[m_id][earliest_dock_index] = finish_time
            job_next_avail_time[job_id] = finish_time + travel_time
            job_op_idx[job_id] += 1
            
        return total_tardiness

    def extract_optimized_schedule(self, position_vector, initial_machine_times=None):
        priority_indices = np.argsort(position_vector)
        job_sequence = self.gene_to_job[priority_indices]
        
        # 1. INISIALISASI LIST DERMAGA (Sama persis dengan calculate_total_tardiness)
        if initial_machine_times is None:
            machine_free_time = {m: [0.0] * self.port_capacities[m] for m in self.port_capacities}
        else:
            machine_free_time = {m: list(times) for m, times in initial_machine_times.items()}
            
        job_next_avail_time = {j: 0.0 for j in self.jobs_data.keys()}
        job_op_idx = {j: 0 for j in self.jobs_data.keys()}
        schedule_records = []
        
        for job_id in job_sequence:
            op_idx = job_op_idx[job_id]
            op_data = self.jobs_data[job_id][op_idx]
            
            m_id = int(op_data['m_id'])
            p_time = op_data['proc_time']
            arr_time = op_data['arrival_time']
            due_date = op_data['due_date']
            travel_time = op_data['travel_time']
            
            port_name = op_data['port_name']
            ship_name = op_data['ship_name']
            buffer_time = op_data['buffer_time']
            
            # 2. LOGIKA PARALLEL MACHINE: Cari dermaga kosong
            earliest_available_dock_time = min(machine_free_time[m_id])
            earliest_dock_index = machine_free_time[m_id].index(earliest_available_dock_time)
            
            ready_time = max(job_next_avail_time[job_id], arr_time)
            earliest_start_time = max(earliest_available_dock_time, ready_time)
            
            # 3. VALIDATOR PASANG SURUT
            start_time, finish_time = get_valid_arrival_and_departure(
                earliest_ready=earliest_start_time, proc_time=p_time, buffer_time=buffer_time,
                port_name=port_name, ship_name=ship_name, tidal_lookup=self.tidal_matrix
            )
            
            # Pencegah Overflow saat ekstraksi
            if start_time == float('inf'):
                 start_time, finish_time = earliest_start_time, earliest_start_time + p_time
            
            tardiness = max(0.0, finish_time - due_date)
            
            schedule_records.append({
                'job_id': job_id,
                'ship_name': ship_name,
                'port_name': port_name,
                'm_id': m_id,
                'arrival_ready_time': ready_time,
                'start_time': start_time,
                'idle_docking_time': (finish_time - start_time) - p_time,
                'finish_time': finish_time,
                'tardiness': tardiness
            })
            
            # 4. UPDATE STATUS HANYA PADA DERMAGA YANG TERPAKAI
            machine_free_time[m_id][earliest_dock_index] = finish_time
            job_next_avail_time[job_id] = finish_time + travel_time
            job_op_idx[job_id] += 1
            
        return pd.DataFrame(schedule_records), machine_free_time