"""
Configurazione API per AI Agent
"""
import os

# Groq API (LLM gratuito)
# IMPORTANTE: Usa variabili d'ambiente per sicurezza
# Imposta: export GROQ_API_KEY="your_key_here" (Linux/Mac)
# Imposta: set GROQ_API_KEY=your_key_here (Windows)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-70b-versatile"  # Modello gratuito veloce

# NewsAPI (gratuito - 100 richieste/giorno)
# IMPORTANTE: Usa variabili d'ambiente per sicurezza
# Imposta: export NEWS_API_KEY="your_key_here" (Linux/Mac)
# Imposta: set NEWS_API_KEY=your_key_here (Windows)
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

