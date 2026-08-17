# -*- coding: utf-8 -*-
import sys
import os
import pandas as pd
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CARPETA_L1 = "L1_fantasy"
CARPETA_L2 = "L2_fantasy"

CATEGORIAS_CONTEO = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'TOV']

def calcular_z_scores_ponderados(df, top_n_jugadores=150):
    # 1. Filtro inicial de volumen
    df_filtrado = df[df['GP'] >= 15].copy()
    
    # 2. Pool de control (Top jugadores por minutos)
    pool = df_filtrado.sort_values(by='MIN', ascending=False).head(top_n_jugadores)
    
    df_z = df_filtrado.copy()

    # Medias globales del pool de control
    media_fg_pct = pool['FG_PCT'].mean()
    media_ft_pct = pool['FT_PCT'].mean()

    # 3. Calculo de Impacto Ponderado para porcentajes
    df_z['IMPACTO_FG'] = (df_z['FG_PCT'] - media_fg_pct) * df_z['FGA']
    df_z['IMPACTO_FT'] = (df_z['FT_PCT'] - media_ft_pct) * df_z['FTA']

    # Recalcular medias y desviaciones de impactos en el pool
    pool_z = df_z.sort_values(by='MIN', ascending=False).head(top_n_jugadores)
    
    # Z-Scores Porcentajes Ponderados
    df_z['Z_FG_PCT'] = (df_z['IMPACTO_FG'] - pool_z['IMPACTO_FG'].mean()) / pool_z['IMPACTO_FG'].std()
    df_z['Z_FT_PCT'] = (df_z['IMPACTO_FT'] - pool_z['IMPACTO_FT'].mean()) / pool_z['IMPACTO_FT'].std()

    # 4. Z-Scores para categorias de conteo
    for cat in CATEGORIAS_CONTEO:
        media = pool[cat].mean()
        desviacion = pool[cat].std()

        if cat == 'TOV':
            df_z[f'Z_{cat}'] = -1 * ((df_z[cat] - media) / desviacion)
        else:
            df_z[f'Z_{cat}'] = (df_z[cat] - media) / desviacion

    # 5. Suma Z-TOTAL (9 categorias)
    columnas_z = ['Z_PTS', 'Z_REB', 'Z_AST', 'Z_STL', 'Z_BLK', 'Z_FG3M', 'Z_FG_PCT', 'Z_FT_PCT', 'Z_TOV']
    df_z['Z_TOTAL'] = df_z[columnas_z].sum(axis=1)

    return df_z.sort_values(by='Z_TOTAL', ascending=False)

def procesar_capa_l2():
    if not os.path.exists(CARPETA_L2):
        os.makedirs(CARPETA_L2)

    archivos = [f for f in os.listdir(CARPETA_L1) if f.endswith('.csv')]
    print(f"Procesando transformacion ponderada L1 -> L2...\n")

    for archivo in archivos:
        ruta_entrada = os.path.join(CARPETA_L1, archivo)
        df_raw = pd.read_csv(ruta_entrada)

        df_valorado = calcular_z_scores_ponderados(df_raw)

        columnas_z = ['Z_PTS', 'Z_REB', 'Z_AST', 'Z_STL', 'Z_BLK', 'Z_FG3M', 'Z_FG_PCT', 'Z_FT_PCT', 'Z_TOV']
        cols_finales = [
            'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'Z_TOTAL'
        ] + columnas_z + ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FGA', 'FT_PCT', 'FTA', 'TOV']

        df_limpio = df_valorado[cols_finales]

        nombre_salida = f"L2_{archivo.replace('l1_nba_raw_', '').replace('nba_raw_', '')}"
        ruta_salida = os.path.join(CARPETA_L2, nombre_salida)

        df_limpio.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
        print(f"Procesado con exito: {nombre_salida}")

if __name__ == "__main__":
    procesar_capa_l2()