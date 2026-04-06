# =============================================================================
# FILE: rov.py
# DESKRIPSI: Implementasi Mekanisme Representasi Solusi (Encoding) menggunakan 
#            Ranked Order Value (ROV) dan Pembangkitan Reference List dinamis.
# =============================================================================
import numpy as np

def generate_lref_per_batch(batch_data):
    """
    Membangun Reference List (L_ref) secara dinamis untuk satu batch spesifik.
    L_ref adalah "DNA" penjadwalan (contoh: [1, 1, 1, 2, 2, 3, ...]) yang merepresentasikan
    jumlah operasi yang dimiliki setiap kapal di batch tersebut.
    """
    # Ekstrak urutan unik Job_ID untuk menjaga konsistensi indeks pemetaan
    unique_jobs = batch_data['Job_ID'].unique()
    
    # Hitung jumlah operasi untuk setiap kapal menggunakan dictionary O(1) lookup
    ops_count = batch_data['Job_ID'].value_counts(sort=False).to_dict()
    
    l_ref_list = []
    for job_id in unique_jobs:
        num_ops = ops_count[job_id]
        # Duplikasi Job_ID sebanyak jumlah operasinya
        l_ref_list.extend([job_id] * num_ops)
        
    return np.array(l_ref_list)

def decode_rov_population(X_population, L_ref_batch):
    """
    [TIDAK DIGUNAKAN DI SINGLE EVALUATION, TAPI DISIMPAN UNTUK VEKTORISASI KELAK]
    Menerjemahkan matriks kontinu menjadi permutasi diskrit untuk seluruh populasi.
    """
    pi = np.argsort(X_population, axis=1)
    S_population = L_ref_batch[pi]
    return S_population

def decode_rov_single(x, L_ref):
    """
    Menerjemahkan vektor posisi kontinu tunggal (1 agen buaya) menjadi urutan 
    operasi kapal menggunakan metode argsort (ROV).
    
    Parameter:
    - x (np.array 1D): Vektor posisi dari CAOA.
    - L_ref (np.array 1D): Reference list batch saat ini.
    
    Return:
    - np.array 1D: Permutasi urutan kapal (S_sequence).
    """
    pi = np.argsort(x)
    return L_ref[pi]