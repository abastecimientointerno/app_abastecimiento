import streamlit as st

st.set_page_config(layout="wide")

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