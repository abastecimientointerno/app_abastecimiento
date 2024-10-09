import plotly.express as px
import pandas as pd
from streamlit_echarts import st_echarts
import ast
from collections import defaultdict





def generate_bar_plot_from_line_data(resultados_df):
    # Convertir 'fecha_vencimiento' a formato datetime
    resultados_df['fecha_vencimiento'] = pd.to_datetime(resultados_df['fecha_vencimiento'], errors='coerce')
    
    # Agrupar por mes y sumar 'valorizado'
    valor_por_mes = resultados_df.groupby(resultados_df['fecha_vencimiento'].dt.to_period('M'))['valorizado'].sum().reset_index()
    
    # Redondear 'valorizado' a dos decimales
    valor_por_mes['valorizado'] = valor_por_mes['valorizado'].round(2)
    
    # Convertir Period a string en formato 'YYYY-MM'
    valor_por_mes['fecha_vencimiento'] = valor_por_mes['fecha_vencimiento'].astype(str)
    
    # Formatear los valores para las etiquetas y el eje Y
    valor_por_mes['valorizado_formatted'] = valor_por_mes['valorizado'].apply(lambda x: f"{x:,.2f}")
    
    # Crear opciones para el gráfico de barras
    options = {
        "title": {"text": "Valorizado de vencimientos por mes"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "category",
            "data": valor_por_mes['fecha_vencimiento'].tolist(),
            "axisLabel": {"rotate": 45, "formatter": "{value}"}
        },
        "yAxis": {
            "type": "value",
            "name": "Valor Total (S/.)",
            "axisLabel": {
            }
        },
        "series": [{
            "name": "Valorizado",
            "type": "bar",
            "data": valor_por_mes['valorizado'].tolist(),
            "label": {
                "show": True,
                "formatter": valor_por_mes['valorizado_formatted'].tolist()  # Usar los valores formateados
            }
        }]
    }
    return options






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

    # Calcular el porcentaje, redondeando a 2 decimales
    valor_por_estado['porcentaje'] = round((valor_por_estado['valorizado'] / valor_por_estado['total']) * 100, 2)

    # Preparar datos para el gráfico
    fechas = valor_por_estado['fecha_vencimiento'].unique().tolist()
    estados = valor_por_estado['estado'].unique().tolist()

    series_data = []
    for estado in estados:
        data = valor_por_estado[valor_por_estado['estado'] == estado]['porcentaje'].tolist()
        series_data.append({
            "name": estado,
            "type": "bar",
            "stack": "total",
            "label": {
                "show": True,
                "position": "inside",
                # Ajustar el formato para mostrar solo dos decimales
                "formatter": "{c} %"
            },
            "data": data
        })

    # Crear opciones para el gráfico de barras apiladas
    options = {
        "title": {"text": "Valorizado según su estado"},
        "tooltip": {
            "trigger": "axis",
            # Ajustar el tooltip para mostrar valores con formato de porcentaje redondeado a 2 decimales
            "formatter": "{b0}: {c0} %"
        },
        "legend": {"data": estados, "top": "bottom"},
        "xAxis": {
            "type": "category",
            "data": fechas,
            "axisLabel": {"rotate": 45, "formatter": "{value}"}
        },
        "yAxis": {
            "type": "value",
            "name": "Porcentaje (%)",
            "axisLabel": {"formatter": "{value} %"}
        },
        "series": series_data
    }

    return options




def show_chart(options):
    st_echarts(options=options, height="400px")

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
