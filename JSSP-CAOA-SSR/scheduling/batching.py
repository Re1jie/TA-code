def create_job_batches(df, batch_size=30):
    # 1. Identifikasi Waktu Kedatangan Terdini untuk setiap Job
    # Asumsi: Operation_Seq == 1 adalah operasi kedatangan awal
    first_ops = df[df['Operation_Seq'] == 1].copy()
    
    # 2. Urutkan Job berdasarkan Arrival_Time paling awal
    sorted_jobs = first_ops.sort_values(by='Arrival_Time')['Job_ID'].tolist()
    
    # 3. Pecah menjadi batch (list of lists)
    batches = [sorted_jobs[i:i + batch_size] for i in range(0, len(sorted_jobs), batch_size)]
    
    return batches