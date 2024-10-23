import streamlit as st
import pandas as pd
from datetime import datetime
from modules.utils_gestion_de_vencimientos import process_data, create_excel
from components.charts_gestion_de_vencimientos import generate_bar_plot_from_line_data, generar_grafico, generate_category_bar_plot, show_chart, kpi_valorizado

st.title("Gestión de vencimientos")

# Cargar archivos en la página principal
st.subheader("Carga de archivos")
col1, col2 = st.columns(2)
with col1:
    mb52_file = st.file_uploader("Cargar archivo :red[MB52]:", type=['xlsx'])
with col2:
    mb25_file = st.file_uploader("Cargar archivo :red[MB25]:", type=['xlsx'])

# Solo proceder si ambos archivos han sido cargados
if mb52_file is not None and mb25_file is not None:
    mb52_df = pd.read_excel(mb52_file)
    mb25_df = pd.read_excel(mb25_file)

    # Procesar los datos
    resultados_df, detalles_df = process_data(mb52_df, mb25_df)
    st.divider()
    # Mostrar resumen de vencimientos
    st.header("¿Que hace la herramienta? 🤔")
    st.write("Identifica automáticamente los materiales que están próximos a vencer en los próximos 90 días. Luego, evalúa la necesidad de estos materiales en diferentes plantas. Los resultados se clasifican en tres categorías: Gestión para materiales requeridos en la misma planta, Traslado para aquellos que necesitan ser enviados a otra planta, y Sin necesidad para los que no presentan demanda. Además, tendrás la opción de generar un archivo Excel con toda la información, facilitando el seguimiento y la toma de decisiones estratégicas en la gestión de inventarios.")
    
    # Generar gráfico de barras para el valorizado de vencimientos
    bar_options = generate_bar_plot_from_line_data(resultados_df)
    st.subheader("Valorizado de proximo a vencer 🧐")
    kpi_1 = kpi_valorizado(resultados_df)
    
    show_chart(bar_options)
    
    # Generar gráfico de barras apiladas por estado
    category_options = generate_category_bar_plot(resultados_df)
    st.subheader("📊 Análisis de necesidades en otros centros 📊")
    st.write("Si aprovechamos los posibles traslados podriamos evitar una posible perdida por vencimiento ✨")
    st.dataframe(category_options)

    
    # Generar gráfico collapsible con la función personalizada
    st.divider()
    st.subheader("Distribución de necesidades 👀")
    st.write("Utiliza este gráfico interactivo para analizar los materiales que están próximos a vencer y las plantas donde existe una necesidad actualmente 🙂‍↕️")
    generar_grafico(detalles_df) 

    # Botón para exportar a Excel
    if st.button("Generar reporte"):
        excel_file = create_excel(resultados_df, detalles_df)
        st.download_button(
            label="Descargar archivo excel",
            data=excel_file,
            file_name="resultados_gestion_logistica.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )