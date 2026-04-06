import numpy as np

def generate_lref_per_batch(batch_data):
    """
    Membangun Reference List (L_ref) secara dinamis untuk satu batch.
    Menggunakan operasi vektorisasi untuk meminimalkan overhead komputasi.
    """
    # 1. Ekstrak urutan unik Job_ID untuk menjaga konsistensi indeks
    unique_jobs = batch_data['Job_ID'].unique()
    
    # 2. Hitung frekuensi (jumlah operasi) tiap Job_ID secara efisien
    # .value_counts() jauh lebih cepat daripada menghitung manual di dalam loop
    ops_count = batch_data['Job_ID'].value_counts(sort=False).to_dict()
    
    # 3. Rakit L_ref
    l_ref_list = []
    for job_id in unique_jobs:
        num_ops = ops_count[job_id]
        # Operasi list extension mengalikan elemen sebanyak num_ops
        l_ref_list.extend([job_id] * num_ops)
        
    return np.array(l_ref_list)

def decode_rov_population(X_population, L_ref_batch):
    """
    Menerjemahkan matriks posisi kontinu CAOA menjadi urutan operasi diskrit
    untuk SELURUH populasi secara simultan.
    
    Parameter:
    - X_population: Matriks NumPy (N, D) -> N buaya, D dimensi (posisi kontinu)
    - L_ref_batch: Array NumPy (D,) -> DNA urutan operasi (Job_ID)
    
    Return:
    - S_population: Matriks NumPy (N, D) -> Permutasi urutan kapal untuk tiap buaya
    """
    
    # 1. PENGURUTAN (SORTING) SIMULTAN
    # Lakukan pengurutan berdasarkan nilai kontinu pada setiap baris (axis=1).
    # Matriks pi akan berisi indeks pengurutan (ranking) untuk setiap buaya.
    # Output pi memiliki dimensi yang sama: (N, D)
    pi = np.argsort(X_population, axis=1)
    
    # 2. PEMETAAN (MAPPING) KE DNA OPERASI
    # Menggunakan fitur Advanced Indexing NumPy.
    # Kita menyuapkan matriks indeks (pi) ke dalam array 1D (L_ref_batch).
    # NumPy secara otomatis memetakan setiap indeks ke nilai Job_ID yang sesuai,
    # menghasilkan matriks jadwal S_population berukuran (N, D) secara instan.
    S_population = L_ref_batch[pi]
    
    return S_population

def decode_rov_single(x, L_ref):
    pi = np.argsort(x)
    return L_ref[pi]