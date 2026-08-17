# -- coding: utf-8 --
import sys
import pandas as pd
from api_client import NBAApiClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def extraer_jugadores():
    client = NBAApiClient()
    jugadores = []
    cursor = None
    pagina = 1

    print("Iniciando pipeline de extracción de jugadores...")

    while True:
        params = {"per_page": 100}
        if cursor:
            params["cursor"] = cursor

        try:
            data = client.get("players", params=params)
            pagina_jugadores = data.get("data", [])
            jugadores.extend(pagina_jugadores)

            cursor = data.get("meta", {}).get("next_cursor")
            print(f"Pagina {pagina} procesada con exito ({len(jugadores)} acumulados).")

            if not cursor:
                break
            pagina += 1

        except Exception as e:
            print(f"Error irrecuperable en la extraccion: {e}")
            break

    if jugadores:
        df = pd.DataFrame(jugadores)
        df['equipo'] = df['team'].apply(lambda x: x['full_name'] if isinstance(x, dict) else "Sin equipo")
        df_limpio = df[['id', 'first_name', 'last_name', 'position', 'equipo']]
        df_limpio.to_csv("jugadores_nba_completos.csv", index=False, encoding='utf-8-sig')
        print(f"\nPipeline finalizado. Guardados {len(df_limpio)} registros.")

if __name__ == "__main__":
    extraer_jugadores()