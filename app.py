import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="RoomieSync", page_icon="🏠")
st.title("🏠 RoomieSync: Reservas")

# --- USAMOS LA URL LIMPIA ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/15tqsksP9b3d2YmLl-bQsEXTySdWSZ5Gz98_h4kiUrWs"

# 1. CONEXIÓN NUEVA (Nombre cambiado a "roomie" para borrar caché)
try:
    # Fíjate que aquí ahora llamamos a "roomie", no a "gsheets"
    conn = st.connection("roomie", type=GSheetsConnection)
    
    # Leemos sin especificar hoja (cogerá la primera por defecto)
    df = conn.read(spreadsheet=SHEET_URL, ttl=0)
except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
    st.stop()

# 2. LIMPIEZA
if df.empty:
    df = pd.DataFrame(columns=['id', 'guestName', 'startDate', 'endDate', 'guests', 'price', 'isTaoFamily', 'checkInTime'])
else:
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
            name = st.text_input("Nombre")
            start = st.date_input("Llegada", min_value=datetime.today())
            guests = st.number_input("Personas", 1, 4, 1)
        with col2:
            price = st.number_input("Precio (€)", 0.0, step=5.0)
            end = st.date_input("Salida", min_value=datetime.today())
            is_tao = st.checkbox("¿Familia TAO?")
        
        if st.form_submit_button("Guardar"):
            if not name:
                st.warning("Pon un nombre")
            else:
                new_booking = pd.DataFrame([{
                    "id": str(datetime.now().timestamp()), 
                    "guestName": name,
                    "startDate": start,
                    "endDate": end,
                    "guests": guests,
                    "price": price,
                    "isTaoFamily": is_tao,
                    "checkInTime": "14:00"
                }])
                updated_df = pd.concat([df, new_booking], ignore_index=True)
                try:
                    # Guardamos en la conexión nueva
                    conn.update(spreadsheet=SHEET_URL, data=updated_df)
                    st.success("¡Guardado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# 4. TABLA
st.subheader("📅 Reservas")
if not df.empty and 'startDate' in df.columns:
    edited_df = st.data_editor(df, hide_index=True, num_rows="dynamic")
    if not df.reset_index(drop=True).equals(edited_df.reset_index(drop=True)):
        conn.update(spreadsheet=SHEET_URL, data=edited_df)
        st.success("Actualizado")
        st.rerun()
