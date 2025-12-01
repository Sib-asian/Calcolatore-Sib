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
    Basato su Poisson bivariato, Dixon-Coles, e ottimizzazioni avanzate.
    """
    
    def __init__(self):
        # Parametri Dixon-Coles ottimizzati (basati su letteratura e dati reali)
        # rho varia tra 0.05-0.15, usiamo valore medio ottimizzato
        self.rho_base = 0.12  # Correlazione base tra gol casa e trasferta
        
        # Precisione calcoli
        self.max_goals_dynamic = True  # Limite gol dinamico
        self.use_log_space = True  # Usa log-space per precisione
        
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
        
        Aggiustamenti per precisione:
        - Smoothing per lambda molto basse (< 0.1) o molto alte (> 4.0)
        - Limiti realistici per evitare valori estremi
        
        Args:
            spread: Spread (negativo = casa favorita, positivo = trasferta favorita)
            total: Total atteso (somma gol attesi)
            
        Returns:
            Tuple[lambda_home, lambda_away]
        """
        lambda_home = (total - spread) / 2.0
        lambda_away = (total + spread) / 2.0
        
        # Smoothing per lambda molto basse (evita problemi numerici)
        lambda_home = max(0.05, lambda_home)
        lambda_away = max(0.05, lambda_away)
        
        # Limite superiore realistico (match molto offensivi raramente superano 4.5 gol attesi per squadra)
        lambda_home = min(4.5, lambda_home)
        lambda_away = min(4.5, lambda_away)
        
        return lambda_home, lambda_away
    
    def get_dynamic_rho(self, lambda_home: float, lambda_away: float) -> float:
        """
        Calcola rho dinamico per Dixon-Coles basato sulle attese gol.
        Rho è più alto per match a basso scoring (più correlazione 0-0, 1-1).
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Valore rho ottimizzato
        """
        avg_lambda = (lambda_home + lambda_away) / 2.0
        
        # Rho più alto per match a basso scoring
        if avg_lambda < 1.5:
            rho = 0.15  # Alta correlazione per match difensivi
        elif avg_lambda < 2.5:
            rho = 0.12  # Valore standard
        else:
            rho = 0.08  # Bassa correlazione per match offensivi
        
        return rho
    
    def get_dynamic_max_goals(self, lambda_home: float, lambda_away: float) -> int:
        """
        Calcola limite gol dinamico in base alle attese gol.
        Ottimizza performance mantenendo precisione > 99.9%.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Limite massimo gol da considerare
        """
        max_lambda = max(lambda_home, lambda_away)
        
        # Formula: copriamo almeno 99.9% della distribuzione
        # Per Poisson, P(X <= k) > 0.999 quando k >= lambda + 3*sqrt(lambda)
        if max_lambda < 1.0:
            return 8
        elif max_lambda < 2.0:
            return 10
        elif max_lambda < 3.0:
            return 12
        else:
            return 15
    
    def dixon_coles_adjustment(self, home_goals: int, away_goals: int, 
                               lambda_home: float, lambda_away: float) -> float:
        """
        Aggiustamento Dixon-Coles migliorato per correggere probabilità di 0-0 e 1-1.
        Questi risultati sono statisticamente più probabili del modello Poisson puro.
        
        Formula migliorata:
        tau(i, j, lambda_home, lambda_away) = 
            1 - lambda_home * lambda_away * rho se (i,j) = (0,0)
            1 + lambda_home * rho se (i,j) = (1,0)
            1 + lambda_away * rho se (i,j) = (0,1)
            1 - rho se (i,j) = (1,1)
            1 altrimenti
        
        Usa rho dinamico basato sulle attese gol per maggiore precisione.
            
        Args:
            home_goals: Gol casa
            away_goals: Gol trasferta
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Fattore di correzione tau
        """
        rho = self.get_dynamic_rho(lambda_home, lambda_away)
        
        if home_goals == 0 and away_goals == 0:
            tau = 1 - lambda_home * lambda_away * rho
        elif home_goals == 1 and away_goals == 0:
            tau = 1 + lambda_home * rho
        elif home_goals == 0 and away_goals == 1:
            tau = 1 + lambda_away * rho
        elif home_goals == 1 and away_goals == 1:
            tau = 1 - rho
        else:
            return 1.0
        
        # Assicuriamo che tau sia sempre positivo
        return max(0.01, tau)
    
    def poisson_probability(self, k: int, lambda_param: float) -> float:
        """
        Calcola probabilità Poisson: P(X = k) = (lambda^k * e^(-lambda)) / k!
        
        Versione ottimizzata con log-space per evitare underflow/overflow
        quando lambda è molto grande o molto piccola.
        
        Args:
            k: Numero di eventi
            lambda_param: Parametro lambda (media)
            
        Returns:
            Probabilità
        """
        if k < 0:
            return 0.0
        
        if self.use_log_space and (lambda_param > 3.0 or lambda_param < 0.3):
            # Usa log-space per precisione con lambda estreme
            log_prob = k * math.log(lambda_param) - lambda_param - sum(math.log(i) for i in range(1, k + 1) if i > 0)
            return math.exp(log_prob)
        else:
            # Calcolo diretto per lambda normali (più veloce)
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
        
        Versione ottimizzata con limite gol dinamico e normalizzazione robusta.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Dict con probabilità 1, X, 2 (normalizzate)
        """
        prob_1 = 0.0  # Casa vince
        prob_X = 0.0  # Pareggio
        prob_2 = 0.0  # Trasferta vince
        
        # Limite gol dinamico per ottimizzazione
        max_goals = self.get_dynamic_max_goals(lambda_home, lambda_away) if self.max_goals_dynamic else 10
        
        for home in range(max_goals + 1):
            for away in range(max_goals + 1):
                prob = self.exact_score_probability(home, away, lambda_home, lambda_away)
                
                if home > away:
                    prob_1 += prob
                elif home == away:
                    prob_X += prob
                else:
                    prob_2 += prob
        
        # Normalizzazione robusta (assicura che somma = 1.0)
        total = prob_1 + prob_X + prob_2
        if total > 0.0001:  # Evita divisione per zero
            prob_1 /= total
            prob_X /= total
            prob_2 /= total
        else:
            # Fallback se calcoli falliscono (molto raro)
            prob_1 = 0.33
            prob_X = 0.34
            prob_2 = 0.33
        
        return {
            '1': prob_1,
            'X': prob_X,
            '2': prob_2
        }
    
    def calculate_gg_ng_probabilities(self, lambda_home: float, lambda_away: float) -> Dict[str, float]:
        """
        Calcola probabilità GG (Goal-Goal, entrambe segnano) e NG (No Goal, almeno una non segna).
        
        Versione ottimizzata con limite gol dinamico e normalizzazione.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Dict con probabilità GG e NG (normalizzate)
        """
        prob_gg = 0.0  # Entrambe segnano
        prob_ng = 0.0  # Almeno una non segna
        
        max_goals = self.get_dynamic_max_goals(lambda_home, lambda_away) if self.max_goals_dynamic else 10
        
        for home in range(max_goals + 1):
            for away in range(max_goals + 1):
                prob = self.exact_score_probability(home, away, lambda_home, lambda_away)
                
                if home > 0 and away > 0:
                    prob_gg += prob
                else:
                    prob_ng += prob
        
        # Normalizzazione
        total = prob_gg + prob_ng
        if total > 0.0001:
            prob_gg /= total
            prob_ng /= total
        
        return {
            'GG': prob_gg,
            'NG': prob_ng
        }
    
    def calculate_over_under_probabilities(self, lambda_home: float, lambda_away: float,
                                          thresholds: List[float] = None) -> Dict[str, float]:
        """
        Calcola probabilità Over/Under per vari totali.
        
        Versione ottimizzata con limite gol dinamico e normalizzazione.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            thresholds: Lista di soglie (default: [0.5, 1.5, 2.5, 3.5, 4.5])
            
        Returns:
            Dict con probabilità Over/Under per ogni soglia (normalizzate)
        """
        if thresholds is None:
            thresholds = [0.5, 1.5, 2.5, 3.5, 4.5]
        
        results = {}
        max_goals = self.get_dynamic_max_goals(lambda_home, lambda_away) if self.max_goals_dynamic else 10
        
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
            
            # Normalizzazione per ogni soglia
            total = prob_over + prob_under
            if total > 0.0001:
                prob_over /= total
                prob_under /= total
            
            results[f'Over {threshold}'] = prob_over
            results[f'Under {threshold}'] = prob_under
        
        return results
    
    def get_dynamic_ht_factor(self, total_lambda: float) -> float:
        """
        Calcola fattore primo tempo dinamico basato sul total atteso.
        
        Statistiche reali mostrano che:
        - Match a basso scoring (< 2.0): ~42% gol nel primo tempo
        - Match normali (2.0-3.0): ~45% gol nel primo tempo  
        - Match ad alto scoring (> 3.0): ~48% gol nel primo tempo
        
        Args:
            total_lambda: Somma delle attese gol (lambda_home + lambda_away)
            
        Returns:
            Fattore di riduzione per primo tempo
        """
        if total_lambda < 2.0:
            return 0.42
        elif total_lambda < 3.0:
            return 0.45
        elif total_lambda < 4.0:
            return 0.47
        else:
            return 0.48
    
    def calculate_ht_probabilities(self, lambda_home: float, lambda_away: float) -> Dict[str, float]:
        """
        Calcola probabilità per mercati primo tempo (HT - Half Time).
        
        Utilizza fattore primo tempo dinamico basato sul total atteso.
        I gol nel primo tempo seguono una distribuzione con lambda ridotta.
        
        Args:
            lambda_home: Attesa gol casa (per match completo)
            lambda_away: Attesa gol trasferta (per match completo)
            
        Returns:
            Dict con probabilità HT 1X2, Over/Under HT
        """
        # Fattore primo tempo dinamico basato sul total
        total_lambda = lambda_home + lambda_away
        ht_factor = self.get_dynamic_ht_factor(total_lambda)
        
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
                              max_goals: int = None) -> Dict[str, float]:
        """
        Calcola probabilità per risultati esatti più probabili.
        
        Versione ottimizzata con limite dinamico per calcolo completo,
        ma mostra solo i risultati più probabili per leggibilità.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            max_goals: Massimo numero di gol per squadra da mostrare (None = usa limite dinamico)
            
        Returns:
            Dict con probabilità risultati esatti (es. "1-0", "2-1", etc.)
        """
        # Usa limite dinamico per calcolo completo (precisione)
        calc_max_goals = self.get_dynamic_max_goals(lambda_home, lambda_away) if self.max_goals_dynamic else 10
        
        # Limite per display (mostra solo i più probabili)
        display_max = max_goals if max_goals is not None else min(5, calc_max_goals)
        
        results = {}
        
        # Calcola tutti i risultati possibili per precisione
        for home in range(calc_max_goals + 1):
            for away in range(calc_max_goals + 1):
                score = f"{home}-{away}"
                prob = self.exact_score_probability(home, away, lambda_home, lambda_away)
                results[score] = prob
        
        # Ordiniamo per probabilità decrescente
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))
        
        # Se richiesto, mostra solo i top risultati
        if max_goals is not None:
            filtered_results = {}
            for home in range(display_max + 1):
                for away in range(display_max + 1):
                    score = f"{home}-{away}"
                    if score in sorted_results:
                        filtered_results[score] = sorted_results[score]
            return filtered_results
        
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

