import streamlit as st
import pandas as pd
from datetime import datetime
import time
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="RoomieSync", page_icon="🏠")
st.title("🏠 RoomieSync: Reservas")

# --- TUS DATOS ---
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"
HOJA_NOMBRE = "Reservas"

# --- 1. CONEXIÓN DIRECTA (CARGA DE DATOS) ---
# Esta función conecta directamente con Google, sin intermediarios que fallen.
def cargar_datos():
    try:
        # Recuperamos secretos y conectamos
        mis_secretos = dict(st.secrets.connections.gsheets)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(mis_secretos, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrimos la hoja
        sh = client.open_by_key(SHEET_ID)
        worksheet = sh.worksheet(HOJA_NOMBRE)
        
        # Leemos TODOS los registros de golpe
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df, worksheet # Devolvemos también la hoja para poder escribir luego
    except Exception as e:
        st.error(f"❌ Error al leer los datos: {e}")
        return pd.DataFrame(), None

# Cargamos los datos al iniciar la app
df, worksheet_actual = cargar_datos()

# --- 2. LIMPIEZA DE DATOS (Para que se vea bonito) ---
if not df.empty:
    # Convertimos las fechas de texto a objetos de fecha reales para el calendario
    for col in ['startDate', 'endDate']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    
    # Aseguramos que el precio sea un número
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)

# --- 3. FORMULARIO DE NUEVA RESERVA ---
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
            elif worksheet_actual is None:
                st.error("No hay conexión con la hoja.")
            else:
                # Preparamos la fila (Todo a Texto/Simple para que Google no se queje)
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
                    st.info("⏳ Guardando en la nube...")
                    # INYECCIÓN DIRECTA
                    worksheet_actual.append_row(nueva_fila)
                    
                    st.success("✅ ¡Reserva guardada!")
                    time.sleep(1)
                    st.rerun() # Recargamos para que salga abajo inmediatamente
                    
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")

# --- 4. TABLA DE RESERVAS ACTIVAS (VISUALIZACIÓN) ---
st.subheader("📅 Reservas Activas")

# Botón manual por si acaso
if st.button("🔄 Refrescar Lista"):
    st.rerun()

if not df.empty and 'guestName' in df.columns:
    # Ordenamos por fecha de llegada
    if 'startDate' in df.columns:
        df = df.sort_values(by="startDate", ascending=True)

    # Mostramos la tabla interactiva (estilo calendario simple)
    st.data_editor(
        df,
        column_config={
            "guestName": "Huésped",
            "startDate": st.column_config.DateColumn("Llegada", format="DD/MM/YYYY"),
            "endDate": st.column_config.DateColumn("Salida", format="DD/MM/YYYY"),
            "price": st.column_config.NumberColumn("Precio", format="%d €"),
            "guests": st.column_config.NumberColumn("Pers."),
            "isTaoFamily": "Familia Tao",
            "id": None,           # Ocultamos el ID
            "checkInTime": None   # Ocultamos la hora
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed" # Evita añadir filas vacías desde la tabla visual
    )
else:
    st.info("📭 No hay reservas todavía en la hoja. ¡Crea la primera!")

# --- 5. HUCHA TOTAL ---
if not df.empty and 'price' in df.columns:
    st.markdown("---")
    total = df['price'].sum()
    st.metric("💰 Hucha Total", f"{total} €")
