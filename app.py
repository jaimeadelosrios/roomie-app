import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🕵️‍♂️ Test de Conexión")

# TU ID DE LA HOJA NUEVA (Matrícula exacta)
SHEET_ID = "1rG8NJjJDZvcpnmTzDQa5iNx8hoLaxw5VHgR2qomFMFc"

try:
    # 1. Intentamos conectar
    conn = st.connection("roomie", type=GSheetsConnection)
    
    # 2. Intentamos leer
    st.write(f"Intentando conectar a la hoja: `{SHEET_ID}`...")
    df = conn.read(spreadsheet=SHEET_ID, ttl=0)
    
    # 3. Si llega aquí, es ÉXITO
    st.success("✅ ¡CONEXIÓN ÉXITOSA! El robot ha entrado.")
    st.write("Esto es lo que veo en la hoja:")
    st.dataframe(df)

except Exception as e:
    # 4. Si falla, nos dirá por qué
    st.error("❌ EL ROBOT NO PUEDE ENTRAR.")
    st.error(f"Mensaje técnico: {e}")
    st.info("💡 PISTA: Si dice '404' o 'Permission denied', es que NO has invitado al email 'romiesync@...' a esta hoja nueva.")
