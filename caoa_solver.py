import pandas as pd
import numpy as np

def run_priority_simulation(voyages_df, port_capacity, priority_vector, return_detailed=False):
    """
    VERSI FINAL: Global Chronological with Virtual Queue Priority.
    
    Args:
        voyages_df: DataFrame input
        port_capacity: Dictionary kapasitas pelabuhan
        priority_vector: Array prioritas (0.0 - 1.0)
        return_detailed (bool): 
            - False: Return float total_lateness (untuk Optimizer)
            - True: Return DataFrame detail (untuk Reporting/Analisis)
    """
    # 1. Setup Data
    sim_df = voyages_df.copy()
    
    # Pastikan format datetime
    if not pd.api.types.is_datetime64_any_dtype(sim_df['ETA_Planned']):
        sim_df['ETA_Planned'] = pd.to_datetime(sim_df['ETA_Planned'])
        
    sim_df['CAOA_Priority'] = priority_vector
    
    # --- LOGIKA PRIORITAS AMAN ---
    max_time_shift_hours = 24.0 
    time_shift = pd.to_timedelta(sim_df['CAOA_Priority'] * max_time_shift_hours, unit='h')
    
    # Waktu Antrean Virtual
    sim_df['Queue_Time'] = sim_df['ETA_Planned'] - time_shift
    
    # URUTKAN GLOBAL BERDASARKAN QUEUE TIME
    sim_df.sort_values(by='Queue_Time', inplace=True)
    
    # 2. STATE MANAGER
    port_state = {p: [pd.Timestamp.min] * cap for p, cap in port_capacity.items()}
    ship_availability = {} 
    
    total_lateness = 0.0
    detailed_results = [] # Penampung data jika return_detailed=True
    
    # 3. PROSES SIMULASI
    for idx, row in sim_df.iterrows():
        ship = row['Ship_Name']
        port = row['Port_Name']
        planned_eta = row['ETA_Planned']
        duration = row['Service_Time_Hours']
        
        # Propagasi Delay
        prev_finish = ship_availability.get(ship, pd.Timestamp.min)
        physical_arrival = max(planned_eta, prev_finish)
        
        # Cek Ketersediaan Dermaga
        berths = port_state.get(port, [pd.Timestamp.min])
        berths.sort()
        free_berth_time = berths[0]
        
        # Waktu Sandar
        berthing_time = max(physical_arrival, free_berth_time)
        
        # Waktu Selesai
        finish_time = berthing_time + pd.to_timedelta(duration, unit='h')
        
        # Hitung Metrics
        lateness_seconds = (berthing_time - planned_eta).total_seconds()
        lateness_hours = max(0.0, lateness_seconds / 3600.0)
        
        total_lateness += lateness_hours
        
        # Update State
        berths[0] = finish_time
        port_state[port] = berths
        ship_availability[ship] = finish_time
        
        # Simpan Detail HANYA jika diminta (untuk menghemat memori saat optimasi)
        if return_detailed:
            waiting_time = (berthing_time - physical_arrival).total_seconds() / 3600.0
            detailed_results.append({
                'Ship_Name': ship,
                'Port_Name': port,
                'ETA_Planned': planned_eta,
                'Optimized_Priority': row['CAOA_Priority'],
                'Queue_Time': row['Queue_Time'],
                'Actual_Arrival': physical_arrival,
                'Actual_Berth': berthing_time,
                'Actual_Departure': finish_time,
                'Delay_Hours': lateness_hours,
                'Waiting_Time_Hours': waiting_time
            })
            
    # RETURN LOGIC
    if return_detailed:
        return pd.DataFrame(detailed_results)
    else:
        return total_lateness