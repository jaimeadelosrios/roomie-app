import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración básica
st.set_page_config(page_title="RoomieSync", page_icon="🏠")
st.title("🏠 RoomieSync: Reservas")

# --- TUS DATOS ---
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"
HOJA_NOMBRE = "Reservas"

# 1. CONEXIÓN INTELIGENTE (Captura el "Error de Éxito")
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_ID, worksheet=HOJA_NOMBRE, ttl=0)

except Exception as e:
    # SI EL ERROR ES "200", SIGNIFICA QUE CONECTÓ PERO SE HIZO UN LÍO
    if "200" in str(e) or "Response" in str(e):
        # Asumimos que está vacío pero conectado, y creamos la estructura manual
        df = pd.DataFrame(columns=['id', 'guestName', 'startDate', 'endDate', 'guests', 'price', 'isTaoFamily', 'checkInTime'])
    else:
        # Si es otro error, lo mostramos
        st.error(f"⚠️ Error real: {e}")
        st.stop()

# 2. LIMPIEZA Y PREPARACIÓN
# Si df viene vacío (o del error 200), aseguramos que tenga columnas
if df.empty:
    if 'guestName' not in df.columns:
        df = pd.DataFrame(columns=['id', 'guestName', 'startDate', 'endDate', 'guests', 'price', 'isTaoFamily', 'checkInTime'])
else:
    # Convertimos formatos
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
                    # Si al guardar da el error 200, también es éxito
                    if "200" in str(e):
                        st.success("¡Reserva guardada (Ignorando alerta 200)!")
                        st.rerun()
                    else:
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
            if "200" in str(e):
                 st.success("Tabla actualizada.")
                 st.rerun()
            else:
                st.error(f"Error al actualizar: {e}")
else:
    st.info("No hay reservas todavía. ¡Estrena la lista!")

if not df.empty and 'price' in df.columns:
    st.markdown("---")
    st.metric("Hucha Total", f"{df['price'].sum()} €")
