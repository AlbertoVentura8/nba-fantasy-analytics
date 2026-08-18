# -*- coding: utf-8 -*-
"""
Script ETL Offline — Generador Multitemporada de Datasets L2
Recorre cada temporada de L2_fantasy/ y genera sus respectivos Game Logs y Palmarés en CSV.
"""

import os
import time
import pandas as pd
from nba_api.stats.endpoints import playerawards, playergamelog

CARPETA_L2 = "L2_fantasy"

def parse_min(val):
    """Convierte el formato de minutos de texto (34:15) a número flotante (34.25)."""
    if pd.isna(val): return 0.0
    val_str = str(val).strip()
    if ':' in val_str:
        parts = val_str.split(':')
        try: return float(parts[0]) + float(parts[1]) / 60.0
        except: return 0.0
    try: return float(val_str)
    except: return 0.0

def generar_datasets_L2():
    if not os.path.exists(CARPETA_L2):
        print(f"❌ La carpeta '{CARPETA_L2}' no existe.")
        return

    # Buscar archivos de promedios L2_YYYY_YY.csv ignorando gamelogs y palmares
    archivos_promedios = [
        f for f in os.listdir(CARPETA_L2) 
        if f.startswith("L2_") and f.endswith(".csv") 
        and not f.startswith("L2_gamelogs_") and f != "L2_palmares.csv"
    ]

    headers = {
        'Host': 'stats.nba.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.nba.com/'
    }

    jugadores_procesados_palmares = set()
    palmares_acumulado = []

    for archivo in archivos_promedios:
        temporada = archivo.replace("L2_", "").replace(".csv", "")
        season_fmt = temporada.replace("_", "-")
        ruta_csv = os.path.join(CARPETA_L2, archivo)
        
        df_players = pd.read_csv(ruta_csv)
        print(f"\n🏀 Processing Temporada: {season_fmt} ({len(df_players)} jugadores)...")
        
        gamelogs_temporada = []

        for idx, row in df_players.iterrows():
            p_id = int(row['PLAYER_ID'])
            p_name = row['PLAYER_NAME']
            p_team = row['TEAM_ABBREVIATION']

            print(f"   [{idx+1}/{len(df_players)}] {p_name} (ID: {p_id})")

            # 1. Extracción de Palmarés (solo una vez por jugador único en la liga)
            if p_id not in jugadores_procesados_palmares:
                jugadores_procesados_palmares.add(p_id)
                try:
                    aw = playerawards.PlayerAwards(player_id=p_id, headers=headers, timeout=5).get_data_frames()[0]
                    if not aw.empty:
                        aw = aw[~aw['DESCRIPTION'].str.contains("Player of the Week|Player of the Month", na=False, case=False)]
                        for desc, group in aw.groupby('DESCRIPTION'):
                            col_s = 'SEASON' if 'SEASON' in group.columns else ('YEAR_AWARDED' if 'YEAR_AWARDED' in group.columns else None)
                            anos = ", ".join(group[col_s].dropna().astype(str).unique().tolist()) if col_s else "Registrado"
                            palmares_acumulado.append({
                                'PLAYER_ID': p_id,
                                'PLAYER_NAME': p_name,
                                'TITULO': f"🏆 {desc} ({len(group)}x)" if len(group) > 1 else f"🏆 {desc}",
                                'ANOS': anos
                            })
                except Exception as e:
                    pass

            # 2. Extracción de Game Logs para la temporada actual
            try:
                gl = playergamelog.PlayerGameLog(player_id=p_id, season=season_fmt, headers=headers, timeout=5).get_data_frames()[0]
                if not gl.empty:
                    gl['PLAYER_NAME'] = p_name
                    gl['TEAM_ABBREVIATION'] = p_team
                    gamelogs_temporada.append(gl)
            except Exception as e:
                pass

            time.sleep(0.3)

        # Guardar Game Logs de la temporada
        if gamelogs_temporada:
            df_gl_temp = pd.concat(gamelogs_temporada, ignore_index=True)
            df_gl_temp['MIN'] = df_gl_temp['MIN'].apply(parse_min)
            df_gl_temp['STOCKS'] = df_gl_temp['STL'] + df_gl_temp['BLK']
            
            ruta_gl_out = os.path.join(CARPETA_L2, f"L2_gamelogs_{temporada}.csv")
            df_gl_temp.to_csv(ruta_gl_out, index=False, encoding='utf-8-sig')
            print(f"✅ Game Logs guardados en {ruta_gl_out}")

    # Guardar Palmarés Global Unificado
    if palmares_acumulado:
        df_palmares = pd.DataFrame(palmares_acumulado)
        ruta_palmares_out = os.path.join(CARPETA_L2, "L2_palmares.csv")
        df_palmares.to_csv(ruta_palmares_out, index=False, encoding='utf-8-sig')
        print(f"\n🏆 Palmarés global guardado en {ruta_palmares_out}")

if __name__ == "__main__":
    generar_datasets_L2()