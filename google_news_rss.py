"""
Google News RSS Feed Client
Client gratuito per recuperare news da Google News tramite RSS
Non richiede API key
Con traduzione automatica in italiano
"""

import requests
from xml.etree import ElementTree as ET
from typing import List, Dict, Any
from urllib.parse import quote_plus
import time

# Traduzione automatica
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("INFO: deep-translator non disponibile, nessuna traduzione automatica")


class GoogleNewsRSS:
    """Client per Google News RSS - completamente gratuito con traduzione automatica"""

    def __init__(self):
        self.base_url = "https://news.google.com/rss/search"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 secondo tra richieste

        # Inizializza traduttore (auto-detect → italiano)
        if TRANSLATOR_AVAILABLE:
            self.translator = GoogleTranslator(source='auto', target='it')
        else:
            self.translator = None

    def _detect_team_language(self, team_name: str) -> tuple[str, str]:
        """
        Rileva lingua e regione ottimali per la squadra

        Returns:
            (language_code, region_code) es. ('de', 'DE') per Bayern
        """
        team_lower = team_name.lower()

        # Bundesliga (Germania)
        if any(x in team_lower for x in ['bayern', 'dortmund', 'leipzig', 'leverkusen', 'frankfurt', 'stuttgart']):
            return ('de', 'DE')

        # Ligue 1 (Francia)
        elif any(x in team_lower for x in ['psg', 'marseille', 'lyon', 'lille', 'monaco', 'nice', 'lens']):
            return ('fr', 'FR')

        # La Liga (Spagna)
        elif any(x in team_lower for x in ['barcelona', 'real madrid', 'atletico', 'sevilla', 'valencia', 'athletic']):
            return ('es', 'ES')

        # Premier League (Inghilterra)
        elif any(x in team_lower for x in ['liverpool', 'manchester', 'chelsea', 'arsenal', 'tottenham', 'city', 'united']):
            return ('en', 'GB')

        # Portugal
        elif any(x in team_lower for x in ['benfica', 'porto', 'sporting']):
            return ('pt', 'PT')

        # Serie A / Italia (default)
        else:
            return ('it', 'IT')

    def _translate_to_italian(self, text: str) -> str:
        """
        Traduce automaticamente testo in italiano

        Args:
            text: Testo da tradurre

        Returns:
            Testo tradotto in italiano (o originale se traduzione fallisce)
        """
        if not self.translator or not text:
            return text

        try:
            # Traduci solo se non è già italiano
            translated = self.translator.translate(text)
            return translated if translated else text
        except Exception as e:
            # Se traduzione fallisce, ritorna originale
            return text

    def _rate_limit(self):
        """Rate limiting gentile"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def search_team_news(self, team_name: str, keywords: List[str] = None, max_results: int = 20, translate: bool = True) -> List[Dict[str, Any]]:
        """
        Cerca news per una squadra su Google News

        Args:
            team_name: Nome squadra (es. "Inter Milan", "Bayern Munich")
            keywords: Keywords aggiuntive (es. ["injuries", "lineup"])
            max_results: Numero massimo risultati
            translate: Se True, traduce titoli in italiano

        Returns:
            Lista di articoli con 'title', 'link', 'pubDate', 'description'
        """
        self._rate_limit()

        # Rileva lingua ottimale per la squadra
        lang_code, region_code = self._detect_team_language(team_name)

        # Costruisci query
        if keywords:
            # Usa OR per keywords multiple
            keywords_str = " OR ".join(keywords)
            query = f"{team_name} ({keywords_str})"
        else:
            # Aggiungi contesto sport in base alla lingua
            sport_keyword = 'football' if lang_code == 'en' else 'calcio' if lang_code == 'it' else 'fußball' if lang_code == 'de' else 'football'
            query = f"{team_name} {sport_keyword}"

        # Costruisci URL con lingua/regione della squadra
        query_encoded = quote_plus(query)
        url = f"{self.base_url}?q={query_encoded}&hl={lang_code}&gl={region_code}&ceid={region_code}:{lang_code}"

        print(f"DEBUG: Cerco notizie per {team_name} in {lang_code.upper()} (regione {region_code})")

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

                        title_original = title_elem.text if title_elem is not None else ''

                        # Traduci titolo in italiano se richiesto
                        if translate and title_original:
                            title_translated = self._translate_to_italian(title_original)
                        else:
                            title_translated = title_original

                        article = {
                            'title': title_translated,  # Titolo tradotto
                            'title_original': title_original,  # Titolo originale (per debug)
                            'link': link_elem.text if link_elem is not None else '',
                            'pubDate': pubdate_elem.text if pubdate_elem is not None else '',
                            'description': desc_elem.text if desc_elem is not None else '',
                            'source': 'Google News RSS',
                            'language': lang_code  # Lingua originale
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
        """Cerca notizie su infortuni - ITALIANO"""
        return self.search_team_news(
            team_name,
            keywords=['infortunati', 'infortunio', 'injury list', 'injured players'],
            max_results=15
        )

    def search_lineup(self, team_name: str) -> List[Dict[str, Any]]:
        """Cerca notizie su formazioni - ITALIANO"""
        return self.search_team_news(
            team_name,
            keywords=['formazione probabile', 'formazione', 'lineup', 'starting XI', 'probabile formazione'],
            max_results=15
        )

    def search_unavailable(self, team_name: str) -> List[Dict[str, Any]]:
        """Cerca giocatori indisponibili - ITALIANO, solo GIOCATORI"""
        return self.search_team_news(
            team_name,
            keywords=['squalificati giocatori', 'giocatori squalificati', 'sospesi giocatori', 'suspended players'],
            max_results=15
        )
