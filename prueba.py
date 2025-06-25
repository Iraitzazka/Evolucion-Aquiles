
# pF9az7g4U2VVVcbU supabase db password
import pandas as pd
import numpy as np
from supabase import create_client, Client

# Configura tu Supabase
supabase_url = "https://lrlruhxjhqcszslbywxr.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxybHJ1aHhqaHFjc3pzbGJ5d3hyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4MzM1OTUsImV4cCI6MjA2NjQwOTU5NX0.mtjyLTjXwUmxoMVWttfZ2ugd0Zbaw7sQcBBYc2XdpLI"
supabase: Client = create_client(supabase_url, supabase_key)

# Carga tu archivo Excel
df = pd.read_excel(r"C:\Users\irait\Desktop\Evolucion-Aquiles\Evolucion Aquiles.xlsx")

# Opcional: verificar columnas
print("Columnas del Excel:", df.columns)

# Asegúrate de que las columnas coincidan con las de la tabla Supabase
expected_cols = {"user", "fecha", "dolor_mañanero", "dolor_dl", "dolor_sl_izq", "dolor_sl_desplazamiento", "dias_correr", "dias_ejercicio_fuerza"}
if not expected_cols.issubset(df.columns):
    raise ValueError("El archivo no contiene las columnas requeridas")

df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%Y-%m-%d")

for col in ["dolor_mañanero", "dolor_dl", "dolor_sl_izq", "dolor_sl_desplazamiento", "dias_correr", "dias_ejercicio_fuerza"]:
    # Luego convierte la columna a entero
    df[col] = df[col].astype("Int64")
    
# Convierte a lista de diccionarios
data = df[["user", "fecha", "dolor_mañanero", "dolor_dl", "dolor_sl_izq", "dolor_sl_desplazamiento", "dias_correr", "dias_ejercicio_fuerza"]].replace({np.nan: None}).to_dict(orient="records")

# Inserta en Supabase
response = supabase.table("aquiles").insert(data).execute()

# Resultado
if response.data:
    print("✅ Datos insertados correctamente")
else:
    print("⚠️ Algo pasó al insertar")
    print(response)