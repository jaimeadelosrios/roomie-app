import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración básica de la página
st.set_page_config(page_title="RoomieSync", page_icon="🏠")

st.title("🏠 RoomieSync: Reservas")

# 1. CONEXIÓN A GOOGLE SHEETS
# Ponemos el enlace aquí directamente para que no falle
SHEET_URL = "https://docs.google.com/spreadsheets/d/15tqsksP9b3d2YmLl-bQsEXTySdWSZ5Gz98_h4kiUrWs"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Le decimos explícitamente qué hoja leer usando la variable de arriba
    df = conn.read(spreadsheet=SHEET_URL, ttl=5)
except Exception as e:
    st.error(f"⚠️ Error detallado: {e}")
    st.stop()

# 2. LIMPIEZA DE DATOS (Para evitar la Pantalla Roja)
# Si la hoja está vacía o tiene datos raros, los arreglamos antes de mostrar nada
if not df.empty:
    # Convertimos fechas de texto a objetos de fecha reales
    if 'startDate' in df.columns:
        df['startDate'] = pd.to_datetime(df['startDate'], errors='coerce').dt.date
    if 'endDate' in df.columns:
        df['endDate'] = pd.to_datetime(df['endDate'], errors='coerce').dt.date
    
    # Aseguramos que el precio y los invitados sean números
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    if 'guests' in df.columns:
        df['guests'] = pd.to_numeric(df['guests'], errors='coerce').fillna(1)
    
    # Rellenamos huecos vacíos en otras columnas para que no den error
    df = df.fillna("")

# 3. FORMULARIO DE NUEVA RESERVA
with st.expander("➕ Añadir Nueva Reserva", expanded=True):
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nombre del Huésped")
            start = st.date_input("Llegada", min_value=datetime.today())
            guests = st.number_input("Personas", min_value=1, max_value=4, value=1)
            
        with col2:
            price = st.number_input("Precio Total (€)", min_value=0.0, step=5.0)
            end = st.date_input("Salida", min_value=datetime.today())
            is_tao = st.checkbox("¿Es familia de TAO? ⭐")
        
        submitted = st.form_submit_button("Guardar Reserva")
        
        if submitted:
            if not name:
                st.warning("Por favor, pon un nombre.")
            else:
                # Preparamos la nueva fila
                new_booking = pd.DataFrame([{
                    "id": str(datetime.now().timestamp()), # ID único basado en la hora
                    "guestName": name,
                    "startDate": start,
                    "endDate": end,
                    "guests": guests,
                    "price": price,
                    "isTaoFamily": is_tao,
                    "checkInTime": "14:00" # Hora por defecto
                }])
                
                # Unimos la nueva reserva con las anteriores
                updated_df = pd.concat([df, new_booking], ignore_index=True)
                
                # Guardamos en Google Sheets
                conn.update(data=updated_df)
                st.success("¡Reserva guardada! Actualizando...")
                st.rerun()

# 4. TABLA DE RESERVAS (Editor)
st.subheader("📅 Reservas Activas")

if not df.empty and 'startDate' in df.columns:
    # Ordenamos por fecha de llegada
    df_sorted = df.sort_values(by="startDate")
    
    # Mostramos el editor
    # Si editas algo aquí directamente, intentará actualizarse
    edited_df = st.data_editor(
        df_sorted,
        column_config={
            "startDate": st.column_config.DateColumn("Llegada", format="DD/MM/YYYY"),
            "endDate": st.column_config.DateColumn("Salida", format="DD/MM/YYYY"),
            "price": st.column_config.NumberColumn("Precio", format="%d €"),
            "isTaoFamily": st.column_config.CheckboxColumn("Familia TAO"),
            "id": None # Ocultamos el ID para que no moleste
        },
        num_rows="dynamic", # Permite añadir filas abajo
        hide_index=True,
        use_container_width=True
    )
    
    # Detectar cambios manuales en la tabla y guardar
    if not df_sorted.reset_index(drop=True).equals(edited_df.reset_index(drop=True)):
        conn.update(data=edited_df)
        st.success("Cambios guardados en la tabla.")
        st.rerun()
else:
    st.info("Aún no hay reservas. ¡Añade la primera arriba!")

# Estadísticas rápidas (Footer)
if not df.empty and 'price' in df.columns:
    total_eur = df['price'].sum()
    st.markdown("---")
    st.metric(label="Total Acumulado en la Hucha", value=f"{total_eur} €")
