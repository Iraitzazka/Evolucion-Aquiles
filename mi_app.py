import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Título de la app
st.title("Evolucion Aquiles")

# Archivo donde se guardarán los datos
FILENAME = "datos_dolor.csv"

# Cargar datos si existen, si no crear DataFrame vacío
if os.path.exists(FILENAME):
    df = pd.read_csv(FILENAME)
else:
    df = pd.DataFrame(columns=['fecha', 'dolor_mañanero'])

# Input: valor del día
valor_hoy = st.number_input("Introduce dolor mañanero de hoy", step=1.0, format="%.2f")

# Botón para guardar
if st.button("Guardar valor de hoy"):
    hoy = pd.Timestamp(datetime.now().date())  # solo fecha, sin hora
    if hoy in df["fecha"].values:
        st.warning("Ya hay un valor guardado para hoy.")
    else:
        nuevo = pd.DataFrame({"fecha": [hoy], "dolor_mañanero": [valor_hoy]})
        df = pd.concat([df, nuevo], ignore_index=True)
        df.to_csv(FILENAME, index=False)
        st.success("Valor guardado correctamente.")

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
