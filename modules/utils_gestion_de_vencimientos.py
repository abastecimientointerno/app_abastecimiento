import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.formatting.rule import ColorScaleRule

def process_data(mb52_df, mb25_df):
    mb52_df['Cad./FPC'] = pd.to_datetime(mb52_df['Cad./FPC'], errors='coerce')
    mb25_df['Fecha de necesidad'] = pd.to_datetime(mb25_df['Fecha de necesidad'], errors='coerce')
    
    fecha_limite = datetime.now() + timedelta(days=90)
    proximos_a_vencer = mb52_df[(mb52_df['Cad./FPC'] > datetime.now()) & (mb52_df['Cad./FPC'] <= fecha_limite)]
    
    resultados = []
    detalles = []
    
    for index, material in proximos_a_vencer.iterrows():
        centro = material['Centro']
        material_id = material['Material']
        material_texto = material['Texto breve de material']
        cantidad_disponible = material['Libre utilización']
        lote = material['Lote']
        valorizado = material['Valor libre util.']
        almacen = material['Almacén']
        ubicacion = material['Ubicación']
        fecha_vencimiento = material['Cad./FPC']

        reservas_mismo_centro = mb25_df[(mb25_df['Texto breve de material'] == material_texto) & 
                                          (mb25_df['Centro'] == centro)]
        reservas_otro_centro = mb25_df[(mb25_df['Texto breve de material'] == material_texto) & 
                                         (mb25_df['Centro'] != centro)]
        
        if not reservas_mismo_centro.empty:
            estado = "Gestión"
            cantidad_reservada = reservas_mismo_centro['Cantidad diferencia'].sum()
            num_reservas = reservas_mismo_centro['Nº reserva'].tolist()
            detalles.append({
                'Centro': centro,
                'Código Material': material_id,
                'Descripción': material_texto,
                'Cantidad Disponible': cantidad_disponible,
                'Unidad de Medida': material['Unidad medida base'],
                'Centro Necesidad': centro,
                'Cantidad Reservada': reservas_mismo_centro['Cantidad diferencia'].tolist(),
                'Número de Reservas': num_reservas,
                'Posición': reservas_mismo_centro['Nº pos.reserva traslado'].tolist(),
                'Estado': estado
            })
        elif not reservas_otro_centro.empty:
            estado = "Traslado"
            cantidad_reservada = reservas_otro_centro['Cantidad diferencia'].sum()
            num_reservas = reservas_otro_centro['Nº reserva'].tolist()
            centro_necesidad = reservas_otro_centro['Centro'].unique().tolist()
            detalles.append({
                'Centro': centro,
                'Código Material': material_id,
                'Descripción': material_texto,
                'Cantidad Disponible': cantidad_disponible,
                'Unidad de Medida': material['Unidad medida base'],
                'Centro Necesidad': centro_necesidad,
                'Cantidad Reservada': reservas_otro_centro['Cantidad diferencia'].tolist(),
                'Número de Reservas': num_reservas,
                'Posición': reservas_otro_centro['Nº pos.reserva traslado'].tolist(),
                'Estado': estado
            })
        else:
            estado = "Sin necesidad"
            cantidad_reservada = 0
            num_reservas = []

        resultados.append({
            'Centro': centro,
            'Material': material_id,
            'Descripción': material_texto,
            'Almacén': almacen,
            'Lote': lote,
            'Valorizado': valorizado,
            'Ubicación': ubicacion,
            'Fecha de Vencimiento': fecha_vencimiento,
            'Cantidad Disponible': cantidad_disponible,
            'Cantidad Reservada': cantidad_reservada,
            'Estado': estado
        })
    
    resultados_df = pd.DataFrame(resultados)
    detalles_df = pd.DataFrame(detalles)
    
    return resultados_df, detalles_df

def create_excel(resultados_df, detalles_df):
    resumen_centro_estado = resultados_df.pivot_table(
        values='Valorizado',
        index='Centro',
        columns='Estado',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    for estado in ['Gestión', 'Traslado', 'Sin necesidad']:
        if estado not in resumen_centro_estado.columns:
            resumen_centro_estado[estado] = 0
    
    resumen_centro_estado = resumen_centro_estado[['Centro', 'Gestión', 'Traslado', 'Sin necesidad']]
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        resultados_df.to_excel(writer, sheet_name='Resumen', index=False)
        detalles_df.to_excel(writer, sheet_name='Detalle', index=False)
        resumen_centro_estado.to_excel(writer, sheet_name='Resumen por Centro', index=False)
        
        workbook = writer.book
        worksheet = workbook['Resumen por Centro']
        
        # Formatear celdas
        for col in ['B', 'C', 'D']:
            for cell in worksheet[col][1:]:
                cell.number_format = '"S/. "#,##0.00'
        
        # Normalización por fila y gráficos
        for row in worksheet.iter_rows(min_row=2, min_col=2, max_col=4):
            total = sum(cell.value for cell in row)
            for cell in row:
                cell.value = cell.value / total if total > 0 else 0
        
        for col in ['B', 'C', 'D']:
            for cell in worksheet[col][1:]:
                cell.number_format = '0.00%'
        
        chart = BarChart()
        chart.type = "col"
        chart.grouping = "percentStacked"
        chart.overlap = 100
        data = Reference(worksheet, min_col=2, min_row=1, max_row=worksheet.max_row, max_col=4)
        cats = Reference(worksheet, min_col=1, min_row=2, max_row=worksheet.max_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.title = "Estados por centro"
        worksheet.add_chart(chart, "F2")
        
        header = worksheet[1]
        for cell in header:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        
        worksheet.conditional_formatting.add(f'B2:D{worksheet.max_row}',
            ColorScaleRule(start_type='min', start_color='FFFFFF',
                           mid_type='percentile', mid_value=50, mid_color='FFFF00',
                           end_type='max', end_color='FF0000'))
    
    output.seek(0)
    return output.getvalue()