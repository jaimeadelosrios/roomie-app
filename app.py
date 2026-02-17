import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración
st.set_page_config(page_title="RoomieSync", page_icon="🏠")
st.title("🏠 RoomieSync: Reservas")

# TU ID DE LA HOJA
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"
HOJA_NOMBRE = "Reservas"  # ¡Importante! Coincide con tu pestaña de Excel

# 1. CONEXIÓN
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Especificamos la hoja exacta para evitar errores de "Response 200"
    df = conn.read(spreadsheet=SHEET_ID, worksheet=HOJA_NOMBRE, ttl=0)
except Exception as e:
    # Si el error es "Response [200]", en realidad es que está vacío o cargando
    if "200" in str(e):
        st.warning("⚠️ La conexión es correcta, pero Google está terminando de despertar.")
        st.info("Por favor, espera 1 minuto más y dale a Reboot. ¡Ya casi estamos!")
        st.stop()
    else:
        st.error(f"⚠️ Error de conexión: {e}")
        st.stop()

# 2. LIMPIEZA
if not df.empty:
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
                
                if df.empty:
                    updated_df = new_booking
                else:
                    updated_df = pd.concat([df, new_booking], ignore_index=True)
                
                try:
                    conn.update(spreadsheet=SHEET_ID, worksheet=HOJA_NOMBRE, data=updated_df)
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
            conn.update(spreadsheet=SHEET_ID, worksheet=HOJA_NOMBRE, data=edited_df)
            st.success("Tabla actualizada.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al actualizar: {e}")
else:
    st.info("No hay reservas todavía. ¡Estrena la lista!")

if not df.empty and 'price' in df.columns:
    st.markdown("---")
    st.metric("Hucha Total", f"{df['price'].sum()} €")
