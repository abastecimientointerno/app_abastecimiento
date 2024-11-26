import pandas as pd

def process_mb52(file):
    # Lógica específica de procesamiento del archivo MB52
    df = pd.read_excel(file)
    # ... proceso específico
    return df
