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
            # PRECIO POR NOCHE
            price_per_night = st.number_input("Precio por Noche (€)", 0.0, step=5.0)
            # Salida por defecto mañana
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
                noches = (end - start).days
                precio_total_calculado = price_per_night * noches
                
                # Mensaje informativo
                st.info(f"ℹ️ Calculando: {noches} noches x {price_per_night}€ = {precio_total_calculado}€ Total")

                # Creamos la fila nueva (diccionario bien cerrado)
                nueva_fila = {
                    "id": str(int(datetime.now().timestamp())),
                    "guestName": name,
                    "startDate": start,
                    "endDate": end,
                    "guests": guests,
                    "price": precio_total_calculado,
                    "isTaoFamily": "Sí" if is_tao else "No",
                    "checkInTime": "14:00"
                }
                
                nuevo_df_temp = pd.DataFrame([nueva_fila])
                if df.empty:
                    df_final = nuevo_df_temp
                else:
                    df_final = pd.concat([df, nuevo_df_temp], ignore_index=True)
                
                with st.spinner("Guardando..."):
                    if guardar_todo_el_dataframe(df_final):
                        st.success(f"✅ Reserva guardada. Total a cobrar: {precio_total_calculado}€")
                        time.sleep(2)
                        st.rerun()

# ==========================================
# SECCIÓN 2: TABLA EDITABLE (CENTRO)
# ==========================================
st.markdown("---")
st.subheader("📝 Gestión de Reservas")
st.caption("Doble clic para editar. Selecciona la fila y pulsa 'Suprimir' para borrar.")

if not df.empty:
    edited_df = st.data_editor(
        df,
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True),
            "guestName": "Huésped",
            "startDate": st.column_config.DateColumn("Llegada", format="DD/MM/YYYY"),
            "endDate": st.column_config.DateColumn("Salida", format="DD/MM/YYYY"),
            "price": st.column_config.NumberColumn("Precio Total (€)", format="%.2f €"),
            "guests": st.column_config.NumberColumn("Pers."),
            "isTaoFamily": st.column_config.SelectboxColumn("Familia TAO", options=["Sí", "No"]),
            "checkInTime": st.column_config.TextColumn("Check-in") 
        },
        num_rows="dynamic",
        use_container_width=True,
        key="editor_principal"
    )

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("💾 GUARDAR CAMBIOS"):
            with st.spinner("Sincronizando..."):
                if guardar_todo_el_dataframe(edited_df):
                    st.success("Cambios guardados.")
                    time.sleep(1)
                    st.rerun()
else:
    st.info("La tabla está vacía.")

# ==========================================
# SECCIÓN 3: CALENDARIO (ABAJO)
# ==========================================
st.markdown("---")
st.subheader("📅 Calendario de Ocupación")

if not df.empty:
    try:
        eventos_calendario = []
        for index, row in df.iterrows():
            # Colores
            es_tao = str(row.get("isTaoFamily")) == "Sí"
            color_evento = "#FFD700" if es_tao else "#3788d8"
            border_color = "#B8860B" if es_tao else "#2C3E50"
            text_color = "#000000" if es_tao else "#FFFFFF"
            
            # Ajuste visual para calendario
            fecha_fin = row["endDate"]
            if isinstance(fecha_fin, (datetime, pd.Timestamp)):
                fecha_fin = fecha_fin.date()
            # Sumamos 1 día para que visualmente cubra la noche completa
            fecha_fin_visual = fecha_fin + timedelta(days=1)

            eventos_calendario.append({
                "title": f"{row['guestName']} ({int(row.get('guests', 1))}p)",
                "start": str(row["startDate"]),
                "end": str(fecha_fin_visual),
                "backgroundColor": color_evento,
                "borderColor": border_color,
                "textColor": text_color,
                "allDay": True
            })

        calendar_options = {
            "editable": False,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,listMonth"
            },
            "initialView": "dayGridMonth",
            "locale": "es",
            "buttonText": {"today": "Hoy", "month": "Mes", "list": "Lista"}
        }
        
        calendar(events=eventos_calendario, options=calendar_options)
        
        # Hucha Total
        st.markdown("---")
        total_money = df['price'].sum()
        st.metric("💰 Hucha Total (Ingresos Previstos)", f"{total_money:,.2f} €")
        
    except Exception as e:
        st.error(f"Error cargando calendario: {e}")
