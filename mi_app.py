import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import numpy as np

# Obtener el día actual
hoy = datetime.now().date()

# Título de la app
st.title("Evolucion Aquiles")

# Carga credenciales
@st.cache_resource
def get_gsheet_client():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
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
def guardar_dato(fecha, dolor_mañanero, dolor_DL, dolor_SL_izq, dolor_SL_desplazamiento, dias_correr, dias_ejercicio_fuerza):
    # Añade una fila al final (fecha, valor)
    sheet.append_row([fecha, dolor_mañanero, dolor_DL, dolor_SL_izq, dolor_SL_desplazamiento, dias_correr, dias_ejercicio_fuerza])

def borrar_fila_fecha(fecha_buscada):
    registros = sheet.get_all_records()
    for idx, fila in enumerate(registros):
        if str(fila['fecha']) == fecha_buscada:
            sheet.delete_rows(idx + 2)  # +2: porque sheet es 1-indexado y la 1ra fila es cabecera
            break

# Cargar datos
try:
    df = leer_datos()
    df["fecha"] = pd.to_datetime(df["fecha"])
except Exception:
    df = pd.DataFrame(columns=["fecha", "dolor_mañanero", "dolor_DL", "dolor_SL_izq", "dolor_SL_desplazamiento", "dias_correr", "dias_ejercicio_fuerza"])

# Input: Dolor Mañanero
dolor_mañanero_hoy = st.number_input("Introduce dolor mañanero de hoy", step=1.0, format="%.2f")

# Input: Correr
correr_hoy_opcion = st.radio("¿Has corrido hoy?", ["Sí", "No"])
correr_hoy = 1 if correr_hoy_opcion == "Sí" else 0

# Input: Fuerza
fuerza_hoy_opcion = st.radio("¿Has Hecho ejercicio de fuerza hoy?", ["Sí", "No"])
fuerza_hoy = 1 if fuerza_hoy_opcion == "Sí" else 0

# Input: Saltos
if hoy.weekday() == 1: # Si es Martes
    dolor_DL_str = st.text_input("Introduce dolor DL de hoy (vacío = None)")
    dolor_DL = float(dolor_DL_str) if dolor_DL_str.strip() else None
    dolor_SL_izqL_str = st.text_input("Introduce dolor SL izquierda de hoy (vacío = None)")
    dolor_SL_izq = float(dolor_SL_izqL_str) if dolor_SL_izqL_str.strip() else None
    dolor_SL_desplazamiento_str = st.text_input("Introduce dolor SL con desplazamiento de hoy (vacío = None)")
    dolor_SL_desplazamiento = float(dolor_SL_desplazamiento_str) if dolor_SL_desplazamiento_str.strip() else None
else:
    dolor_DL = None
    dolor_SL_izq = None
    dolor_SL_desplazamiento = None

#Boton Para Guargar
if st.button("Guardar datos de hoy"):
    hoy_str = hoy.isoformat()  # string 'YYYY-MM-DD'
    if (df["fecha"].dt.date == datetime.now().date()).any():
        st.warning("Ya hay un valor guardado para hoy.")
        # Mostrar checkbox de confirmación
        confirmar = st.checkbox("¿Deseas sobrescribir los datos de hoy?")

        if confirmar:
            borrar_fila_fecha(hoy_str)
            guardar_dato(hoy_str, dolor_mañanero_hoy, dolor_DL, dolor_SL_izq,
                         dolor_SL_desplazamiento, correr_hoy, fuerza_hoy)
            st.success("Valores sobrescritos.")
            st.experimental_rerun()
    else:
        guardar_dato(hoy_str, dolor_mañanero_hoy, dolor_DL, dolor_SL_izq, dolor_SL_desplazamiento, correr_hoy, fuerza_hoy)
        st.success("Valores guardados.")
        st.experimental_rerun()

df = df.replace({None: np.nan})
df = df.replace({'': np.nan})

# Mostrar gráfico
if not df.empty:
    df = df.sort_values("fecha")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df["fecha"], df["dolor_mañanero"], marker='o', linestyle='-', label='Dolor Mañanero')
    ax.plot(df["fecha"], df["dolor_DL"], marker='o', linestyle='-', color='red', label='Saltos DL')
    ax.plot(df["fecha"], df["dolor_SL_izq"], marker='o', linestyle='-', color='green', label='Saltos SL izq')
    ax.plot(df["fecha"], df["dolor_SL_desplazamiento"], marker='o', linestyle='-', color='yellow', label='Saltos desplazamiento')

    ax.axvspan(pd.Timestamp('2025-05-31'), pd.Timestamp('2025-06-08'), color='purple', alpha=0.15, label='Periodo inactivo')

    ax.axvline(pd.Timestamp('2025-05-15'), color='black', linestyle='--', linewidth=2)
    ax.text(pd.Timestamp('2025-05-15'), 7, '1. visita Igor', verticalalignment='bottom', horizontalalignment='left', color='black')

    ax.axvline(pd.Timestamp('2025-05-24'), color='black', linestyle='--', linewidth=2)
    ax.text(pd.Timestamp('2025-05-24'), 7, 'Quemazon al estirar isquio', verticalalignment='bottom', horizontalalignment='left', color='black')

    label = True
    for fecha, tick in zip(df["fecha"], df["dias_correr"]):
        if tick == 1:
            if label:
                ax.vlines(x=fecha, ymin=0, ymax=0.5, color='orange', linewidth=3, label='correr')
                label = False
            else:
                ax.vlines(x=fecha, ymin=0, ymax=0.5, color='orange', linewidth=3)

    label = True
    for fecha, tick in zip(df["fecha"], df["dias_ejercicio_fuerza"]):
        if tick == 1:
            if label:
                ax.vlines(x=fecha, ymin=0, ymax=0.5, color='brown', linewidth=1, label='ejercicio fuerza')
                label = False
            else:
                ax.vlines(x=fecha, ymin=0, ymax=0.5, color='brown', linewidth=1)

    ax.set_xlabel("Fecha")
    ax.set_ylabel("Indice Dolor")
    ax.set_ylim([0, 10.5])
    ax.grid(True)
    fig.tight_layout()
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")  # rota etiquetas del eje x para mejor lectura
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=3)
    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("No hay datos aún.")
