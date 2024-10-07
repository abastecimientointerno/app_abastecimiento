import plotly.express as px
import pandas as pd

def generate_bar_plot_from_line_data(resultados_df):
    # Asegurarse de que 'Fecha de Vencimiento' esté en formato datetime
    resultados_df['Fecha de Vencimiento'] = pd.to_datetime(resultados_df['Fecha de Vencimiento'], errors='coerce')
    
    # Generar gráfico de barras para "Valorizado de vencimientos en los próximos 90 días"
    valor_por_fecha = resultados_df.groupby('Fecha de Vencimiento')['Valorizado'].sum().reset_index()
    
    # Ordenar por fecha de forma descendente
    valor_por_fecha = valor_por_fecha.sort_values(by='Fecha de Vencimiento', ascending=False)
    
    # Formatear la fecha a un formato de América Latina
    valor_por_fecha['Fecha de Vencimiento'] = valor_por_fecha['Fecha de Vencimiento'].dt.strftime('%d/%m/%Y')

    fig_barra_vencimientos = px.bar(
        valor_por_fecha, 
        x='Fecha de Vencimiento', 
        y='Valorizado', 
        title='Valorizado de vencimientos en los próximos 90 días',
        labels={'Valorizado': 'Valor Total', 'Fecha de Vencimiento': ''}
    )
    
    # Añadir anotaciones
    for i in range(len(valor_por_fecha)):
        valor_formateado = f"S/. {valor_por_fecha['Valorizado'][i]:,.2f}"
        fig_barra_vencimientos.add_annotation(
            x=valor_por_fecha['Fecha de Vencimiento'][i],
            y=valor_por_fecha['Valorizado'][i],
            text=valor_formateado,
            showarrow=False,  # Se quitan las flechas
            ax=0,
            ay=-30
        )
    
    fig_barra_vencimientos.update_xaxes(title='Fecha de Vencimiento')
    fig_barra_vencimientos.update_yaxes(title='Valor Total')
    return fig_barra_vencimientos

def generate_bar_plot(resultados_df):
    # Asegurarse de que 'Fecha de Vencimiento' esté en formato datetime
    resultados_df['Fecha de Vencimiento'] = pd.to_datetime(resultados_df['Fecha de Vencimiento'], errors='coerce')
    
    # Generar gráfico de barras para análisis de gestión de vencimiento
    valor_por_estado = resultados_df.groupby(['Fecha de Vencimiento', 'Estado'])['Valorizado'].sum().reset_index()
    valor_total_por_fecha = valor_por_estado.groupby('Fecha de Vencimiento')['Valorizado'].sum().reset_index()
    valor_por_estado = valor_por_estado.merge(valor_total_por_fecha, on='Fecha de Vencimiento', suffixes=('', '_total'))
    valor_por_estado['Porcentaje'] = (valor_por_estado['Valorizado'] / valor_por_estado['Valorizado_total']) * 100

    # Ordenar por fecha de forma descendente
    valor_por_estado = valor_por_estado.sort_values(by='Fecha de Vencimiento', ascending=False)
    
    # Crear el gráfico apilado al 100%
    fig_barras = px.bar(
        valor_por_estado, 
        x='Fecha de Vencimiento', 
        y='Porcentaje', 
        color='Estado',
        title='Análisis de gestión de vencimiento',
        labels={'Porcentaje': 'Porcentaje (%)', 'Fecha de Vencimiento': ''},
        barmode='stack',  # Cambiado a 'stack' para apilar
        color_discrete_sequence=['#FFC107', '#F44336', '#9C27B0']  # Colores: Ámbar, Rojo y Magenta
    )

    # Añadir anotaciones de porcentaje directamente sobre las barras
    for i in range(len(valor_por_estado)):
        porcentaje_formateado = f"{valor_por_estado['Porcentaje'][i]:,.2f}%"
        fig_barras.add_annotation(
            x=valor_por_estado['Fecha de Vencimiento'][i],
            y=valor_por_estado['Porcentaje'][i],
            text=porcentaje_formateado,
            showarrow=False,  # Se quitan las flechas
            font=dict(size=10, color="black"),
            yshift=5  # Ajuste para que no se superponga a la barra
        )
    
    fig_barras.update_xaxes(title='Fecha de Vencimiento', categoryorder='total ascending')  # Ordenar el eje x correctamente
    fig_barras.update_yaxes(title='Porcentaje (%)')
    
    # Mover la leyenda a la parte superior centrada
    fig_barras.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(tickformat=".0%")  # Formato del eje y en porcentajes
    )

    return fig_barras