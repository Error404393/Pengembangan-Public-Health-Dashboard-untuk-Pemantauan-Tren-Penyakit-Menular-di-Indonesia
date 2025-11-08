import pandas as pd

# --------------------------
# 1️⃣ Load Dataset Asli
# --------------------------
raw_path = "dinkes-od_18509_jml_kasus_penyakit_demam_berdarah_dengue_dbd__kabu_v3_data.csv"
df = pd.read_csv(raw_path)

print("=== Data Awal ===")
print(df.info())
print(df.head())

# --------------------------
# 2️⃣ Normalisasi Nama Kolom
# --------------------------
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# --------------------------
# 3️⃣ Hapus Kolom yang Tidak Relevan
# --------------------------
drop_cols = [col for col in df.columns if 'kode' in col or 'id' in col]
df = df.drop(columns=drop_cols, errors='ignore')

# --------------------------
# 4️⃣ Cek Missing Values
# --------------------------
print("\n=== Missing Values Sebelum ===")
print(df.isna().sum())

# Tentukan kolom nama kabupaten/kota
if "nama_kabupaten_kota" in df.columns:
    df = df.rename(columns={"nama_kabupaten_kota": "kabupaten_kota"})
elif "kabupaten_kota" not in df.columns:
    raise KeyError("Kolom kabupaten/kota tidak ditemukan dalam dataset.")

# Drop baris kosong pada kolom penting
df = df.dropna(subset=["kabupaten_kota", "jumlah_kasus", "tahun"], how="any")

# Pastikan jumlah_kasus numerik
df["jumlah_kasus"] = pd.to_numeric(df["jumlah_kasus"], errors="coerce").fillna(0).astype(int)

# --------------------------
# 5️⃣ Bersihkan Format String
# --------------------------
df["kabupaten_kota"] = df["kabupaten_kota"].str.strip().str.title()
if "nama_provinsi" in df.columns:
    df["nama_provinsi"] = df["nama_provinsi"].str.title()

# --------------------------
# 6️⃣ Hapus Duplikasi
# --------------------------
dupes = df.duplicated(subset=["kabupaten_kota", "tahun"])
if dupes.any():
    print(f"\n⚠️ Ditemukan {dupes.sum()} duplikat, menghapusnya...")
    df = df.drop_duplicates(subset=["kabupaten_kota", "tahun"])

# --------------------------
# 7️⃣ Validasi Tahun
# --------------------------
df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce").astype("Int64")
df = df[df["tahun"].between(2010, 2025, inclusive="both")]

# --------------------------
# 8️⃣ Simpan Hasil Bersih
# --------------------------
clean_path = "dbd_jabar_cleaned.csv"
df.to_csv(clean_path, index=False)

print("\n✅ Data berhasil dibersihkan dan disimpan sebagai:", clean_path)
print("\n=== Cuplikan Data Bersih ===")
print(df.head())
print("\nJumlah baris akhir:", len(df))
