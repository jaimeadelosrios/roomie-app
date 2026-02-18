import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🕵️‍♂️ Diagnóstico Final")

# TU ID DE LA HOJA
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"

st.write("1. Intentando conectar con credenciales 'gsheets'...")

try:
    # Creamos la conexión
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    st.write("2. Intentando leer la hoja (Sin especificar nombre de pestaña)...")
    
    # LEEMOS SIN DECIR EL NOMBRE DE LA HOJA (Para evitar errores de nombres)
    df = conn.read(spreadsheet=SHEET_ID, ttl=0)
    
    st.success("✅ ¡LEÍDO CON ÉXITO!")
    st.write("Esto es lo que veo en la hoja:")
    st.dataframe(df)
    
    st.info("👇 Si ves la tabla arriba, copia el nombre de las columnas:")
    st.write(df.columns.tolist())

except Exception as e:
    st.error("❌ AQUÍ ESTÁ EL ERROR REAL:")
    # Imprimimos el error tal cual, sin ocultarlo
    st.code(str(e))
    
    st.markdown("---")
    st.warning("🔎 PISTAS:")
    error_text = str(e).lower()
    if "403" in error_text:
        st.write("👉 **403**: Google Drive API no está activa o el email del robot no tiene permiso.")
    elif "404" in error_text:
        st.write("👉 **404**: El ID de la hoja está mal o el robot no está invitado.")
    elif "worksheet" in error_text:
        st.write("👉 **Worksheet**: No encuentra la pestaña 'Reservas'.")
