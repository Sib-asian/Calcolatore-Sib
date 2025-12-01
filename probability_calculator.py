"""
Calcolatore di Probabilità Avanzato per Scommesse Calcistiche
Basato su modelli Poisson bivariati e aggiustamenti Dixon-Coles
"""

import numpy as np
from typing import Dict, List, Tuple
import math


class AdvancedProbabilityCalculator:
    """
    Calcolatore avanzato di probabilità per mercati scommesse calcistiche.
    Utilizza modelli statistici complessi per calcolare probabilità accurate.
    """
    
    def __init__(self):
        # Parametri Dixon-Coles per correggere probabilità 0-0 e 1-1
        self.rho = 0.1  # Correlazione tra gol casa e trasferta
        self.xi = 0.1   # Aggiustamento per match a basso scoring
        
    def spread_to_expected_goals(self, spread: float, total: float) -> Tuple[float, float]:
        """
        Converte spread e total in attese gol (lambda) per casa e trasferta.
        
        Formula:
        - total = lambda_home + lambda_away
        - spread = lambda_home - lambda_away
        
        Risolvendo:
        - lambda_home = (total + spread) / 2
        - lambda_away = (total - spread) / 2
        
        NOTA: Se spread è negativo (casa favorita), lambda_home deve essere MAGGIORE.
        Quindi la formula corretta è:
        - lambda_home = (total - spread) / 2  (se spread negativo, questo aumenta)
        - lambda_away = (total + spread) / 2  (se spread negativo, questo diminuisce)
        
        Args:
            spread: Spread (negativo = casa favorita, positivo = trasferta favorita)
            total: Total atteso (somma gol attesi)
            
        Returns:
            Tuple[lambda_home, lambda_away]
        """
        lambda_home = (total - spread) / 2.0
        lambda_away = (total + spread) / 2.0
        
        # Assicuriamo che le lambda siano sempre positive
        lambda_home = max(0.01, lambda_home)
        lambda_away = max(0.01, lambda_away)
        
        return lambda_home, lambda_away
    
    def dixon_coles_adjustment(self, home_goals: int, away_goals: int, 
                               lambda_home: float, lambda_away: float) -> float:
        """
        Aggiustamento Dixon-Coles per correggere probabilità di 0-0 e 1-1.
        Questi risultati sono statisticamente più probabili del modello Poisson puro.
        
        Formula:
        tau(i, j, lambda_home, lambda_away) = 
            1 - lambda_home * lambda_away * rho se (i,j) = (0,0)
            1 + lambda_home * rho se (i,j) = (1,0)
            1 + lambda_away * rho se (i,j) = (0,1)
            1 - rho se (i,j) = (1,1)
            1 altrimenti
            
        Args:
            home_goals: Gol casa
            away_goals: Gol trasferta
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Fattore di correzione tau
        """
        if home_goals == 0 and away_goals == 0:
            return 1 - lambda_home * lambda_away * self.rho
        elif home_goals == 1 and away_goals == 0:
            return 1 + lambda_home * self.rho
        elif home_goals == 0 and away_goals == 1:
            return 1 + lambda_away * self.rho
        elif home_goals == 1 and away_goals == 1:
            return 1 - self.rho
        else:
            return 1.0
    
    def poisson_probability(self, k: int, lambda_param: float) -> float:
        """
        Calcola probabilità Poisson: P(X = k) = (lambda^k * e^(-lambda)) / k!
        
        Args:
            k: Numero di eventi
            lambda_param: Parametro lambda (media)
            
        Returns:
            Probabilità
        """
        if k < 0:
            return 0.0
        return (lambda_param ** k * math.exp(-lambda_param)) / math.factorial(k)
    
    def exact_score_probability(self, home_goals: int, away_goals: int,
                               lambda_home: float, lambda_away: float) -> float:
        """
        Calcola probabilità di un risultato esatto usando Poisson + Dixon-Coles.
        
        Args:
            home_goals: Gol casa
            away_goals: Gol trasferta
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Probabilità del risultato esatto
        """
        # Probabilità Poisson base
        prob_home = self.poisson_probability(home_goals, lambda_home)
        prob_away = self.poisson_probability(away_goals, lambda_away)
        
        # Aggiustamento Dixon-Coles
        tau = self.dixon_coles_adjustment(home_goals, away_goals, lambda_home, lambda_away)
        
        return prob_home * prob_away * tau
    
    def calculate_1x2_probabilities(self, lambda_home: float, lambda_away: float) -> Dict[str, float]:
        """
        Calcola probabilità 1X2 (1 = Casa, X = Pareggio, 2 = Trasferta).
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Dict con probabilità 1, X, 2
        """
        prob_1 = 0.0  # Casa vince
        prob_X = 0.0  # Pareggio
        prob_2 = 0.0  # Trasferta vince
        
        # Calcoliamo per tutti i possibili risultati (fino a 10 gol per squadra)
        max_goals = 10
        for home in range(max_goals + 1):
            for away in range(max_goals + 1):
                prob = self.exact_score_probability(home, away, lambda_home, lambda_away)
                
                if home > away:
                    prob_1 += prob
                elif home == away:
                    prob_X += prob
                else:
                    prob_2 += prob
        
        # Normalizzazione per sicurezza
        total = prob_1 + prob_X + prob_2
        if total > 0:
            prob_1 /= total
            prob_X /= total
            prob_2 /= total
        
        return {
            '1': prob_1,
            'X': prob_X,
            '2': prob_2
        }
    
    def calculate_gg_ng_probabilities(self, lambda_home: float, lambda_away: float) -> Dict[str, float]:
        """
        Calcola probabilità GG (Goal-Goal, entrambe segnano) e NG (No Goal, almeno una non segna).
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Dict con probabilità GG e NG
        """
        prob_gg = 0.0  # Entrambe segnano
        prob_ng = 0.0  # Almeno una non segna
        
        max_goals = 10
        for home in range(max_goals + 1):
            for away in range(max_goals + 1):
                prob = self.exact_score_probability(home, away, lambda_home, lambda_away)
                
                if home > 0 and away > 0:
                    prob_gg += prob
                else:
                    prob_ng += prob
        
        return {
            'GG': prob_gg,
            'NG': prob_ng
        }
    
    def calculate_over_under_probabilities(self, lambda_home: float, lambda_away: float,
                                          thresholds: List[float] = None) -> Dict[str, float]:
        """
        Calcola probabilità Over/Under per vari totali.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            thresholds: Lista di soglie (default: [0.5, 1.5, 2.5, 3.5, 4.5])
            
        Returns:
            Dict con probabilità Over/Under per ogni soglia
        """
        if thresholds is None:
            thresholds = [0.5, 1.5, 2.5, 3.5, 4.5]
        
        results = {}
        max_goals = 10
        
        for threshold in thresholds:
            prob_over = 0.0
            prob_under = 0.0
            
            for home in range(max_goals + 1):
                for away in range(max_goals + 1):
                    total_goals = home + away
                    prob = self.exact_score_probability(home, away, lambda_home, lambda_away)
                    
                    if total_goals > threshold:
                        prob_over += prob
                    elif total_goals < threshold:
                        prob_under += prob
                    # Se total_goals == threshold (solo per interi), non aggiungiamo nulla
                    # perché Over/Under sono sempre con .5
            
            results[f'Over {threshold}'] = prob_over
            results[f'Under {threshold}'] = prob_under
        
        return results
    
    def calculate_ht_probabilities(self, lambda_home: float, lambda_away: float) -> Dict[str, float]:
        """
        Calcola probabilità per mercati primo tempo (HT - Half Time).
        
        Utilizza il fatto che i gol nel primo tempo seguono una distribuzione
        con lambda ridotta (circa 45% del totale, basato su statistiche reali).
        
        Args:
            lambda_home: Attesa gol casa (per match completo)
            lambda_away: Attesa gol trasferta (per match completo)
            
        Returns:
            Dict con probabilità HT 1X2, Over/Under HT
        """
        # Fattore di riduzione per primo tempo (circa 45% dei gol avvengono nel primo tempo)
        ht_factor = 0.45
        lambda_home_ht = lambda_home * ht_factor
        lambda_away_ht = lambda_away * ht_factor
        
        # 1X2 HT
        ht_1x2 = self.calculate_1x2_probabilities(lambda_home_ht, lambda_away_ht)
        
        # Over/Under HT
        ht_over_under = self.calculate_over_under_probabilities(
            lambda_home_ht, lambda_away_ht, 
            thresholds=[0.5, 1.5, 2.5]
        )
        
        return {
            'HT_1': ht_1x2['1'],
            'HT_X': ht_1x2['X'],
            'HT_2': ht_1x2['2'],
            **ht_over_under
        }
    
    def calculate_exact_scores(self, lambda_home: float, lambda_away: float,
                              max_goals: int = 5) -> Dict[str, float]:
        """
        Calcola probabilità per risultati esatti più probabili.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            max_goals: Massimo numero di gol per squadra da considerare
            
        Returns:
            Dict con probabilità risultati esatti (es. "1-0", "2-1", etc.)
        """
        results = {}
        
        for home in range(max_goals + 1):
            for away in range(max_goals + 1):
                score = f"{home}-{away}"
                prob = self.exact_score_probability(home, away, lambda_home, lambda_away)
                results[score] = prob
        
        # Ordiniamo per probabilità decrescente
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_results
    
    def calculate_all_probabilities(self, spread_opening: float, total_opening: float,
                                   spread_current: float, total_current: float) -> Dict:
        """
        Calcola tutte le probabilità per apertura e corrente.
        
        Args:
            spread_opening: Spread apertura
            total_opening: Total apertura
            spread_current: Spread corrente
            total_current: Total corrente
            
        Returns:
            Dict completo con tutte le probabilità calcolate
        """
        # Calcolo attese gol per apertura
        lambda_home_opening, lambda_away_opening = self.spread_to_expected_goals(
            spread_opening, total_opening
        )
        
        # Calcolo attese gol per corrente
        lambda_home_current, lambda_away_current = self.spread_to_expected_goals(
            spread_current, total_current
        )
        
        # Calcolo probabilità apertura
        opening_probs = {
            '1X2': self.calculate_1x2_probabilities(lambda_home_opening, lambda_away_opening),
            'GG_NG': self.calculate_gg_ng_probabilities(lambda_home_opening, lambda_away_opening),
            'Over_Under': self.calculate_over_under_probabilities(lambda_home_opening, lambda_away_opening),
            'HT': self.calculate_ht_probabilities(lambda_home_opening, lambda_away_opening),
            'Exact_Scores': self.calculate_exact_scores(lambda_home_opening, lambda_away_opening),
            'Expected_Goals': {
                'Home': lambda_home_opening,
                'Away': lambda_away_opening
            }
        }
        
        # Calcolo probabilità corrente
        current_probs = {
            '1X2': self.calculate_1x2_probabilities(lambda_home_current, lambda_away_current),
            'GG_NG': self.calculate_gg_ng_probabilities(lambda_home_current, lambda_away_current),
            'Over_Under': self.calculate_over_under_probabilities(lambda_home_current, lambda_away_current),
            'HT': self.calculate_ht_probabilities(lambda_home_current, lambda_away_current),
            'Exact_Scores': self.calculate_exact_scores(lambda_home_current, lambda_away_current),
            'Expected_Goals': {
                'Home': lambda_home_current,
                'Away': lambda_away_current
            }
        }
        
        return {
            'Opening': opening_probs,
            'Current': current_probs,
            'Movement': {
                'Spread_Change': spread_current - spread_opening,
                'Total_Change': total_current - total_opening,
                'Home_EG_Change': lambda_home_current - lambda_home_opening,
                'Away_EG_Change': lambda_away_current - lambda_away_opening
            }
        }

