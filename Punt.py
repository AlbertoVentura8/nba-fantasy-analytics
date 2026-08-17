# -*- coding: utf-8 -*-
import sys
import os
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CARPETA_L2 = "L2_fantasy"

def simular_estrategia_punt(temporada="2025_26", categorias_punt=None, top_n=100):
    if categorias_punt is None:
        categorias_punt = []

    archivo_l2 = os.path.join(CARPETA_L2, f"l2_{temporada}.csv")
    if not os.path.exists(archivo_l2):
        print(f"Error: No se encontro la capa L2 para {temporada}")
        return

    df = pd.read_csv(archivo_l2)
    
    # Seleccionar columnas Z excepto Z_TOTAL
    cols_z = [c for c in df.columns if c.startswith('Z_') and c != 'Z_TOTAL']
    
    # Excluir las categorias que decidimos ignorar (Punt)
    cols_z_activas = [c for c in cols_z if c.replace('Z_', '') not in categorias_punt]

    # Recalcular Z-Score personalizado para la estrategia
    df['Z_CUSTOM'] = df[cols_z_activas].sum(axis=1)
    df_ranking = df.sort_values(by='Z_CUSTOM', ascending=False)

    print(f"\n=== RANKING FANTASY (PUNT: {', '.join(categorias_punt) if categorias_punt else 'NINGUNA'}) ===")
    cols_vista = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'Z_TOTAL', 'Z_CUSTOM', 'PTS', 'REB', 'AST', 'STL', 'BLK']
    
    # Redondear float para salida limpia
    df_res = df_ranking[cols_vista].head(top_n).copy()
    df_res['Z_TOTAL'] = df_res['Z_TOTAL'].round(2)
    df_res['Z_CUSTOM'] = df_res['Z_CUSTOM'].round(2)

    print(df_res.to_string(index=False))

if __name__ == "__main__":
    # Ejemplo: Estrategia Punt FT% y TOV (ideal para perfiles estilo Giannis Antetokounmpo)
    simular_estrategia_punt(temporada="2025_26", categorias_punt=['FT_PCT', 'TOV'], top_n=100)