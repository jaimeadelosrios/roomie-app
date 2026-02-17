import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🕵️‍♂️ Inspector Final")

# Verificamos si al borrar el espacio ya lo detecta
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.balloons()
    st.success("✅ ¡BINGO! ¡YA TENEMOS LAS LLAVES!")
    st.write("Ahora la App ya sabe quién es el robot. Puedes poner el código de reservas.")
else:
    st.error("❌ SIGUE SIN VERLO. Asegúrate de que la primera línea es '[connections.gsheets]' totalmente pegada a la izquierda.")
