import streamlit_authenticator as stauth
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from supabase import create_client, Client
import numpy as np
from funciones import *

# Configuración de pandas para evitar downcasting silencioso. Evito warnings
pd.set_option('future.no_silent_downcasting', True)

# Conexion a BD 
SUPABASE_URL = "https://lrlruhxjhqcszslbywxr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxybHJ1aHhqaHFjc3pzbGJ5d3hyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4MzM1OTUsImV4cCI6MjA2NjQwOTU5NX0.mtjyLTjXwUmxoMVWttfZ2ugd0Zbaw7sQcBBYc2XdpLI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Login y autenticación 
config = load_config(supabase)
authenticator = get_authenticator(config)

# APP 

# Obtener el día actual
hoy = datetime.now().date()

# Título de la app
st.title("Evolucion Aquiles")

#Redirecciones
if st.session_state.get("go_to_inicio"):
    st.session_state["menu"] = "Inicio"
    st.session_state["go_to_inicio"] = False

if st.session_state.get("go_to_login"):
    st.session_state["menu"] = "Iniciar sesión"
    st.session_state["go_to_login"] = False

# Sidebar controlado por session_state
if "menu" not in st.session_state:
    st.session_state["menu"] = "Iniciar sesión"  # valor por defecto
menu_radio = st.sidebar.radio("Opciones", ["Iniciar sesión", "Registrarse", "Inicio"], index=["Iniciar sesión", "Registrarse", "Inicio"].index(st.session_state["menu"]))

# Solo actualizamos si hay cambio real
if menu_radio != st.session_state["menu"]:
    st.session_state["menu"] = menu_radio
    st.rerun()

#Iniciar sesiones
if st.session_state["menu"] == "Iniciar sesión":
    #Si ya esta loggeado
    if st.session_state.get('authentication_status'):
        st.warning("Ya estás autenticado. Por favor, cierra sesión para registrarte con otro usuario.")
        st.session_state["go_to_inicio"] = True
        st.rerun()
    else:
        try:
            authenticator.login()
        except Exception as e:
            st.error(e)
        if st.session_state.get('authentication_status'):
            authenticator.logout()
            st.write(f'Welcome *{st.session_state.get("name")}*')
            st.session_state["go_to_inicio"] = True
            st.rerun()
        elif st.session_state.get('authentication_status') is False:
            st.error('Username/password is incorrect')
        elif st.session_state.get('authentication_status') is None:
            st.warning('Please enter your username and password')

#Registrarse
elif st.session_state["menu"] == "Registrarse":
    #Si ya esta loggeado
    if st.session_state.get('authentication_status'):
        st.warning("Ya estás autenticado. Para registrarte con otro usuario, primero cierra sesión.")
        # Mostrar botón de logout
        if st.button("Cerrar sesión"):
            authenticator.logout()  # Esto elimina las claves asociadas del session_state
            st.session_state["menu"] = "Registrarse"  # Redirigir al registro tras logout
            # Limpia manualmente las claves
            for key in ["authentication_status", "username", "name", "email", "logout"]:
                st.session_state.pop(key, None)
            st.rerun()
    else:
        try:
            email_of_registered_user, \
            username_of_registered_user, \
            name_of_registered_user = authenticator.register_user()

            if email_of_registered_user:
                # Verificamos si ya existe el email
                response = supabase.table("users").select("email").eq("email", email_of_registered_user).execute()

                if len(response.data) > 0:
                    st.warning("Ese correo ya está registrado.")
                else:
                    # Hash de la contraseña introducida (ya está en el config temporal)
                    hashed_password = config['credentials']['usernames'][username_of_registered_user]['password']

                    # Insertamos el nuevo usuario en la tabla de supabase
                    insertar_datos(supabase,
                        {"username": username_of_registered_user,
                        "name": name_of_registered_user,
                        "email": email_of_registered_user,
                        "password": hashed_password}, 
                        "users")
                    st.success("Usuario registrado correctamente. Iniciando sesión...")

                    # Guardar el usuario como autenticado directamente
                    st.session_state.update({
                        "authentication_status": True,
                        "username": username_of_registered_user,
                        "name": name_of_registered_user,
                        "email": email_of_registered_user,
                        "go_to_inicio": True
                    })
                    st.rerun()

        except Exception as e:
            st.error(f"Error en el registro: {e}")

#Pagina principal
elif st.session_state["menu"] == "Inicio":
    #Si esta loggeado
    if st.session_state.get('authentication_status'):
        user = st.session_state.get("username")
        if user:
            correo = config['credentials']['usernames'][user]['email']

            df = obtener_datos(supabase, correo)
            df["fecha"] = pd.to_datetime(df["fecha"])

            # Función para manejar el click
            def guardar_click_callback():
                st.session_state.guardar_click = True

            # Inicializa el estado si no está presente
            if "guardar_click" not in st.session_state:
                st.session_state.guardar_click = False
            if "confirmar_overwrite" not in st.session_state:
                st.session_state.confirmar_overwrite = False

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
                        eliminar_fila(supabase, id_fila)
                        dolor_DL = int(dolor_DL) if dolor_DL is not None else None
                        dolor_SL_izq = int(dolor_SL_izq) if dolor_SL_izq is not None else None
                        dolor_SL_desplazamiento = int(dolor_SL_desplazamiento) if dolor_SL_desplazamiento is not None else None
                        insertar_datos(supabase,
                                       {'user': correo, 
                                        'fecha':hoy_str, 
                                        'dolor_mañanero':int(dolor_mañanero_hoy), 
                                        'dolor_dl':dolor_DL, 
                                        'dolor_sl_izq':dolor_SL_izq, 
                                        'dolor_sl_desplazamiento':dolor_SL_desplazamiento, 
                                        'dias_correr':int(correr_hoy), 
                                        'dias_ejercicio_fuerza':int(fuerza_hoy)},
                                        "aquiles")
                        st.success("Valores sobrescritos.")
                        st.session_state.guardar_click = False
                        st.rerun()
                else:
                    dolor_DL = int(dolor_DL) if dolor_DL is not None else None
                    dolor_SL_izq = int(dolor_SL_izq) if dolor_SL_izq is not None else None
                    dolor_SL_desplazamiento = int(dolor_SL_desplazamiento) if dolor_SL_desplazamiento is not None else None
                    insertar_datos(supabase,
                                   {'user': correo, 
                                'fecha':hoy_str, 
                                'dolor_mañanero':int(dolor_mañanero_hoy), 
                                'dolor_dl':dolor_DL, 
                                'dolor_sl_izq':dolor_SL_izq, 
                                'dolor_sl_desplazamiento':dolor_SL_desplazamiento, 
                                'dias_correr':int(correr_hoy), 
                                'dias_ejercicio_fuerza':int(fuerza_hoy)},
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

                if user == 'iraitz':
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

    else:
        st.warning("Por favor, inicia sesión para acceder a la aplicación.")
        st.session_state["go_to_login"] = True
        st.rerun()
