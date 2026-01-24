import pandas as pd
from datetime import timedelta

def detect_clashes(voyage_file, port_file, output_file='conflict_report.csv'):
    # 1. Load Data
    print("Memuat data...")
    voyages = pd.read_csv(voyage_file)
    ports = pd.read_csv(port_file)
    
    # Konversi format tanggal
    voyages['ETA_Planned'] = pd.to_datetime(voyages['ETA_Planned'])
    
    # Hitung ETD (Estimated Time of Departure) = ETA + Service Time
    # Kita asumsikan Service Time dalam Jam
    voyages['ETD_Planned'] = voyages['ETA_Planned'] + pd.to_timedelta(voyages['Service_Time_Hours'], unit='h')
    
    # Buat Dictionary Kapasitas: {'TANJUNG PRIOK': 5, ...}
    port_caps = dict(zip(ports['Nama_Pelabuhan'], ports['Total_Berths']))
    
    clash_log = []
    
    # 2. Iterasi Per Pelabuhan
    unique_ports = voyages['Port_Name'].unique()
    
    for port in unique_ports:
        # Ambil semua kunjungan ke pelabuhan ini
        visits = voyages[voyages['Port_Name'] == port].copy()
        
        # Ambil kapasitas (Default 1 jika tidak ada di data port)
        cap = port_caps.get(port, 1)
        
        # --- ALGORITMA SWEEP LINE ---
        # Kita ubah setiap kunjungan menjadi 2 event: DATANG (+1) dan PERGI (-1)
        timeline = []
        for idx, row in visits.iterrows():
            timeline.append((row['ETA_Planned'], 1, row['Ship_Name'], row['Voyage_ID']))
            timeline.append((row['ETD_Planned'], -1, row['Ship_Name'], row['Voyage_ID']))
            
        # Urutkan timeline berdasarkan waktu
        timeline.sort(key=lambda x: x[0])
        
        current_occupancy = 0
        active_ships = []
        
        for time_point, change, ship, voy_id in timeline:
            if change == 1: # Kapal Datang
                current_occupancy += 1
                active_ships.append(f"{ship}({voy_id})")
            else: # Kapal Pergi
                current_occupancy -= 1
                if f"{ship}({voy_id})" in active_ships:
                    active_ships.remove(f"{ship}({voy_id})")
            
            # --- CEK KONFLIK ---
            if current_occupancy > cap:
                # KONFLIK TERDETEKSI!
                # Jumlah kapal > Jumlah Berth
                clash_log.append({
                    'Port': port,
                    'Time_Start': time_point,
                    'Occupancy': current_occupancy,
                    'Capacity': cap,
                    'Ships_Involved': " | ".join(active_ships)
                })

    # 3. Simpan Laporan
    if len(clash_log) > 0:
        report_df = pd.DataFrame(clash_log)
        report_df.to_csv(output_file, index=False)
        print(f"\n[BAHAYA] Ditemukan {len(report_df)} titik konflik!")
        print(f"Laporan detail disimpan di: {output_file}")
        
        # Tampilkan preview
        print("\n--- Cuplikan Konflik ---")
        print(report_df[['Port', 'Time_Start', 'Ships_Involved']].head())
        return True # Ada konflik
    else:
        print("\n[AMAN] Tidak ada konflik jadwal yang ditemukan.")
        return False # Tidak ada konflik

if __name__ == "__main__":
    # Jalankan deteksi
    # Pastikan nama file sesuai dengan file CSV Anda
    # has_conflict = detect_clashes('voyage_data.csv', 'port_data.csv')
    has_conflict = detect_clashes('voyage_data_all.csv', 'port_data.csv')