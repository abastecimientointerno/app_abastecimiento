from streamlit_echarts import st_echarts

def graficar_proyeccion_pesca(df_proyeccion_pesca):
    df_proyeccion_pesca = df_proyeccion_pesca.fillna(0)
    
    fechas = df_proyeccion_pesca['ds'].dt.strftime('%Y-%m-%d').tolist()
    
    proyeccion = df_proyeccion_pesca['yhat'].round(2).tolist()
    limite_inferior = df_proyeccion_pesca['yhat_lower'].round(2).tolist()
    limite_superior = df_proyeccion_pesca['yhat_upper'].round(2).tolist()
    
    pesca_real = df_proyeccion_pesca['real_data'].round(2).tolist()

    options = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "formatter": [
                "{a0} <br/>{b0}: {c0} <br/>",
                "{a1} <br/>{b1}: {c1} <br/>",
                "{a2} <br/>{b2}: {c2} <br/>",
                "{a3} <br/>{b3}: {c3} <br/>"
            ]
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "25%", 
            "containLabel": True
        },
        "xAxis": {
            "type": "time",
            "boundaryGap": False,
            "axisLabel": {
                "align": "center",
                "interval": 'auto',  
            },
            "splitLine": {
                "show": False
            },
            "axisLine": {
                "onZero": False
            }
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {
                "formatter": "{value}",
                "color": "#666"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "dataZoom": [
            {
                "type": "inside",
                "start": 0,
                "end": 100
            },
            {
                "start": 0,
                "end": 100
            }
        ],
        "legend": {
            "data": ["Proyección", "Límite Inferior", "Límite Superior", "Pesca Real"],
            "top": "top",
            "textStyle": {
                "color": "#666"
            }
        },
        "series": [
            {
                "name": "Proyección",
                "type": "line",
                "data": list(zip(fechas, proyeccion)),
                "lineStyle": {"color": "#5470C6", "width": 1},
                "symbol": "circle",
                "symbolSize": 2
            },
            {
                "name": "Límite Inferior",
                "type": "line",
                "data": list(zip(fechas, limite_inferior)),
                "lineStyle": { "type": "dotted", "width": 1},
                "symbol": "none"
            },
            {
                "name": "Límite Superior",
                "type": "line",
                "data": list(zip(fechas, limite_superior)),
                "lineStyle": { "type": "dotted", "width": 1},
                "symbol": "none"
            },
            {
                "name": "Pesca Real",
                "type": "line",
                "data": list(zip(fechas, pesca_real)),
                "lineStyle": {"color": "#EE6666", "width": 2},
                "symbol": "circle",
                "symbolSize": 5
            }
        ],
        "animationDuration": 1000,
        "height": "500px"
    }

    st_echarts(options=options, height="630px")

def get_tooltip_data(params):
    return [
        f"{params[0]['seriesName']} <br/>{params[0]['name']}: {params[0]['value']:.2f} <br/>",
        f"{params[1]['seriesName']} <br/>{params[1]['name']}: {params[1]['value']:.2f} <br/>",
        f"{params[2]['seriesName']} <br/>{params[2]['name']}: {params[2]['value']:.2f} <br/>",
        f"{params[3]['seriesName']} <br/>{params[3]['name']}: {params[3]['value']:.2f} <br/>"
    ]