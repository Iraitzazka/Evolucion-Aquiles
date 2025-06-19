import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Título de la app
st.title("Evolucion Aquiles")

# Carga credenciales
@st.cache_resource
def get_gsheet_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client

client = get_gsheet_client()

# Abre la hoja por nombre
sheet = client.open("Evolucion Aquiles").sheet1

# Leer datos de la hoja
def leer_datos():
    records = sheet.get_all_records()
    return pd.DataFrame(records)

# Escribir un nuevo dato
def guardar_dato(fecha, valor):
    # Añade una fila al final (fecha, valor)
    sheet.append_row([fecha, valor])

# Cargar datos
try:
    df = leer_datos()
    df["fecha"] = pd.to_datetime(df["fecha"])
except Exception:
    df = pd.DataFrame(columns=["fecha", "valor"])

# Input: valor del día
valor_hoy = st.number_input("Introduce dolor mañanero de hoy", step=1.0, format="%.2f")

#Boton Para Guargar
if st.button("Guardar valor de hoy"):
    hoy = datetime.now().date().isoformat()  # string 'YYYY-MM-DD'
    if (df["fecha"].dt.date == datetime.now().date()).any():
        st.warning("Ya hay un valor guardado para hoy.")
    else:
        guardar_dato(hoy, valor_hoy)
        st.success("Valor guardado en Google Sheets.")
        st.experimental_rerun()

# Mostrar gráfico
if not df.empty:
    df = df.sort_values("fecha")
    fig, ax = plt.subplots()
    ax.plot(df["fecha"], df["dolor_mañanero"], marker="o", linestyle="-")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("dolor_mañanero")
    ax.set_title("Evolución diaria")
    ax.grid(True)
    st.pyplot(fig)
else:
    st.info("No hay datos aún.")
