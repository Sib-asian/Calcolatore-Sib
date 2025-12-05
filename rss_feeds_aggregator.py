"""
RSS Feeds Aggregator
Aggrega news da RSS feeds di siti sportivi
"""
import feedparser
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from cache_manager import CacheManager
import config
from text_parser_advanced import TextParserAdvanced

class RSSFeedsAggregator:
    """Aggrega news da RSS feeds di siti sportivi"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.parser = TextParserAdvanced()
        
        # RSS feeds di siti sportivi (gratuiti, pubblici)
        # Nota: alcuni feed potrebbero non essere disponibili, gestiti con try/except
        self.rss_feeds = {
            'gazzetta': {
                'url': 'https://www.gazzetta.it/rss/home.xml',
                'name': 'Gazzetta dello Sport',
                'sport_section': True
            },
            'corriere_sport': {
                'url': 'https://www.corriere.it/rss/homepage.xml',
                'name': 'Corriere dello Sport',
                'sport_section': True
            },
            # Feed che potrebbero non essere disponibili, commentati per ora
            # 'sky_sport': {
            #     'url': 'https://sport.sky.it/rss',
            #     'name': 'Sky Sport',
            #     'sport_section': True
            # },
            # 'tuttosport': {
            #     'url': 'https://www.tuttosport.com/rss',
            #     'name': 'Tuttosport',
            #     'sport_section': True
            # },
            # 'calciomercato': {
            #     'url': 'https://www.calciomercato.com/rss',
            #     'name': 'Calciomercato.com',
            #     'sport_section': True
            # },
        }
        
        self.last_fetch_time = {}
        self.min_fetch_interval = 300  # 5 minuti tra fetch dello stesso feed
    
    def _should_fetch(self, feed_key: str) -> bool:
        """Verifica se è il momento di fare fetch del feed"""
        if feed_key not in self.last_fetch_time:
            return True
        
        time_since_last = time.time() - self.last_fetch_time[feed_key]
        return time_since_last >= self.min_fetch_interval
    
    def _fetch_rss_feed(self, feed_config: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Recupera articoli da un RSS feed
        
        Args:
            feed_config: Configurazione feed (url, name, ecc.)
            
        Returns:
            Lista di articoli o None se errore
        """
        try:
            url = feed_config['url']
            
            # Controlla cache
            cache_key = f"rss_{feed_config.get('name', 'unknown')}"
            cached = self.cache.get_cached_search(cache_key)
            if cached and isinstance(cached, list):
                # Cache valida per 1 ora
                return cached[:20]  # Max 20 articoli
            
            # Fetch feed
            response = requests.get(url, timeout=config.WEB_SEARCH_TIMEOUT_SECONDS)
            response.raise_for_status()
            
            # Parse RSS
            feed = feedparser.parse(response.content)
            
            if feed.bozo and feed.bozo_exception:
                # Feed malformato, ignora
                return None
            
            articles = []
            for entry in feed.entries[:20]:  # Max 20 articoli per feed
                article = {
                    'title': entry.get('title', ''),
                    'snippet': entry.get('summary', '') or entry.get('description', ''),
                    'url': entry.get('link', ''),
                    'date': entry.get('published', '') or entry.get('updated', ''),
                    'source': feed_config['name']
                }
                
                # Estrai informazioni strutturate
                parsed = self.parser.parse_news_article(article['title'], article['snippet'])
                article['parsed_info'] = parsed
                
                articles.append(article)
            
            # Salva in cache
            if articles:
                self.cache.save_search(cache_key, articles, ttl_hours=1)
                self.last_fetch_time[feed_config.get('name', 'unknown')] = time.time()
            
            return articles
            
        except Exception as e:
            print(f"Errore fetch RSS feed {feed_config.get('name', 'unknown')}: {e}")
            return None
    
    def search_team_news(self, team_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Cerca news su una squadra da tutti i RSS feeds
        
        Args:
            team_name: Nome della squadra
            max_results: Numero massimo di risultati
            
        Returns:
            Lista di articoli rilevanti
        """
        all_articles = []
        
        # Cerca in tutti i feed
        for feed_key, feed_config in self.rss_feeds.items():
            if not self._should_fetch(feed_key):
                # Usa cache se disponibile
                cache_key = f"rss_{feed_config.get('name', 'unknown')}"
                cached = self.cache.get_cached_search(cache_key)
                if cached:
                    all_articles.extend(cached)
                    continue
            
            articles = self._fetch_rss_feed(feed_config)
            if articles:
                all_articles.extend(articles)
        
        # Filtra per rilevanza (cerca team_name nel titolo o snippet)
        team_lower = team_name.lower()
        relevant_articles = []
        
        for article in all_articles:
            title = article.get('title', '').lower()
            snippet = article.get('snippet', '').lower()
            
            # Controlla se squadra è menzionata
            if team_lower in title or team_lower in snippet:
                relevant_articles.append(article)
        
        # Ordina per data (più recenti prima)
        relevant_articles.sort(
            key=lambda x: x.get('date', ''),
            reverse=True
        )
        
        return relevant_articles[:max_results]
    
    def get_recent_news(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Recupera news recenti da tutti i feed
        
        Args:
            max_results: Numero massimo di risultati
            
        Returns:
            Lista di articoli recenti
        """
        all_articles = []
        
        for feed_key, feed_config in self.rss_feeds.items():
            articles = self._fetch_rss_feed(feed_config)
            if articles:
                all_articles.extend(articles)
        
        # Ordina per data
        all_articles.sort(
            key=lambda x: x.get('date', ''),
            reverse=True
        )
        
        return all_articles[:max_results]
    
    def get_team_structured_info(self, team_name: str) -> Dict[str, Any]:
        """
        Recupera informazioni strutturate su una squadra da RSS
        
        Args:
            team_name: Nome della squadra
            
        Returns:
            Dict con 'news', 'injuries', 'formations', 'players'
        """
        news = self.search_team_news(team_name, max_results=15)
        
        # Aggrega informazioni estratte
        all_players = []
        all_formations = []
        all_injuries = []
        
        for article in news:
            parsed = article.get('parsed_info', {})
            
            # Raccogli giocatori menzionati
            players = parsed.get('players_mentioned', [])
            all_players.extend(players)
            
            # Raccogli formazioni
            formations = parsed.get('formations', [])
            all_formations.extend(formations)
            
            # Raccogli infortuni
            injuries = parsed.get('injuries', [])
            all_injuries.extend(injuries)
        
        # Rimuovi duplicati
        unique_players = list(set(all_players))[:20]  # Max 20 giocatori
        unique_formations = list(set(all_formations))
        
        return {
            'news': news[:10],  # Max 10 news
            'injuries': all_injuries[:10],  # Max 10 infortuni
            'formations': unique_formations[:5],  # Max 5 formazioni
            'players_mentioned': unique_players,
            'source': 'rss_feeds'
        }

