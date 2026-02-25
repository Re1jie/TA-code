import pandas as pd

DATA_PATH = "JSSP-CAOA-SSR/Data/raw_data.csv"
df = pd.read_csv(DATA_PATH)

bulan_map = {
    "Jan": "Jan",
    "Feb": "Feb",
    "Mar": "Mar",
    "Apr": "Apr",
    "Mei": "May",
    "Jun": "Jun",
    "Jul": "Jul",
    "Agu": "Aug",
    "Sep": "Sep",
    "Okt": "Oct",
    "Nov": "Nov",
    "Des": "Dec"
}

def normalize_date(date_str):
    if pd.isna(date_str):
        return None
    
    for indo, eng in bulan_map.items():
        date_str = date_str.replace(indo, eng)
    return date_str

df["ETA_TANGGAL"] = df["ETA_TANGGAL"].apply(normalize_date)

# Build datetime ETA
df["ETA_DATETIME"] = pd.to_datetime(
    df["ETA_TANGGAL"] + " " + df["ETA_JAM"],
    format="%d-%b-%y %H:%M",
    errors="coerce"
)

# Sort kronologis
df = df.sort_values(
    ["NAMA_KAPAL", "ETA_DATETIME"]
).reset_index(drop=True)

# Deteksi batas voyage
results = []

for kapal, kapal_df in df.groupby("NAMA_KAPAL"):

    kapal_df = kapal_df.reset_index(drop=True)

    voyages = kapal_df["VOYAGE"].unique()

    for i in range(len(voyages) - 1):

        v_now = voyages[i]
        v_next = voyages[i + 1]

        df_now = kapal_df[kapal_df["VOYAGE"] == v_now]
        df_next = kapal_df[kapal_df["VOYAGE"] == v_next]

        last_row = df_now.iloc[-1]
        first_row = df_next.iloc[0]

        eta_last = last_row["ETA_DATETIME"]
        eta_next = first_row["ETA_DATETIME"]

        valid = eta_last == eta_next

        results.append({
            "NAMA_KAPAL": kapal,
            "VOYAGE_A": v_now,
            "VOYAGE_B": v_next,
            "ETA_LAST": eta_last,
            "ETA_NEXT": eta_next,
            "VALID": valid
        })

# Export/output
result_df = pd.DataFrame(results)

result_df.to_csv("validasi_voyage.csv", index=False)

print(result_df)