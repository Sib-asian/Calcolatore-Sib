"""
Google News RSS Feed Client
Client gratuito per recuperare news da Google News tramite RSS
Non richiede API key
"""

import requests
from xml.etree import ElementTree as ET
from typing import List, Dict, Any
from urllib.parse import quote_plus
import time


class GoogleNewsRSS:
    """Client per Google News RSS - completamente gratuito"""

    def __init__(self):
        self.base_url = "https://news.google.com/rss/search"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 secondo tra richieste per essere gentili

    def _rate_limit(self):
        """Rate limiting gentile"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def search_team_news(self, team_name: str, keywords: List[str] = None, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Cerca news per una squadra su Google News

        Args:
            team_name: Nome squadra (es. "Inter Milan", "Bayern Munich")
            keywords: Keywords aggiuntive (es. ["injuries", "lineup"])
            max_results: Numero massimo risultati

        Returns:
            Lista di articoli con 'title', 'link', 'pubDate', 'description'
        """
        self._rate_limit()

        # Costruisci query
        if keywords:
            # Usa OR per keywords multiple
            keywords_str = " OR ".join(keywords)
            query = f"{team_name} football ({keywords_str})"
        else:
            query = f"{team_name} football"

        # Parametri URL
        params = {
            'q': query,
            'hl': 'en',  # Lingua inglese per più risultati
            'gl': 'US',  # Regione USA
            'ceid': 'US:en'
        }

        # Costruisci URL manualmente per evitare problemi encoding
        query_encoded = quote_plus(query)
        url = f"{self.base_url}?q={query_encoded}&hl=en&gl=US&ceid=US:en"

        try:
            response = requests.get(url, timeout=15)

            if response.status_code == 200:
                # Parsa XML RSS
                root = ET.fromstring(response.content)
                items = root.findall('.//item')

                results = []
                for item in items[:max_results]:
                    try:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        pubdate_elem = item.find('pubDate')
                        desc_elem = item.find('description')

                        article = {
                            'title': title_elem.text if title_elem is not None else '',
                            'link': link_elem.text if link_elem is not None else '',
                            'pubDate': pubdate_elem.text if pubdate_elem is not None else '',
                            'description': desc_elem.text if desc_elem is not None else '',
                            'source': 'Google News RSS'
                        }

                        if article['title']:  # Solo se ha almeno un titolo
                            results.append(article)
                    except Exception as e:
                        # Salta articolo mal formattato
                        continue

                return results
            else:
                print(f"Google News RSS error: {response.status_code}")
                return []

        except Exception as e:
            print(f"Google News RSS exception: {e}")
            return []

    def search_injuries(self, team_name: str) -> List[Dict[str, Any]]:
        """Cerca notizie su infortuni"""
        return self.search_team_news(
            team_name,
            keywords=['injuries', 'injured', 'injury list', 'infortunio', 'infortunati'],
            max_results=15
        )

    def search_lineup(self, team_name: str) -> List[Dict[str, Any]]:
        """Cerca notizie su formazioni"""
        return self.search_team_news(
            team_name,
            keywords=['lineup', 'starting XI', 'team news', 'formazione', 'probabile formazione'],
            max_results=15
        )

    def search_unavailable(self, team_name: str) -> List[Dict[str, Any]]:
        """Cerca giocatori indisponibili (squalificati, sospesi)"""
        return self.search_team_news(
            team_name,
            keywords=['suspended', 'banned', 'unavailable', 'squalificato', 'sospeso'],
            max_results=15
        )
