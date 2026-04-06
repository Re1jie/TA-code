# =============================================================================
# FILE: config.py
# DESKRIPSI: File konfigurasi global untuk parameter eksperimen dan algoritma.
# =============================================================================

# Ukuran batch (jumlah kapal/Job yang diproses secara simultan dalam satu jendela optimasi)
BATCH_SIZE = 15

# Konfigurasi parameter untuk algoritma Crocodile Ambush Optimization Algorithm (CAOA)
CAOA_CONFIG = {
    "N": 30,                # Ukuran populasi (jumlah agen/buaya)
    "max_iter": 300,        # Maksimum iterasi per batch
    "lb": -5.0,             # Batas bawah ruang pencarian kontinu awal
    "ub": 5.0,              # Batas atas ruang pencarian kontinu awal
    "alpha": 0.3,           # Koefisien pergerakan menuju pemimpin (eksploitasi)
    "beta": 0.1,            # Koefisien pergerakan acak (eksplorasi)
    "gamma": 0.1,           # Laju peluruhan energi buaya
    "delta": 1e-3,          # Ambang batas (threshold) toleransi memburuknya fitness sebelum di-reset
    "initial_energy": 10.0, # Energi awal setiap agen buaya
}