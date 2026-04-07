import pandas as pd

def preprocess_schedule(input_file, output_file):
    df = pd.read_csv(input_file)

    # cari ETD yang 23:59
    mask = df['ETD_JAM'] == '23:59'

    # tambah 1 hari pada tanggalnya
    df.loc[mask, 'ETD_TANGGAL'] = (
        pd.to_datetime(df.loc[mask, 'ETD_TANGGAL'], format='%d-%b-%y', errors='coerce')
        + pd.Timedelta(days=1)
    ).dt.strftime('%d-%b-%y')

    # ubah jam jadi 00:00
    df.loc[mask, 'ETD_JAM'] = '00:00'

    df.to_csv(output_file, index=False)
    return df


if __name__ == "__main__":
    input_file = './data/voyage_data.csv'
    output_file = './data/2359to0000_voyage_data.csv'
    preprocess_schedule(input_file, output_file)