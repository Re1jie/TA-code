import plotly.express as px
import pandas as pd
import re
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# =====================================================
# INIT DASH APP (HARUS PALING ATAS)
# =====================================================
app = Dash(__name__)

# =====================================================
# LOAD DATA
# =====================================================
DATA_INPUT = '/home/re1jie/TA-code/JSSP-CAOA-SSR/Data/raw_data.csv'
df = pd.read_csv(DATA_INPUT)

# =====================================================
# NORMALISASI BULAN
# =====================================================
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

pattern = re.compile("|".join(bulan_map.keys()))

def normalize_date(date_str):
    if pd.isna(date_str):
        return None
    return pattern.sub(lambda x: bulan_map[x.group()], str(date_str))

df["ETA_TANGGAL"] = df["ETA_TANGGAL"].apply(normalize_date)
df["ETD_TANGGAL"] = df["ETD_TANGGAL"].apply(normalize_date)

# =====================================================
# BUILD DATETIME
# =====================================================
df["ETA"] = pd.to_datetime(
    df["ETA_TANGGAL"] + " " + df["ETA_JAM"],
    format="%d-%b-%y %H:%M",
    errors="coerce"
)

df["ETD"] = pd.to_datetime(
    df["ETD_TANGGAL"] + " " + df["ETD_JAM"],
    format="%d-%b-%y %H:%M",
    errors="coerce"
)

df = df.sort_values(["NAMA_KAPAL", "ETA"])

# isi ETD kosong pakai ETA berikutnya
df["ETD"] = df["ETD"].fillna(
    df.groupby("NAMA_KAPAL")["ETA"].shift(-1)
)

df = df.reset_index(drop=True)

df["NEXT_ETA"] = df.groupby("NAMA_KAPAL")["ETA"].shift(-1)

# =====================================================
# BUILD TIMELINE
# =====================================================
sandar = df.copy()
sandar["START"] = sandar["ETA"]
sandar["END"] = sandar["ETD"]
sandar["STATUS"] = "Sandar"

layar = df.copy()
layar["START"] = layar["ETD"]
layar["END"] = layar["NEXT_ETA"]
layar["STATUS"] = "Layar"

layar = layar.dropna(subset=["START", "END"])

timeline = pd.concat([sandar, layar], ignore_index=True)
timeline = timeline[timeline["END"] > timeline["START"]]

# =====================================================
# FIGURE BUILDER (JANGAN GLOBAL FIGURE)
# =====================================================
def build_figure(data):

    fig = px.timeline(
        data,
        x_start="START",
        x_end="END",
        y="NAMA_KAPAL",
        color="STATUS",
        hover_data=["VOYAGE", "PELABUHAN", "ETA", "ETD"]
    )

    fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        title="Timeline Operasional Kapal (Sandar vs Layar)",
        xaxis_title="Waktu",
        yaxis_title="Kapal",
        hovermode="closest",
        height=800
    )

    return fig

# =====================================================
# LAYOUT (SATU SAJA)
# =====================================================
app.layout = html.Div([
    html.H2("Dashboard Timeline Kapal"),

    dcc.DatePickerRange(
        id="date-range",
        start_date=timeline["START"].min(),
        end_date=timeline["END"].max(),
        display_format="DD MMM YYYY"
    ),

    dcc.Graph(
        id="timeline-chart",
        style={"height": "90vh", "width": "100%"},
        config={
            "scrollZoom": True,
            "displayModeBar": True
        }
    )
])

# =====================================================
# CALLBACK (FILTER DATA SEBELUM RENDER)
# =====================================================
@app.callback(
    Output("timeline-chart", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_chart(start_date, end_date):

    if start_date is None or end_date is None:
        return build_figure(timeline)

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered = timeline[
        (timeline["END"] >= start_date) &
        (timeline["START"] <= end_date)
    ]

    return build_figure(filtered)

# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)