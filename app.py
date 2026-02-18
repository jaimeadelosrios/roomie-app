import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time
import gspread
from google.oauth2.service_account import Credentials

# Configuración básica
st.set_page_config(page_title="RoomieSync", page_icon="🏠")
st.title("🏠 RoomieSync: Reservas")

# --- TUS DATOS ---
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"
HOJA_NOMBRE = "Reservas"

# 1. CONEXIÓN PARA LEER (Aquí el intermediario sí funciona bien)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_ID, worksheet=HOJA_NOMBRE, ttl=0)
except Exception:
    df = pd.DataFrame()

# Limpieza para mostrar la tabla
if not df.empty:
    for col in ['startDate', 'endDate']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df = df.fillna("")

# 3. FORMULARIO
with st.expander("➕ Añadir Nueva Reserva", expanded=True):
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre del Huésped")
            start = st.date_input("Llegada", min_value=datetime.today())
            guests = st.number_input("Personas", 1, 4, 1)
        with col2:
            price = st.number_input("Precio Total (€)", 0.0, step=5.0)
            end = st.date_input("Salida", min_value=datetime.today())
            is_tao = st.checkbox("¿Es familia de TAO? ⭐")
        
        submitted = st.form_submit_button("Guardar Reserva")
        
        if submitted:
            if not name:
                st.warning("Falta el nombre.")
            else:
                # Preparamos la fila tal cual la quiere Google (todo texto o números simples)
                nueva_fila = [
                    str(int(datetime.now().timestamp())), # id
                    name,                                 # guestName
                    str(start),                           # startDate
                    str(end),                             # endDate
                    int(guests),                          # guests
                    float(price),                         # price
                    "Sí" if is_tao else "No",             # isTaoFamily
                    "14:00"                               # checkInTime
                ]
                
                try:
                    st.info("⏳ Contactando directamente con Google...")
                    
                    # --- AQUÍ ESTÁ LA MAGIA: CONEXIÓN PURA ---
                    # 1. Recuperamos las llaves de tus secretos
                    mis_secretos = dict(st.secrets.connections.gsheets)
                    
                    # 2. Definimos los permisos
                    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                    
                    # 3. Creamos la credencial "real"
                    creds = Credentials.from_service_account_info(mis_secretos, scopes=scope)
                    
                    # 4. Autorizamos al cliente nativo (gspread)
                    client = gspread.authorize(creds)
                    
                    # 5. Abrimos la hoja y escribimos
                    sh = client.open_by_key(SHEET_ID)
                    worksheet = sh.worksheet(HOJA_NOMBRE)
                    
                    # ¡INYECCIÓN DIRECTA! 💉
                    worksheet.append_row(nueva_fila)
                    
                    st.success("✅ ¡CONEXIÓN DIRECTA EXITOSA! Reserva guardada.")
                    st.cache_data.clear()
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error crítico: {e}")

# 4. TABLA
st.subheader("📅 Reservas Activas")

if st.button("🔄 Refrescar Tabla"):
    st.cache_data.clear()
    st.rerun()

if not df.empty and 'guestName' in df.columns:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No veo reservas. Si acabas de guardar, dale a Refrescar.")

if not df.empty and 'price' in df.columns:
    st.markdown("---")
    total = pd.to_numeric(df['price'], errors='coerce').sum()
    st.metric("Hucha Total", f"{total} €")
