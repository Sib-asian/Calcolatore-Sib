"""
Web Search Module (Gratuito)
Utilizza DuckDuckGo per ricerche web senza API key
Con ricerca intelligente multi-variante e Wikipedia lookup
"""
import time
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import config
from cache_manager import CacheManager
from team_search_intelligent import TeamSearchIntelligent
from text_parser_advanced import TextParserAdvanced

class WebSearchFree:
    """Gestisce ricerche web gratuite tramite DuckDuckGo"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.team_search = TeamSearchIntelligent()
        self.text_parser = TextParserAdvanced()
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
        Cerca news specifiche per una squadra usando ricerca intelligente
        
        Args:
            team_name: Nome della squadra
            max_results: Numero massimo di risultati
            
        Returns:
            Lista di news con 'title', 'snippet', 'url', 'date'
        """
        # Ottieni nome completo e query varianti
        full_name, query_variants = self.team_search.get_team_search_queries(team_name)
        
        # Controlla cache
        cache_key = f"news_{team_name.lower()}"
        cached = self.cache.get_cached_search(cache_key)
        if cached:
            return cached[:max_results]
        
        # Rate limiting
        self._rate_limit()
        
        all_results = []
        seen_urls = set()
        
        try:
            with DDGS() as ddgs:
                # Prova ogni variante di query
                for query in query_variants[:5]:  # Max 5 varianti per evitare troppe richieste
                    try:
                        # Prova prima news specifiche
                        for r in ddgs.news(query, max_results=max_results):
                            url = r.get('url', '')
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                all_results.append({
                                    'title': r.get('title', ''),
                                    'snippet': r.get('body', ''),
                                    'url': url,
                                    'date': r.get('date', '')
                                })
                                
                                if len(all_results) >= max_results:
                                    break
                        
                        # Se abbiamo abbastanza risultati, fermati
                        if len(all_results) >= max_results:
                            break
                            
                        # Se non trova news, prova ricerca normale
                        if len(all_results) < max_results:
                            for r in ddgs.text(query, max_results=2):
                                url = r.get('href', '')
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    all_results.append({
                                        'title': r.get('title', ''),
                                        'snippet': r.get('body', ''),
                                        'url': url,
                                        'date': ''
                                    })
                                    
                                    if len(all_results) >= max_results:
                                        break
                        
                        if len(all_results) >= max_results:
                            break
                            
                    except Exception as e:
                        # Continua con prossima query se questa fallisce
                        continue
                
                # Salva in cache
                if all_results:
                    self.cache.save_search(cache_key, all_results, ttl_hours=24)
                
                return all_results[:max_results]
        except Exception as e:
            print(f"Errore ricerca news DuckDuckGo: {e}")
            return []
    
    def search_injuries(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Cerca informazioni su infortuni squadra usando nome completo - RICERCA MULTILINGUA APPROFONDITA
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Lista di risultati su infortuni
        """
        # Ottieni nome completo
        full_name, _ = self.team_search.get_team_search_queries(team_name)
        
        # Query multilingua per infortuni (PRIORITIZZATE + FALLBACK generiche)
        queries = [
            # Priorità 1: Inglese (più risultati)
            f"{full_name} injured players today",
            f"{full_name} injury list",
            f"{full_name} injuries",
            # Priorità 2: Italiano
            f"{full_name} infortuni oggi",
            f"{full_name} calciatori infortunati",
            f"{full_name} infortuni",
            # Priorità 3: Portoghese (per squadre portoghesi)
            f"{full_name} lesões hoje",
            f"{full_name} lesionados",
            # Priorità 4: Query generiche (FALLBACK se le specifiche non funzionano)
            f"{full_name} news",
            f"{team_name} news",
            f"{full_name} latest news"
        ]
        
        all_results = []
        seen_urls = set()
        
        # Prova query in ordine di priorità (FERMATI DOPO 8-10 RISULTATI BUONI)
        for query in queries:
            try:
                results = self.search_web(query, max_results=3)  # Ridotto a 3 per query
                for r in results:
                    url = r.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
                        if len(all_results) >= 10:  # FERMATI DOPO 10 RISULTATI
                            break
                if len(all_results) >= 10:
                    break
            except Exception as e:
                print(f"DEBUG: Errore query '{query}': {e}")
                continue
        
        return all_results[:10]  # Max 10 risultati (sufficienti per estrarre info)
    
    def search_unavailable(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Cerca giocatori indisponibili (squalificati, sospesi) - RICERCA MULTILINGUA OTTIMIZZATA
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Lista di risultati con 'title', 'snippet', 'url'
        """
        # Ottieni nome completo
        full_name, _ = self.team_search.get_team_search_queries(team_name)
        
        # Query multilingua per indisponibili (PRIORITIZZATE + FALLBACK generiche)
        queries = [
            # Priorità 1: Inglese
            f"{full_name} suspended players",
            f"{full_name} banned players",
            f"{full_name} unavailable",
            # Priorità 2: Italiano
            f"{full_name} squalificati oggi",
            f"{full_name} sospesi partita",
            f"{full_name} indisponibili",
            # Priorità 3: Portoghese
            f"{full_name} suspensos",
            f"{full_name} indisponíveis",
            # Priorità 4: Query generiche (FALLBACK)
            f"{full_name} team news",
            f"{team_name} news"
        ]
        
        all_results = []
        seen_urls = set()
        
        # Prova query in ordine di priorità (FERMATI DOPO 8-10 RISULTATI BUONI)
        for query in queries:
            try:
                results = self.search_web(query, max_results=3)  # Ridotto a 3 per query
                for r in results:
                    url = r.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
                        if len(all_results) >= 10:  # FERMATI DOPO 10 RISULTATI
                            break
                if len(all_results) >= 10:
                    break
            except Exception as e:
                print(f"DEBUG: Errore query '{query}': {e}")
                continue
        
        return all_results[:10]  # Max 10 risultati (sufficienti per estrarre info)
    
    def search_lineup(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Cerca informazioni su formazioni usando nome completo - RICERCA MULTILINGUA APPROFONDITA
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Lista di risultati su formazioni
        """
        # Ottieni nome completo
        full_name, _ = self.team_search.get_team_search_queries(team_name)
        
        # Query multilingua per formazioni (PRIORITIZZATE + FALLBACK generiche)
        queries = [
            # Priorità 1: Inglese
            f"{full_name} probable lineup",
            f"{full_name} starting XI",
            f"{full_name} lineup",
            # Priorità 2: Italiano
            f"{full_name} formazione probabile",
            f"{full_name} probabile formazione",
            f"{full_name} formazione",
            # Priorità 3: Portoghese
            f"{full_name} formação provável",
            f"{full_name} escalação",
            # Priorità 4: Query generiche (FALLBACK)
            f"{full_name} team news",
            f"{team_name} news"
        ]
        
        all_results = []
        seen_urls = set()
        
        # Prova query in ordine di priorità (FERMATI DOPO 8-10 RISULTATI BUONI)
        for query in queries:
            try:
                results = self.search_web(query, max_results=3)  # Ridotto a 3 per query
                for r in results:
                    url = r.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
                        if len(all_results) >= 10:  # FERMATI DOPO 10 RISULTATI
                            break
                if len(all_results) >= 10:
                    break
            except Exception as e:
                print(f"DEBUG: Errore query '{query}': {e}")
                continue
        
        return all_results[:10]  # Max 10 risultati (sufficienti per estrarre info)
    
