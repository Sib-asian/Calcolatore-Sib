"""
Raccolta dati da API gratuite
Gestisce cache e rate limiting
OTTIMIZZATO: Riduce chiamate API, migliora cache
"""
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import time
from src.config import (
    FOOTBALL_DATA_API_KEY, FOOTBALL_DATA_BASE, 
    CACHE_DIR, CACHE_DURATION_HOURS
)

class DataCollector:
    """Raccoglie dati statistici delle squadre con cache ottimizzata"""
    
    def __init__(self):
        self.headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY} if FOOTBALL_DATA_API_KEY else {}
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_api_call = 0
        self.min_api_interval = 6.1  # Secondi tra chiamate (10/min = 6 sec)
    
    def _rate_limit(self):
        """Gestisce rate limiting API (10 richieste/minuto)"""
        now = time.time()
        time_since_last = now - self.last_api_call
        if time_since_last < self.min_api_interval:
            sleep_time = self.min_api_interval - time_since_last
            time.sleep(sleep_time)
        self.last_api_call = time.time()
    
    def _get_cache_path(self, key: str) -> Path:
        """Genera path cache file"""
        return self.cache_dir / f"{key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Verifica se cache è ancora valida"""
        if not cache_path.exists():
            return False
        
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - file_time < timedelta(hours=CACHE_DURATION_HOURS)
    
    def _load_cache(self, cache_path: Path) -> Optional[Dict]:
        """Carica dati da cache"""
        if self._is_cache_valid(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_cache(self, cache_path: Path, data: Dict):
        """Salva dati in cache"""
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def _api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        Esegue richiesta API con rate limiting e gestione errori
        
        Returns:
            Dict con dati o None se errore
        """
        self._rate_limit()
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit exceeded
                print("⚠️  Rate limit API raggiunto. Attendi 1 minuto...")
                time.sleep(60)
                # Retry una volta
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                if response.status_code == 200:
                    return response.json()
            elif response.status_code == 403:
                print("⚠️  API key non valida o scaduta. Verifica .env")
            else:
                print(f"⚠️  Errore API: {response.status_code}")
            
            return None
        except requests.exceptions.Timeout:
            print("⚠️  Timeout API. Riprova più tardi.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Errore connessione API: {e}")
            return None
    
    def get_team_matches(self, team_id: int, limit: int = 10) -> List[Dict]:
        """
        Recupera ultimi match di una squadra
        OTTIMIZZATO: Cache più intelligente
        """
        cache_key = f"team_{team_id}_matches_{limit}"
        cache_path = self._get_cache_path(cache_key)
        
        # Prova cache prima
        cached = self._load_cache(cache_path)
        if cached:
            return cached
        
        # Se non in cache, chiama API
        url = f"{FOOTBALL_DATA_BASE}/teams/{team_id}/matches"
        params = {"limit": limit, "status": "FINISHED"}
        
        data = self._api_request(url, params)
        if data:
            matches = data.get("matches", [])
            if matches:
                self._save_cache(cache_path, matches)
            return matches
        
        # Fallback: prova a caricare cache scaduta come ultima risorsa
        if cache_path.exists():
            print(f"⚠️  Usando cache scaduta per squadra {team_id}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return []
    
    def get_head_to_head(self, team1_id: int, team2_id: int) -> List[Dict]:
        """
        Recupera confronti diretti tra due squadre
        OTTIMIZZATO: Cache per coppia squadre
        """
        # Ordina ID per cache consistente
        id1, id2 = sorted([team1_id, team2_id])
        cache_key = f"h2h_{id1}_{id2}"
        cache_path = self._get_cache_path(cache_key)
        
        # Prova cache
        cached = self._load_cache(cache_path)
        if cached:
            return cached
        
        # Chiama API solo per una squadra (più efficiente)
        url = f"{FOOTBALL_DATA_BASE}/teams/{team1_id}/matches"
        params = {"limit": 20, "status": "FINISHED"}
        
        data = self._api_request(url, params)
        if data:
            all_matches = data.get("matches", [])
            
            # Filtra solo match tra le due squadre
            h2h_matches = []
            for match in all_matches:
                home_id = match.get("homeTeam", {}).get("id")
                away_id = match.get("awayTeam", {}).get("id")
                if (home_id == team1_id and away_id == team2_id) or \
                   (home_id == team2_id and away_id == team1_id):
                    h2h_matches.append(match)
            
            if h2h_matches:
                self._save_cache(cache_path, h2h_matches)
            return h2h_matches
        
        # Fallback: cache scaduta
        if cache_path.exists():
            print(f"⚠️  Usando cache scaduta per H2H {team1_id} vs {team2_id}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return []
    
    def get_upcoming_match(self, team1_id: int, team2_id: int) -> Optional[Dict]:
        """Cerca prossima partita tra due squadre"""
        try:
            # Prova a cercare nella competizione della squadra 1
            team1_info = self._get_team_info(team1_id)
            if not team1_info:
                return None
            
            league_code = team1_info.get("league_code")
            if not league_code:
                return None
            
            url = f"{FOOTBALL_DATA_BASE}/competitions/{league_code}/matches"
            params = {"status": "SCHEDULED"}
            
            data = self._api_request(url, params)
            if data:
                matches = data.get("matches", [])
                
                for match in matches:
                    home_id = match.get("homeTeam", {}).get("id")
                    away_id = match.get("awayTeam", {}).get("id")
                    if (home_id == team1_id and away_id == team2_id) or \
                       (home_id == team2_id and away_id == team1_id):
                        return match
        except Exception as e:
            print(f"Errore nel recupero prossima partita: {e}")
        
        return None
    
    def _get_team_info(self, team_id: int) -> Optional[Dict]:
        """Recupera info base squadra (con cache)"""
        cache_key = f"team_info_{team_id}"
        cache_path = self._get_cache_path(cache_key)
        
        cached = self._load_cache(cache_path)
        if cached:
            return cached
        
        url = f"{FOOTBALL_DATA_BASE}/teams/{team_id}"
        data = self._api_request(url)
        
        if data:
            self._save_cache(cache_path, data)
            return data
        
        return None
    
    def calculate_team_stats(self, team_id: int, is_home: bool = True) -> Dict:
        """
        Calcola statistiche squadra dagli ultimi match
        OTTIMIZZATO: Usa cache, fallback intelligente
        """
        matches = self.get_team_matches(team_id, limit=10)
        
        if not matches:
            # Fallback: statistiche default basate su media generale
            return {
                "goals_scored_avg": 1.5,
                "goals_conceded_avg": 1.5,
                "form_points": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "matches_count": 0
            }
        
        # Filtra per casa/trasferta se necessario
        relevant_matches = []
        for match in matches:
            home_id = match.get("homeTeam", {}).get("id")
            if (is_home and home_id == team_id) or (not is_home and home_id != team_id):
                relevant_matches.append(match)
        
        # Se non abbastanza match specifici, usa tutti (meglio di niente)
        if len(relevant_matches) < 3:
            relevant_matches = matches[:min(10, len(matches))]
        
        goals_scored = []
        goals_conceded = []
        points = 0
        wins = 0
        draws = 0
        losses = 0
        
        for match in relevant_matches:
            home_id = match.get("homeTeam", {}).get("id")
            score = match.get("score", {}).get("fullTime", {})
            home_score = score.get("home")
            away_score = score.get("away")
            
            if home_score is None or away_score is None:
                continue
            
            if home_id == team_id:
                goals_scored.append(home_score)
                goals_conceded.append(away_score)
                if home_score > away_score:
                    points += 3
                    wins += 1
                elif home_score == away_score:
                    points += 1
                    draws += 1
                else:
                    losses += 1
            else:
                goals_scored.append(away_score)
                goals_conceded.append(home_score)
                if away_score > home_score:
                    points += 3
                    wins += 1
                elif away_score == home_score:
                    points += 1
                    draws += 1
                else:
                    losses += 1
        
        # Calcola medie
        if goals_scored:
            goals_scored_avg = sum(goals_scored) / len(goals_scored)
        else:
            goals_scored_avg = 1.5
        
        if goals_conceded:
            goals_conceded_avg = sum(goals_conceded) / len(goals_conceded)
        else:
            goals_conceded_avg = 1.5
        
        return {
            "goals_scored_avg": goals_scored_avg,
            "goals_conceded_avg": goals_conceded_avg,
            "form_points": points,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "matches_count": len(relevant_matches)
        }
    
    def calculate_h2h_stats(self, team1_id: int, team2_id: int) -> Dict:
        """Calcola statistiche confronti diretti"""
        h2h_matches = self.get_head_to_head(team1_id, team2_id)
        
        if not h2h_matches:
            return {
                "team1_wins": 0,
                "team2_wins": 0,
                "draws": 0,
                "total_matches": 0,
                "team1_goals_avg": 1.5,
                "team2_goals_avg": 1.5
            }
        
        team1_wins = 0
        team2_wins = 0
        draws = 0
        team1_goals = []
        team2_goals = []
        
        for match in h2h_matches[:10]:  # Max 10 H2H
            home_id = match.get("homeTeam", {}).get("id")
            score = match.get("score", {}).get("fullTime", {})
            home_score = score.get("home", 0)
            away_score = score.get("away", 0)
            
            if home_id == team1_id:
                team1_goals.append(home_score)
                team2_goals.append(away_score)
                if home_score > away_score:
                    team1_wins += 1
                elif home_score < away_score:
                    team2_wins += 1
                else:
                    draws += 1
            else:
                team1_goals.append(away_score)
                team2_goals.append(home_score)
                if away_score > home_score:
                    team1_wins += 1
                elif away_score < home_score:
                    team2_wins += 1
                else:
                    draws += 1
        
        return {
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "draws": draws,
            "total_matches": len(h2h_matches),
            "team1_goals_avg": sum(team1_goals) / len(team1_goals) if team1_goals else 1.5,
            "team2_goals_avg": sum(team2_goals) / len(team2_goals) if team2_goals else 1.5
        }
