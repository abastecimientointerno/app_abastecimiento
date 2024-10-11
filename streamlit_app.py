import streamlit as st

st.set_page_config(layout="wide")

# Lista de páginas
pages = [
    {"module": "views/home.py", "title": "Inicio", "icon": ":material/home:", "default": True},
    {"module": "views/app_gestion_de_insumos.py", "title": "Gestión de insumos", "icon": ":material/local_fire_department:"},
    {"module": "views/app_gestion_de_vencimientos.py", "title": "Gestión de vencimientos", "icon": ":material/event_busy:"},
    {"module": "views/app_herramienta_de_planificacion.py", "title": "Herramienta de planificación", "icon": ":material/chart_data:"},
    {"module": "views/app_materiales_en_transito.py", "title": "Materiales en tránsito", "icon": ":material/local_shipping:"},
    # Agrega más páginas aquí
]

# Crear objetos de página
streamlit_pages = [
    st.Page(page["module"], title=page["title"], icon=page["icon"], default=page.get("default", False))
    for page in pages
]

# Agrupar páginas
pg = st.navigation({
    "Opciones": [streamlit_pages[0]],  # Inicio
    "Aplicaciones": streamlit_pages[1:],  # Las demás páginas
})

# Ocultar el ícono de GitHub
st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.logo("assets/logo.png")

pg.run()