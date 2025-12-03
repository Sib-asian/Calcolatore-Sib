"""
Identificatore di squadre con fuzzy matching
OTTIMIZZATO: Database pre-costruito, meno chiamate API
"""
from fuzzywuzzy import fuzz, process
import json
from pathlib import Path
from typing import Optional, Tuple, Dict
import requests
from src.config import FOOTBALL_DATA_API_KEY, FOOTBALL_DATA_BASE, SUPPORTED_LEAGUES, CACHE_DIR

class TeamIdentifier:
    """Identifica e normalizza nomi delle squadre"""
    
    def __init__(self):
        self.teams_db = {}
        self.teams_db_path = CACHE_DIR / "teams_database.json"
        self._load_teams_database()
    
    def _load_teams_database(self):
        """Carica database squadre da cache o crea nuovo"""
        if self.teams_db_path.exists():
            try:
                with open(self.teams_db_path, 'r', encoding='utf-8') as f:
                    self.teams_db = json.load(f)
                print(f"✓ Database squadre caricato: {len(self.teams_db)} squadre")
            except Exception as e:
                print(f"⚠️  Errore caricamento database: {e}. Ricostruendo...")
                self._build_teams_database()
        else:
            print("📥 Database squadre non trovato. Costruendo...")
            self._build_teams_database()
    
    def _build_teams_database(self):
        """
        Costruisce database squadre da API Football-Data.org
        OTTIMIZZATO: Chiamate batch, gestione errori
        """
        print("Costruendo database squadre...")
        headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY} if FOOTBALL_DATA_API_KEY else {}
        
        total_teams = 0
        failed_leagues = []
        
        for league_name, league_code in SUPPORTED_LEAGUES.items():
            try:
                url = f"{FOOTBALL_DATA_BASE}/competitions/{league_code}/teams"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    teams = data.get("teams", [])
                    
                    for team in teams:
                        team_id = team.get("id")
                        team_name = team.get("name", "")
                        short_name = team.get("shortName", "")
                        tla = team.get("tla", "")
                        
                        # Aggiungi tutte le varianti del nome
                        variants = [team_name, short_name, tla]
                        variants = [v for v in variants if v]  # Rimuovi vuoti
                        
                        self.teams_db[team_id] = {
                            "id": team_id,
                            "name": team_name,
                            "short_name": short_name,
                            "tla": tla,
                            "variants": variants,
                            "league": league_name,
                            "league_code": league_code
                        }
                    
                    total_teams += len(teams)
                    print(f"  ✓ {league_name}: {len(teams)} squadre")
                    
                    # Rate limiting: 10 req/min = 6 sec tra chiamate
                    import time
                    time.sleep(6.1)
                else:
                    print(f"  ⚠️  {league_name}: Errore {response.status_code}")
                    failed_leagues.append(league_name)
            except Exception as e:
                print(f"  ⚠️  {league_name}: Errore {e}")
                failed_leagues.append(league_name)
        
        # Salva database
        if self.teams_db:
            with open(self.teams_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.teams_db, f, ensure_ascii=False, indent=2)
            print(f"\n✓ Database squadre creato: {total_teams} squadre")
            if failed_leagues:
                print(f"⚠️  Leghe non caricate: {', '.join(failed_leagues)}")
        else:
            print("❌ Errore: Nessuna squadra caricata!")
    
    def identify_team(self, team_input: str, threshold: int = 70) -> Optional[Dict]:
        """
        Identifica una squadra dal nome inserito
        
        Args:
            team_input: Nome squadra inserito dall'utente
            threshold: Soglia minima di similarità (0-100)
        
        Returns:
            Dict con info squadra o None se non trovata
        """
        if not self.teams_db:
            print("⚠️  Database squadre vuoto. Ricostruendo...")
            self._build_teams_database()
            if not self.teams_db:
                return None
        
        # Crea lista di tutte le varianti dei nomi
        all_variants = []
        for team_id, team_info in self.teams_db.items():
            for variant in team_info["variants"]:
                all_variants.append((variant, team_id))
        
        # Fuzzy matching
        best_match = process.extractOne(
            team_input,
            [v[0] for v in all_variants],
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            matched_name = best_match[0]
            # Trova team_id corrispondente
            for variant, team_id in all_variants:
                if variant == matched_name:
                    return self.teams_db[team_id]
        
        return None
    
    def parse_match_input(self, input_text: str) -> Tuple[Dict, Dict]:
        """
        Parsa input tipo "Juventus vs Inter" o "Juventus - Inter"
        
        Returns:
            Tuple (home_team, away_team)
        
        Raises:
            ValueError: Se formato non valido o squadre non trovate
        """
        # Normalizza separatori
        separators = [" vs ", " VS ", " - ", " – ", " v ", " V "]
        for sep in separators:
            if sep in input_text:
                parts = input_text.split(sep, 1)
                if len(parts) == 2:
                    home_name = parts[0].strip()
                    away_name = parts[1].strip()
                    
                    home_team = self.identify_team(home_name)
                    away_team = self.identify_team(away_name)
                    
                    if home_team and away_team:
                        return (home_team, away_team)
                    else:
                        missing = []
                        if not home_team:
                            missing.append(home_name)
                        if not away_team:
                            missing.append(away_name)
                        raise ValueError(f"Squadre non trovate: {', '.join(missing)}")
        
        raise ValueError("Formato input non valido. Usa: 'Squadra1 vs Squadra2'")
