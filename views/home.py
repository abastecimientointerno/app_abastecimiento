import streamlit as st
import streamlit.components.v1 as components

# Título de la app con separación
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 20px;'>Hola, ¡bienvenido! 🐒</h1>
    <h6 style='text-align: center; margin-bottom: 100px;'>Utiliza esta aplicación para generar tus reportes de manera sencilla. Utiliza las diferentes herramientas disponibles en el menú lateral</6>
""", unsafe_allow_html=True)

# Cargar el HTML de partículas
components.html(open("particles.html").read(), height=700)
