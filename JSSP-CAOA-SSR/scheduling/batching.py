# =============================================================================
# FILE: batching.py
# DESKRIPSI: Modul untuk memecah dataset operasional kapal menjadi kelompok-kelompok 
#            (batches) berdasarkan waktu kedatangan awal untuk optimasi sekuensial.
# =============================================================================

def create_job_batches(df, batch_size):
    """
    Memecah seluruh Job ke dalam beberapa batch berdasarkan waktu kedatangan terdini.
    Pendekatan ini menjaga agar seluruh operasi dari satu kapal (satu Job_ID)
    tetap berada di dalam ruang optimasi yang sama (tidak terpotong).
    
    Parameter:
    - df (pd.DataFrame): Dataset JSSP yang telah dipraproses.
    - batch_size (int): Jumlah Job unik per batch.
    
    Return:
    - batches (list of lists): Daftar batch, di mana tiap elemen adalah list of Job_ID.
    """
    # 1. Identifikasi Waktu Kedatangan Terdini untuk setiap Job
    # dengan op_seq == 1 merepresentasikan pelabuhan pertama dalam voyage
    first_ops = df[df['op_seq'] == 1].copy()
    
    # 2. Urutkan Job secara kronologis berdasarkan kedatangan pertama (Arrival_Time)
    sorted_jobs = first_ops.sort_values(by='arrival_time')['job_id'].tolist()
    
    # 3. Kelompokkan array Job_ID yang telah diurutkan ke dalam potongan sebesar batch_size
    batches = [sorted_jobs[i:i + batch_size] for i in range(0, len(sorted_jobs), batch_size)]
    
    return batches