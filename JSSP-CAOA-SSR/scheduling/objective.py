# =============================================================================
# FILE: objective.py
# DESKRIPSI: Decoder jadwal semi-aktif dan Fungsi Evaluasi Keterlambatan (Tardiness).
# =============================================================================
import numpy as np

def evaluate_schedule_tardiness(S_sequence, job_lookup_dict, port_registry):
    """
    Menghitung Total Tardiness dari urutan kapal (S_sequence) dengan mensimulasikan
    pergerakan fisik kapal dari satu pelabuhan ke pelabuhan lain berdasarkan memori antar-batch.
    """
    total_tardiness = 0.0
    
    # --- 1. STATE TRACKERS (PELACAK STATUS) ---
    # Melacak operasi ke-berapa yang sedang dikerjakan setiap kapal (dimulai dari step 1)
    job_step_tracker = {job_id: 1 for job_id in np.unique(S_sequence)}
    
    # Melacak kapan kapal selesai sandar dari pelabuhan sebelumnya (mencegah teleportasi fisik)
    ship_last_completion = {job_id: 0.0 for job_id in np.unique(S_sequence)}
    
    # Salinan memori pelabuhan agar evaluasi CAOA internal tidak menimpa state global secara permanen
    local_port_registry = port_registry.copy()
    
    # --- 2. DEKODE JADWAL (SIMULASI FISIKA PELABUHAN) ---
    for job_id in S_sequence:
        current_step = job_step_tracker[job_id]
        
        # Pengambilan data instan dengan kompleksitas O(1)
        op_data = job_lookup_dict[job_id][current_step]
        machine_id = op_data['machine']
        proc_time = op_data['proc_time']
        static_arrival = op_data['arrival']
        travel_time = op_data['travel']
        
        # A. Hitung Waktu Kedatangan Aktual Kapal (Actual Arrival)
        if current_step == 1:
            # Jika ini pelabuhan pertama, kapal datang sesuai jadwal statis
            actual_arrival = static_arrival
        else:
            # Jika pelabuhan lanjutan, kapal baru bisa tiba setelah selesai di pelabuhan lalu + berlayar
            actual_arrival = max(static_arrival, ship_last_completion[job_id] + travel_time)
            
        # B. Tentukan Waktu Mulai Operasi (Start Time)
        # Kapal hanya bisa bersandar jika ia sudah tiba DAN pelabuhan sudah ditinggalkan kapal lain
        port_ready_time = local_port_registry.get(machine_id, 0.0)
        start_time = max(actual_arrival, port_ready_time)
        
        # C. Hitung Waktu Selesai (Completion Time)
        completion_time = start_time + proc_time
        
        # D. Perbarui Status Fisik Jaringan
        local_port_registry[machine_id] = completion_time
        ship_last_completion[job_id] = completion_time
        job_step_tracker[job_id] += 1
        
        # E. Hitung Penalti Keterlambatan (Tardiness)
        # Sesuai teori JSSP: Keterlambatan dihitung pada operasi terakhir (penyelesaian voyage)
        if current_step == job_lookup_dict[job_id]['max_op']:
            due_date = op_data['due_date']
            tardiness = max(0.0, completion_time - due_date)
            total_tardiness += tardiness
            
    # Mengembalikan fitness value DAN memori pelabuhan yang telah ter-update akibat S_sequence ini
    return total_tardiness, local_port_registry