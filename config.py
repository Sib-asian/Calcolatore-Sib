"""
Configurazione API per AI Agent
"""
import os
from pathlib import Path

# Carica variabili d'ambiente da file .env se presente
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv non installato, usa solo variabili d'ambiente di sistema
    pass

# Groq API (LLM gratuito)
# Legge da variabile d'ambiente o file .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Modello aggiornato: llama-3.1-70b-versatile è stato dismesso
# Usa uno di questi modelli disponibili:
# - llama-3.1-8b-instant (più veloce, meno potente)
# - llama-3.3-70b-versatile (più recente, simile al vecchio)
# - mixtral-8x7b-32768 (molto potente)
GROQ_MODEL = "llama-3.3-70b-versatile"  # Modello aggiornato

# NewsAPI (gratuito - 100 richieste/giorno)
# Legge da variabile d'ambiente o file .env
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE_URL = "https://newsapi.org/v2"

# Cache settings
CACHE_NEWS_TTL_HOURS = 24  # News valide per 24h
CACHE_SEARCH_TTL_HOURS = 6  # Ricerche valide per 6h
CACHE_DB_PATH = "ai_cache.db"  # SQLite database path

# Rate limiting
GROQ_RATE_LIMIT_PER_MINUTE = 30  # Limite Groq
DUCKDUCKGO_RATE_LIMIT_PER_MINUTE = 10  # Limite conservativo DuckDuckGo
NEWS_API_RATE_LIMIT_PER_DAY = 100  # Limite NewsAPI free tier

# Timeout settings
GROQ_TIMEOUT_SECONDS = 30
WEB_SEARCH_TIMEOUT_SECONDS = 10
NEWS_API_TIMEOUT_SECONDS = 10

