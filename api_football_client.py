"""
API Football Client
Client per recuperare statistiche squadre da API-Football.com
"""

import requests
import time
from typing import Dict, List, Optional
from config import (
    API_FOOTBALL_KEY, 
    API_FOOTBALL_BASE_URL,
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)


class APIFootballClient:
    """
    Client per API-Football con cache in-memory e gestione errori.
    """
    
    def __init__(self, api_key: str = API_FOOTBALL_KEY):
        """
        Inizializza client API.
        
        Args:
            api_key: Chiave API Football
        """
        self.api_key = api_key
        self.base_url = API_FOOTBALL_BASE_URL
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': api_key
        }
        self.cache = {}  # Cache in-memory per sessione
        self.last_request_time = 0
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Effettua richiesta API con retry e rate limiting.
        
        Args:
            endpoint: Endpoint API (es. '/teams')
            params: Parametri query
            
        Returns:
            Response JSON o None se errore
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(MAX_RETRIES):
            try:
                # Rate limiting: max 1 req/secondo
                time_since_last = time.time() - self.last_request_time
                if time_since_last < 1.0:
                    time.sleep(1.0 - time_since_last)
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=API_TIMEOUT
                )
                
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('response'):
                        return data
                    else:
                        return None
                elif response.status_code == 429:
                    # Rate limit exceeded
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    return None
                else:
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return None
        
        return None
    
    def search_team(self, team_name: str) -> Optional[Dict]:
        """
        Cerca squadra per nome con logica intelligente.
        
        Priorità:
        1. Alias esatti (Milan → AC Milan)
        2. Match nome esatto
        3. Squadre top leghe europee
        4. Escluse squadre giovanili/femminili
        
        Args:
            team_name: Nome squadra (es. 'Inter', 'Juventus')
            
        Returns:
            Dict con team_id e team_name o None
        """
        # Alias per squadre ambigue (chiave=input, valore=nome corretto per API)
        team_aliases = {
            'milan': 'AC Milan',
            'inter': 'Inter',
            'roma': 'AS Roma',
            'lazio': 'Lazio',
            'bologna': 'Bologna',
            'parma': 'Parma',
            'city': 'Manchester City',
            'united': 'Manchester United',
            'psg': 'Paris Saint Germain',
            'atletico': 'Atletico Madrid',
        }
        
        # Check alias
        search_term = team_name
        team_key_lower = team_name.lower().strip()
        if team_key_lower in team_aliases:
            search_term = team_aliases[team_key_lower]
        
        # Check cache
        cache_key = f"team_{search_term.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # API call
        data = self._make_request('/teams', {'search': search_term})
        
        if not data or not data.get('response'):
            return None
        
        teams = data['response']
        
        if len(teams) == 0:
            return None
        
        # Priorità: squadre da top leghe europee + match nome esatto
        # Top leagues IDs (Serie A, Premier, La Liga, Bundesliga, Ligue 1, etc)
        top_league_ids = [
            135,  # Serie A (Italia)
            39,   # Premier League (Inghilterra)
            140,  # La Liga (Spagna)
            78,   # Bundesliga (Germania)
            61,   # Ligue 1 (Francia)
            94,   # Primeira Liga (Portogallo)
            88,   # Eredivisie (Olanda)
            203,  # Super Lig (Turchia)
            2,    # Champions League
            3,    # Europa League
        ]
        
        # Cerca match migliore
        best_team = None
        best_score = -1
        
        for team_data in teams:
            team = team_data['team']
            venue = team_data.get('venue', {})
            
            score = 0
            
            # 1. Match nome esatto (case-insensitive)
            if team['name'].lower() == team_name.lower():
                score += 100
            elif team['name'].lower().startswith(team_name.lower()):
                score += 50
            elif team_name.lower() in team['name'].lower():
                score += 25
            
            # 2. Top league bonus
            # Nota: L'API non restituisce direttamente la league nel search,
            # quindi diamo priorità a paesi top
            country = team.get('country', '')
            if country in ['England', 'Italy', 'Spain', 'Germany', 'France']:
                score += 30
            elif country in ['Portugal', 'Netherlands', 'Belgium', 'Turkey']:
                score += 20
            
            # 3. Penalità PESANTE per squadre "secondarie" (giovanili, femminili, riserve)
            name_lower = team['name'].lower()
            if any(x in name_lower for x in ['u19', 'u20', 'u21', 'u23', 'u18', 'youth', 'primavera']):
                score -= 500  # Penalità molto alta per giovanili
            elif any(x in name_lower for x in [' b', ' ii', ' c', ' reserves']):
                score -= 400  # Penalità alta per squadre B/C/riserve
            elif any(x in name_lower for x in [' w', 'women', 'femminile']):
                score -= 500  # Penalità molto alta per femminile
            
            if score > best_score:
                best_score = score
                best_team = team
        
        if best_team is None:
            best_team = teams[0]['team']  # Fallback al primo
        
        result = {
            'team_id': best_team['id'],
            'team_name': best_team['name'],
            'logo': best_team.get('logo', ''),
            'country': best_team.get('country', '')
        }
        
        # Cache
        self.cache[cache_key] = result
        return result
    
    def get_team_last_matches(self, team_id: int, venue: str = 'all', limit: int = 5) -> List[Dict]:
        """
        Recupera ultimi match di una squadra.
        
        Args:
            team_id: ID squadra
            venue: 'home', 'away', o 'all'
            limit: Numero match da recuperare
            
        Returns:
            Lista di match con risultati e gol
        """
        params = {
            'team': team_id,
            'last': limit * 5 if venue in ['home', 'away'] else limit * 2,  # Moltiplicatore più alto per venue specifico
            'status': 'FT'  # Solo match finiti
        }
        
        data = self._make_request('/fixtures', params)
        
        if not data or not data.get('response'):
            return []
        
        fixtures = data['response']
        matches = []
        
        for fixture in fixtures:
            teams = fixture['teams']
            goals = fixture['goals']
            
            # Determina se casa o trasferta
            is_home = teams['home']['id'] == team_id
            is_away = teams['away']['id'] == team_id
            
            if not (is_home or is_away):
                continue
            
            # Filtra per venue
            if venue == 'home' and not is_home:
                continue
            if venue == 'away' and not is_away:
                continue
            
            # Estrai info
            if is_home:
                goals_for = goals['home']
                goals_against = goals['away']
            else:
                goals_for = goals['away']
                goals_against = goals['home']
            
            # Determina risultato
            if goals_for > goals_against:
                result = 'W'
            elif goals_for < goals_against:
                result = 'L'
            else:
                result = 'D'
            
            matches.append({
                'result': result,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'venue': 'home' if is_home else 'away'
            })
            
            # Stop quando abbiamo abbastanza match
            if len(matches) >= limit:
                break
        
        return matches[:limit]
    
    def calculate_team_stats(self, matches: List[Dict]) -> Dict:
        """
        Calcola statistiche da lista match.
        
        Args:
            matches: Lista match da get_team_last_matches
            
        Returns:
            Dict con stats calcolate
        """
        if not matches:
            return {
                'matches_count': 0,
                'results': [],
                'goals_scored_avg': 0.0,
                'goals_conceded_avg': 0.0,
                'form_factor': 0.5,
                'variance': 0.0
            }
        
        results = [m['result'] for m in matches]
        goals_scored = [m['goals_for'] for m in matches]
        goals_conceded = [m['goals_against'] for m in matches]
        
        # Media gol
        avg_scored = sum(goals_scored) / len(goals_scored)
        avg_conceded = sum(goals_conceded) / len(goals_conceded)
        
        # Form factor (peso decrescente: più recente = più importante)
        # W=1.0, D=0.5, L=0.0
        weights = [0.35, 0.25, 0.20, 0.12, 0.08][:len(results)]
        points = {'W': 1.0, 'D': 0.5, 'L': 0.0}
        
        form = sum(
            points[result] * weight 
            for result, weight in zip(results, weights)
        ) / sum(weights)
        
        # Variance gol segnati (per stabilità)
        mean = avg_scored
        variance = sum((x - mean) ** 2 for x in goals_scored) / len(goals_scored)
        
        return {
            'matches_count': len(matches),
            'results': results,
            'goals_scored_avg': round(avg_scored, 2),
            'goals_conceded_avg': round(avg_conceded, 2),
            'form_factor': round(form, 3),
            'variance': round(variance, 3)
        }
    
    def get_team_stats(self, team_name: str, venue: str = 'home') -> Optional[Dict]:
        """
        Recupera statistiche complete squadra.
        
        Args:
            team_name: Nome squadra
            venue: 'home' o 'away'
            
        Returns:
            Dict con tutte le stats o None se errore
        """
        # Check cache completa
        cache_key = f"stats_{team_name.lower()}_{venue}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 1. Cerca squadra
        team = self.search_team(team_name)
        if not team:
            return None
        
        # 2. Recupera ultimi match
        matches = self.get_team_last_matches(team['team_id'], venue=venue, limit=5)
        if not matches:
            return None
        
        # 3. Calcola stats
        stats = self.calculate_team_stats(matches)
        
        # 4. Combina tutto
        result = {
            'team_name': team['team_name'],
            'team_id': team['team_id'],
            'venue': venue,
            **stats
        }
        
        # Cache
        self.cache[cache_key] = result
        return result


# Singleton per app Streamlit
_client_instance = None

def get_api_client() -> APIFootballClient:
    """
    Ottieni istanza singleton del client API.
    
    Returns:
        APIFootballClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = APIFootballClient()
    return _client_instance

