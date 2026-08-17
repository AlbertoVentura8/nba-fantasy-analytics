import os
from dotenv import load_dotenv

load_dotenv()

class Config:
	API_KEY=os.getenv("API_KEY_BALLDONTLIE")
	BASE_URL="https://api.balldontlie.io/v1"

	if not API_KEY:
		raise ValueError("Error critico: No definida la API_KEY en .env")