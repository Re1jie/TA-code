import pandas as pd
import numpy as np

def run_priority_simulation(voyages_df, port_capacity, priority_vector):
    """
    VERSI FINAL: Global Chronological with Virtual Queue Priority.
    Menjamin tidak ada bug 'Time Travel' (34 tahun delay).
    """
    # 1. Setup Data
    sim_df = voyages_df.copy()
    
    # Pastikan format datetime
    if not pd.api.types.is_datetime64_any_dtype(sim_df['ETA_Planned']):
        sim_df['ETA_Planned'] = pd.to_datetime(sim_df['ETA_Planned'])
        
    sim_df['CAOA_Priority'] = priority_vector
    
    # --- LOGIKA PRIORITAS AMAN ---
    # Kita buat 'Queue_Time' (Waktu Antrean Virtual).
    # Kapal Prioritas 1.0 akan "dimajukan" waktu antreannya sebanyak 2 JAM.
    # Kapal Prioritas 0.0 tetap di waktu aslinya.
    # Pergeseran kecil ini cukup untuk menyalip antrean, tapi tidak merusak urutan Voyage.
    
    max_time_shift_hours = 24.0 
    time_shift = pd.to_timedelta(sim_df['CAOA_Priority'] * max_time_shift_hours, unit='h')
    
    # Waktu Antrean = ETA Asli - (Prioritas * 2 Jam)
    # Semakin tinggi prioritas, semakin kecil (awal) Queue_Time-nya.
    sim_df['Queue_Time'] = sim_df['ETA_Planned'] - time_shift
    
    # URUTKAN GLOBAL BERDASARKAN QUEUE TIME
    # Ini inti perbaikannya: Kita memproses timeline secara global, bukan per pelabuhan.
    sim_df.sort_values(by='Queue_Time', inplace=True)
    
    # 2. STATE MANAGER
    port_state = {p: [pd.Timestamp.min] * cap for p, cap in port_capacity.items()}
    ship_availability = {} # Kapan kapal selesai dari port sebelumnya
    
    total_lateness = 0.0
    
    # 3. PROSES SIMULASI (Sama persis dengan diagnostic_check, tapi urutannya sudah dimanipulasi prioritas)
    for idx, row in sim_df.iterrows():
        ship = row['Ship_Name']
        port = row['Port_Name']
        planned_eta = row['ETA_Planned'] # Tetap gunakan ETA asli untuk hitung delay
        duration = row['Service_Time_Hours']
        
        # Kapan kapal siap secara fisik? (Tunggu voyage sebelumnya selesai)
        prev_finish = ship_availability.get(ship, pd.Timestamp.min)
        
        # Kapal tiba di lokasi = Max(Jadwal Tiket, Selesai dari Port Lalu)
        physical_arrival = max(planned_eta, prev_finish)
        
        # Cek Ketersediaan Dermaga
        berths = port_state.get(port, [pd.Timestamp.min]) # Default 1 berth
        berths.sort() # [0] adalah berth yang paling cepat kosong
        free_berth_time = berths[0]
        
        # Waktu Sandar = Max(Kapal Tiba, Dermaga Kosong)
        # Di sinilah 'Queue_Time' bekerja. Karena baris ini diproses lebih dulu (akibat sort),
        # kapal prioritas tinggi akan mengambil 'free_berth_time' yang lebih awal.
        berthing_time = max(physical_arrival, free_berth_time)
        
        # Waktu Selesai
        finish_time = berthing_time + pd.to_timedelta(duration, unit='h')
        
        # Hitung Lateness (Keterlambatan dari Jadwal Tiket)
        # Rumus: Waktu Sandar Aktual - ETA Planned
        lateness = (berthing_time - planned_eta).total_seconds() / 3600.0
        
        # Hanya hitung jika positif (terlambat)
        total_lateness += max(0.0, lateness)
        
        # Update State
        berths[0] = finish_time
        port_state[port] = berths
        ship_availability[ship] = finish_time
            
    return total_lateness