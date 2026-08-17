# -- coding: utf-8 --
import sys
import os
import time
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Carpeta dedicada para almacenar las descargas raw
CARPETA_RAW = "L1_fantasy"

def generar_temporadas(cantidad=10, ano_inicio=2025):
    """
    Genera una lista de cadenas con formato 'YYYY-YY' para la API de la NBA.
    Ejemplo: '2025-26', '2024-25', '2023-24'...
    """
    temporadas = []
    for i in range(cantidad):
        year = ano_inicio - i
        next_year_str = str(year + 1)[-2:]
        temporadas.append(f"{year}-{next_year_str}")
    return temporadas

def descargar_raw_historico():
    # Crear la carpeta de destino si no existe
    if not os.path.exists(CARPETA_RAW):
        os.makedirs(CARPETA_RAW)
        print(f"Carpeta '{CARPETA_RAW}' creada con exito.")

    temporadas = generar_temporadas(cantidad=10, ano_inicio=2025)
    print("Iniciando extraccion RAW de las ultimas 10 temporadas...\n")

    for temporada in temporadas:
        print(f"Procesando temporada {temporada}...")
        
        try:
            # Peticion de todas las columnas disponibles en la API
            stats_endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
                season=temporada,
                per_mode_detailed='PerGame',
                timeout=30
            )
            
            # Obtencion directa del DataFrame en bruto
            df_raw = stats_endpoint.get_data_frames()[0]

            if not df_raw.empty:
                # Nombre estandarizado de archivo
                nombre_archivo = os.path.join(CARPETA_RAW, f"nba_raw_{temporada.replace('-', '_')}.csv")
                
                # Exportacion completa preservando codificacion
                df_raw.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
                
                filas, columnas = df_raw.shape
                print(f"  -> Guardado: {nombre_archivo} [{filas} jugadores, {columnas} columnas]")
            else:
                print(f"  -> Sin datos devueltos para {temporada}")

            # Pausa de seguridad para no saturar los servidores de la NBA
            time.sleep(2.0)

        except Exception as e:
            print(f"  -> Error procesando la temporada {temporada}: {e}")

if __name__ == "__main__":
    descargar_raw_historico()