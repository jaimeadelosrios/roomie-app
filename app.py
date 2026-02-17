import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🕵️‍♂️ Inspector de Llaves")

# 1. Comprobamos si Streamlit ve la sección [connections.gsheets]
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.success("✅ ¡BINGO! La App ha encontrado la caja fuerte [connections.gsheets]")
    
    creds = st.secrets.connections.gsheets
    
    # 2. Verificamos la clave privada (que es la que suele fallar)
    if "private_key" in creds:
        key = creds["private_key"]
        if "-----BEGIN PRIVATE KEY-----" in key:
            st.success("✅ La clave privada parece válida (tiene el encabezado correcto).")
            # Imprimimos los primeros caracteres para verificar que no es nula
            st.info(f"Clave detectada: {key[:30]}...")
        else:
            st.error("⚠️ La clave privada existe pero NO tiene el formato correcto (le falta el encabezado).")
    else:
        st.error("❌ DANGER: Falta la línea 'private_key' dentro de los secrets.")

    # 3. Intentamos conectar
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        st.write("Objeto de conexión creado correctamente.")
    except Exception as e:
        st.error(f"Error al crear el objeto: {e}")

else:
    st.error("❌ LA APP ESTÁ CIEGA: No encuentra [connections.gsheets] en los Secrets.")
    st.warning("Esto significa que hay un error de escritura en el archivo secrets.toml. Puede ser un espacio antes del corchete o una comilla sin cerrar.")
    st.write("Lo que la App ve en realidad es esto:")
    st.write(st.secrets)
