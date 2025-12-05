"""
News Aggregator (Gratuito)
Utilizza NewsAPI (free tier) + DuckDuckGo come fallback
Con ricerca intelligente per nomi completi squadre
"""
import requests
import time
from typing import Dict, Any, List, Optional
import config
from cache_manager import CacheManager
from web_search_free import WebSearchFree
from team_search_intelligent import TeamSearchIntelligent
from rss_feeds_aggregator import RSSFeedsAggregator
from text_parser_advanced import TextParserAdvanced

class NewsAggregatorFree:
    """Aggrega news da NewsAPI e DuckDuckGo con cache intelligente"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.web_search = WebSearchFree()
        self.team_search = TeamSearchIntelligent()
        self.rss_aggregator = RSSFeedsAggregator()
        self.text_parser = TextParserAdvanced()
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
        """Recupera news da NewsAPI se disponibile usando nome completo squadra"""
        self._check_daily_limit()
        
        # Controlla limite giornaliero
        if self.news_api_requests_today >= config.NEWS_API_RATE_LIMIT_PER_DAY:
            self.news_api_available = False
            return None
        
        try:
            # Ottieni nome completo squadra
            full_name, _ = self.team_search.get_team_search_queries(team_name)
            
            # Query ottimizzata con nome completo
            # Prova prima con nome completo, poi con originale
            queries = [
                f"{full_name} AND (calcio OR football OR soccer)",
                f"{team_name} AND (calcio OR football OR soccer)"
            ]
            
            url = f"{config.NEWS_API_BASE_URL}/everything"
            
            # Prova prima query (nome completo)
            for query in queries:
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
                    
                    # Se troviamo risultati, restituiscili
                    if results:
                        self.news_api_requests_today += 1
                        return results
                else:
                    # Se errore, disabilita NewsAPI per oggi
                    if response.status_code == 429:  # Too many requests
                        self.news_api_available = False
                        return None
                    # Continua con prossima query se questa fallisce
                    continue
            
            # Se nessuna query ha funzionato
            return None
                
        except Exception as e:
            print(f"Errore NewsAPI: {e}")
            return None
    
    def get_team_news(self, team_name: str) -> Dict[str, Any]:
        """
        Recupera news per una squadra da multiple fonti (RSS, NewsAPI, DuckDuckGo)
        con parsing avanzato per estrarre nomi, formazioni e infortuni
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Dict con 'news', 'injuries', 'lineup', 'formations', 'players_mentioned', 'source'
        """
        # Controlla cache
        cached = self.cache.get_cached_news(team_name)
        if cached:
            return cached
        
        result = {
            'news': [],
            'injuries': [],
            'lineup': [],
            'formations': [],
            'players_mentioned': [],
            'source': 'multiple'
        }
        
        all_news = []
        all_injuries = []
        all_formations = []
        all_players = []
        
        # 1. Prova RSS Feeds (priorità alta, aggiornamenti frequenti)
        try:
            rss_info = self.rss_aggregator.get_team_structured_info(team_name)
            if rss_info.get('news'):
                all_news.extend(rss_info['news'])
                result['source'] = 'rss_feeds'
            
            if rss_info.get('injuries'):
                all_injuries.extend(rss_info['injuries'])
            
            if rss_info.get('formations'):
                all_formations.extend(rss_info['formations'])
            
            if rss_info.get('players_mentioned'):
                all_players.extend(rss_info['players_mentioned'])
        except Exception as e:
            print(f"Errore RSS aggregator: {e}")
        
        # 2. Prova NewsAPI (se disponibile)
        if self.news_api_available and len(all_news) < 10:
            try:
                newsapi_results = self._get_news_from_newsapi(team_name)
                if newsapi_results:
                    # Arricchisci con parsing
                    newsapi_results = self.text_parser.enhance_search_results(newsapi_results)
                    all_news.extend(newsapi_results)
                    if result['source'] == 'multiple':
                        result['source'] = 'newsapi+rss'
            except Exception as e:
                print(f"Errore NewsAPI: {e}")
        
        # 3. Fallback a DuckDuckGo (se ancora pochi risultati)
        if len(all_news) < 5:
            try:
                duckduckgo_results = self.web_search.search_news(team_name, max_results=5)
                all_news.extend(duckduckgo_results)
                if result['source'] == 'multiple':
                    result['source'] = 'duckduckgo+rss'
            except Exception as e:
                print(f"Errore DuckDuckGo: {e}")
        
        # 4. Cerca infortuni e formazioni con DuckDuckGo (se non trovati)
        if not all_injuries:
            try:
                injuries_results = self.web_search.search_injuries(team_name)
                # Estrai infortuni dai risultati
                for injury_result in injuries_results:
                    parsed = self.text_parser.parse_news_article(
                        injury_result.get('title', ''),
                        injury_result.get('snippet', '')
                    )
                    if parsed.get('injuries'):
                        all_injuries.extend(parsed['injuries'])
            except Exception as e:
                print(f"Errore ricerca infortuni: {e}")
        
        if not all_formations:
            try:
                lineup_results = self.web_search.search_lineup(team_name)
                # Estrai formazioni dai risultati
                for lineup_result in lineup_results:
                    parsed = self.text_parser.parse_news_article(
                        lineup_result.get('title', ''),
                        lineup_result.get('snippet', '')
                    )
                    if parsed.get('formations'):
                        all_formations.extend(parsed['formations'])
            except Exception as e:
                print(f"Errore ricerca formazioni: {e}")
        
        # Rimuovi duplicati e aggrega
        # News: rimuovi duplicati per URL
        seen_urls = set()
        unique_news = []
        for news in all_news:
            url = news.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_news.append(news)
        
        # Infortuni: rimuovi duplicati per giocatore
        seen_players = set()
        unique_injuries = []
        for injury in all_injuries:
            player = injury.get('player', '') if isinstance(injury, dict) else ''
            if player and player not in seen_players:
                seen_players.add(player)
                unique_injuries.append(injury)
        
        # Formazioni: rimuovi duplicati
        unique_formations = list(set(all_formations))
        
        # Giocatori: rimuovi duplicati
        unique_players = list(set(all_players))
        
        # Aggiorna risultato
        result['news'] = unique_news[:15]  # Max 15 news
        result['injuries'] = unique_injuries[:10]  # Max 10 infortuni
        result['formations'] = unique_formations[:5]  # Max 5 formazioni
        result['players_mentioned'] = unique_players[:20]  # Max 20 giocatori
        result['lineup'] = []  # Mantenuto per compatibilità
        
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

