"""
News Aggregator (Gratuito)
Utilizza NewsAPI (free tier) + DuckDuckGo come fallback
"""
import requests
import time
from typing import Dict, Any, List, Optional
import config
from cache_manager import CacheManager
from web_search_free import WebSearchFree

class NewsAggregatorFree:
    """Aggrega news da NewsAPI e DuckDuckGo con cache intelligente"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.web_search = WebSearchFree()
        self.news_api_requests_today = 0
        self.last_reset_date = time.strftime('%Y-%m-%d')
        self.news_api_available = True
    
    def _check_daily_limit(self):
        """Controlla e resetta contatore giornaliero NewsAPI"""
        today = time.strftime('%Y-%m-%d')
        if today != self.last_reset_date:
            self.news_api_requests_today = 0
            self.last_reset_date = today
            self.news_api_available = True
    
    def _get_news_from_newsapi(self, team_name: str) -> Optional[List[Dict[str, Any]]]:
        """Recupera news da NewsAPI se disponibile"""
        self._check_daily_limit()
        
        # Controlla limite giornaliero
        if self.news_api_requests_today >= config.NEWS_API_RATE_LIMIT_PER_DAY:
            self.news_api_available = False
            return None
        
        try:
            # Query ottimizzata per calcio italiano/internazionale
            query = f"{team_name} AND (calcio OR football OR soccer)"
            
            url = f"{config.NEWS_API_BASE_URL}/everything"
            params = {
                'q': query,
                'language': 'it',  # Italiano
                'sortBy': 'publishedAt',
                'pageSize': 5,
                'apiKey': config.NEWS_API_KEY
            }
            
            response = requests.get(
                url,
                params=params,
                timeout=config.NEWS_API_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                # Formatta risultati
                results = []
                for article in articles:
                    if article.get('title') and article.get('description'):
                        results.append({
                            'title': article.get('title', ''),
                            'snippet': article.get('description', ''),
                            'url': article.get('url', ''),
                            'date': article.get('publishedAt', ''),
                            'source': article.get('source', {}).get('name', '')
                        })
                
                self.news_api_requests_today += 1
                return results if results else None
            else:
                # Se errore, disabilita NewsAPI per oggi
                if response.status_code == 429:  # Too many requests
                    self.news_api_available = False
                return None
                
        except Exception as e:
            print(f"Errore NewsAPI: {e}")
            return None
    
    def get_team_news(self, team_name: str) -> Dict[str, Any]:
        """
        Recupera news per una squadra
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Dict con 'news', 'injuries', 'lineup', 'source'
        """
        # Controlla cache
        cached = self.cache.get_cached_news(team_name)
        if cached:
            return cached
        
        result = {
            'news': [],
            'injuries': [],
            'lineup': [],
            'source': 'cache'
        }
        
        # Prova NewsAPI prima
        if self.news_api_available:
            newsapi_results = self._get_news_from_newsapi(team_name)
            if newsapi_results:
                result['news'] = newsapi_results
                result['source'] = 'newsapi'
            else:
                # Fallback a DuckDuckGo
                result['news'] = self.web_search.search_news(team_name, max_results=5)
                result['source'] = 'duckduckgo'
        else:
            # Usa solo DuckDuckGo
            result['news'] = self.web_search.search_news(team_name, max_results=5)
            result['source'] = 'duckduckgo'
        
        # Cerca infortuni e formazioni
        result['injuries'] = self.web_search.search_injuries(team_name)
        result['lineup'] = self.web_search.search_lineup(team_name)
        
        # Salva in cache
        self.cache.save_news(team_name, result)
        
        return result
    
    def get_news_summary(self, team_name: str) -> str:
        """
        Genera un riassunto testuale delle news
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Stringa con riassunto news
        """
        news_data = self.get_team_news(team_name)
        
        summary_parts = []
        
        if news_data['news']:
            summary_parts.append(f"📰 **Ultime notizie {team_name}:**")
            for i, article in enumerate(news_data['news'][:3], 1):
                summary_parts.append(f"{i}. {article.get('title', 'N/A')}")
                if article.get('snippet'):
                    summary_parts.append(f"   {article.get('snippet', '')[:100]}...")
        
        if news_data['injuries']:
            summary_parts.append(f"\n🏥 **Infortuni:**")
            for injury in news_data['injuries'][:2]:
                summary_parts.append(f"- {injury.get('title', 'N/A')}")
        
        if news_data['lineup']:
            summary_parts.append(f"\n📋 **Formazioni:**")
            for lineup in news_data['lineup'][:2]:
                summary_parts.append(f"- {lineup.get('title', 'N/A')}")
        
        return "\n".join(summary_parts) if summary_parts else f"Nessuna news recente trovata per {team_name}"

