import streamlit as st
import pandas as pd
from datetime import datetime
import time
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px  # Librería para el calendario visual

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="RoomieSync", page_icon="🏠", layout="wide") # Layout wide para que quepa el calendario
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
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        return df
    return pd.DataFrame()

def guardar_todo_el_dataframe(df_nuevo):
    """
    ⚠️ IMPORTANTE: Esta función BORRA la hoja y la REESCRIBE con los datos nuevos.
    Es la única forma de permitir ediciones y borrados complejos de forma sencilla.
    """
    ws = get_worksheet()
    if ws:
        try:
            # 1. Convertimos fechas a texto (string) para que Google no se queje
            df_guardar = df_nuevo.copy()
            df_guardar['startDate'] = df_guardar['startDate'].astype(str)
            df_guardar['endDate'] = df_guardar['endDate'].astype(str)
            
            # 2. Preparamos los datos (Lista de Listas)
            # Incluimos los encabezados
            datos_lista = [df_guardar.columns.values.tolist()] + df_guardar.values.tolist()
            
            # 3. Borramos y Escribimos
            ws.clear() # Limpia todo
            ws.update(datos_lista) # Escribe lo nuevo
            return True
        except Exception as e:
            st.error(f"Error al actualizar la hoja: {e}")
            return False
    return False

# --- CARGA INICIAL ---
df = cargar_datos()

# Procesamiento de tipos de datos (Fechas y Números)
if not df.empty:
    for col in ['startDate', 'endDate']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    if 'guests' in df.columns:
        df['guests'] = pd.to_numeric(df['guests'], errors='coerce').fillna(1)
    
    # Aseguramos que todas las columnas existan
    required_cols = ['id', 'guestName', 'startDate', 'endDate', 'guests', 'price', 'isTaoFamily', 'checkInTime']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

# --- INTERFAZ CON PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📅 Calendario Visual", "📝 Tabla (Editar/Borrar)", "➕ Añadir Reserva"])

# ==========================================
# PESTAÑA 1: CALENDARIO VISUAL (Gantt)
# ==========================================
with tab1:
    st.subheader("Ocupación Visual")
    if not df.empty:
        # Preparamos datos para el gráfico
        df_chart = df.copy()
        # Plotly necesita formato datetime completo, no solo date
        df_chart['Inicio'] = pd.to_datetime(df_chart['startDate'])
        df_chart['Fin'] = pd.to_datetime(df_chart['endDate'])
        
        # Colores: Si es familia TAO sale en Oro, si no, colores automáticos por nombre
        # Creamos una columna de color
        df_chart['Tipo'] = df_chart.apply(lambda x: 'Familia TAO ⭐' if str(x['isTaoFamily']) == "Sí" else x['guestName'], axis=1)

        fig = px.timeline(
            df_chart, 
            x_start="Inicio", 
            x_end="Fin", 
            y="guestName", # En el eje Y ponemos los nombres
            color="Tipo",  # Coloreamos por tipo o nombre
            title="Calendario de Reservas",
            labels={"guestName": "Huésped"},
            height=400
        )
        
        # Ajustes visuales para que parezca un calendario
        fig.update_yaxes(autorange="reversed") # Para que el primero salga arriba
        fig.update_layout(xaxis_title="Fechas", yaxis_title="")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas rápidas
        c1, c2 = st.columns(2)
        c1.metric("Reservas Totales", len(df))
        total_money = df['price'].sum()
        c2.metric("Hucha Estimada", f"{total_money} €")
        
    else:
        st.info("No hay datos para mostrar en el calendario.")

# ==========================================
# PESTAÑA 2: TABLA EDITOR (CRUD)
# ==========================================
with tab2:
    st.header("Gestión de Reservas")
    st.info("💡 **Instrucciones:** Puedes editar cualquier celda directamente. Para **BORRAR**, selecciona las filas a la izquierda y pulsa la tecla 'Suprimir' (Del) o usa el icono de papelera que aparecerá.")

    if not df.empty:
        # Mostramos el editor
        # num_rows="dynamic" permite añadir y borrar filas
        edited_df = st.data_editor(
            df,
            column_config={
                "id": st.column_config.TextColumn("ID", disabled=True), # Protegemos el ID
                "guestName": "Nombre Huésped",
                "startDate": st.column_config.DateColumn("Llegada", format="DD/MM/YYYY"),
                "endDate": st.column_config.DateColumn("Salida", format="DD/MM/YYYY"),
                "price": st.column_config.NumberColumn("Precio (€)", format="%.2f €"),
                "guests": st.column_config.NumberColumn("Pers.", min_value=1, max_value=10),
                "isTaoFamily": st.column_config.SelectboxColumn("¿Familia TAO?", options=["Sí", "No"]),
                "checkInTime": st.column_config.TimeColumn("Hora Check-in")
            },
            num_rows="dynamic", # ¡ESTO PERMITE BORRAR Y AÑADIR!
            use_container_width=True,
            key="editor_reservas"
        )

        # Botón para GUARDAR LOS CAMBIOS
        st.write("")
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("💾 GUARDAR CAMBIOS EN GOOGLE", type="primary"):
                with st.spinner("Sincronizando con la nube..."):
                    exito = guardar_todo_el_dataframe(edited_df)
                    if exito:
                        st.success("¡Base de datos actualizada correctamente!")
                        time.sleep(1)
                        st.rerun()
    else:
        st.warning("La tabla está vacía.")

# ==========================================
# PESTAÑA 3: FORMULARIO ORIGINAL
# ==========================================
with tab3:
    st.subheader("Nueva Reserva Rápida")
    with st.form("booking_form_tab"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre del Huésped")
            start = st.date_input("Llegada", min_value=datetime.today())
            guests = st.number_input("Personas", 1, 4, 1)
        with col2:
            price = st.number_input("Precio Total (€)", 0.0, step=5.0)
            end = st.date_input("Salida", min_value=datetime.today())
            is_tao = st.checkbox("¿Es familia de TAO? ⭐")
        
        submitted = st.form_submit_button("Añadir Reserva")
        
        if submitted:
            if not name:
                st.warning("Falta el nombre.")
            else:
                nueva_fila = {
                    "id": str(int(datetime.now().timestamp())),
                    "guestName": name,
                    "startDate": start, # Objeto date
                    "endDate": end,     # Objeto date
                    "guests": guests,
                    "price": price,
                    "isTaoFamily": "Sí" if is_tao else "No",
                    "checkInTime": "14:00"
                }
                
                # Añadimos la fila al DF actual y guardamos todo
                # Es más seguro reescribir todo para mantener consistencia
                nuevo_df_temp = pd.DataFrame([nueva_fila])
                if df.empty:
                    df_final = nuevo_df_temp
                else:
                    df_final = pd.concat([df, nuevo_df_temp], ignore_index=True)
                
                with st.spinner("Guardando..."):
                    guardar_todo_el_dataframe(df_final)
                    st.success("Reserva añadida.")
                    time.sleep(1)
                    st.rerun()
