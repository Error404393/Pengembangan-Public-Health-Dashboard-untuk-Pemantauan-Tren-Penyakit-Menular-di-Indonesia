import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests

# -----------------------------------
# KONFIGURASI DASAR
# -----------------------------------
st.set_page_config(
    page_title="Dashboard DBD Jawa Barat",
    layout="wide",
)

st.title("Dashboard Pemantauan Kasus DBD - Provinsi Jawa Barat")

# -----------------------------------
# LOAD DATA
# -----------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("dbd_jabar_cleaned.csv")
    df["tahun"] = df["tahun"].astype(int)
    return df

df = load_data()

# Validasi kolom penting
expected_cols = ["kabupaten_kota", "jumlah_kasus", "tahun"]
if not all(col in df.columns for col in expected_cols):
    st.error("Dataset tidak memiliki kolom yang sesuai. Harap jalankan data_cleaning.py terlebih dahulu.")
    st.stop()

# -----------------------------------
# SIDEBAR FILTER
# -----------------------------------
st.sidebar.header("Filter Tampilan")
years = sorted(df["tahun"].unique())
selected_year = st.sidebar.selectbox("Pilih Tahun", years, index=len(years)-1)
filtered = df[df["tahun"] == selected_year]

# -----------------------------------
# METRICS
# -----------------------------------
total_cases = int(filtered["jumlah_kasus"].sum())
avg_case = int(filtered["jumlah_kasus"].mean())
max_row = filtered.loc[filtered["jumlah_kasus"].idxmax()]

col1, col2, col3 = st.columns(3)
col1.metric("Total Kasus DBD Jawa Barat", f"{total_cases:,}")
col2.metric("Rata-rata Kasus per Kabupaten/Kota", f"{avg_case:,}")
col3.metric("Kasus Tertinggi", f"{max_row['kabupaten_kota']} ({max_row['jumlah_kasus']:,})")

# -----------------------------------
# TAB VISUALISASI
# -----------------------------------
st.markdown("## Visualisasi Tren dan Distribusi Kasus")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Tren Tahunan",
    "Sebaran Kabupaten/Kota",
    "Peta Interaktif",
    "Cuaca & Analisis Lingkungan",
    "Informasi & Kontak"
])

# -----------------------------------
# TAB 1 - Tren Tahunan
# -----------------------------------
with tab1:
    yearly = df.groupby("tahun")["jumlah_kasus"].sum().reset_index()
    fig_trend = px.line(
        yearly,
        x="tahun",
        y="jumlah_kasus",
        markers=True,
        title="Tren Kasus DBD di Jawa Barat per Tahun",
        labels={"jumlah_kasus": "Jumlah Kasus", "tahun": "Tahun"}
    )
    fig_trend.update_traces(line_color="#ff4b4b", line_width=3)
    st.plotly_chart(fig_trend, use_container_width=True)

# -----------------------------------
# TAB 2 - Sebaran Kasus per Kabupaten
# -----------------------------------
with tab2:
    fig_bar = px.bar(
        filtered.sort_values("jumlah_kasus", ascending=True),
        x="jumlah_kasus",
        y="kabupaten_kota",
        orientation="h",
        title=f"Jumlah Kasus DBD per Kabupaten/Kota ({selected_year})",
        labels={"jumlah_kasus": "Jumlah Kasus", "kabupaten_kota": "Kabupaten/Kota"},
        color="jumlah_kasus",
        color_continuous_scale="Reds"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------------
# TAB 3 - Peta Interaktif
# -----------------------------------
with tab3:
    st.write("Sebaran Kasus DBD di Jawa Barat berdasarkan jumlah kasus")

    @st.cache_data
    def load_geojson():
        with open("Jabar_By_Kab.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        return geojson_data

    geojson_jabar = load_geojson()

    filtered["kabupaten_kota_clean"] = (
        filtered["kabupaten_kota"]
        .str.upper()
        .str.replace("KABUPATEN ", "")
        .str.replace("KOTA ", "")
        .str.strip()
    )

    for feat in geojson_jabar["features"]:
        feat["properties"]["KABKOT"] = str(feat["properties"]["KABKOT"]).upper().strip()

    fig_map = px.choropleth_mapbox(
        filtered,
        geojson=geojson_jabar,
        locations="kabupaten_kota_clean",
        featureidkey="properties.KABKOT",
        color="jumlah_kasus",
        color_continuous_scale="Reds",
        mapbox_style="carto-positron",
        title=f"Peta Sebaran Kasus DBD Jawa Barat ({selected_year})",
        center={"lat": -6.9, "lon": 107.6},
        zoom=7,
        opacity=0.8,
        labels={"jumlah_kasus": "Jumlah Kasus"}
    )
    st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------------
# TAB 4 - Cuaca & Analisis Lingkungan
# -----------------------------------
with tab4:
    st.subheader("Cuaca dan Risiko Lingkungan terhadap DBD")

    kota_coords = {
        "Bandung": (-6.9175, 107.6191),
        "Bogor": (-6.5971, 106.8060),
        "Bekasi": (-6.2349, 107.0000),
        "Depok": (-6.4025, 106.7942),
        "Cirebon": (-6.7320, 108.5523),
        "Sukabumi": (-6.9220, 106.9281),
        "Garut": (-7.2110, 107.9087),
        "Tasikmalaya": (-7.3274, 108.2207)
    }

    kota_pilih = st.selectbox("Pilih Kabupaten/Kota untuk melihat data cuaca", list(kota_coords.keys()))
    lat, lon = kota_coords[kota_pilih]

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,precipitation_sum&timezone=Asia%2FJakarta"
        r = requests.get(url, timeout=10)
        data = r.json()

        df_weather = pd.DataFrame({
            "Tanggal": data["daily"]["time"],
            "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
            "Curah Hujan (mm)": data["daily"]["precipitation_sum"]
        })

        st.write(f"Data Cuaca 7 Hari Terakhir - {kota_pilih}")
        st.dataframe(df_weather.tail(7))

        fig_weather = px.line(
            df_weather,
            x="Tanggal",
            y=["Suhu Maks (°C)", "Curah Hujan (mm)"],
            title=f"Tren Cuaca di {kota_pilih}",
            markers=True
        )
        st.plotly_chart(fig_weather, use_container_width=True)

        st.info(
            f"Curah hujan tinggi dan suhu antara 25–30°C di {kota_pilih} meningkatkan risiko perkembangbiakan nyamuk Aedes aegypti."
        )

    except Exception as e:
        st.error(f"Gagal memuat data cuaca: {e}")

# -----------------------------------
# TAB 5 - Informasi & Kontak
# -----------------------------------
with tab5:
    st.subheader("Informasi Penanganan dan Pencegahan DBD")

    st.markdown("""
**Langkah Pencegahan Utama:**
1. Menguras dan menutup tempat penampungan air seminggu sekali.  
2. Mengubur barang bekas yang bisa menampung air hujan.  
3. Memelihara ikan pemakan jentik di kolam atau bak air.  
4. Menggunakan lotion anti nyamuk dan memasang kelambu.  
5. Segera periksa ke fasilitas kesehatan jika mengalami demam tinggi mendadak.
    """)

    st.markdown("""
**Tindakan Penanganan Kasus DBD:**
- Segera ke puskesmas atau rumah sakit terdekat untuk pemeriksaan darah.  
- Minum air putih yang cukup untuk mencegah dehidrasi.  
- Jangan menunda pengobatan apabila demam tinggi disertai bintik merah.
    """)

    st.divider()
    st.subheader("Kontak Darurat dan Informasi Kesehatan")
    st.markdown("""
- Call Center Dinas Kesehatan Jawa Barat: **(022) 4230037**  
- Call Center Ambulans Nasional: **119 (Gratis)**  
- WhatsApp DBD Center: **0812-1234-5678**  
- Website Resmi: [dinkes.jabarprov.go.id](https://dinkes.jabarprov.go.id)
    """)

    st.divider()
    st.subheader("Kondisi Darurat")

    if st.button("🚨 Laporkan Kondisi Darurat Sekarang"):
        st.error("PANGGILAN DARURAT DIKIRIM KE CALL CENTER 119 DAN DINAS KESEHATAN JAWA BARAT")
        st.info("Tim medis akan segera menindaklanjuti laporan Anda. Harap tetap tenang dan siapkan informasi lokasi serta kondisi pasien.")

    st.divider()
    st.subheader("Form Laporan Masyarakat")

    with st.form("form_laporan"):
        nama = st.text_input("Nama Lengkap")
        lokasi = st.text_input("Kabupaten/Kota")
        deskripsi = st.text_area("Deskripsi Laporan (misal: ada genangan air, banyak nyamuk, dll)")
        submitted = st.form_submit_button("Kirim Laporan")

        if submitted:
            if not nama or not lokasi or not deskripsi:
                st.warning("Harap lengkapi semua kolom sebelum mengirim laporan.")
            else:
                st.success("Laporan Anda berhasil dikirim. Terima kasih atas partisipasinya.")
                st.write("Ringkasan laporan:")
                st.write(f"- Nama: {nama}")
                st.write(f"- Lokasi: {lokasi}")
                st.write(f"- Deskripsi: {deskripsi}")

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("---")
st.caption("Data: Dinas Kesehatan Jawa Barat & Open-Meteo | Dashboard oleh R. Dika Natakusumah")
