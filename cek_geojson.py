import json

with open("Jabar_By_Kab.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)

# Ambil satu fitur untuk lihat nama key-nya
print("Keys di 'properties':", list(data["features"][0]["properties"].keys()))
print("Contoh properties:", data["features"][0]["properties"])
