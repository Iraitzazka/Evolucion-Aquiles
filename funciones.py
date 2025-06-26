import streamlit_authenticator as stauth
import streamlit as st
import pandas as pd

##################### Conexion a BD #####################
#Función para leer datos de la tabla
def obtener_datos(supabase, correo):
    response = supabase.table("aquiles").select("*").eq("user", correo).execute()
     # Intentamos acceder a error de forma segura
    error = getattr(response, "error", None)
    if error:
        st.error(f"Error cargando datos: {error.message}")
        return pd.DataFrame()
    else:
        return pd.DataFrame(response.data, columns=['user','fecha','dolor_mañanero', 'dolor_dl','dolor_sl_izq','dolor_sl_desplazamiento', 'dias_correr','dias_ejercicio_fuerza'])

def insertar_datos(supabase, fila_dict, table):
    response = supabase.table(table).insert(fila_dict).execute()
    error = getattr(response, "error", None)
    if error:
        st.error(f"Error cargando datos.")
    else:
        st.success("Datos guardados correctamente.")

def eliminar_fila(supabase, id_fila):
    response = supabase.table("aquiles").delete().eq("id", id_fila).execute()
    error = getattr(response, "error", None)
    if error:
        st.error(f"Error al eliminar")
    else:
        st.success("Fila eliminada correctamente.")


def load_config(supabase):
    # Obtener todos los usuarios
    response = supabase.table("users").select("*").execute()
    users = response.data
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

# Inicializar autenticador
def get_authenticator(config):
    return stauth.Authenticate(
        config['credentials'],
        "auth_cookie_name",
        "auth_signature_key",
        cookie_expiry_days=30
        )