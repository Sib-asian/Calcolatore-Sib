"""
Modelli statistici per predizioni calcio
Poisson distribution per gol, Elo ratings per forza squadre
"""
import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple
import json
from pathlib import Path
from src.config import DATA_DIR

class PoissonModel:
    """Modello Poisson per predire gol e risultati"""
    
    def __init__(self):
        self.elo_ratings_path = DATA_DIR / "elo_ratings.json"
        self.elo_ratings = self._load_elo_ratings()
        self.base_elo = 1500
    
    def _load_elo_ratings(self) -> Dict:
        """Carica Elo ratings da file"""
        if self.elo_ratings_path.exists():
            with open(self.elo_ratings_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_elo_ratings(self):
        """Salva Elo ratings"""
        with open(self.elo_ratings_path, 'w') as f:
            json.dump(self.elo_ratings, f, indent=2)
    
    def get_team_elo(self, team_id: int) -> float:
        """Ottiene Elo rating squadra (default 1500)"""
        return self.elo_ratings.get(str(team_id), self.base_elo)
    
    def update_elo(self, team1_id: int, team2_id: int, score1: int, score2: int, k_factor: int = 32):
        """Aggiorna Elo dopo un match"""
        elo1 = self.get_team_elo(team1_id)
        elo2 = self.get_team_elo(team2_id)
        
        expected1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
        expected2 = 1 / (1 + 10 ** ((elo1 - elo2) / 400))
        
        # Risultato reale
        if score1 > score2:
            actual1, actual2 = 1, 0
        elif score1 < score2:
            actual1, actual2 = 0, 1
        else:
            actual1, actual2 = 0.5, 0.5
        
        # Aggiorna Elo
        new_elo1 = elo1 + k_factor * (actual1 - expected1)
        new_elo2 = elo2 + k_factor * (actual2 - expected2)
        
        self.elo_ratings[str(team1_id)] = new_elo1
        self.elo_ratings[str(team2_id)] = new_elo2
        self._save_elo_ratings()
    
    def predict_goals(self, home_attack: float, away_attack: float, 
                     home_defense: float, away_defense: float,
                     home_advantage: float = 0.3) -> Tuple[float, float]:
        """
        Predice gol attesi usando Poisson
        
        Args:
            home_attack: Media gol fatti casa
            away_attack: Media gol fatti trasferta
            home_defense: Media gol subiti casa
            away_defense: Media gol subiti trasferta
            home_advantage: Bonus per fattore casa
        
        Returns:
            (expected_home_goals, expected_away_goals)
        """
        # Calcola forza attacco/difesa
        home_strength = (home_attack + away_defense) / 2 + home_advantage
        away_strength = (away_attack + home_defense) / 2
        
        # Normalizza per evitare valori estremi
        home_strength = max(0.1, min(5.0, home_strength))
        away_strength = max(0.1, min(5.0, away_strength))
        
        return (home_strength, away_strength)
    
    def predict_1x2(self, home_goals_exp: float, away_goals_exp: float) -> Dict[str, float]:
        """
        Predice probabilità 1X2 usando Poisson
        
        Returns:
            {"1": prob_home, "X": prob_draw, "2": prob_away}
        """
        # Calcola probabilità per ogni possibile risultato (max 5 gol per squadra)
        prob_home = 0
        prob_draw = 0
        prob_away = 0
        
        for i in range(6):  # 0-5 gol casa
            for j in range(6):  # 0-5 gol trasferta
                prob = poisson.pmf(i, home_goals_exp) * poisson.pmf(j, away_goals_exp)
                
                if i > j:
                    prob_home += prob
                elif i == j:
                    prob_draw += prob
                else:
                    prob_away += prob
        
        # Normalizza
        total = prob_home + prob_draw + prob_away
        if total > 0:
            prob_home /= total
            prob_draw /= total
            prob_away /= total
        
        return {
            "1": prob_home,
            "X": prob_draw,
            "2": prob_away
        }
    
    def predict_over_under(self, home_goals_exp: float, away_goals_exp: float, 
                          threshold: float = 2.5) -> Dict[str, float]:
        """
        Predice Over/Under
        
        Returns:
            {"over": prob, "under": prob}
        """
        total_goals_exp = home_goals_exp + away_goals_exp
        
        # Usa Poisson per somma gol
        prob_over = 0
        prob_under = 0
        
        for goals in range(11):  # 0-10 gol totali
            prob = poisson.pmf(goals, total_goals_exp)
            if goals > threshold:
                prob_over += prob
            else:
                prob_under += prob
        
        # Normalizza
        total = prob_over + prob_under
        if total > 0:
            prob_over /= total
            prob_under /= total
        
        return {
            "over": prob_over,
            "under": prob_under
        }
    
    def predict_exact_goals(self, home_goals_exp: float, away_goals_exp: float) -> Dict[int, float]:
        """
        Predice probabilità gol esatti totali
        
        Returns:
            {gol_totali: probabilità}
        """
        total_goals_exp = home_goals_exp + away_goals_exp
        probabilities = {}
        
        for goals in range(8):  # 0-7 gol totali
            prob = poisson.pmf(goals, total_goals_exp)
            probabilities[goals] = max(0, prob)
        
        # Normalizza
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v/total for k, v in probabilities.items()}
        
        return probabilities
    
    def predict_btts(self, home_goals_exp: float, away_goals_exp: float) -> Dict[str, float]:
        """
        Predice Both Teams To Score
        
        Returns:
            {"yes": prob, "no": prob}
        """
        # Probabilità che entrambe segnino almeno 1 gol
        prob_home_scores = 1 - poisson.pmf(0, home_goals_exp)
        prob_away_scores = 1 - poisson.pmf(0, away_goals_exp)
        
        prob_both = prob_home_scores * prob_away_scores
        prob_not_both = 1 - prob_both
        
        return {
            "yes": prob_both,
            "no": prob_not_both
        }
    
    def predict_ht(self, home_goals_exp: float, away_goals_exp: float) -> Dict[str, float]:
        """
        Predice risultato primo tempo
        Tipicamente primo tempo ha ~40% dei gol totali
        """
        ht_home_exp = home_goals_exp * 0.4
        ht_away_exp = away_goals_exp * 0.4
        
        return self.predict_1x2(ht_home_exp, ht_away_exp)
    
    def predict_ht_ft(self, home_goals_exp: float, away_goals_exp: float) -> Dict[str, float]:
        """
        Predice combinato HT/FT
        """
        ht_probs = self.predict_ht(home_goals_exp, away_goals_exp)
        ft_probs = self.predict_1x2(home_goals_exp, away_goals_exp)
        
        # Combinazioni possibili
        combinations = {
            "1/1": ht_probs["1"] * ft_probs["1"],
            "1/X": ht_probs["1"] * ft_probs["X"],
            "1/2": ht_probs["1"] * ft_probs["2"],
            "X/1": ht_probs["X"] * ft_probs["1"],
            "X/X": ht_probs["X"] * ft_probs["X"],
            "X/2": ht_probs["X"] * ft_probs["2"],
            "2/1": ht_probs["2"] * ft_probs["1"],
            "2/X": ht_probs["2"] * ft_probs["X"],
            "2/2": ht_probs["2"] * ft_probs["2"]
        }
        
        # Normalizza
        total = sum(combinations.values())
        if total > 0:
            combinations = {k: v/total for k, v in combinations.items()}
        
        return combinations





