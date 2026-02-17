import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🕵️‍♂️ Inspector de Llaves - Intento 2")

# Verificamos si la reparación funcionó
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.success("✅ ¡AHORA SÍ! La App ha encontrado las llaves.")
    st.write("Ahora sí puedes volver a poner el código de reservas.")
else:
    st.error("❌ SIGUE CIEGA. El problema está en el formato del texto en Secrets.")
    st.write("Por favor, mándame una captura de pantalla de cómo se ve tu caja de Secrets.")
