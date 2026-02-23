import pandas as pd
import numpy as np

# 1. Load Data
print("Memuat data untuk diagnosa...")
voyages = pd.read_csv('results/caoa_final_schedule.csv')
ports = pd.read_csv('port_data.csv')

# Konversi Tanggal (WAJIB)
voyages['ETA_Planned'] = pd.to_datetime(voyages['ETA_Planned'])

# 2. Setup Sederhana
caps = dict(zip(ports['Nama_Pelabuhan'], ports['Total_Berths']))
port_state = {p: [pd.Timestamp.min] * cap for p, cap in caps.items()}
ship_availability = {} 

# Urutkan
voyages.sort_values(by='ETA_Planned', inplace=True)

# 3. Iterasi untuk cek per baris
results = []
for idx, row in voyages.iterrows():
    ship = row['Ship_Name']
    port = row['Port_Name']
    planned = row['ETA_Planned']
    duration = row['Service_Time_Hours']
    
    # Kapan kapal siap (fisik)
    prev_finish = ship_availability.get(ship, pd.Timestamp.min)
    arrival = max(planned, prev_finish)
    
    # Cek Berth
    berths = port_state.get(port, [pd.Timestamp.min])
    berths.sort()
    free_berth = berths[0]
    
    # Sandar
    berthing = max(arrival, free_berth)
    finish = berthing + pd.to_timedelta(duration, unit='h')
    
    # Hitung Delay Individual
    delay = (berthing - planned).total_seconds() / 3600.0
    
    # Simpan state
    berths[0] = finish
    port_state[port] = berths
    ship_availability[ship] = finish
    
    results.append({
        'Ship': ship,
        'Port': port,
        'ETA': planned,
        'Actual': berthing,
        'Delay_Hours': delay
    })

# 4. Tampilkan Tersangka Utama
df_res = pd.DataFrame(results)
print("\n=== TOP 10 TERSANGKA DELAY ===")
print(df_res.sort_values(by='Delay_Hours', ascending=False).head(10))

# Cek apakah ada tahun aneh
years = df_res['ETA'].dt.year.unique()
print(f"\nTahun yang terdeteksi di data: {years}")