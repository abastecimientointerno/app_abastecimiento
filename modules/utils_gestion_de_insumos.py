import pandas as pd
import numpy as np
from typing import Tuple, List
from streamlit_echarts import st_echarts
import requests
import json
from prophet import Prophet

def generar_id_localidad(centro: str, almacen: str) -> str:
    """Genera un ID de localidad basado en el Centro y el Almacén."""
    return 'TCNO-HUB' if centro == 'TCNO' and almacen == 'HUB' else centro

def generar_ids_y_stock(df: pd.DataFrame, tipo: str = 'general') -> pd.DataFrame:
    """Genera las columnas necesarias para un DataFrame específico."""
    df['id_localidad'] = df.apply(lambda row: generar_id_localidad(row['Centro'], row['Almacén']), axis=1)
    df['id_insumo'] = df['Material']
    
    if 'Libre utilización' in df.columns and 'Inspecc.de calidad' in df.columns and tipo == 'general':
        df['stock_libre_mas_calidad'] = df['Libre utilización'] + df['Inspecc.de calidad']
    
    df['id_localidad_insumo'] = df['id_localidad'] + df['id_insumo'].astype(str)
    return df

def generar_ids_y_stock_valor(df: pd.DataFrame, tipo: str = 'general') -> pd.DataFrame:
    """Genera las columnas necesarias y calcula valores para un DataFrame específico."""
    df = generar_ids_y_stock(df, tipo)
    
    if 'Valor libre util.' in df.columns and 'Valor en insp.cal.' in df.columns and tipo == 'general':
        df['valor_libre_mas_calidad'] = df['Valor libre util.'] + df['Valor en insp.cal.']
    
    return df.groupby('id_localidad')[['stock_libre_mas_calidad', 'valor_libre_mas_calidad']].sum().reset_index()

def generar_y_separar_mb52(df: pd.DataFrame, tipo: str = 'general') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Genera las columnas necesarias para el DataFrame MB52 y lo separa en cuatro DataFrames según el almacén."""
    df = generar_ids_y_stock(df, tipo)
    
    df = df.groupby(['id_localidad', 'Almacén', 'id_insumo', 'id_localidad_insumo'])['stock_libre_mas_calidad'].sum().reset_index()
    
    def filter_and_rename(df, almacen, suffix):
        filtered = df[df['Almacén'] == almacen].copy()
        filtered = filtered.rename(columns={'stock_libre_mas_calidad': f'stock_libre_mas_calidad_{suffix}'})
        return filtered
    
    df_mb52_produccion = filter_and_rename(df, 'PI01', 'produccion')
    df_mb52_transito = filter_and_rename(df, '', 'transito')
    df_mb52_hub = filter_and_rename(df, 'L003', 'hub')
    df_mb52_general = df[~df['Almacén'].isin(['PI01', '', 'L003'])].copy()
    df_mb52_general = df_mb52_general.rename(columns={'stock_libre_mas_calidad': 'stock_libre_mas_calidad_general'})
    
    return df_mb52_produccion, df_mb52_transito, df_mb52_hub, df_mb52_general


def calcular_cobertura(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula varias métricas de cobertura para el DataFrame."""
    df['stock_cobertura_ideal'] = (df['ratio_nominal'] * df['maxima_descarga']) / df['rendimiento'] * df['cobertura_ideal']
    
    for tipo in ['general', 'hub', 'transito', 'produccion']:
        col = f'stock_libre_mas_calidad_{tipo}'
        if tipo == 'general':
            df[col] = df[col].fillna(0)
        acumulado = df[[c for c in df.columns if c.startswith('stock_libre_mas_calidad_') and c <= col]].sum(axis=1)
        
        df[f'cobertura_teorica_con_stock_{tipo}'] = np.where(
            df['ratio_nominal'] != 0,
            (acumulado * df['cobertura_ideal']) / df['stock_cobertura_ideal'].replace(0, 1),
            0
        )
        
        df[f'cobertura_real_{tipo}'] = np.where(
            df['ratio_nominal'] != 0,
            acumulado / df['consumo_diario'],
            0
        )
    
    cobertura_cols = [col for col in df.columns if col.startswith('cobertura_real_')]
    df[cobertura_cols] = df[cobertura_cols].replace([np.inf, -np.inf], 0)
    
    return df

def procesar_datos(df_base: pd.DataFrame, df_mb52_produccion: pd.DataFrame, df_mb52_transito: pd.DataFrame, 
                   df_mb52_hub: pd.DataFrame, df_mb52_general: pd.DataFrame, df_consumo_total: pd.DataFrame, 
                   df_insumos: pd.DataFrame) -> pd.DataFrame:
    """Procesa y combina los diferentes DataFrames para generar el resultado final."""
    df_base['id_localidad_insumo'] = df_base['id_localidad'] + df_base['id_insumo'].astype(str)
    
    # Asegúrate de que todas las columnas necesarias estén presentes
    stock_columns = [
        'stock_libre_mas_calidad_produccion',
        'stock_libre_mas_calidad_transito',
        'stock_libre_mas_calidad_hub',
        'stock_libre_mas_calidad_general'
    ]
    
    for df, col in zip([df_mb52_produccion, df_mb52_transito, df_mb52_hub, df_mb52_general], stock_columns):
        df_base = pd.merge(df_base, df[['id_localidad_insumo', col]], on='id_localidad_insumo', how='left')
    
    df_base = df_base.fillna(0)
    
    # Calcula el stock_libre_mas_calidad total
    df_base['stock_libre_mas_calidad'] = df_base[stock_columns].sum(axis=1)
    
    df_base['excedentes'] = np.maximum(df_base['stock_libre_mas_calidad'] - df_base['stock_cobertura_ideal'], 0)
    df_base['faltantes'] = np.maximum(df_base['stock_cobertura_ideal'] - df_base['stock_libre_mas_calidad'], 0)
    
    df_base = pd.merge(df_base, df_consumo_total[['id_localidad_insumo', 'consumo_diario', 'Cantidad', 'dias_de_pesca']], 
                       on='id_localidad_insumo', how='left')
    
    df_base = calcular_cobertura(df_base)
    
    return df_base
    


#Api portal pesca
def consultar_pesca(inicio, final):
    # URL de la API
    url = "https://node-flota-prd.cfapps.us10.hana.ondemand.com/api/reportePesca/ConsultarPescaDescargada"

    # Encabezados de la solicitud
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-ES,es;q=0.9",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://tasaproduccion.launchpad.cfapps.us10.hana.ondemand.com",
    }

    # Datos de la solicitud (payload)
    payload = {
        "p_options": [],
        "options": [
            {
                "cantidad": "10",
                "control": "MULTIINPUT",
                "key": "FECCONMOV",
                "valueHigh": final,
                "valueLow": inicio
            }
        ],
        "p_rows": "",
        "p_user": "JHUAMANCIZA"
    }

    # Realizar la solicitud POST
    response = requests.post(url, headers=headers, json=payload)

    # Verificar la respuesta
    if response.status_code == 200:
        # Convertir la respuesta JSON a un diccionario de Python
        response_dict = response.json()

        # Crear un DataFrame a partir de los datos de "str_des"
        df_datos = pd.DataFrame(response_dict['str_des'])

        # Convertir la columna "FCSAZ" a tipo datetime para trabajar con fechas
        df_datos['FCSAZ'] = pd.to_datetime(df_datos['FCSAZ'], format='%d/%m/%Y')

        # Eliminar duplicados para contar solo días únicos de pesca por planta
        unique_days_per_plant = df_datos[['WERKS', 'FCSAZ']].drop_duplicates()

        # Contar los días únicos de pesca por cada planta
        df_dias_produccion = unique_days_per_plant['WERKS'].value_counts().reset_index()
        df_dias_produccion.columns = ['id_localidad', 'dias_de_pesca']

        return df_datos, df_dias_produccion

    else:
        print(f"Error: {response.status_code}")
        return None, None

#Proyecciones
def realizar_proyeccion(df_pesca):
    # Convertir la columna de fecha a tipo datetime
    df_pesca['ds'] = pd.to_datetime(df_pesca['FIDES'], dayfirst=True)

    # Asegurarse de que la columna CNPDS sea numérica, convirtiendo errores a NaN
    df_pesca['CNPDS'] = pd.to_numeric(df_pesca['CNPDS'], errors='coerce')

    # Rellenar NaN con 0
    df_pesca['CNPDS'] = df_pesca['CNPDS'].fillna(0)

    # Totalizar por día (sumar todas las descargas en cada día)
    df_daily = df_pesca.groupby('ds')['CNPDS'].sum().reset_index()

    # Renombrar columnas para que Prophet pueda trabajar con ellas ('ds' para fecha y 'y' para la variable objetivo)
    df_daily.columns = ['ds', 'y']

    # Crear y ajustar el modelo Prophet
    model = Prophet()
    model.fit(df_daily)

    # Crear un DataFrame con las fechas a futuro para predecir (por ejemplo, 30 días hacia adelante)
    future = model.make_future_dataframe(periods=15)

    # Hacer las predicciones
    forecast = model.predict(future)

    # Asegurarse de que no haya valores negativos
    forecast['yhat'] = forecast['yhat'].apply(lambda x: max(0, x))
    forecast['yhat_lower'] = forecast['yhat_lower'].apply(lambda x: max(0, x))
    forecast['yhat_upper'] = forecast['yhat_upper'].apply(lambda x: max(0, x))

    # Agregar los datos reales a la proyección
    # Unir los datos reales y las predicciones por fecha
    forecast = forecast.merge(df_daily, on='ds', how='left')
    
    # Renombrar la columna 'y' para que refleje que son datos reales
    forecast.rename(columns={'y': 'real_data'}, inplace=True)

    # Devolver el DataFrame de proyección con los datos reales
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'real_data']]