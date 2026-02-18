import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import gspread
from google.oauth2.service_account import Credentials
from streamlit_calendar import calendar

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="RoomieSync", page_icon="🏠", layout="wide")
st.title("🏠 RoomieSync: Gestión Total")

# --- TUS DATOS ---
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"
HOJA_NOMBRE = "Reservas"

# --- FUNCIONES DE CONEXIÓN ---
def get_worksheet():
    """Conecta con Google y devuelve la hoja de trabajo."""
    try:
        mis_secretos = dict(st.secrets.connections.gsheets)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(mis_secretos, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        return sh.worksheet(HOJA_NOMBRE)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

def cargar_datos():
    """Lee todos los datos y los convierte en DataFrame."""
    ws = get_worksheet()
    if ws:
        try:
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_todo_el_dataframe(df_nuevo):
    """BORRA la hoja y la REESCRIBE con los datos nuevos."""
    ws = get_worksheet()
    if ws:
        try:
            df_guardar = df_nuevo.copy()
            # Convertimos todo a texto para asegurar que Google lo acepte
            df_guardar['startDate'] = df_guardar['startDate'].astype(str)
            df_guardar['endDate'] = df_guardar['endDate'].astype(str)
            
            # Preparamos los datos
            datos_lista = [df_guardar.columns.values.tolist()] + df_guardar.values.tolist()
            
            ws.clear()
            ws.update(datos_lista)
            return True
        except Exception as e:
            st.error(f"Error al actualizar la hoja: {e}")
            return False
    return False

# --- CARGA INICIAL ---
df = cargar_datos()

# Limpieza y Conversión de Tipos
if not df.empty:
    for col in ['startDate', 'endDate']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    if 'guests' in df.columns:
        df['guests'] = pd.to_numeric(df['guests'], errors='coerce').fillna(1)
    
    df = df.fillna("")

# ==========================================
# SECCIÓN 1: FORMULARIO (Precio por Noche)
# ==========================================
with st.expander("➕ Añadir Nueva Reserva", expanded=True):
    with st.form("booking_form_top"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre del Huésped")
            start = st.date_input("Llegada", min_value=datetime.today())
            guests = st.number_input("Personas", 1, 4, 1)
        with col2:
            # CAMBIO: Ahora pedimos PRECIO POR NOCHE
            price_per_night = st.number_input("Precio por Noche (€)", 0.0, step=5.0)
            end = st.date_input("Salida", min_value=datetime.today() + timedelta(days=1))
            is_tao = st.checkbox("¿Es familia de TAO? ⭐")
        
        submitted = st.form_submit_button("Añadir Reserva", type="primary")
        
        if submitted:
            if not name:
                st.warning("Falta el nombre.")
            elif end <= start:
                st.error("La fecha de salida debe ser posterior a la llegada.")
            else:
                # CÁLCULO AUTOMÁTICO DEL TOTAL
                # (Fecha Fin - Fecha Inicio).days ya hace la resta correcta de noches
                noches = (end - start).days
                precio_total_calculado = price_per_night * noches
                
                st.toast(f"ℹ️ Calculando: {noches} noches x {price_per_night}€ = {precio_total_calculado}€ Total")

                nueva_fila = {
                    "id": str(int(datetime.now().timestamp())),
                    "guestName": name,
                    "startDate": start,
