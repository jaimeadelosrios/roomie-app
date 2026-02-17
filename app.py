import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

# --- Configuración de la Página ---
st.set_page_config(
    page_title="RoomieSync 2026",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Gestión de Datos (Híbrido: CSV Local o Google Sheets) ---
DATA_FILE = "bookings.csv"

def load_data():
    """
    Carga datos. Prioriza Google Sheets si está configurado en .streamlit/secrets.toml,
    de lo contrario usa un CSV local.
    """
    # 1. Intenta cargar desde Google Sheets (Producción)
    # Para usar esto, crea .streamlit/secrets.toml con tus credenciales
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read()
        return df
    except Exception:
        pass

    # 2. Fallback a CSV Local (Desarrollo / Demo)
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # Datos iniciales de ejemplo
        return pd.DataFrame([
            {
                "Guest": "Tía María (TAO)",
                "Start": "2026-01-05",
                "End": "2026-01-10",
                "Time": "15:00",
                "Guests": 2,
                "Price": 150,
                "IsTao": True,
                "Notes": "Viene de visita sorpresa"
            }
        ])

def save_data(df):
    """Guarda los datos en CSV local o Google Sheets"""
    # Guardar en CSV local siempre como respaldo
    df.to_csv(DATA_FILE, index=False)
    
    # Intentar guardar en Google Sheets si existe la conexión
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=df)
        st.toast("✅ Guardado en Google Sheets", icon="☁️")
    except:
        st.toast("✅ Guardado localmente", icon="💾")

# --- Lógica de Negocio ---
def check_overlap(new_start, new_end, df, ignore_index=None):
    """Verifica si hay solapamiento de fechas"""
    if df.empty:
        return False
        
    # Convertir columnas a datetime para comparar
    df_temp = df.copy()
    if ignore_index is not None:
        df_temp = df_temp.drop(ignore_index)
        
    df_temp['Start'] = pd.to_datetime(df_temp['Start']).dt.date
    df_temp['End'] = pd.to_datetime(df_temp['End']).dt.date
    
    # Lógica de solapamiento: (StartA <= EndB) and (EndA >= StartB)
    mask = (df_temp['Start'] <= new_end) & (df_temp['End'] >= new_start)
    return df_temp[mask].shape[0] > 0

# --- Interfaz Principal ---
st.title("🏠 RoomieSync")
st.markdown("Gestión de la habitación compartida.")

# Cargar estado
if 'data' not in st.session_state:
    st.session_state.data = load_data()

df = st.session_state.data

# Conversión de tipos para manipulación segura
df['Start'] = pd.to_datetime(df['Start']).dt.date
df['End'] = pd.to_datetime(df['End']).dt.date

# --- Pestañas de Navegación (Estilo App Móvil) ---
tab_home, tab_cal, tab_stats = st.tabs(["📝 Gestionar", "📅 Calendario", "📊 Info"])

# ==========================================
# PESTAÑA 1: INICIO (Formulario + Lista)
# ==========================================
with tab_home:
    # --- Formulario de Entrada ---
    with st.expander("➕ Nueva Reserva", expanded=True):
        with st.form("add_booking_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            guest_name = st.text_input("Huésped", placeholder="Ej. Juan Pérez")
            
            with col1:
                start_date = st.date_input("Llegada", date.today())
                check_in_time = st.time_input("Hora", datetime.strptime("14:00", "%H:%M").time())
            with col2:
                end_date = st.date_input("Salida", date.today() + timedelta(days=2))
                price = st.number_input("Precio Total (€)", min_value=0, step=10)
            
            c1, c2 = st.columns(2)
            with c1:
                num_guests = st.number_input("Personas", min_value=1, max_value=4, value=1)
            with c2:
                st.write("") # Spacer
                is_tao = st.checkbox("⭐ Familia TAO")
            
            submitted = st.form_submit_button("Guardar Reserva", use_container_width=True, type="primary")
            
            if submitted:
                if not guest_name:
                    st.error("⚠️ Falta el nombre del huésped")
                elif start_date > end_date:
                    st.error("⚠️ La fecha de salida debe ser posterior a la llegada")
                elif check_overlap(start_date, end_date, df):
                    st.error("⛔ ¡Conflicto! Ya hay una reserva en esas fechas.")
                else:
                    new_entry = pd.DataFrame([{
                        "Guest": guest_name,
                        "Start": start_date,
                        "End": end_date,
                        "Time": str(check_in_time)[:5],
                        "Guests": num_guests,
                        "Price": price,
                        "IsTao": is_tao,
                        "Notes": ""
                    }])
                    # Concatenar y guardar
                    updated_df = pd.concat([df, new_entry], ignore_index=True)
                    st.session_state.data = updated_df
                    save_data(updated_df)
                    st.rerun()

    # --- Tabla de Gestión (Editable) ---
    st.subheader("Reservas Activas")
    
    if not df.empty:
        # Ordenar por fecha
        df_sorted = df.sort_values(by="Start", ascending=True)
        
        # Usamos data_editor para permitir borrar/editar directamente
        edited_df = st.data_editor(
            df_sorted,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Guest": st.column_config.TextColumn("Nombre", width="medium", required=True),
                "Start": st.column_config.DateColumn("Entrada", format="DD/MM/YYYY"),
                "End": st.column_config.DateColumn("Salida", format="DD/MM/YYYY"),
                "Time": st.column_config.TimeColumn("Hora", format="HH:mm"),
                "Price": st.column_config.NumberColumn("€", format="%d €"),
                "IsTao": st.column_config.CheckboxColumn("⭐", width="small"),
                "Notes": st.column_config.TextColumn("Notas", width="small"),
                "Guests": st.column_config.NumberColumn("Pers.", min_value=1, max_value=4)
            },
            hide_index=True
        )

        # Detectar cambios y guardar
        # Nota: Comparar DataFrames es complejo, aquí guardamos si el tamaño cambia o valores cambian
        if not df_sorted.equals(edited_df):
            st.session_state.data = edited_df
            save_data(edited_df)
            st.rerun()
    else:
        st.info("No hay reservas. ¡Añade la primera arriba!")

# ==========================================
# PESTAÑA 2: CALENDARIO (Visualización)
# ==========================================
with tab_cal:
    st.subheader("Agenda Visual")
    
    if not df.empty:
        # Convertir a formato lista de diccionarios para iterar
        timeline_data = df.sort_values("Start").to_dict('records')
        
        current_month = None
        
        for booking in timeline_data:
            b_start = booking['Start']
            b_month_name = b_start.strftime("%B %Y").capitalize()
            
            # Cabecera de mes
            if b_month_name != current_month:
                st.markdown(f"### {b_month_name}")
                current_month = b_month_name
            
            # Tarjeta de Reserva
            tao_badge = "⭐" if booking['IsTao'] else ""
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 4px solid #6366f1; margin-bottom: 10px;">
                    <div style="font-weight: bold; font-size: 1.1em; color: #1e293b;">
                        {tao_badge} {booking['Guest']}
                    </div>
                    <div style="display: flex; justify-content: space-between; color: #64748b; font-size: 0.9em;">
                        <span>📅 {booking['Start'].strftime('%d')} - {booking['End'].strftime('%d %b')}</span>
                        <span>🕑 {booking['Time']}</span>
                    </div>
                    <div style="font-size: 0.8em; color: #94a3b8; margin-top: 4px;">
                        {booking['Guests']} pers. • {booking['Price']}€
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("Agenda vacía.")

# ==========================================
# PESTAÑA 3: ESTADÍSTICAS
# ==========================================
with tab_stats:
    st.subheader("Resumen Financiero")
    
    if not df.empty:
        # Filtros básicos por mes actual
        today = date.today()
        current_month_mask = (pd.to_datetime(df['Start']).dt.month == today.month) & \
                             (pd.to_datetime(df['Start']).dt.year == today.year)
        
        month_df = df[current_month_mask]
        
        col1, col2 = st.columns(2)
        
        # Métricas
        total_revenue = month_df['Price'].sum()
        total_bookings = len(month_df)
        tao_families = len(month_df[month_df['IsTao'] == True])
        
        # Calcular noches
        total_nights = 0
        for _, row in month_df.iterrows():
            total_nights += (row['End'] - row['Start']).days
            
        with col1:
            st.metric("Ingresos (Mes)", f"{total_revenue} €")
            st.metric("Noches Ocupadas", total_nights)
            
        with col2:
            st.metric("Reservas Totales", total_bookings)
            st.metric("Visitas Familia TAO", tao_families)
            
        st.markdown("---")
        st.caption(f"Datos calculados para {today.strftime('%B %Y')}")
        
    else:
        st.warning("Necesitas datos para ver estadísticas.")

