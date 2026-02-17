import streamlit as st

st.title("🕵️‍♂️ Inspector Básico")

st.write("Contenido bruto de los secretos:")
st.write(st.secrets)

if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.success("✅ ¡CONEXIÓN DETECTADA!")
    st.write(f"Dato de prueba: {st.secrets.connections.gsheets.get('prueba', 'No leído')}")
else:
    st.error("❌ SIGUE CIEGO. El problema es tu navegador o el editor.")
