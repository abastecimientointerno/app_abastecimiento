import streamlit as st
import pandas as pd
from datetime import datetime
from modules.utils_gestion_de_vencimientos import process_data, create_excel
from components.charts_gestion_de_vencimientos import generate_bar_plot_from_line_data, generate_bar_plot

st.title("Aplicación para gestión de vencimientos")

# Cargar archivos en la página principal
st.header("Carga de archivos Excel")
col1, col2 = st.columns(2)
with col1:
    mb52_file = st.file_uploader("Cargar archivo MB52", type=['xlsx'])
with col2:
    mb25_file = st.file_uploader("Cargar archivo MB25", type=['xlsx'])

# Solo proceder si ambos archivos han sido cargados
if mb52_file is not None and mb25_file is not None:
    mb52_df = pd.read_excel(mb52_file)
    mb25_df = pd.read_excel(mb25_file)

    # Procesar los datos
    resultados_df, detalles_df = process_data(mb52_df, mb25_df)

    # Mostrar resumen de vencimientos
    st.header("Resumen de vencimientos en los próximos 90 días")
    resultados_df['Fecha de Vencimiento'] = pd.to_datetime(resultados_df['Fecha de Vencimiento'])
    resultados_df['Fecha de Vencimiento'] = resultados_df['Fecha de Vencimiento'].dt.strftime('%b %Y').str.capitalize()

    # Generar gráfico de barras para el valorizado de vencimientos
    fig_barra_vencimientos = generate_bar_plot_from_line_data(resultados_df)
    st.plotly_chart(fig_barra_vencimientos)

    # Generar gráfico de barras para análisis de gestión de vencimiento
    fig_barras = generate_bar_plot(resultados_df)
    st.plotly_chart(fig_barras)

    # Botón para exportar a Excel
    if st.button("Generar reporte"):
        excel_file = create_excel(resultados_df, detalles_df)
        st.download_button(
            label="Descargar archivo excel",
            data=excel_file,
            file_name="resultados_gestion_logistica.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
