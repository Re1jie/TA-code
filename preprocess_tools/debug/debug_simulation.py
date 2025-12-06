import pandas as pd
import numpy as np
from caoa_solver import run_priority_simulation

# 1. Load Data
print("Memuat data...")
voyages = pd.read_csv('results/caoa_final_schedule.csv')
# voyages = pd.read_csv('voyage_data.csv')
ports = pd.read_csv('port_data.csv')

# --- PERBAIKAN KRUSIAL DI SINI ---
# Ubah kolom ETA_Planned dari String menjadi Datetime
print("Mengonversi format tanggal...")
voyages['ETA_Planned'] = pd.to_datetime(voyages['ETA_Planned'])
# ---------------------------------

caps = dict(zip(ports['Nama_Pelabuhan'], ports['Total_Berths']))

# 2. Buat prioritas dummy (semua 0.5)
dummy_priority = np.full(len(voyages), 0.5)

# 3. Jalankan
print("Menjalankan Test Single Run...")
try:
    delay = run_priority_simulation(voyages, caps, dummy_priority)
    print(f"✅ SUKSES! Total Delay: {delay:.2f} Jam")
except Exception as e:
    print(f"❌ MASIH ERROR: {e}")