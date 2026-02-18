import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# Configuración básica
st.set_page_config(page_title="RoomieSync", page_icon="🏠")
st.title("🏠 RoomieSync: Reservas")

# --- TUS DATOS ---
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"
HOJA_NOMBRE = "Reservas"

# 1. CONEXIÓN (La de siempre)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
    st.stop()

# 2. LECTURA (Solo para mostrar la tabla abajo)
try:
    # Leemos la hoja para mostrarla
    df = conn.read(spreadsheet=SHEET_ID, worksheet=HOJA_NOMBRE, ttl=0)
    # Si da el falso error 200, creamos tabla vacía
except Exception:
    df = pd.DataFrame()

# Limpieza básica para la visualización
if not df.empty:
    # Convertimos a formato fecha y número para que se vea bonito
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
                # --- AQUÍ ESTÁ EL CAMBIO MÁGICO ---
                # En vez de crear DataFrames complejos, preparamos una lista simple
                # El orden debe coincidir EXACTO con tus columnas en Excel:
                # A: id, B: guestName, C: startDate, D: endDate, E: guests, F: price, G: isTaoFamily, H: checkInTime
                
                nueva_fila = [
                    str(int(datetime.now().timestamp())), # id
                    name,                                 # guestName
                    str(start),                           # startDate (Texto)
                    str(end),                             # endDate (Texto)
                    guests,                               # guests
                    price,                                # price
                    "Sí" if is_tao else "No",             # isTaoFamily
                    "14:00"                               # checkInTime
                ]
                
                try:
                    st.info("⏳ Enviando datos a Google...")
                    
                    # Usamos el cliente interno (gspread) para escribir DIRECTAMENTE
                    # Esto se salta los errores de la librería Streamlit
                    client = conn.client
                    sh = client.open_by_key(SHEET_ID)
                    worksheet = sh.worksheet(HOJA_NOMBRE)
                    
                    # ¡INYECCIÓN DIRECTA!
                    worksheet.append_row(nueva_fila)
                    
                    st.success("✅ ¡Guardado Confirmado!")
                    st.cache_data.clear() # Limpiamos memoria
                    time.sleep(1)
                    st.rerun()            # Recargamos
                    
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")

# 4. TABLA
st.subheader("📅 Reservas Activas")

if st.button("🔄 Refrescar Tabla"):
    st.cache_data.clear()
    st.rerun()

if not df.empty and 'guestName' in df.columns:
    # Mostramos la tabla tal cual viene de Google
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No veo reservas. Si acabas de guardar una, dale al botón de Refrescar.")

if not df.empty and 'price' in df.columns:
    st.markdown("---")
    # Truco para sumar precios aunque vengan como texto
    total = pd.to_numeric(df['price'], errors='coerce').sum()
    st.metric("Hucha Total", f"{total} €")
