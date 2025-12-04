"""
Script per scaricare dati storici da Football-Data.org
Salva in data/historical/ per training modelli ML
"""
import requests
import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
HISTORICAL_DIR = BASE_DIR / "data" / "historical"
HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)

FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

# Leghe da scaricare
LEAGUES = {
    "SA": "Serie A",
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1"
}

def download_league_matches(league_code: str, league_name: str, years: int = 2):
    """Scarica match storici di una lega"""
    print(f"\nScaricando {league_name} ({league_code})...")
    
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY} if FOOTBALL_DATA_API_KEY else {}
    matches_data = []
    
    # Calcola date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    try:
        # Ottieni competizione
        url = f"{FOOTBALL_DATA_BASE}/competitions/{league_code}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"  ❌ Errore accesso competizione: {response.status_code}")
            return
        
        # Scarica match (ultimi N anni)
        url = f"{FOOTBALL_DATA_BASE}/competitions/{league_code}/matches"
        params = {
            "dateFrom": start_date.strftime("%Y-%m-%d"),
            "dateTo": end_date.strftime("%Y-%m-%d"),
            "status": "FINISHED"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            
            for match in matches:
                home_team = match.get("homeTeam", {}).get("name", "")
                away_team = match.get("awayTeam", {}).get("name", "")
                score = match.get("score", {}).get("fullTime", {})
                home_score = score.get("home")
                away_score = score.get("away")
                match_date = match.get("utcDate", "")
                
                if home_score is not None and away_score is not None:
                    matches_data.append({
                        "date": match_date[:10] if match_date else "",
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": home_score,
                        "away_score": away_score,
                        "league": league_name
                    })
            
            print(f"  ✓ Scaricati {len(matches_data)} match")
        else:
            print(f"  ❌ Errore: {response.status_code}")
            return
        
        # Salva in CSV
        csv_path = HISTORICAL_DIR / f"matches_{league_code.lower()}.csv"
        if matches_data:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=matches_data[0].keys())
                writer.writeheader()
                writer.writerows(matches_data)
            print(f"  ✓ Salvato in {csv_path}")
        
        # Rate limiting
        time.sleep(6)  # 10 richieste/min = 6 secondi tra richieste
        
    except Exception as e:
        print(f"  ❌ Errore: {e}")

def main():
    """Funzione principale"""
    print("=" * 60)
    print("Download Dati Storici - Calcolatore Sib")
    print("=" * 60)
    
    if not FOOTBALL_DATA_API_KEY:
        print("⚠️  FOOTBALL_DATA_API_KEY non configurata in .env")
        print("   Il download sarà limitato (rate limit più basso)")
        response = input("   Continuare comunque? (s/n): ")
        if response.lower() != 's':
            return
    
    years = int(input("Anni di dati da scaricare (default 2): ") or "2")
    
    total_matches = 0
    for league_code, league_name in LEAGUES.items():
        download_league_matches(league_code, league_name, years)
        time.sleep(1)  # Pausa tra leghe
    
    print("\n" + "=" * 60)
    print("Download completato!")
    print(f"Dati salvati in: {HISTORICAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()





