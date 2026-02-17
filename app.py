import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración básica
st.set_page_config(page_title="RoomieSync", page_icon="🏠")
st.title("🏠 RoomieSync: Reservas")

# --- LA DIRECCIÓN MAESTRA (La ponemos aquí para que no falle nunca) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/15tqsksP9b3d2YmLl-bQsEXTySdWSZ5Gz98_h4kiUrWs"
HOJA_NOMBRE = "Reservas"

# 1. CONEXIÓN
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leemos especificando URL y Hoja
    df = conn.read(spreadsheet=SHEET_URL, worksheet=HOJA_NOMBRE, ttl=0)
except Exception as e:
    st.error(f"⚠️ Error de conexión inicial: {e}")
    st.stop()

# 2. LIMPIEZA DE DATOS
# Si la hoja está vacía (como acabamos de hacer), creamos la estructura base
if df.empty:
    df = pd.DataFrame(columns=['id', 'guestName', 'startDate', 'endDate', 'guests', 'price', 'isTaoFamily', 'checkInTime'])
else:
    # Si hay datos, aseguramos formatos
    for col in ['startDate', 'endDate']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    if 'guests' in df.columns:
        df['guests'] = pd.to_numeric(df['guests'], errors='coerce').fillna(1)
    
    df = df.fillna("")

# 3. FORMULARIO
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
                st.warning("Falta el nombre.")
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
                
                # Concatenamos
                updated_df = pd.concat([df, new_booking], ignore_index=True)
                
                # GUARDADO BLINDADO: Le damos la URL y la Hoja explícitamente
                try:
                    conn.update(spreadsheet=SHEET_URL, worksheet=HOJA_NOMBRE, data=updated_df)
                    st.success("¡Reserva guardada con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# 4. TABLA
st.subheader("📅 Reservas Activas")
if not df.empty and 'startDate' in df.columns:
    df_sorted = df.sort_values(by="startDate")
    
    edited_df = st.data_editor(
        df_sorted,
        column_config={
            "startDate": st.column_config.DateColumn("Llegada", format="DD/MM/YYYY"),
            "endDate": st.column_config.DateColumn("Salida", format="DD/MM/YYYY"),
            "price": st.column_config.NumberColumn("Precio", format="%d €"), 
            "id": None
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True
    )
    
    if not df_sorted.reset_index(drop=True).equals(edited_df.reset_index(drop=True)):
        try:
            conn.update(spreadsheet=SHEET_URL, worksheet=HOJA_NOMBRE, data=edited_df)
            st.success("Tabla actualizada.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al actualizar tabla: {e}")

# Footer
if not df.empty and 'price' in df.columns:
    st.markdown("---")
    st.metric("Hucha Total", f"{df['price'].sum()} €")
