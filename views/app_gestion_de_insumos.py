import pandas as pd
import streamlit as st
from modules.utils_gestion_de_insumos import (generar_ids_y_stock, generar_ids_y_stock_valor, generar_y_separar_mb52, 
                        procesar_datos, consultar_pesca, realizar_proyeccion
)
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configuración de la app
st.title("Gestión de insumos")
st.subheader("Carga de archivos y parámetros:")
# Subida de archivos
uploaded_file_datasets = st.file_uploader("Cargar archivo :red[datasets]:", type="xlsx")
uploaded_file_mb51 = st.file_uploader("Cargar archivo :red[MB51]:", type="xlsx")
uploaded_file_mb52 = st.file_uploader("Cargar archivo :red[MB52]:", type="xlsx")

# Selectores de fechas con formato latinoamericano (día/mes/año)
inicio = st.date_input(":red[Selecciona la fecha de inicio de la pesca]:", datetime(2024, 4, 15), format="DD/MM/YYYY")
final = st.date_input(":red[Selecciona la fecha de cierre de la pesca]:", datetime(2024, 7, 6), format="DD/MM/YYYY")

# Convertir fechas a formato requerido
inicio_str = inicio.strftime("%Y%m%d")
final_str = final.strftime("%Y%m%d")

# Control para tolerancia con slider (0% a 100%)
tolerancia = st.slider("Selecciona el (%) de tolerancia para los :red[días de cobertura]", 0, 100, 10) / 100

# Función para cargar datos en paralelo
def cargar_datos_en_paralelo(archivos):
    dfs = {}
    with ThreadPoolExecutor() as executor:
        future_to_sheet = {
            executor.submit(pd.read_excel, archivo, sheet_name='Sheet1'): key
            for key, archivo in archivos.items() if key != 'datasets'
        }
        sheets_future = executor.submit(
            lambda: {sheet: pd.read_excel(archivos['datasets'], sheet_name=sheet) for sheet in ['db_capacidad_instalada', 'db_cuota', 'db_ratios_planta_insumo', 'db_insumos']}
        )
        
        for future in future_to_sheet:
            key = future_to_sheet[future]
            dfs[key] = future.result()

        dfs.update(sheets_future.result())
    
    return dfs

# Procesar datos principales
def procesar_datos_principales(dfs):
    # Crear mapeo de id_sap a id_insumo desde df_insumos
    df_insumos = pd.DataFrame(dfs['db_insumos'])
    mapeo_sap_insumo = df_insumos[['id_sap', 'id_insumo']].drop_duplicates()
    
    # Mapear id_insumo en MB51 y MB52
    if 'Material' in dfs['mb51'].columns:
        dfs['mb51'] = pd.merge(
            dfs['mb51'], 
            mapeo_sap_insumo.rename(columns={'id_sap': 'Material'}),
            on='Material', 
            how='left'
        )
    
    if 'Material' in dfs['mb52'].columns:
        dfs['mb52'] = pd.merge(
            dfs['mb52'], 
            mapeo_sap_insumo.rename(columns={'id_sap': 'Material'}),
            on='Material', 
            how='left'
        )
    
    df_valor_centros = generar_ids_y_stock_valor(dfs['mb52'], 'general')
    
    dfs['mb51'] = generar_ids_y_stock(dfs['mb51'])
    df_mb52_produccion, df_mb52_transito, df_mb52_hub, df_mb52_general = generar_y_separar_mb52(dfs['mb52'])
    df_cuota = pd.DataFrame(dfs['db_cuota'])
    
    df_ratios = pd.DataFrame(dfs['db_ratios_planta_insumo'])
    df_ratios['id_mix'] = df_ratios['id_localidad'] + df_ratios['id_insumo'].astype(str)
    
    df_homologado = pd.DataFrame(df_insumos)
    df_homologado['id_mix'] = df_homologado['id_localidad'] + df_homologado['id_insumo'].astype(str)
    
    df_homologacion = pd.merge(df_homologado, 
                               df_ratios[['id_mix','ratio_nominal','familia','familia_2']],
                               on='id_mix', how='left'
                               )
    
    df_base = pd.merge(df_homologacion, 
                       dfs['db_capacidad_instalada'][['id_localidad', 'cip', 'rendimiento', 'cobertura_ideal', 'maxima_descarga', 'cobertura_meta']],
                       on='id_localidad', how='left')
    
    df_base['stock_cobertura_ideal'] = (
        (df_base['ratio_nominal'] * df_base['maxima_descarga']) / df_base['rendimiento'] * df_base['cobertura_ideal']
        )
    
    # Calcular consumo total por id_localidad e id_insumo (no por id_sap)
    df_consumo_total = dfs['mb51'].groupby(['id_localidad', 'id_insumo'])['Cantidad'].sum().abs().reset_index()
    
    # Pesca api
    df_datos, df_dias_produccion = consultar_pesca(inicio_str, final_str)
    
    # Agregar días de pesca
    df_consumo_total = pd.merge(df_consumo_total, df_dias_produccion[['id_localidad', 'dias_de_pesca']], 
                                on='id_localidad', how='left')
    df_consumo_total['consumo_diario'] = df_consumo_total['Cantidad'] / df_consumo_total['dias_de_pesca'].fillna(1)
    
    df_consumo_total['id_localidad_insumo'] = df_consumo_total['id_localidad'].astype(str) + df_consumo_total['id_insumo'].astype(str)
    
    return df_valor_centros, df_base, df_mb52_produccion, df_mb52_transito, df_mb52_hub, df_mb52_general, df_consumo_total, df_datos, df_cuota

# Ejecutar análisis cuando se haga clic en el botón
if st.button("Ejecutar análisis"):
    if uploaded_file_datasets and uploaded_file_mb51 and uploaded_file_mb52:
        with st.spinner('Procesando los datos, por favor espera...'):
            # Cargar datos subidos
            archivos_subidos = {
                'datasets': uploaded_file_datasets,
                'mb51': uploaded_file_mb51,
                'mb52': uploaded_file_mb52,
            }
            dfs = cargar_datos_en_paralelo(archivos_subidos)
            # Procesar datos principales
            df_valor_centros, df_base, df_mb52_produccion, df_mb52_transito, df_mb52_hub, df_mb52_general, df_consumo_total, df_datos, df_cuota = procesar_datos_principales(dfs)
            
            # Procesar el resto de los datos
            df_resultado, df_resultado_por_insumo = procesar_datos(df_base, df_mb52_produccion, df_mb52_transito, df_mb52_hub, df_mb52_general, 
                                          df_consumo_total, dfs['db_insumos'])
            
            df_proyeccion_pesca = realizar_proyeccion(df_datos)
            
            # Guardar archivo Excel con los resultados
            with pd.ExcelWriter('resultados.xlsx') as writer:
                df_resultado.to_excel(writer, sheet_name='seguimiento_insumos', index=False)
                df_resultado_por_insumo.to_excel(writer, sheet_name='seguimiento_por_insumo', index=False)
                df_datos.to_excel(writer, sheet_name='seguimiento_pesca', index=False)
                df_valor_centros.to_excel(writer, sheet_name='valorizado_centros', index=False)
                df_proyeccion_pesca.to_excel(writer, sheet_name='proyeccion_pesca', index=False)
                df_cuota.to_excel(writer, sheet_name='cuota', index=False)

                # Hoja con la fecha y hora actual
                pd.DataFrame({'tolerancia': [tolerancia]}).to_excel(writer, sheet_name='parametros', index=False)

            # Crear botón de descarga para el archivo Excel
            with open("resultados.xlsx", "rb") as file:
                st.download_button(label="Descargar resultados en Excel", data=file, file_name="resultados.xlsx")
    else:
        st.warning("Por favor, sube todos los archivos requeridos antes de ejecutar el análisis.")
