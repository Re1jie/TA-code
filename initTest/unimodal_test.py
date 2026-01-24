import numpy as np
import matplotlib.pyplot as plt
from CAOA import CAOA
# from CAOASSR import CAOA_SSR

# 1. Definisi Fungsi Objektif
def sphere_function(x):
    return np.sum(x**2)

# 2. Parameter Setup
N = 50            
iterasi = 100 
dim = 10             
lb = -100
ub = 100
interval_log = iterasi / 10

print(f"Mulai Simulasi: N={N}, Dim={dim}, Iter={iterasi}")
print("="*50)

# 3. Jalankan Algoritma (Pass parameter verbose_interval)
score, best_pos, curve = CAOA(N, iterasi, lb, ub, dim, sphere_function, verbose_interval=interval_log)

# 4. Tampilkan Hasil Akhir
print("\n" + "="*50)
print(f"SIMULASI SELESAI.")
print(f"Global Best Score: {score}")
# print(f"Global Best Position: {best_pos}") # Optional: Mungkin terlalu panjang diprint

# 5. Simpan Grafik
plt.figure(figsize=(10, 6))
plt.plot(curve)
plt.title(f'Konvergensi Algoritma (Dim={dim}, N={N})')
plt.xlabel('Iterasi')
plt.ylabel('Fitness Logaritma')
plt.yscale('log') # Gunakan skala log agar grafik lebih informatif
plt.grid(True, which="both", ls="-", alpha=0.5)
plt.savefig("unimodal_convergence.png")