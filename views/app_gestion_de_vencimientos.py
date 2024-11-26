import streamlit as st
import pandas as pd
from datetime import datetime
from modules.utils_gestion_de_vencimientos import process_data, create_excel
from components.charts_gestion_de_vencimientos import generate_bar_plot_from_line_data, generar_grafico, tabla_resumen, show_chart, kpi_valorizado

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
    st.write("Esta herramienta identifica automáticamente los materiales que vencerán en los próximos 90 días y evalúa su necesidad en las diferentes plantas, clasificándolos en 'Gestión', 'Traslado' y 'Sin necesidad'. Con esta información, podremos gestionar los materiales de manera efectiva y ademas genera un archivo Excel para facilitar el seguimiento y la toma de decisiones en la gestión de inventarios")
    
    # Generar gráfico de barras para el valorizado de vencimientos
    bar_options = generate_bar_plot_from_line_data(resultados_df)
    st.subheader("1.🔎 Evaluemos el valor de los materiales que están próximos a vencer en los próximos 90 días 🧐")
    kpi_1 = kpi_valorizado(resultados_df)
    
    show_chart(bar_options)
    
    # Generar gráfico de barras apiladas por estado
    tabla_resumen = tabla_resumen(resultados_df)
    st.subheader("2.✨ Analizamos e identificamos oportunidades de consumo para materiales próximos a vencer. 📊")
    st.write("Al aprovechar los posibles traslados, podremos minimizar el riesgo de pérdidas por vencimiento de materiales. ⏳")
    st.dataframe(tabla_resumen)

    # Generar gráfico collapsible con la función personalizada
    st.divider()
    st.subheader("3.🧐 Exploración de oportunidades de consumo para materiales próximos a vencer 👀")
    st.write("Utilizamos este gráfico interactivo para identificar los materiales que están próximos a vencer y los centros donde actualmente existe una necesidad. Así, podríamos trasladar los materiales para minimizar los riesgos de pérdida por vencimiento y también podremos verificar si hay alguna necesidad de esos materiales en nuestro propio centro. 🙂‍↕️")
    generar_grafico(detalles_df) 
    st.info('Recuerda que puedes obtener información más detallada sobre traslados, reservas y lotes si descargas el archivo de Excel con los resultados del análisis.')    
    # Botón para exportar a Excel
    if st.button("Generar reporte"):
        excel_file = create_excel(resultados_df, detalles_df)
        st.download_button(
            label="Descargar archivo excel",
            data=excel_file,
            file_name="resultados_gestion_vencimientos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )