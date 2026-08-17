# -- coding: utf-8 --
import sys
import os
import pandas as pd
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CARPETA_L1= "L1_fantasy"
CARPETA_L2 = "L2_fantasy"

# Las 9 categorias tradicionales de Fantasy NBA
CATEGORIAS_9CAT = [
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FT_PCT', 'TOV'
]

def calcular_z_scores(df, top_n_jugadores=150):
    # 1. Filtro inicial: Minimo 15 partidos jugados
    df_filtrado = df[df['GP'] >= 15].copy()

    # 2. Pool Fantasy de control (Top 150 por minutos)
    pool_fantasy = df_filtrado.sort_values(by='MIN', ascending=False).head(top_n_jugadores)

    df_z = df_filtrado.copy()
    
    # 3. Calculo de desviaciones sobre el pool de control
    for cat in CATEGORIAS_9CAT:
        media = pool_fantasy[cat].mean()
        desviacion = pool_fantasy[cat].std()

        # Las perdidas (TOV) restan en Fantasy: invertimos el valor
        if cat == 'TOV':
            df_z[f'Z_{cat}'] = -1 * ((df_z[cat] - media) / desviacion)
        else:
            df_z[f'Z_{cat}'] = (df_z[cat] - media) / desviacion

    # 4. Suma de Z-Scores de las 9 categorias
    columnas_z = [f'Z_{cat}' for cat in CATEGORIAS_9CAT]
    df_z['Z_TOTAL'] = df_z[columnas_z].sum(axis=1)

    return df_z.sort_values(by='Z_TOTAL', ascending=False)

def procesar_capa_l2():
    if not os.path.exists(CARPETA_L2):
        os.makedirs(CARPETA_L2)
        print(f"Directorio '{CARPETA_L2}' creado con exito.")

    archivos = [f for f in os.listdir(CARPETA_L1) if f.endswith('.csv')]
    print(f"Transformando datos de '{CARPETA_L1}' hacia capa '{CARPETA_L2}'...\n")

    for archivo in archivos:
        ruta_entrada = os.path.join(CARPETA_L1, archivo)
        df_raw = pd.read_csv(ruta_entrada)

        df_valorado = calcular_z_scores(df_raw)

        cols_finales = [
            'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN',
            'Z_TOTAL', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FT_PCT', 'TOV'
        ]
        
        df_limpio = df_valorado[cols_finales]

        nombre_salida = f"L2_{archivo.replace('nba_raw_', '')}"
        ruta_salida = os.path.join(CARPETA_L2, nombre_salida)

        df_limpio.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
        print(f"Procesado: {archivo} -> Guardado en: {ruta_salida}")

if __name__ == "__main__":
    procesar_capa_l2()