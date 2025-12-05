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
        Recupera SOLO informazioni essenziali match-day: infortuni, indisponibili, formazioni
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Dict con 'injuries', 'formations', 'unavailable', 'match_notes' (NO news generiche)
        """
        # Controlla cache
        cached = self.cache.get_cached_news(team_name)
        if cached:
            return cached
        
        result = {
            'injuries': [],
            'formations': [],
            'unavailable': [],  # Squalificati, sospesi, ecc.
            'match_notes': [],  # Note essenziali match-day
            'source': 'multiple'
        }
        
        all_injuries = []
        all_formations = []
        all_unavailable = []
        
        # 1. Cerca INFORTUNI con query specifiche MULTILINGUA (approfondita)
        try:
            injuries_results = self.web_search.search_injuries(team_name)
            print(f"DEBUG: Trovati {len(injuries_results)} risultati per infortuni {team_name}")
            for injury_result in injuries_results:
                title = injury_result.get('title', '')
                snippet = injury_result.get('snippet', '')
                # Combina title e snippet per parsing migliore
                full_text = f"{title} {snippet}"
                parsed = self.text_parser.parse_news_article(title, snippet)
                if parsed.get('injuries'):
                    all_injuries.extend(parsed['injuries'])
                    print(f"DEBUG: Estratti {len(parsed['injuries'])} infortuni da: {title[:50]}")
        except Exception as e:
            print(f"Errore ricerca infortuni: {e}")
        
        # 2. Cerca FORMAZIONI con query specifiche MULTILINGUA (approfondita)
        try:
            lineup_results = self.web_search.search_lineup(team_name)
            print(f"DEBUG: Trovati {len(lineup_results)} risultati per formazioni {team_name}")
            for lineup_result in lineup_results:
                title = lineup_result.get('title', '')
                snippet = lineup_result.get('snippet', '')
                parsed = self.text_parser.parse_news_article(title, snippet)
                if parsed.get('formations'):
                    all_formations.extend(parsed['formations'])
                    print(f"DEBUG: Estratte {len(parsed['formations'])} formazioni da: {title[:50]}")
        except Exception as e:
            print(f"Errore ricerca formazioni: {e}")
        
        # 3. Cerca INDISPONIBILI (squalificati, sospesi) con query specifiche MULTILINGUA (approfondita)
        try:
            unavailable_results = self.web_search.search_unavailable(team_name)
            print(f"DEBUG: Trovati {len(unavailable_results)} risultati per indisponibili {team_name}")
            for unavailable_result in unavailable_results:
                title = unavailable_result.get('title', '')
                snippet = unavailable_result.get('snippet', '')
                parsed = self.text_parser.parse_news_article(title, snippet)
                # Estrai giocatori indisponibili
                injuries = parsed.get('injuries', [])
                for injury in injuries:
                    if isinstance(injury, dict):
                        status = injury.get('status', '').lower()
                        player = injury.get('player', '')
                        # Cerca keywords di indisponibilità nel testo
                        full_text = f"{title} {snippet}".lower()
                        if ('suspended' in status or 'squalificato' in status or 'sospeso' in status or
                            'suspended' in full_text or 'squalificato' in full_text or 'sospeso' in full_text or
                            'banned' in full_text or 'ban' in full_text):
                            all_unavailable.append(injury)
                            print(f"DEBUG: Trovato indisponibile: {player} ({status})")
        except Exception as e:
            print(f"Errore ricerca indisponibili: {e}")
        
        # Rimuovi duplicati
        seen_players = set()
        unique_injuries = []
        for injury in all_injuries:
            player = injury.get('player', '') if isinstance(injury, dict) else ''
            if player and player not in seen_players:
                seen_players.add(player)
                unique_injuries.append(injury)
        
        # Indisponibili: rimuovi duplicati
        seen_unavailable = set()
        unique_unavailable = []
        for unavailable in all_unavailable:
            player = unavailable.get('player', '') if isinstance(unavailable, dict) else ''
            if player and player not in seen_unavailable:
                seen_unavailable.add(player)
                unique_unavailable.append(unavailable)
        
        # Formazioni: rimuovi duplicati
        unique_formations = list(set(all_formations))
        
        # Aggiorna risultato (SOLO info essenziali, NO news generiche)
        result['injuries'] = unique_injuries[:10]  # Max 10 infortuni
        result['formations'] = unique_formations[:5]  # Max 5 formazioni
        result['unavailable'] = unique_unavailable[:10]  # Max 10 indisponibili
        
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

