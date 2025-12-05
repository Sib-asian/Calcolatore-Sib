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
from text_parser_advanced import TextParserAdvanced

# RSS Feeds opzionale (richiede feedparser che può avere problemi di dipendenze)
try:
    from rss_feeds_aggregator import RSSFeedsAggregator
    RSS_AVAILABLE = True
except ImportError:
    RSS_AVAILABLE = False
    print("INFO: RSSFeedsAggregator non disponibile (feedparser mancante)")

class NewsAggregatorFree:
    """Aggrega news da NewsAPI e DuckDuckGo con cache intelligente"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.web_search = WebSearchFree()
        self.team_search = TeamSearchIntelligent()
        self.rss_aggregator = RSSFeedsAggregator() if RSS_AVAILABLE else None
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
    
    def _get_news_from_newsapi(self, team_name: str, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Recupera news da NewsAPI se disponibile usando nome completo squadra"""
        self._check_daily_limit()

        # Controlla limite giornaliero
        if self.news_api_requests_today >= config.NEWS_API_RATE_LIMIT_PER_DAY:
            self.news_api_available = False
            return None

        try:
            # Ottieni nome completo squadra
            full_name, _ = self.team_search.get_team_search_queries(team_name)

            # Query ottimizzata: SEMPLICI per massimizzare risultati
            # NewsAPI free tier ha pochi articoli recenti, query troppo complesse = 0 risultati
            queries = [
                f"{full_name}",  # Nome completo
                f"{team_name}"   # Nome originale come fallback
            ]

            url = f"{config.NEWS_API_BASE_URL}/everything"

            # Prova prima query (nome completo)
            for query in queries:
                # Lingua basata sul nome squadra per migliori risultati
                if any(x in team_name.lower() for x in ['bayern', 'dortmund', 'leipzig']):
                    lang = 'de,en'  # Tedesco + Inglese per Bundesliga
                elif any(x in team_name.lower() for x in ['psg', 'marseille', 'lyon', 'monaco']):
                    lang = 'fr,en'  # Francese + Inglese per Ligue 1
                elif any(x in team_name.lower() for x in ['benfica', 'porto', 'sporting']):
                    lang = 'pt,en'  # Portoghese + Inglese
                elif any(x in team_name.lower() for x in ['barcelona', 'real madrid', 'atletico']):
                    lang = 'es,en'  # Spagnolo + Inglese
                else:
                    lang = 'en,it'  # Default: Inglese + Italiano

                params = {
                    'q': query,
                    'language': lang,
                    'sortBy': 'publishedAt',
                    'pageSize': max_results,
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
                        if article.get('title'):
                            results.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'content': article.get('content', ''),
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
        # Controlla cache (TEMPORANEAMENTE DISABILITATO per test)
        # cached = self.cache.get_cached_news(team_name)
        # if cached:
        #     return cached
        
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
        
        # PRIORITÀ 1: Prova NewsAPI (più affidabile di DuckDuckGo)
        try:
            print(f"DEBUG: Provo NewsAPI per {team_name}...")
            newsapi_results = self._get_news_from_newsapi(team_name)
            print(f"DEBUG: NewsAPI trovati {len(newsapi_results) if newsapi_results else 0} risultati")
            
            # Processa risultati NewsAPI
            if newsapi_results:
                for article in newsapi_results:
                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = article.get('content', '')
                    full_text = f"{title} {description} {content}"
                    
                    # Cerca infortuni
                    parsed = self.text_parser.parse_news_article(title, description or content)
                    if parsed.get('injuries'):
                        all_injuries.extend(parsed['injuries'])
                        print(f"DEBUG: NewsAPI - Estratti {len(parsed['injuries'])} infortuni")
                    
                    # Cerca formazioni
                    if parsed.get('formations'):
                        all_formations.extend(parsed['formations'])
                        print(f"DEBUG: NewsAPI - Estratte {len(parsed['formations'])} formazioni")
                    
                    # FALLBACK: cerca keywords anche senza parsing strutturato
                    if any(kw in full_text.lower() for kw in ['injured', 'injury', 'infortunio', 'infortunato']):
                        players = self.text_parser.extract_player_names(full_text, max_names=3)
                        for player in players:
                            if not any(i.get('player', '') == player for i in all_injuries if isinstance(i, dict)):
                                all_injuries.append({'player': player, 'status': 'unknown', 'context': full_text[:100]})
                                print(f"DEBUG: NewsAPI - Estratto infortunio fallback: {player}")
                    
                    # Cerca formazioni anche senza parsing strutturato
                    formations_found = self.text_parser.extract_formations(full_text)
                    if formations_found:
                        all_formations.extend(formations_found)
                        print(f"DEBUG: NewsAPI - Estratte formazioni fallback: {formations_found}")
        except Exception as e:
            print(f"DEBUG: Errore NewsAPI: {e}")
        
        # PRIORITÀ 2: Prova DuckDuckGo solo se NewsAPI non ha trovato abbastanza risultati
        if len(all_injuries) < 3:
            try:
                print(f"DEBUG: NewsAPI insufficiente, provo DuckDuckGo per {team_name}...")
                injuries_results = self.web_search.search_injuries(team_name)
                print(f"DEBUG: DuckDuckGo trovati {len(injuries_results)} risultati per infortuni")
                if not injuries_results:
                    try:
                        generic_results = self.web_search.search_web(f"{team_name} news", max_results=5)
                        injuries_results = generic_results
                        print(f"DEBUG: Query generiche DuckDuckGo trovate {len(generic_results)} risultati")
                    except Exception as e:
                        print(f"DEBUG: Errore query generiche DuckDuckGo: {e}")
                        injuries_results = []
                
                for injury_result in injuries_results:
                    title = injury_result.get('title', '')
                    snippet = injury_result.get('snippet', '')
                    full_text = f"{title} {snippet}"
                    parsed = self.text_parser.parse_news_article(title, snippet)
                    if parsed.get('injuries'):
                        all_injuries.extend(parsed['injuries'])
                        print(f"DEBUG: DuckDuckGo - Estratti {len(parsed['injuries'])} infortuni")
                    elif any(kw in full_text.lower() for kw in ['injured', 'injury', 'infortunio', 'infortunato']):
                        players = self.text_parser.extract_player_names(full_text, max_names=3)
                        for player in players:
                            if not any(i.get('player', '') == player for i in all_injuries if isinstance(i, dict)):
                                all_injuries.append({'player': player, 'status': 'unknown', 'context': full_text[:100]})
                                print(f"DEBUG: DuckDuckGo - Estratto infortunio fallback: {player}")
            except Exception as e:
                print(f"Errore DuckDuckGo infortuni: {e}")
        
        # 2. Cerca FORMAZIONI (NewsAPI già processato sopra, qui solo DuckDuckGo se necessario)
        if len(all_formations) < 1:
            try:
                lineup_results = self.web_search.search_lineup(team_name)
                print(f"DEBUG: DuckDuckGo trovati {len(lineup_results)} risultati per formazioni")
                if not lineup_results:
                    try:
                        generic_results = self.web_search.search_web(f"{team_name} lineup", max_results=5)
                        lineup_results = generic_results
                        print(f"DEBUG: Query generiche formazioni DuckDuckGo trovate {len(generic_results)} risultati")
                    except Exception as e:
                        print(f"DEBUG: Errore query generiche formazioni DuckDuckGo: {e}")
                        lineup_results = []
                
                for lineup_result in lineup_results:
                    title = lineup_result.get('title', '')
                    snippet = lineup_result.get('snippet', '')
                    parsed = self.text_parser.parse_news_article(title, snippet)
                    if parsed.get('formations'):
                        all_formations.extend(parsed['formations'])
                        print(f"DEBUG: DuckDuckGo - Estratte {len(parsed['formations'])} formazioni")
                    else:
                        full_text = f"{title} {snippet}"
                        formations_found = self.text_parser.extract_formations(full_text)
                        if formations_found:
                            all_formations.extend(formations_found)
                            print(f"DEBUG: DuckDuckGo - Estratte formazioni fallback: {formations_found}")
            except Exception as e:
                print(f"Errore DuckDuckGo formazioni: {e}")
        
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
        
        # DEBUG: Stampa riepilogo finale
        print(f"DEBUG FINALE per {team_name}:")
        print(f"  - Infortuni trovati: {len(unique_injuries)}")
        print(f"  - Formazioni trovate: {len(unique_formations)}")
        print(f"  - Indisponibili trovati: {len(unique_unavailable)}")
        if unique_injuries:
            print(f"  - Esempio infortuni: {[i.get('player', 'N/A') if isinstance(i, dict) else str(i)[:30] for i in unique_injuries[:3]]}")
        if unique_formations:
            print(f"  - Formazioni: {unique_formations}")
        
        # FALLBACK FINALE: Se non abbiamo trovato nulla, aggiungi almeno informazioni generiche
        if not unique_injuries and not unique_formations and not unique_unavailable:
            print(f"DEBUG: Nessun dato trovato per {team_name}, aggiungo info generica...")
            # Prova una ricerca generica finale con NewsAPI
            try:
                generic_news = self._get_news_from_newsapi(team_name, max_results=3)
                if generic_news:
                    # Estrai almeno il titolo della prima news come informazione
                    first_news = generic_news[0]
                    result['match_notes'] = [f"Ultime news: {first_news.get('title', '')[:100]}"]
                    print(f"DEBUG: Aggiunta news generica: {first_news.get('title', '')[:50]}")
            except Exception as e:
                print(f"DEBUG: Errore fallback finale: {e}")
        
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

