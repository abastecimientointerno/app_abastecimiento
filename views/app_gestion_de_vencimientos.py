import streamlit as st
import pandas as pd
import plotly.express as px
from modules.utils_gestion_de_vencimientos import process_data, create_excel
from datetime import datetime

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
    # Generar gráfico de línea
    valor_por_fecha = resultados_df.groupby('Fecha de Vencimiento')['Valorizado'].sum().reset_index()
    fig_linea = px.line(
        valor_por_fecha, 
        x='Fecha de Vencimiento', 
        y='Valorizado', 
        title='Valorizado de vencimientos en los próximos 90 días',
        labels={'Valorizado': 'Valor Total', 'Fecha de Vencimiento': ''},
        line_shape='spline'
    )
    # Añadir anotaciones
    for i in range(len(valor_por_fecha)):
        valor_formateado = f"S/. {valor_por_fecha['Valorizado'][i]:,.2f}"
        fig_linea.add_annotation(
            x=valor_por_fecha['Fecha de Vencimiento'][i],
            y=valor_por_fecha['Valorizado'][i],
            text=valor_formateado,
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-30
        )
    fig_linea.update_xaxes(autorange='reversed')
    st.plotly_chart(fig_linea)
    # Gráfico de barras
    valor_por_estado = resultados_df.groupby(['Fecha de Vencimiento', 'Estado'])['Valorizado'].sum().reset_index()
    valor_total_por_fecha = valor_por_estado.groupby('Fecha de Vencimiento')['Valorizado'].sum().reset_index()
    valor_por_estado = valor_por_estado.merge(valor_total_por_fecha, on='Fecha de Vencimiento', suffixes=('', '_total'))
    valor_por_estado['Porcentaje'] = (valor_por_estado['Valorizado'] / valor_por_estado['Valorizado_total']) * 100
    fig_barras = px.bar(
        valor_por_estado, 
        x='Fecha de Vencimiento', 
        y='Porcentaje', 
        color='Estado',
        title='Análisis de gestión de vencimiento',
        labels={'Porcentaje': 'Porcentaje (%)', 'Fecha de Vencimiento': ''},
        barmode='relative'
    )
    fig_barras.update_xaxes(autorange='reversed')
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