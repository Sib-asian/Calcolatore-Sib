"""
Team Search Intelligente
Utilizza Wikipedia per trovare nomi completi squadre e genera query multi-variante
"""
import re
import time
from typing import List, Dict, Any, Optional, Tuple
import wikipediaapi
from cache_manager import CacheManager
import config

class TeamSearchIntelligent:
    """Ricerca intelligente nomi squadre con Wikipedia e query multi-variante"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.wiki = wikipediaapi.Wikipedia(
            language='it',  # Prova prima italiano
            user_agent='CalcolatoreSIB/1.0'
        )
        self.wiki_en = wikipediaapi.Wikipedia(
            language='en',  # Fallback inglese
            user_agent='CalcolatoreSIB/1.0'
        )
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 0.5 secondi tra richieste Wikipedia
    
    def _rate_limit(self):
        """Rispetta rate limiting per Wikipedia"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _normalize_team_name(self, team_name: str) -> str:
        """Normalizza nome squadra per ricerca"""
        # Rimuovi spazi extra e converti in lowercase
        normalized = re.sub(r'\s+', ' ', team_name.strip().lower())
        # Rimuovi caratteri speciali problematici
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        return normalized
    
    def _search_wikipedia(self, query: str, lang: str = 'it') -> Optional[Dict[str, Any]]:
        """
        Cerca una squadra su Wikipedia
        
        Args:
            query: Query di ricerca
            lang: Lingua ('it' o 'en')
            
        Returns:
            Dict con 'title', 'full_name', 'summary' o None
        """
        self._rate_limit()
        
        wiki = self.wiki if lang == 'it' else self.wiki_en
        
        try:
            # Cerca pagina
            page = wiki.page(query)
            
            if page.exists():
                # Estrai informazioni
                title = page.title
                summary = page.summary[:200] if page.summary else ""
                
                # Verifica che sia una pagina di squadra calcio
                if any(keyword in summary.lower() for keyword in ['calcio', 'football', 'soccer', 'club', 'squadra']):
                    return {
                        'title': title,
                        'full_name': title,
                        'summary': summary,
                        'lang': lang
                    }
        except Exception as e:
            # Ignora errori, prova fallback
            pass
        
        return None
    
    def find_team_full_name(self, team_name: str) -> Optional[str]:
        """
        Trova il nome completo di una squadra usando Wikipedia
        
        Args:
            team_name: Nome squadra (es: "brest", "monaco", "benfica", "sporting")
            
        Returns:
            Nome completo (es: "Stade Brestois 29", "S.L. Benfica", "Sporting CP") o None
        """
        # Mappa alias comuni per squadre famose
        team_aliases = {
            'benfica': ['S.L. Benfica', 'Benfica', 'Sport Lisboa e Benfica'],
            'sporting': ['Sporting CP', 'Sporting Clube de Portugal', 'Sporting Lisbona'],
            'porto': ['FC Porto', 'Porto', 'Futebol Clube do Porto'],
            'inter': ['Inter', 'Inter Milan', 'FC Internazionale Milano'],
            'milan': ['AC Milan', 'Milan', 'Associazione Calcio Milan'],
            'juve': ['Juventus', 'Juventus FC'],
            'roma': ['AS Roma', 'Roma'],
            'lazio': ['SS Lazio', 'Lazio'],
            'napoli': ['SSC Napoli', 'Napoli'],
            'atalanta': ['Atalanta BC', 'Atalanta'],
            'fiorentina': ['ACF Fiorentina', 'Fiorentina'],
            'bologna': ['Bologna FC 1909', 'Bologna'],
            'barca': ['FC Barcelona', 'Barcelona', 'Barça'],
            'real': ['Real Madrid', 'Real Madrid CF'],
            'atletico': ['Atlético Madrid', 'Atletico Madrid'],
            'psg': ['Paris Saint-Germain', 'PSG'],
            'lyon': ['Olympique Lyonnais', 'Lyon'],
            'marsiglia': ['Olympique de Marseille', 'Marseille', 'OM'],
            'lilla': ['Lille OSC', 'Lille'],
            'monaco': ['AS Monaco', 'Monaco'],
            'brest': ['Stade Brestois 29', 'Brest'],
            'mainz': ['1. FSV Mainz 05', 'Mainz 05', 'Mainz'],
            'monchengladbach': ['Borussia Mönchengladbach', 'Mönchengladbach', 'Gladbach'],
            'dortmund': ['Borussia Dortmund', 'Dortmund'],
            'bayern': ['FC Bayern München', 'Bayern Munich', 'Bayern'],
            'liverpool': ['Liverpool FC', 'Liverpool'],
            'city': ['Manchester City', 'Man City'],
            'united': ['Manchester United', 'Man United'],
            'chelsea': ['Chelsea FC', 'Chelsea'],
            'arsenal': ['Arsenal FC', 'Arsenal'],
            'tottenham': ['Tottenham Hotspur', 'Spurs'],
            'ajax': ['AFC Ajax', 'Ajax'],
            'psv': ['PSV Eindhoven', 'PSV'],
            'feyenoord': ['Feyenoord', 'Feyenoord Rotterdam']
        }
        
        normalized = self._normalize_team_name(team_name)
        
        # Controlla alias prima
        for alias, full_names in team_aliases.items():
            if alias in normalized or normalized in alias:
                return full_names[0]  # Restituisci il primo nome completo
        
        # Controlla cache
        cache_key = f"team_name_{normalized}"
        cached = self.cache.get_cached_search(cache_key)
        if cached and isinstance(cached, list) and len(cached) > 0:
            if isinstance(cached[0], dict) and 'full_name' in cached[0]:
                return cached[0]['full_name']
        
        normalized = self._normalize_team_name(team_name)
        
        # Query varianti per Wikipedia
        queries = [
            normalized,
            f"{normalized} calcio",
            f"{normalized} football",
            f"{normalized} fc",
            f"{normalized} club",
            f"AS {normalized}",
            f"Stade {normalized}",
            f"{normalized} squadra"
        ]
        
        # Prova prima in italiano
        for query in queries:
            result = self._search_wikipedia(query, lang='it')
            if result:
                full_name = result['full_name']
                # Salva in cache
                self.cache.save_search(cache_key, [result], ttl_hours=24*7)  # Cache 7 giorni
                return full_name
        
        # Fallback inglese
        for query in queries:
            result = self._search_wikipedia(query, lang='en')
            if result:
                full_name = result['full_name']
                # Salva in cache
                self.cache.save_search(cache_key, [result], ttl_hours=24*7)
                return full_name
        
        return None
    
    def generate_query_variants(self, team_name: str, full_name: Optional[str] = None) -> List[str]:
        """
        Genera varianti intelligenti di query per ricerca
        
        Args:
            team_name: Nome squadra originale
            full_name: Nome completo trovato (opzionale)
            
        Returns:
            Lista di query varianti
        """
        variants = []
        normalized = self._normalize_team_name(team_name)
        
        # Se abbiamo nome completo, usalo
        if full_name:
            variants.extend([
                full_name,
                f"{full_name} news",
                f"{full_name} calcio",
                f"{full_name} football",
                f"{full_name} ultime notizie"
            ])
        
        # Varianti base
        variants.extend([
            f"{normalized} calcio",
            f"{normalized} football",
            f"{normalized} soccer",
            f"{normalized} news",
            f"{normalized} ultime notizie",
            f"{normalized} squadra",
            f"AS {normalized}",
            f"FC {normalized}",
            f"{normalized} club"
        ])
        
        # Rimuovi duplicati mantenendo ordine
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant.lower() not in seen:
                seen.add(variant.lower())
                unique_variants.append(variant)
        
        return unique_variants[:10]  # Max 10 varianti
    
    def get_team_search_queries(self, team_name: str) -> Tuple[str, List[str]]:
        """
        Ottiene nome completo e query varianti per una squadra
        
        Args:
            team_name: Nome squadra
            
        Returns:
            Tuple (full_name, query_variants)
            - full_name: Nome completo trovato o team_name originale
            - query_variants: Lista di query varianti
        """
        # Prova a trovare nome completo
        full_name = self.find_team_full_name(team_name)
        
        # Genera query varianti
        query_variants = self.generate_query_variants(team_name, full_name)
        
        # Usa nome completo se trovato, altrimenti originale
        display_name = full_name if full_name else team_name
        
        return display_name, query_variants
    
    def get_multi_language_queries(self, team_name: str, full_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Genera query multi-lingua per ricerca internazionale
        
        Args:
            team_name: Nome squadra
            full_name: Nome completo (opzionale)
            
        Returns:
            Dict con query per ogni lingua
        """
        base_name = full_name if full_name else team_name
        
        queries = {
            'it': [
                f"{base_name} calcio news",
                f"{base_name} ultime notizie",
                f"{base_name} infortuni"
            ],
            'en': [
                f"{base_name} football news",
                f"{base_name} latest news",
                f"{base_name} injuries"
            ],
            'fr': [
                f"{base_name} football actualités",
                f"{base_name} dernières nouvelles",
                f"{base_name} blessures"
            ],
            'es': [
                f"{base_name} fútbol noticias",
                f"{base_name} últimas noticias",
                f"{base_name} lesiones"
            ]
        }
        
        return queries

