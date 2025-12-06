import numpy as np
import pandas as pd
from caoa_solver import run_priority_simulation  # Wajib ada file caoa_solver.py di folder yang sama

class AdvancedCAOA:
    def __init__(self, data_file, port_file, 
                 pop_size=50, max_iter=100,
                 alpha=0.6, beta=0.8, gamma=0.8, delta=1e-4, initial_energy=100.0):
        """
        Inisialisasi Optimizer CAOA berdasarkan parameter dari file MATLAB.
        Referensi: sensitivity_alpha.m, sensitivity_beta.m, dll.
        """
        
        # --- 1. Load Data Infrastruktur ---
        self.voyages = pd.read_csv(data_file)
        # Pastikan kolom tanggal dibaca sebagai datetime
        self.voyages['ETA_Planned'] = pd.to_datetime(self.voyages['ETA_Planned'])
        
        ports = pd.read_csv(port_file)
        self.port_caps = dict(zip(ports['Nama_Pelabuhan'], ports['Total_Berths']))
        
        # --- 2. Parameter CAOA ---
        self.dim = len(self.voyages) # Dimensi Kromosom = Jumlah Baris Jadwal
        self.pop_size = pop_size
        self.max_iter = max_iter
        
        # Parameter Fisika Buaya (Sesuai sensitivity_*.m)
        self.alpha = alpha   # Attack factor (Kecepatan mengejar Leader)
        self.beta = beta     # Random walk factor (Gangguan/Noise saat bergerak)
        self.gamma = gamma   # Energy consumption rate (Laju kelelahan)
        self.delta = delta   # Improvement threshold (Batas minimal perubahan)
        self.init_energy = initial_energy # Energi awal buaya
        
        # Batas Search Space (Prioritas 0.0 s/d 1.0)
        self.lb = 0.0
        self.ub = 1.0

    def optimize(self):
        # --- 1. Inisialisasi Populasi (Adaptasi initialization.m) ---
        # Posisi awal buaya diacak seragam (Uniform Random)
        population = np.random.uniform(self.lb, self.ub, (self.pop_size, self.dim))
        
        # Inisialisasi Energi Awal
        energies = np.full(self.pop_size, self.init_energy)
        
        # Hitung Fitness Awal (Total Delay)
        print(f"Menghitung fitness awal untuk {self.pop_size} kandidat...")
        fitness = np.array([
            run_priority_simulation(self.voyages, self.port_caps, ind) 
            for ind in population
        ])
        
        # Cari Global Best (gBest) - Minimasi
        best_idx = np.argmin(fitness)
        gBestScore = fitness[best_idx]
        gBestPos = population[best_idx].copy()
        
        print(f"Start Optimization. Initial Best Delay: {gBestScore:.2f} Hours")
        
        # --- 2. Main Loop CAOA (Adaptasi CAOA.m) ---
        for t in range(self.max_iter):
            old_positions = population.copy()
            
            for i in range(self.pop_size):
                # Leader Position adalah Solusi Terbaik saat ini
                leader_position = gBestPos
                
                # --- MOVEMENT EQUATION ---
                # Rumus: X_new = X + alpha*(Leader - X) + beta*(1 - 2*rand)
                r = np.random.random()
                
                # Gerakan Menyerang (Attack) + Gerakan Acak (Random Walk)
                # alpha mengatur seberapa kuat buaya tertarik ke solusi terbaik
                # beta mengatur seberapa liar buaya bergerak (eksplorasi)
                movement = self.alpha * (leader_position - population[i]) + \
                           self.beta * (1.0 - 2.0 * r)
                
                new_pos = population[i] + movement
                
                # Boundary Handling (Pastikan prioritas tetap 0.0 - 1.0)
                new_pos = np.clip(new_pos, self.lb, self.ub)
                
                # Evaluasi Posisi Baru
                new_fit = run_priority_simulation(self.voyages, self.port_caps, new_pos)
                
                # --- GREEDY SELECTION (Minimization) ---
                # Jika solusi baru lebih baik (Delay lebih KECIL), kita ambil.
                if new_fit < fitness[i]:
                    # Cek signifikansi perubahan (Delta)
                    if abs(fitness[i] - new_fit) > self.delta:
                        population[i] = new_pos
                        fitness[i] = new_fit
                        
                        # Update Global Best jika rekor pecah
                        if new_fit < gBestScore:
                            gBestScore = new_fit
                            gBestPos = new_pos.copy()
                            print(f"Iterasi {t+1}: REKOR BARU! Delay turun ke {gBestScore:.2f} Jam")

            # --- ENERGY MECHANISM (Fitur Unik CAOA) ---
            # Hitung jarak perpindahan fisik buaya di iterasi ini
            # Jarak Euclidean: sqrt(sum((x_new - x_old)^2))
            distances = np.sqrt(np.sum((population - old_positions)**2, axis=1))
            
            # Kurangi energi berdasarkan jarak tempuh dan faktor gamma
            # Semakin jauh bergerak, semakin cepat lelah
            energies = energies - (self.gamma * distances)
            
            # Cek buaya yang kehabisan energi (Depleted)
            depleted_indices = np.where(energies <= 0)[0]
            
            if len(depleted_indices) > 0:
                # RESET: Buaya yang lelah akan "respawn" di lokasi acak baru
                # Ini mekanisme anti-stagnasi (agar tidak terjebak di optimum lokal)
                population[depleted_indices] = np.random.uniform(
                    self.lb, self.ub, (len(depleted_indices), self.dim)
                )
                
                # Isi ulang energi penuh
                energies[depleted_indices] = self.init_energy
                
                # Hitung ulang fitness untuk buaya yang baru respawn
                for idx in depleted_indices:
                    fitness[idx] = run_priority_simulation(
                        self.voyages, self.port_caps, population[idx]
                    )
            
            # Logging Progress per 10 Iterasi
            if (t+1) % 10 == 0:
                avg_fit = np.mean(fitness)
                print(f"Iterasi {t+1}/{self.max_iter} | Best: {gBestScore:.2f} h | Avg Pop: {avg_fit:.2f} h | Depleted: {len(depleted_indices)}")

        return gBestPos, gBestScore

# --- BLOCK EKSEKUSI ---
if __name__ == "__main__":
    # Konfigurasi Parameter (Bisa di-tuning sesuai sensitivitas)
    optimizer = AdvancedCAOA(
        data_file='voyage_data_all.csv',  # Pastikan pakai file jadwal yang sudah "dirusak"
        port_file='port_data.csv',           # Pastikan file port sudah di-update berth-nya
        pop_size=50,       # Jumlah buaya
        max_iter=50,      # Lama evolusi
        alpha=0.3,         # Attack speed (0.5 - 0.7 biasanya bagus)
        beta=0.1,          # Random noise (0.1 - 0.3)
        gamma=1.0,        # Energy loss (Semakin besar, semakin sering reset)
        initial_energy=10.0
    )
    
    print("Mulai Optimasi Advanced CAOA...")
    best_prio, min_delay = optimizer.optimize()
    
    print("\n=== HASIL AKHIR ===")
    print(f"Total Delay Minimum: {min_delay:.2f} Jam")
    
    # Simpan Jadwal Optimal
    df_result = optimizer.voyages.copy()
    df_result['Optimized_Priority'] = best_prio
    # Urutkan hasil agar enak dibaca (Per Pelabuhan, lalu Waktu)
    df_result.sort_values(by=['Port_Name', 'ETA_Planned'], inplace=True)
    
    output_filename = 'caoa_final_schedule.csv'
    df_result.to_csv(output_filename, index=False)
    print(f"Jadwal solusi disimpan ke '{output_filename}'")