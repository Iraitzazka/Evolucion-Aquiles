import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from supabase import create_client, Client
import numpy as np

# Configuración de pandas para evitar downcasting silencioso. Evito warnings
pd.set_option('future.no_silent_downcasting', True)
CONFIG_FILE = 'config.yaml'

##################### Conexion a BD #####################
SUPABASE_URL = "https://lrlruhxjhqcszslbywxr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxybHJ1aHhqaHFjc3pzbGJ5d3hyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4MzM1OTUsImV4cCI6MjA2NjQwOTU5NX0.mtjyLTjXwUmxoMVWttfZ2ugd0Zbaw7sQcBBYc2XdpLI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

#Función para leer datos de la tabla
def obtener_datos(correo):
    response = supabase.table("aquiles").select("*").eq("user", correo).execute()
     # Intentamos acceder a error de forma segura
    error = getattr(response, "error", None)
    if error:
        st.error(f"Error cargando datos: {error.message}")
        return pd.DataFrame()
    else:
        st.error(f"obtener_datos, response.data: {response.data}")
        st.error(f"Columnas: {pd.DataFrame(response.data).columns}")
        return pd.DataFrame(response.data)

def insertar_datos(fila_dict, table):
    response = supabase.table(table).insert(fila_dict).execute()
    error = getattr(response, "error", None)
    if error:
        st.error(f"Error cargando datos.")
    else:
        st.success("Datos guardados correctamente.")

def eliminar_fila(id_fila):
    response = supabase.table("aquiles").delete().eq("id", id_fila).execute()
    error = getattr(response, "error", None)
    if error:
        st.error(f"Error al eliminar")
    else:
        st.success("Fila eliminada correctamente.")

###########################################################################

##################### Login y autenticación #####################
with open(CONFIG_FILE) as file:
    config = yaml.load(file, Loader=SafeLoader)



# Cargar archivo de configuración
def load_config():
    # Obtener todos los usuarios
    response = supabase.table("users").select("*").execute()
    users = response.data
    st.write(f'users en load config *{users}*')
    # Construir config
    config = {"credentials": {"usernames": {}}}
    for user in users:
        username = user["username"]
        config["credentials"]["usernames"][username] = {
            "email": user["email"],
            "name": user["name"],
            "password": user["password"]  
        }

    return config
# def load_config():
#     with open(CONFIG_FILE) as file:
#         return yaml.load(file, Loader=SafeLoader)

# Guardar cambios en archivo de configuración
def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

# Inicializar autenticador
def get_authenticator(config):
    return stauth.Authenticate(
        config['credentials'],
        "auth_cookie_name",
        "auth_signature_key",
        cookie_expiry_days=30
        )

config = load_config()
authenticator = get_authenticator(config)

###########################################################################

##################### APP #####################

# Obtener el día actual
hoy = datetime.now().date()

# Título de la app
st.title("Evolucion Aquiles")

menu = st.sidebar.radio("Opciones", ["Iniciar sesión", "Registrarse"])

if menu == "Iniciar sesión":
    try:
        authenticator.login()
        st.write(f'config *{config['credentials']}*')
    except Exception as e:
        st.error(e)
    if st.session_state.get('authentication_status'):
        authenticator.logout()
        st.write(f'Welcome *{st.session_state.get("name")}*')
        
        # Inicializa el estado si no está presente
        if "guardar_click" not in st.session_state:
            st.session_state.guardar_click = False
        if "confirmar_overwrite" not in st.session_state:
            st.session_state.confirmar_overwrite = False

        user = st.session_state.get("username")
        if user:

            correo = config['credentials']['usernames'][user]['email']

            df = obtener_datos(correo)
            df["fecha"] = pd.to_datetime(df["fecha"])

            # Función para manejar el click
            def guardar_click_callback():
                st.session_state.guardar_click = True

            # Input: Dolor Mañanero
            dolor_mañanero_hoy = st.number_input("Introduce dolor mañanero de hoy", step=1.0, format="%.2f")

            # Input: Correr
            correr_hoy_opcion = st.radio("¿Has corrido hoy?", ["Sí", "No"])
            correr_hoy = 1 if correr_hoy_opcion == "Sí" else 0

            # Input: Fuerza
            fuerza_hoy_opcion = st.radio("¿Has hecho ejercicio de fuerza hoy?", ["Sí", "No"])
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
            st.button("Guardar datos de hoy", on_click=guardar_click_callback)
            if st.session_state.guardar_click:
                hoy_str = hoy.isoformat()  # string 'YYYY-MM-DD'
                if (df["fecha"].dt.date == datetime.now().date()).any():
                    st.warning("Ya hay un valor guardado para hoy.")
                    # Mostrar checkbox de confirmación
                    st.session_state.confirmar_overwrite = st.checkbox("¿Deseas sobrescribir los datos de hoy?", value=st.session_state.confirmar_overwrite)

                    if st.session_state.confirmar_overwrite:
                        id_fila = df.loc[df["fecha"].dt.date == datetime.now().date(), "id"].values[0]
                        eliminar_fila(id_fila)
                        insertar_datos({'user': correo, 
                                        'fecha':hoy_str, 
                                        'dolor_mañanaero':dolor_mañanero_hoy, 
                                        'dolor_dl':dolor_DL, 
                                        'dolor_sl_izq':dolor_SL_izq, 
                                        'dolor_sl_desplazamiento':dolor_SL_desplazamiento, 
                                        'correr_hoy':correr_hoy, 
                                        'fuerza_hoy':fuerza_hoy},
                                        "aquiles")
                        st.success("Valores sobrescritos.")
                        st.session_state.guardar_click = False
                        st.rerun()
                else:
                    insertar_datos({'user': correo, 
                                        'fecha':hoy_str, 
                                        'dolor_mañanaero':dolor_mañanero_hoy, 
                                        'dolor_dl':dolor_DL, 
                                        'dolor_sl_izq':dolor_SL_izq, 
                                        'dolor_sl_desplazamiento':dolor_SL_desplazamiento, 
                                        'correr_hoy':correr_hoy, 
                                        'fuerza_hoy':fuerza_hoy},
                                        "aquiles")
                    st.success("Valores guardados.")
                    st.session_state.guardar_click = False
                    st.rerun()

            df.replace([None, ''], np.nan, inplace=True)

            # Mostrar gráfico
            if not df.empty:
                df = df.sort_values("fecha")
                fig, ax = plt.subplots(figsize=(10, 6))

                ax.plot(df["fecha"], df["dolor_mañanero"], marker='o', linestyle='-', label='Dolor Mañanero')
                
                df[["dolor_dl", "dolor_sl_izq", "dolor_sl_desplazamiento"]] = df[["dolor_dl", "dolor_sl_izq", "dolor_sl_desplazamiento"]].apply(pd.to_numeric, errors='coerce')
                df_interpolado = df[["dolor_dl", "dolor_sl_izq", "dolor_sl_desplazamiento"]].interpolate()
                ax.plot(df["fecha"], df_interpolado["dolor_dl"], marker=None, linestyle='-', color='red', label='Saltos DL')
                ax.plot(df["fecha"], df_interpolado["dolor_sl_izq"], marker=None, linestyle='-', color='green', label='Saltos Sl izq')
                ax.plot(df["fecha"], df_interpolado["dolor_sl_desplazamiento"], marker=None, linestyle='-', color='yellow', label='Saltos desplazamiento')

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

    elif st.session_state.get('authentication_status') is False:
        st.error('Username/password is incorrect')
    elif st.session_state.get('authentication_status') is None:
        st.warning('Please enter your username and password')

elif menu == "Registrarse":
    try:
        email_of_registered_user, \
        username_of_registered_user, \
        name_of_registered_user = authenticator.register_user()
        st.write("Debug:", email_of_registered_user, username_of_registered_user, name_of_registered_user)

        if email_of_registered_user:
            # Verificamos si ya existe el email
            response = supabase.table("users").select("email").eq("email", email_of_registered_user).execute()

            if len(response.data) > 0:
                st.warning("Ese correo ya está registrado.")
            else:
                # Hash de la contraseña introducida (ya está en el config temporal)
                hashed_password = config['credentials']['usernames'][username_of_registered_user]['password']

                # Insertamos el nuevo usuario en la tabla de supabase
                insertar_datos({
                    "username": username_of_registered_user,
                    "name": name_of_registered_user,
                    "email": email_of_registered_user,
                    "password": hashed_password}, 
                    "users")
    except Exception as e:
        st.error(f"Error en el registro: {e}")



