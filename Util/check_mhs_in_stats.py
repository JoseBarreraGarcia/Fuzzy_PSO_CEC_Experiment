import pandas as pd

# Verificar estadísticas de cada función
for funcion in ['F1', 'F8', 'F9', 'F16']:
    try:
        df = pd.read_csv(f'./Resultados/resumen/BEN/estadisticas_{funcion}.csv')
        mhs = df['MH'].unique()
        print(f"{funcion}: {len(mhs)} MH -> {', '.join(sorted(mhs))}")
    except Exception as e:
        print(f"{funcion}: ERROR - {e}")
