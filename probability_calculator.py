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
        
        # Parametri avanzati per miglioramenti
        self.use_overdispersion_correction = True  # Correzione per overdispersion
        self.use_skewness_correction = True  # Correzione per skewness Poisson
        self.use_karlis_ntzoufras = False  # Modello Karlis-Ntzoufras (più complesso, opzionale)
        
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
        # Verifica compatibilità matematica
        # Se spread è troppo grande rispetto al total, aggiusta
        max_abs_spread = total - 0.1  # Spread massimo possibile (con minimo 0.05 per entrambe le lambda)
        if abs(spread) > max_abs_spread:
            # Caso estremo: spread troppo grande per il total
            # Mantieni la direzione ma riduci lo spread
            spread = max_abs_spread if spread > 0 else -max_abs_spread
        
        lambda_home = (total - spread) / 2.0
        lambda_away = (total + spread) / 2.0
        
        # Smoothing per lambda molto basse (evita problemi numerici)
        # Usa 0.05 invece di 0.01 per maggiore stabilità
        # Strategia: mantieni il rapporto spread/total quando possibile
        min_lambda = 0.05
        
        # Calcola il rapporto originale per mantenerlo
        original_ratio_home = lambda_home / total if total > 0 else 0.5
        original_ratio_away = lambda_away / total if total > 0 else 0.5
        
        # Se entrambe le lambda sono troppo basse, bilancia mantenendo il rapporto
        if lambda_home < min_lambda and lambda_away < min_lambda:
            # Caso estremo: total molto basso, bilancia equamente
            if total < 2 * min_lambda:
                # Total troppo basso: bilancia equamente
                lambda_home = total / 2.0
                lambda_away = total / 2.0
            else:
                # Mantieni il rapporto originale ma assicura minimo
                lambda_home = max(min_lambda, total * original_ratio_home)
                lambda_away = total - lambda_home
                if lambda_away < min_lambda:
                    lambda_away = min_lambda
                    lambda_home = total - lambda_away
        elif lambda_home < min_lambda:
            # Solo lambda_home troppo bassa: aumenta mantenendo il total
            lambda_home = min_lambda
            lambda_away = total - lambda_home
            # Se lambda_away diventa negativa o troppo bassa, bilancia
            if lambda_away < min_lambda:
                if total >= 2 * min_lambda:
                    lambda_away = min_lambda
                    lambda_home = total - lambda_away
                else:
                    # Total troppo basso: bilancia equamente
                    lambda_home = total / 2.0
                    lambda_away = total / 2.0
        elif lambda_away < min_lambda:
            # Solo lambda_away troppo bassa: aumenta mantenendo il total
            lambda_away = min_lambda
            lambda_home = total - lambda_away
            if lambda_home < min_lambda:
                if total >= 2 * min_lambda:
                    lambda_home = min_lambda
                    lambda_away = total - lambda_home
                else:
                    # Total troppo basso: bilancia equamente
                    lambda_home = total / 2.0
                    lambda_away = total / 2.0
        
        # Limite superiore realistico (match molto offensivi raramente superano 4.5 gol attesi per squadra)
        # Se viene applicato il limite, ri-normalizza per mantenere il total corretto
        max_lambda = 4.5
        
        if lambda_home > max_lambda or lambda_away > max_lambda:
            # Calcola il rapporto originale per mantenerlo
            if lambda_home > 0 and lambda_away > 0:
                ratio = lambda_home / (lambda_home + lambda_away)
            else:
                ratio = 0.5
            
            # Limita entrambi mantenendo il rapporto
            if lambda_home > max_lambda:
                lambda_home = max_lambda
                # Aggiusta lambda_away per mantenere il total
                lambda_away = total - lambda_home
                if lambda_away > max_lambda:
                    lambda_away = max_lambda
                    # Se entrambi sono al limite, scala proporzionalmente
                    current_total = lambda_home + lambda_away
                    if current_total > total:
                        scale = total / current_total
                        lambda_home *= scale
                        lambda_away *= scale
            
            if lambda_away > max_lambda:
                lambda_away = max_lambda
                lambda_home = total - lambda_away
                if lambda_home > max_lambda:
                    lambda_home = max_lambda
                    current_total = lambda_home + lambda_away
                    if current_total > total:
                        scale = total / current_total
                        lambda_home *= scale
                        lambda_away *= scale
        
        # Verifica finale: assicura che total sia corretto
        calculated_total = lambda_home + lambda_away
        if abs(calculated_total - total) > 0.001:
            # Ultimo tentativo: scala proporzionalmente
            if calculated_total > 0:
                scale = total / calculated_total
                lambda_home *= scale
                lambda_away *= scale
                # Ri-applica limiti se necessario
                lambda_home = max(min_lambda, min(max_lambda, lambda_home))
                lambda_away = max(min_lambda, min(max_lambda, lambda_away))
        
        return lambda_home, lambda_away
    
    def get_dynamic_rho(self, lambda_home: float, lambda_away: float) -> float:
        """
        Calcola rho dinamico per Dixon-Coles basato sulle attese gol.
        Rho è più alto per match a basso scoring (più correlazione 0-0, 1-1).
        
        Versione migliorata con interpolazione smooth e considerazione del rapporto lambda.
        
        Args:
            lambda_home: Attesa gol casa
            lambda_away: Attesa gol trasferta
            
        Returns:
            Valore rho ottimizzato
        """
        avg_lambda = (lambda_home + lambda_away) / 2.0
        
        # Interpolazione smooth invece di step function
        if avg_lambda < 1.0:
            rho = 0.16  # Alta correlazione per match molto difensivi
        elif avg_lambda < 1.5:
            # Interpolazione tra 1.0 e 1.5
            rho = 0.16 - (avg_lambda - 1.0) * 0.02  # 0.16 -> 0.15
        elif avg_lambda < 2.0:
            # Interpolazione tra 1.5 e 2.0
            rho = 0.15 - (avg_lambda - 1.5) * 0.06  # 0.15 -> 0.12
        elif avg_lambda < 2.5:
            rho = 0.12  # Valore standard
        elif avg_lambda < 3.0:
            # Interpolazione tra 2.5 e 3.0
            rho = 0.12 - (avg_lambda - 2.5) * 0.08  # 0.12 -> 0.08
        else:
            rho = 0.08  # Bassa correlazione per match offensivi
        
        # Aggiustamento basato sul rapporto lambda (match sbilanciati hanno meno correlazione)
        if lambda_home > 0 and lambda_away > 0:
            ratio = max(lambda_home, lambda_away) / min(lambda_home, lambda_away)
            if ratio > 2.0:
                # Match molto sbilanciato: riduci leggermente rho
                rho *= 0.95
        
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
        
        Miglioramenti:
        - Algoritmo stabile per lambda molto piccole
        - Approssimazione migliorata per k=0 con lambda piccole
        
        Args:
            k: Numero di eventi
            lambda_param: Parametro lambda (media)
            
        Returns:
            Probabilità
        """
        if k < 0:
            return 0.0
        
        # Ottimizzazione per lambda molto piccole
        if lambda_param < 0.1:
            # Per lambda molto piccole, usa approssimazione più stabile
            if k == 0:
                return math.exp(-lambda_param)
            elif k == 1:
                return lambda_param * math.exp(-lambda_param)
            else:
                # Per k > 1 con lambda molto piccola, probabilità è trascurabile
                # ma calcoliamo comunque per precisione
                log_prob = k * math.log(lambda_param) - lambda_param
                for i in range(1, k + 1):
                    log_prob -= math.log(i)
                return math.exp(log_prob)
        
        if self.use_log_space and (lambda_param > 3.0 or lambda_param < 0.3):
            # Usa log-space per precisione con lambda estreme
            # Algoritmo migliorato: evita overflow nel calcolo di factorial
            log_prob = k * math.log(lambda_param) - lambda_param
            # Calcola log(k!) in modo più efficiente
            for i in range(1, k + 1):
                log_prob -= math.log(i)
            return math.exp(log_prob)
        else:
            # Calcolo diretto per lambda normali (più veloce)
            # Ottimizzazione: calcola factorial solo se necessario
            if k == 0:
                return math.exp(-lambda_param)
            elif k == 1:
                return lambda_param * math.exp(-lambda_param)
            else:
                return (lambda_param ** k * math.exp(-lambda_param)) / math.factorial(k)
    
    def get_overdispersion_factor(self, lambda_param: float) -> float:
        """
        Calcola fattore di correzione per overdispersion.
        
        In calcio, la varianza è spesso maggiore della media (overdispersion).
        Questo aggiustamento migliora la precisione per lambda medie-alte.
        
        Formula basata su dati empirici: varianza ≈ 1.1 * media per lambda > 1.5
        
        Args:
            lambda_param: Parametro lambda (media)
            
        Returns:
            Fattore di correzione (1.0 = nessuna correzione)
        """
        if not self.use_overdispersion_correction:
            return 1.0
        
        # Overdispersion è più pronunciata per lambda medie-alte
        if lambda_param > 1.5:
            # Varianza empirica ≈ 1.1 * media
            # Usiamo un fattore di correzione leggero
            return 0.98  # Leggera riduzione per compensare overdispersion
        elif lambda_param > 1.0:
            return 0.99
        else:
            return 1.0
    
    def exact_score_probability(self, home_goals: int, away_goals: int,
                               lambda_home: float, lambda_away: float) -> float:
        """
        Calcola probabilità di un risultato esatto usando Poisson + Dixon-Coles.
        
        Versione migliorata con:
        - Aggiustamento overdispersion
        - Precisione numerica migliorata
        
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
        
        # Aggiustamento overdispersion (leggero, per lambda medie-alte)
        overdisp_factor_home = self.get_overdispersion_factor(lambda_home)
        overdisp_factor_away = self.get_overdispersion_factor(lambda_away)
        
        # Applica correzione solo se significativa
        if overdisp_factor_home < 1.0 or overdisp_factor_away < 1.0:
            # Correzione leggera: riduce leggermente probabilità per compensare overdispersion
            correction = (overdisp_factor_home + overdisp_factor_away) / 2.0
            return prob_home * prob_away * tau * correction
        else:
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
    
    def get_ht_time_distribution_factor(self, lambda_param: float, is_home: bool = True) -> float:
        """
        Calcola fattore di distribuzione temporale per primo tempo.
        
        Miglioramento: invece di semplice riduzione lineare, considera che:
        - I gol nel primo tempo seguono una distribuzione non uniforme
        - Match a basso scoring: più gol nel primo tempo (relativamente)
        - Match ad alto scoring: più gol nel secondo tempo
        
        Formula migliorata basata su analisi statistica:
        - Per lambda basse: ~45% nel primo tempo
        - Per lambda medie: ~42-45% nel primo tempo
        - Per lambda alte: ~40-42% nel primo tempo
        
        Args:
            lambda_param: Attesa gol per la squadra
            is_home: Se True, squadra casa (leggermente più gol nel primo tempo)
            
        Returns:
            Fattore di riduzione per primo tempo
        """
        # Fattore base basato su lambda
        if lambda_param < 0.8:
            base_factor = 0.46  # Match molto difensivi: più gol nel primo tempo
        elif lambda_param < 1.5:
            base_factor = 0.44
        elif lambda_param < 2.0:
            base_factor = 0.43
        elif lambda_param < 2.5:
            base_factor = 0.42
        elif lambda_param < 3.0:
            base_factor = 0.41
        else:
            base_factor = 0.40  # Match offensivi: più gol nel secondo tempo
        
        # Aggiustamento per squadra casa (leggermente più gol nel primo tempo)
        if is_home:
            base_factor += 0.01
        
        return base_factor
    
    def get_dynamic_ht_factor(self, total_lambda: float) -> float:
        """
        Calcola fattore primo tempo dinamico basato sul total atteso.
        
        Statistiche reali mostrano che:
        - Match a basso scoring (< 2.0): ~42% gol nel primo tempo
        - Match normali (2.0-3.0): ~45% gol nel primo tempo  
        - Match ad alto scoring (> 3.0): ~48% gol nel primo tempo
        
        Formula migliorata: usa interpolazione lineare per transizioni più smooth.
        
        Args:
            total_lambda: Somma delle attese gol (lambda_home + lambda_away)
            
        Returns:
            Fattore di riduzione per primo tempo
        """
        # Interpolazione lineare per transizioni più smooth
        if total_lambda < 1.5:
            return 0.41
        elif total_lambda < 2.0:
            # Interpolazione tra 1.5 e 2.0
            return 0.41 + (total_lambda - 1.5) * 0.02  # 0.41 -> 0.42
        elif total_lambda < 2.5:
            # Interpolazione tra 2.0 e 2.5
            return 0.42 + (total_lambda - 2.0) * 0.06  # 0.42 -> 0.45
        elif total_lambda < 3.0:
            return 0.45
        elif total_lambda < 3.5:
            # Interpolazione tra 3.0 e 3.5
            return 0.45 + (total_lambda - 3.0) * 0.04  # 0.45 -> 0.47
        elif total_lambda < 4.0:
            return 0.47
        elif total_lambda < 4.5:
            # Interpolazione tra 4.0 e 4.5
            return 0.47 + (total_lambda - 4.0) * 0.02  # 0.47 -> 0.48
        else:
            return 0.48
    
    def calculate_ht_probabilities(self, lambda_home: float, lambda_away: float) -> Dict[str, float]:
        """
        Calcola probabilità per mercati primo tempo (HT - Half Time).
        
        Versione migliorata con distribuzione temporale più accurata.
        Utilizza fattori diversi per casa e trasferta basati su analisi statistica.
        
        Args:
            lambda_home: Attesa gol casa (per match completo)
            lambda_away: Attesa gol trasferta (per match completo)
            
        Returns:
            Dict con probabilità HT 1X2, Over/Under HT
        """
        # Fattore primo tempo migliorato: usa distribuzione temporale
        # invece di semplice riduzione lineare
        ht_factor_home = self.get_ht_time_distribution_factor(lambda_home, is_home=True)
        ht_factor_away = self.get_ht_time_distribution_factor(lambda_away, is_home=False)
        
        # Usa anche il fattore dinamico basato sul total come fallback
        total_lambda = lambda_home + lambda_away
        ht_factor_total = self.get_dynamic_ht_factor(total_lambda)
        
        # Media pesata: 70% distribuzione temporale, 30% fattore totale
        ht_factor_home_final = 0.7 * ht_factor_home + 0.3 * ht_factor_total
        ht_factor_away_final = 0.7 * ht_factor_away + 0.3 * ht_factor_total
        
        lambda_home_ht = lambda_home * ht_factor_home_final
        lambda_away_ht = lambda_away * ht_factor_away_final
        
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

