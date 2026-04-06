import numpy as np

def evaluate_schedule_tardiness(S_sequence, batch_data, port_registry):
    """
    Fungsi ini membaca urutan diskrit S, mensimulasikan jadwal di pelabuhan, 
    dan mengembalikan nilai skalar Total Tardiness.
    """
    total_tardiness = 0.0
    
    # --- LOGIKA PENJADWALAN SEMI-AKTIF (WIP) ---
    # 1. Loop melalui setiap elemen di S_sequence
    # 2. Cari data waktu kedatangan (A) dan waktu proses (p) di batch_data
    # 3. Cek port_registry untuk ketersediaan pelabuhan
    # 4. Hitung C = max(A, port_ready) + p
    # 5. Tardiness += max(0, C - Due_Date)
    
    # Untuk simulasi agar kode jalan, kita kembalikan nilai dummy
    total_tardiness = float(np.sum(S_sequence * np.arange(len(S_sequence))))
    return total_tardiness