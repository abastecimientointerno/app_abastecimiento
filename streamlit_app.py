import streamlit as st

# --- PAGE SETUP ---
st.set_page_config(layout="wide")  # Configuración del layout

about_page = st.Page(
    "views/home.py",
    title="Inicio",
    icon=":material/home:",
    default=True,
)

project_1_page = st.Page(
    "views/app_gestion_de_insumos.py",
    title="Gestion de insumo",
    icon=":material/local_fire_department:",
)

project_2_page = st.Page(
    "views/app_gestion_de_vencimientos.py",
    title="Gestion de vencimientos",
    icon=":material/event_busy:",
)
project_3_page = st.Page(
    "views/app_herramienta_de_planificacion.py",
    title="Herramienta de planificacion",
    icon=":material/chart_data:",
)
project_4_page = st.Page(
    "views/app_materiales_en_transito.py",
    title="Materiales en tránsito",
    icon=":material/local_shipping:",
)

# --- NAVIGATION SETUP [WITHOUT SECTIONS] ---
# pg = st.navigation(pages=[about_page, project_1_page, project_2_page])

# --- NAVIGATION SETUP [WITH SECTIONS]---
pg = st.navigation(
    {   
        "Opciones": [about_page],
        "Aplicaciones": [project_1_page, project_2_page,project_3_page,project_4_page],
    }
)
# Ocultar el ícono de GitHub
st.markdown(
    """
    <style>
    .stApp > header > div > div > div:nth-child(2) {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# --- SHARED ON ALL PAGES ---
st.logo("assets/logo.png")

# --- RUN NAVIGATION ---
pg.run()
