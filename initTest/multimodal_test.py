import numpy as np
import matplotlib.pyplot as plt
from CAOA import CAOA

# 1. Fungsi Objektif Multimodal: Rastrigin
def rastrigin_function(x):
    d = len(x)
    return 10 * d + np.sum(x**2 - 10 * np.cos(2 * np.pi * x))

# 2. Parameter Setup
N = 50
iterasi = 500          
dim = 10
lb = -5.12
ub = 5.12
interval_log = iterasi // 10  # HARUS integer

print(f"Mulai Simulasi Multimodal (Rastrigin)")
print(f"N={N}, Dim={dim}, Iter={iterasi}")
print("="*50)

# 3. Jalankan Algoritma
score, best_pos, curve = CAOA(
    N, iterasi, lb, ub, dim,
    rastrigin_function,
    verbose_interval=interval_log
)

# 4. Hasil Akhir
print("\n" + "="*50)
print("SIMULASI SELESAI")
print(f"Global Best Score: {score}")
# print(f"Global Best Position: {best_pos}")

# 5. Plot Konvergensi
plt.figure(figsize=(10, 6))
plt.plot(curve)
plt.title(f'Konvergensi CAOA pada Rastrigin (Dim={dim}, N={N})')
plt.xlabel('Iterasi')
plt.ylabel('Fitness')
plt.yscale('log')
plt.grid(True, which="both", alpha=0.5)
plt.savefig("rastrigin_convergence.png")