import plotly.express as px
import pandas as pd
from streamlit_echarts import st_echarts
import ast
from collections import defaultdict
import plotly.graph_objects as go
import streamlit as st


def kpi_valorizado(resultados_df):
    # Sumar el total 'valorizado'
    total_valorizado = resultados_df['valorizado'].sum()

    # Formatear el valor como moneda en soles peruanos
    total_valorizado_formatted = f"S/. {total_valorizado:,.2f}"

    # CSS para dar estilo a la tarjeta
    st.markdown(
        """
        <style>
        .card {
            background-color: #f9f9f9;
            padding: 20px;
            margin: 10px;
            border-radius: 10px;
            border: 1px solid #ddd;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .card h4 {
            margin: 0;
            color: #333;
        }
        .card p {
            margin: 5px 0 0;
            font-size: 18px;
            font-weight: bold;
            color: #007BFF;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Crear la tarjeta usando HTML
    st.markdown(
        f"""
        <div class="card">
            <h3>Valorizado de vencimientos en los próximos 90 días</h3>
            <p>{total_valorizado_formatted}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return total_valorizado

def show_chart(fig):
    st.plotly_chart(fig, use_container_width=True)

def generate_bar_plot_from_line_data(resultados_df):
    # Convertir 'fecha_vencimiento' a formato datetime
    resultados_df['fecha_vencimiento'] = pd.to_datetime(resultados_df['fecha_vencimiento'], errors='coerce')
    
    # Agrupar por mes y sumar 'valorizado'
    valor_por_mes = resultados_df.groupby(resultados_df['fecha_vencimiento'].dt.to_period('M'))['valorizado'].sum().reset_index()
    
    # Redondear 'valorizado' a dos decimales
    valor_por_mes['valorizado'] = valor_por_mes['valorizado'].round(2)
    
    # Convertir Period a string en formato 'MM/YYYY'
    valor_por_mes['fecha_vencimiento'] = valor_por_mes['fecha_vencimiento'].dt.to_timestamp().dt.strftime('%m/%Y')

    # Crear el gráfico de líneas
    fig = go.Figure()

    # Añadir la línea suavizada
    fig.add_trace(go.Scatter(
        x=valor_por_mes['fecha_vencimiento'],
        y=valor_por_mes['valorizado'],
        mode='lines+markers',
        name='Valorizado',
        line=dict(shape='spline', smoothing=1.1, width=1.5),  # Línea suavizada y más gruesa
        marker=dict(
            symbol='circle-open',
            size=12,),  # Tamaño de los marcadores
    ))

    # Actualizar el diseño del gráfico
    fig.update_layout(
        title_font=dict(size=16,color='black'),
        yaxis_tickprefix='S/',
        yaxis_tickformat=',.2f',
        xaxis_tickangle=-45,
        yaxis=dict(
            showgrid=True, 
            gridcolor='AliceBlue',
            tickfont=dict( weight='bold')
            ),  # Color de la cuadrícula
        xaxis=dict(
            showgrid=True, 
            gridcolor='rgba(242, 226, 5, 1)',
            tickfont=dict( weight='bold')
            ),
        
        # Añadir fondo blanco semi-transparente a las etiquetas
        annotations=[
            dict(
                x=x,
                y=y,
                text=f"💰 S/{y:,.2f}",
                showarrow=True,
                yshift=20,
                font=dict(size=15,color='black'),
                bgcolor='rgba(191, 242, 5, 1)',
                borderwidth=1,
                borderpad=4                          # Padding interno
            )
            for x, y in zip(valor_por_mes['fecha_vencimiento'], valor_por_mes['valorizado'])
        ]
    )

    return fig



def generate_category_bar_plot(resultados_df):
    # Convertir 'fecha_vencimiento' a formato datetime
    resultados_df['fecha_vencimiento'] = pd.to_datetime(resultados_df['fecha_vencimiento'], errors='coerce')

    # Agrupar por mes y estado
    valor_por_estado = resultados_df.groupby([resultados_df['fecha_vencimiento'].dt.to_period('M'), 'estado'])['valorizado'].sum().reset_index()

    # Convertir Period a string en formato 'YYYY-MM'
    valor_por_estado['fecha_vencimiento'] = valor_por_estado['fecha_vencimiento'].astype(str)

    # Calcular el total por mes
    total_por_mes = valor_por_estado.groupby('fecha_vencimiento')['valorizado'].sum().reset_index()
    total_por_mes = total_por_mes.rename(columns={"valorizado": "total"})

    # Unir los totales al DataFrame original
    valor_por_estado = valor_por_estado.merge(total_por_mes, on='fecha_vencimiento')

    # Crear la tabla pivote sumando los valores de "valorizado"
    pivot_df = pd.pivot_table(valor_por_estado, 
                              index='estado', 
                              columns='fecha_vencimiento', 
                              values='valorizado', 
                              aggfunc='sum', 
                              fill_value=0)

    # Agregar columna de "Total general" por estado
    pivot_df['Total general'] = pivot_df.sum(axis=1)

    # Agregar fila de "Total general" por columna
    pivot_df.loc['Total general'] = pivot_df.sum()

    # Reordenar para que la fila de 'Total general' esté al final

    return pivot_df



# Función para asegurarse de que los campos que contienen listas se lean correctamente
def safe_eval(value):
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return [value]  # Devolver como lista de un solo elemento si no se puede evaluar
    return value if isinstance(value, list) else [value]

# Función para construir el árbol de datos
def build_tree(resultados_df):
    # Aplicar la función safe_eval para asegurar que todas las entradas sean listas
    resultados_df['centro_necesidad'] = resultados_df['centro_necesidad'].apply(safe_eval)
    resultados_df['cantidad_reservada'] = resultados_df['cantidad_reservada'].apply(safe_eval)

    tree = []
    centros_unicos = resultados_df['centro'].unique()

    for centro in centros_unicos:
        centro_data = resultados_df[resultados_df['centro'] == centro]
        centro_node = {"name": centro, "children": []}
        estado_nodos = defaultdict(lambda: {"name": "", "children": []})

        for _, row in centro_data.iterrows():
            codigo_material = row['codigo_material']
            descripcion = row['descripcion']
            estado = row['estado']
            cantidad = row['cantidad']
            centros_necesidad = row['centro_necesidad']
            cantidades_reservadas = row['cantidad_reservada']

            material_info = f"{codigo_material}: {descripcion} = {cantidad}"
            estado_node = estado_nodos[estado]
            if not estado_node["name"]:
                estado_node["name"] = f"{estado}"
                centro_node["children"].append(estado_node)

            material_node = next((child for child in estado_node["children"] if child["name"] == material_info), None)
            if not material_node:
                material_node = {"name": material_info, "children": []}
                estado_node["children"].append(material_node)

            # Asegurar que centros_necesidad y cantidades_reservadas tengan la misma longitud
            max_len = max(len(centros_necesidad), len(cantidades_reservadas))
            centros_necesidad = centros_necesidad + [None] * (max_len - len(centros_necesidad))
            cantidades_reservadas = cantidades_reservadas + [0] * (max_len - len(cantidades_reservadas))

            # Procesar centros de necesidad y cantidades reservadas
            for cn, cr in zip(centros_necesidad, cantidades_reservadas):
                if cn is not None:  # Asegurarse de que el centro de necesidad existe
                    cn_info = f"{cn} = {cr or 0}"
                    cn_node = next((child for child in material_node["children"] if child["name"] == cn_info), None)
                    if not cn_node:
                        # Crear un nuevo nodo para este centro de necesidad
                        material_node["children"].append({"name": cn_info})

        # Eliminar nodos de material sin hijos
        for estado_node in centro_node["children"]:
            estado_node["children"] = [child for child in estado_node["children"] if child["children"]]
        
        # Eliminar nodos de estado sin hijos
        centro_node["children"] = [child for child in centro_node["children"] if child["children"]]
        
        if centro_node["children"]:
            tree.append(centro_node)

    return {"name": "Materiales próximos a vencer", "children": tree}

# Función para generar y devolver el gráfico
def generar_grafico(df):
    tree_data = build_tree(df)

    # Opciones del gráfico con etiquetas estilizadas
    options = {
        "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
        "series": [{
            "type": "tree",
            "data": [tree_data],
            "top": "10%",
            "left": "5%",
            "bottom": "10%",
            "right": "20%",
            "symbolSize": 7,
            "label": {
                "position": "left",
                "verticalAlign": "middle",
                "align": "right",
                "fontSize": 12,
                "color": "#555",
                "backgroundColor": "rgba(255,255,255,0.8)",
                "padding": [4, 8, 4, 8],
                "borderRadius": 5,
                "borderColor": "#ccc",
                "borderWidth": 1,
                "shadowColor": "rgba(0, 0, 0, 0.2)",
                "shadowBlur": 3
            },
            "leaves": {
                "label": {
                    "position": "right",
                    "verticalAlign": "middle",
                    "align": "left"
                }
            },
            "emphasis": {"focus": "descendant"},
            "expandAndCollapse": True,
            "animationDuration": 550,
            "animationDurationUpdate": 750,
            "initialTreeDepth": 1,
            "roam": "move"
        }]
    }

    # Devolver el gráfico para mostrarlo
    return st_echarts(options=options, height="800px")
