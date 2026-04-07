import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import re
import glob
import os

VOYAGE_DATA = './data/voyage_data_2025/voyage_data_0000.csv'
TIDAL_RULES = './data/tidal_rules.csv'

TRANSFORMED = './data/transformed_data.csv'
PREPROCESSED = './data/preprocessed_transformed_data.csv'
FINAL_OUTPUT = './data/preprocessed_transformed_data_with_buffer_time.csv'


# =============================
# STEP 1 — TRANSFORM TO JSSP
# =============================
def jssp_transform(file_path, output_path):
    print(f"[1] Transform: {file_path}")
    df = pd.read_csv(file_path, dtype={'VOYAGE': str})
    
    ID_TO_EN = {
        'Des': 'Dec', 'Mei': 'May', 'Agt': 'Aug',
        'Agu': 'Aug', 'Okt': 'Oct', 'Juli': 'Jul', 'Juni': 'Jun'
    }

    def parse_dt(d, t):
        if pd.isna(d) or pd.isna(t):
            return pd.NaT
        d_str = str(d).strip()
        for id_m, en_m in ID_TO_EN.items():
            d_str = d_str.replace(id_m, en_m)
        try:
            return datetime.strptime(f"{d_str} {str(t).strip()}", "%d-%b-%y %H:%M")
        except:
            return pd.NaT

    df['ETA_FULL'] = df.apply(lambda x: parse_dt(x['ETA_TANGGAL'], x['ETA_JAM']), axis=1)
    df['ETD_FULL'] = df.apply(lambda x: parse_dt(x['ETD_TANGGAL'], x['ETD_JAM']), axis=1)

    df = df.dropna(subset=['ETA_FULL']).sort_values('ETA_FULL')

    # mapping port → machine
    unique_ports = sorted(df['PELABUHAN'].unique())
    port_map = {p: i+1 for i, p in enumerate(unique_ports)}
    df['Machine_ID'] = df['PELABUHAN'].map(port_map)

    df['JOB_KEY'] = df['NAMA_KAPAL'] + "_" + df['VOYAGE']
    unique_jobs = df['JOB_KEY'].unique()
    job_map = {k: i+1 for i, k in enumerate(unique_jobs)}

    global_start = datetime(2025, 1, 1, 0, 0)

    jssp_rows = []

    for job_key, group in df.groupby('JOB_KEY'):
        group = group.sort_values('ETA_FULL')
        records = group.to_dict('records')
        seq = 1

        for i in range(len(records) - 1):
            row = records[i]
            next_row = records[i + 1]

            arr_rel = (row['ETA_FULL'] - global_start).total_seconds() / 3600.0

            if pd.notna(row['ETD_FULL']):
                proc_time = (row['ETD_FULL'] - row['ETA_FULL']).total_seconds() / 3600.0
                due_date_rel = (row['ETD_FULL'] - global_start).total_seconds() / 3600.0
            else:
                proc_time = 0.0
                due_date_rel = arr_rel

            travel_time = 0.0
            if pd.notna(row['ETD_FULL']) and pd.notna(next_row['ETA_FULL']):
                travel_delta = next_row['ETA_FULL'] - row['ETD_FULL']
                travel_time = max(0.0, travel_delta.total_seconds() / 3600.0)

            jssp_rows.append({
                'job_id': job_map[job_key],
                'ship_name': row['NAMA_KAPAL'],
                'voyage': row['VOYAGE'],
                'op_seq': seq,
                'm_id': row['Machine_ID'],
                'port_name': row['PELABUHAN'],
                'travel_time': round(travel_time, 2),
                'arrival_time': round(arr_rel, 2),
                'proc_time': max(0.0, round(proc_time, 2)),
                'due_date': round(due_date_rel, 2),
            })

            seq += 1

    final_df = pd.DataFrame(jssp_rows)
    final_df = final_df.sort_values(by=['job_id', 'op_seq'])
    final_df.to_csv(output_path, index=False)

    print(f"    -> saved {output_path}")


# =============================
# STEP 2 — PREPROCESS
# =============================
def preprocess_jssp_data(input_file, output_file):
    print(f"[2] Preprocess: {input_file}")
    df = pd.read_csv(input_file)
    df = df.sort_values(by=['job_id', 'op_seq']).reset_index(drop=True)

    docking_mask = (df['op_seq'] == 1) & (df['proc_time'] > 100)
    docking_jobs = df[docking_mask]['job_id'].unique()

    print(f"    docking jobs removed: {len(docking_jobs)}")

    df_valid = df[~df['job_id'].isin(docking_jobs)].copy()
    df_valid.to_csv(output_file, index=False)

    print(f"    -> saved {output_file}")


# =============================
# STEP 3 — MERGE TIDAL RULES
# =============================
def merge_tidal_rules(jssp_file, rules_file, output_file):
    print(f"[3] Merge tidal rules")

    df_jadwal = pd.read_csv(jssp_file)
    df_rules = pd.read_csv(rules_file)

    # normalize
    df_jadwal['ship_name'] = df_jadwal['ship_name'].astype(str).str.replace(' ', '').str.upper()
    df_jadwal['port_name'] = df_jadwal['port_name'].astype(str).str.replace(' ', '').str.upper()

    df_rules['ship_name'] = df_rules['ship_name'].astype(str).str.replace(' ', '').str.upper()
    df_rules['port_name'] = df_rules['port_name'].astype(str).str.replace(' ', '').str.upper()

    df_merged = pd.merge(
        df_jadwal,
        df_rules[['port_name', 'ship_name', 'buffer_time']],
        on=['port_name', 'ship_name'],
        how='left'
    )

    df_merged['buffer_time'] = df_merged['buffer_time'].fillna(0).astype(int)

    df_merged.to_csv(output_file, index=False)

    print(f"    -> saved {output_file}")

if __name__ == "__main__":
    print("=== JSSP PIPELINE START ===")

    jssp_transform(VOYAGE_DATA, TRANSFORMED)
    preprocess_jssp_data(TRANSFORMED, PREPROCESSED)
    merge_tidal_rules(PREPROCESSED, TIDAL_RULES, FINAL_OUTPUT)

    print("=== PIPELINE DONE ===")
    print(f"Final output: {FINAL_OUTPUT}")