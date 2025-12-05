"""
Web Search Module (Gratuito)
Utilizza DuckDuckGo per ricerche web senza API key
"""
import time
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import config
from cache_manager import CacheManager

class WebSearchFree:
    """Gestisce ricerche web gratuite tramite DuckDuckGo"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.last_request_time = 0
        self.min_request_interval = 60 / config.DUCKDUCKGO_RATE_LIMIT_PER_MINUTE  # Secondi tra richieste
    
    def _rate_limit(self):
        """Rispetta rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Cerca informazioni sul web usando DuckDuckGo
        
        Args:
            query: Query di ricerca
            max_results: Numero massimo di risultati
            
        Returns:
            Lista di risultati con 'title', 'snippet', 'url'
        """
        # Controlla cache
        cached = self.cache.get_cached_search(query)
        if cached:
            return cached[:max_results]
        
        # Rate limiting
        self._rate_limit()
        
        try:
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        'title': r.get('title', ''),
                        'snippet': r.get('body', ''),
                        'url': r.get('href', '')
                    })
                
                # Salva in cache
                if results:
                    self.cache.save_search(query, results)
                
                return results
        except Exception as e:
            print(f"Errore ricerca DuckDuckGo: {e}")
            return []
    
    def search_news(self, team_name: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Cerca news specifiche per una squadra
        
        Args:
            team_name: Nome della squadra
            max_results: Numero massimo di risultati
            
        Returns:
            Lista di news con 'title', 'snippet', 'url', 'date'
        """
        # Query ottimizzata per news calcio
        query = f"{team_name} calcio news ultime notizie"
        
        # Controlla cache
        cache_key = f"news_{team_name}"
        cached = self.cache.get_cached_search(cache_key)
        if cached:
            return cached[:max_results]
        
        # Rate limiting
        self._rate_limit()
        
        try:
            with DDGS() as ddgs:
                results = []
                # Cerca news recenti
                for r in ddgs.news(f"{team_name} calcio", max_results=max_results):
                    results.append({
                        'title': r.get('title', ''),
                        'snippet': r.get('body', ''),
                        'url': r.get('url', ''),
                        'date': r.get('date', '')
                    })
                
                # Se non trova news, prova ricerca normale
                if not results:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append({
                            'title': r.get('title', ''),
                            'snippet': r.get('body', ''),
                            'url': r.get('href', ''),
                            'date': ''
                        })
                
                # Salva in cache
                if results:
                    self.cache.save_search(cache_key, results, ttl_hours=24)
                
                return results
        except Exception as e:
            print(f"Errore ricerca news DuckDuckGo: {e}")
            return []
    
    def search_injuries(self, team_name: str) -> List[Dict[str, Any]]:
        """Cerca informazioni su infortuni squadra"""
        query = f"{team_name} infortuni calciatori"
        return self.search_web(query, max_results=3)
    
    def search_lineup(self, team_name: str) -> List[Dict[str, Any]]:
        """Cerca informazioni su formazioni"""
        query = f"{team_name} formazione probabile"
        return self.search_web(query, max_results=3)

