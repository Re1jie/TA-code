import pandas as pd
import os

# --- KONFIGURASI ---
INPUT_CSV = 'voyage_data_all.csv'  # Pastikan ini nama file output dari tahap sebelumnya
OUTPUT_DIR = 'Split_By_Month'        # Folder untuk menyimpan hasil pecahan

def classify_and_split(input_file, output_folder):
    print(f"Membaca data dari: {input_file}...")
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} tidak ditemukan.")
        return

    # 1. Load Data
    df = pd.read_csv(input_file)
    
    # 2. Preprocessing Tanggal
    # Konversi ke datetime objects untuk ekstraksi bulan
    df['ETA_Dt'] = pd.to_datetime(df['ETA_Planned'], errors='coerce')
    
    # Buat kolom bantuan 'Period' (Format: YYYY-MM) untuk setiap baris
    # Baris dengan tanggal kosong akan diabaikan dalam voting
    df['Period'] = df['ETA_Dt'].dt.to_period('M')

    print("Melakukan klasifikasi Majority Voting per Voyage...")

    # 3. Algoritma Majority Voting
    # Fungsi untuk mencari modus (nilai terbanyak) dari bulan dalam satu grup
    def get_majority_period(x):
        # Ambil semua periode valid dalam satu voyage
        periods = x.dropna()
        if periods.empty:
            return "Unknown"
        # Kembalikan periode yang paling sering muncul (Mode)
        # Jika seri, ambil yang pertama
        return periods.mode()[0]

    # Group by Ship & Voyage, lalu cari bulan dominannya
    voyage_majority_map = df.groupby(['Ship_Name', 'Voyage_ID'])['Period'].apply(get_majority_period)
    
    # Ubah hasil mapping menjadi Dictionary untuk mapping balik ke DataFrame utama
    # Contoh: {('KM AWU', 'VOY_01_2025'): Period('2025-01'), ...}
    mapping_dict = voyage_majority_map.to_dict()

    # 4. Terapkan Klasifikasi ke DataFrame Utama
    # Fungsi untuk mapping balik
    def apply_classification(row):
        key = (row['Ship_Name'], row['Voyage_ID'])
        return mapping_dict.get(key, "Unknown")

    df['Classified_Month'] = df.apply(apply_classification, axis=1)

    # 5. Memisahkan File (Splitting)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Membuat folder output: {output_folder}")

    # Ambil daftar bulan unik yang berhasil diklasifikasikan
    unique_months = df['Classified_Month'].unique()

    print(f"\nDitemukan {len(unique_months)} periode bulan berbeda.")
    
    for month in unique_months:
        if str(month) == "Unknown":
            # Handle data yang gagal diklasifikasi (misal voyage tanpa tanggal sama sekali)
            month_str = "Unknown_Date"
            subset = df[df['Classified_Month'] == "Unknown"].copy()
        else:
            # month adalah object Period, kita ubah ke string "YYYY_MM"
            month_str = str(month).replace('-', '_')
            subset = df[df['Classified_Month'] == month].copy()
        
        # Bersihkan kolom bantuan sebelum save
        subset_final = subset.drop(columns=['ETA_Dt', 'Period', 'Classified_Month'])
        
        # Generate nama file
        filename = f"Voyage_Data_{month_str}.csv"
        save_path = os.path.join(output_folder, filename)
        
        # Simpan
        subset_final.to_csv(save_path, index=False)
        print(f"  -> Disimpan: {filename} ({len(subset_final)} baris)")

    print("\nProses selesai.")

if __name__ == "__main__":
    classify_and_split(INPUT_CSV, OUTPUT_DIR)