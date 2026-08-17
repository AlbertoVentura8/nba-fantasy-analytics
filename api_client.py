import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from config import Config

class NBAApiClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": Config.API_KEY})

        # Estrategia industrial de retries con exponential backoff
        retries = Retry(
            total=5,                  # Maximo 5 reintentos por peticion
            backoff_factor=2,         # Tiempos de espera: 2s, 4s, 8s, 16s...
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)

    def get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{Config.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()