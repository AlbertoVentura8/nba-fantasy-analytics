# -*- coding: utf-8 -*-
import sys
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def extraer_promedios_nba(temporada="2025-26"):
    print(f"Conectando con stats.nba.com para la temporada {temporada}...")

    try:
        # Peticion global a la API oficial de la NBA
        stats_endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
            season=temporada,
            per_mode_detailed='PerGame'
        )
        
        df_raw = stats_endpoint.get_data_frames()[0]
        
        if df_raw.empty:
            print("No se encontraron registros.")
            return

        # Mapeo y seleccion de metricas esenciales para Fantasy
        columnas_claves = {
            'PLAYER_ID': 'id',
            'PLAYER_NAME': 'jugador',
            'TEAM_ABBREVIATION': 'equipo',
            'GP': 'partidos_jugados',
            'MIN': 'minutos',
            'PTS': 'puntos',
            'REB': 'rebotes',
            'AST': 'asistencias',
            'STL': 'robos',
            'BLK': 'tapones',
            'FG3M': 'triples_anotados',
            'FG_PCT': 'pct_tiro_campo',
            'FT_PCT': 'pct_tiro_libre',
            'TOV': 'perdidas'
        }

        df_fantasy = df_raw[list(columnas_claves.keys())].rename(columns=columnas_claves)

        # Filtro de activos: solo jugadores con partidos disputados
        df_activos = df_fantasy[df_fantasy['partidos_jugados'] > 0]

        df_activos.to_csv("estadisticas_fantasy_nba.csv", index=False, encoding='utf-8-sig')
        print(f"\nExito! Guardados {len(df_activos)} jugadores activos en 'estadisticas_fantasy_nba.csv'")

    except Exception as e:
        print(f"Error en la extraccion: {e}")

if __name__ == "__main__":
    # Formato esperado: '2023-24', '2024-25' o '2025-26'
    extraer_promedios_nba(temporada="2025-26")