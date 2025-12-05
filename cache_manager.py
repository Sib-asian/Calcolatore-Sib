"""
Cache Manager per AI Agent
Gestisce cache SQLite per news, ricerche web e altri dati
"""
import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import config

class CacheManager:
    """Gestisce cache SQLite per ottimizzare chiamate API"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.CACHE_DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Inizializza database e crea tabelle se non esistono"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella per cache news
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_cache (
                team_name TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                timestamp REAL NOT NULL,
                expires_at REAL NOT NULL
            )
        ''')
        
        # Tabella per cache ricerche web
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                query TEXT PRIMARY KEY,
                results TEXT NOT NULL,
                timestamp REAL NOT NULL,
                expires_at REAL NOT NULL
            )
        ''')
        
        # Indici per performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_expires ON news_cache(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_expires ON search_cache(expires_at)')
        
        conn.commit()
        conn.close()
    
    def _cleanup_expired(self):
        """Rimuove entry scadute (chiamato automaticamente)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = time.time()
        
        cursor.execute('DELETE FROM news_cache WHERE expires_at < ?', (now,))
        cursor.execute('DELETE FROM search_cache WHERE expires_at < ?', (now,))
        
        conn.commit()
        conn.close()
    
    def get_cached_news(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Recupera news dalla cache se valide"""
        self._cleanup_expired()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT data, timestamp FROM news_cache WHERE team_name = ? AND expires_at > ?',
            (team_name.lower(), time.time())
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def save_news(self, team_name: str, data: Dict[str, Any], ttl_hours: int = None):
        """Salva news in cache con TTL"""
        ttl_hours = ttl_hours or config.CACHE_NEWS_TTL_HOURS
        now = time.time()
        expires_at = now + (ttl_hours * 3600)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT OR REPLACE INTO news_cache (team_name, data, timestamp, expires_at)
               VALUES (?, ?, ?, ?)''',
            (team_name.lower(), json.dumps(data), now, expires_at)
        )
        
        conn.commit()
        conn.close()
    
    def get_cached_search(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Recupera risultati ricerca dalla cache se validi"""
        self._cleanup_expired()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT results, timestamp FROM search_cache WHERE query = ? AND expires_at > ?',
            (query.lower(), time.time())
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def save_search(self, query: str, results: List[Dict[str, Any]], ttl_hours: int = None):
        """Salva risultati ricerca in cache con TTL"""
        ttl_hours = ttl_hours or config.CACHE_SEARCH_TTL_HOURS
        now = time.time()
        expires_at = now + (ttl_hours * 3600)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT OR REPLACE INTO search_cache (query, results, timestamp, expires_at)
               VALUES (?, ?, ?, ?)''',
            (query.lower(), json.dumps(results), now, expires_at)
        )
        
        conn.commit()
        conn.close()
    
    def clear_cache(self, cache_type: str = None):
        """Pulisce cache (opzionale: specifica 'news' o 'search')"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if cache_type == 'news':
            cursor.execute('DELETE FROM news_cache')
        elif cache_type == 'search':
            cursor.execute('DELETE FROM search_cache')
        else:
            cursor.execute('DELETE FROM news_cache')
            cursor.execute('DELETE FROM search_cache')
        
        conn.commit()
        conn.close()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Restituisce statistiche cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM news_cache WHERE expires_at > ?', (time.time(),))
        news_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM search_cache WHERE expires_at > ?', (time.time(),))
        search_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'news_entries': news_count,
            'search_entries': search_count
        }

