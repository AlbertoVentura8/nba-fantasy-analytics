# -*- coding: utf-8 -*-
import sys
import os
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CARPETA_L2 = "L2_fantasy"

def consultar_top_fantasy(temporada="2023_24", top_n=15):
    archivo_l2 = os.path.join(CARPETA_L2, f"l2_{temporada}.csv")
    
    if not os.path.exists(archivo_l2):
        print(f"Error: No existe el dataset '{archivo_l2}' en la capa L2.")
        return

    df = pd.read_csv(archivo_l2)
    
    # Formateo de decimales a 2 posiciones para lectura limpia
    cols_float = df.select_dtypes(include=['float64']).columns
    df[cols_float] = df[cols_float].round(2)

    top_df = df.head(top_n)

    print(f"\n=== TOP {top_n} FANTASY (Z-TOTAL) - TEMPORADA {temporada.replace('_', '-')} ===")
    columnas_vista = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'Z_TOTAL', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M']
    print(top_df[columnas_vista].to_string(index=False))

if __name__ == "__main__":
    # Puedes cambiar la temporada a '2024_25', '2022_23', etc.
    consultar_top_fantasy(temporada="2025_26", top_n=15)