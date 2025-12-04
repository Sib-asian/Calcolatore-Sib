"""
Configurazione centrale del sistema
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = DATA_DIR / "cache"
HISTORICAL_DIR = DATA_DIR / "historical"

# Crea directory se non esistono
for dir_path in [DATA_DIR, MODELS_DIR, CACHE_DIR, HISTORICAL_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Keys (da impostare in .env)
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# API Endpoints
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
RAPIDAPI_FOOTBALL_BASE = "https://api-football-v1.p.rapidapi.com/v3"

# Rate limiting
FOOTBALL_DATA_RATE_LIMIT = 10  # richieste per minuto
CACHE_DURATION_HOURS = 6  # durata cache in ore

# Leghe supportate (codici Football-Data.org)
SUPPORTED_LEAGUES = {
    "Serie A": "SA",
    "Premier League": "PL",
    "La Liga": "PD",
    "Bundesliga": "BL1",
    "Ligue 1": "FL1",
    "Champions League": "CL",
    "Europa League": "EL",
    "Eredivisie": "DED",
    "Primeira Liga": "PPL",
    "Super Lig": "TSL",
    "Serie A Brasil": "BSA",
    "Primera División Argentina": "PD",
    "MLS": "MLS",
    "Liga MX": "LMX"
}

# Modelli ML
MODEL_CONFIG = {
    "1X2": {
        "type": "xgboost",
        "features": ["home_attack", "away_attack", "home_defense", "away_defense", 
                    "home_form", "away_form", "h2h_home_wins", "h2h_draws", "h2h_away_wins"]
    },
    "over_under": {
        "type": "xgboost",
        "features": ["home_goals_avg", "away_goals_avg", "home_conceded_avg", "away_conceded_avg"]
    },
    "btts": {
        "type": "xgboost",
        "features": ["home_attack", "away_attack", "home_defense", "away_defense"]
    }
}





