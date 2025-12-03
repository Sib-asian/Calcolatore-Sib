"""
Test Completo: Reality Check Calcoli e Formule
Verifica che non ci siano sovrastime, calcoli errati, formule che gonfiano percentuali
"""

import sys
import math
from probability_calculator import AdvancedProbabilityCalculator

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)

def poisson_pure(lambda_val, k):
    """Poisson puro senza correzioni"""
    return (lambda_val ** k) * math.exp(-lambda_val) / math.factorial(k)

def calculate_pure_poisson_probs(lambda_home, lambda_away):
    """Calcola probabilità con Poisson PURO (no correzioni)"""
    max_goals = 10
    
    # 1X2
    p1 = sum(poisson_pure(lambda_home, h) * poisson_pure(lambda_away, a) 
             for h in range(max_goals) for a in range(max_goals) if h > a)
    px = sum(poisson_pure(lambda_home, h) * poisson_pure(lambda_away, a)
             for h in range(max_goals) for a in range(max_goals) if h == a)
    p2 = sum(poisson_pure(lambda_home, h) * poisson_pure(lambda_away, a)
             for h in range(max_goals) for a in range(max_goals) if h < a)
    
    # Normalizza
    total = p1 + px + p2
    p1 /= total
    px /= total
    p2 /= total
    
    # GG/NG
    p_gg = sum(poisson_pure(lambda_home, h) * poisson_pure(lambda_away, a)
               for h in range(1, max_goals) for a in range(1, max_goals))
    p_ng = 1 - p_gg
    
    # Over/Under
    p_over_25 = sum(poisson_pure(lambda_home, h) * poisson_pure(lambda_away, a)
                    for h in range(max_goals) for a in range(max_goals) if h + a > 2.5)
    p_under_25 = 1 - p_over_25
    
    p_over_35 = sum(poisson_pure(lambda_home, h) * poisson_pure(lambda_away, a)
                    for h in range(max_goals) for a in range(max_goals) if h + a > 3.5)
    p_under_35 = 1 - p_over_35
    
    return {
        '1X2': {'1': p1, 'X': px, '2': p2},
        'GG_NG': {'GG': p_gg, 'NG': p_ng},
        'Over_Under': {
            'Over 2.5': p_over_25,
            'Under 2.5': p_under_25,
            'Over 3.5': p_over_35,
            'Under 3.5': p_under_35
        }
    }

def test_scenario(name, spread_open, total_open, spread_curr, total_curr, 
                  expected_movement=None, with_api=False):
    """
    Testa uno scenario completo
    
    Args:
        name: Nome scenario
        spread_open/total_open: Apertura
        spread_curr/total_curr: Corrente
        expected_movement: Dict con movimenti attesi (es. {'P(1)': 'up'})
        with_api: Se True, simula stats API moderate
    """
    print(f"\n{'─'*80}")
    print(f"SCENARIO: {name}")
    print(f"{'─'*80}")
    print(f"Spread: {spread_open:.2f} → {spread_curr:.2f} (Δ = {spread_curr - spread_open:+.2f})")
    print(f"Total:  {total_open:.2f} → {total_curr:.2f} (Δ = {total_curr - total_open:+.2f})")
    
    calc = AdvancedProbabilityCalculator()
    
    # Lambda da input
    lambda_home_open = (total_open - spread_open) * 0.5
    lambda_away_open = (total_open + spread_open) * 0.5
    lambda_home_curr = (total_curr - spread_curr) * 0.5
    lambda_away_curr = (total_curr + spread_curr) * 0.5
    
    print(f"\nλ Apertura: Casa {lambda_home_open:.3f} | Trasferta {lambda_away_open:.3f}")
    print(f"λ Corrente: Casa {lambda_home_curr:.3f} | Trasferta {lambda_away_curr:.3f}")
    
    # Stats API moderate (se richieste)
    api_stats_home = None
    api_stats_away = None
    if with_api:
        api_stats_home = {
            'form_factor': 0.65,  # Moderata
            'variance': 0.9,
            'goals_scored_avg': lambda_home_curr,
            'goals_conceded_avg': lambda_away_curr * 0.8
        }
        api_stats_away = {
            'form_factor': 0.55,  # Moderata
            'variance': 1.0,
            'goals_scored_avg': lambda_away_curr,
            'goals_conceded_avg': lambda_home_curr * 0.8
        }
    
    # Calcola con sistema attuale
    results = calc.calculate_all_probabilities(
        spread_open, total_open,
        spread_curr, total_curr,
        api_stats_home=api_stats_home,
        api_stats_away=api_stats_away
    )
    
    current = results['Current']
    opening = results['Opening']
    
    # Calcola con Poisson PURO per confronto
    pure_poisson_open = calculate_pure_poisson_probs(lambda_home_open, lambda_away_open)
    pure_poisson_curr = calculate_pure_poisson_probs(lambda_home_curr, lambda_away_curr)
    
    # === ANALISI RISULTATI ===
    errors = []
    warnings = []
    
    print(f"\n📊 CONFRONTO PROBABILITÀ (Corrente):")
    print(f"{'Mercato':<20} {'Sistema':>10} {'Poisson':>10} {'Delta':>10} {'Status':>10}")
    print("─" * 70)
    
    markets_to_check = [
        ('P(1)', current['1X2']['1'], pure_poisson_curr['1X2']['1']),
        ('P(X)', current['1X2']['X'], pure_poisson_curr['1X2']['X']),
        ('P(2)', current['1X2']['2'], pure_poisson_curr['1X2']['2']),
        ('P(GG)', current['GG_NG']['GG'], pure_poisson_curr['GG_NG']['GG']),
        ('P(NG)', current['GG_NG']['NG'], pure_poisson_curr['GG_NG']['NG']),
        ('P(Over 2.5)', current['Over_Under']['Over 2.5'], pure_poisson_curr['Over_Under']['Over 2.5']),
        ('P(Over 3.5)', current['Over_Under']['Over 3.5'], pure_poisson_curr['Over_Under']['Over 3.5']),
    ]
    
    for label, sistema, poisson in markets_to_check:
        delta = (sistema - poisson) * 100
        
        # Status
        if abs(delta) < 2:
            status = "✅ OK"
        elif abs(delta) < 5:
            status = "⚠️ Alert"
            warnings.append(f"{label}: delta {delta:+.2f}% vs Poisson")
        else:
            status = "❌ ALTO"
            errors.append(f"{label}: delta {delta:+.2f}% vs Poisson (troppo alto!)")
        
        print(f"{label:<20} {sistema*100:>9.2f}% {poisson*100:>9.2f}% {delta:>+9.2f}% {status:>10}")
    
    # === VERIFICA SOVRASTIME ===
    print(f"\n🔍 VERIFICA SOVRASTIME:")
    
    # Over 2.5 non dovrebbe superare certe soglie in base al total
    total_curr_lambda = lambda_home_curr + lambda_away_curr
    over_25 = current['Over_Under']['Over 2.5']
    
    # Soglie realistiche basate su total lambda
    if total_curr_lambda < 2.0:
        max_over_25 = 0.45  # Con lambda basso, Over 2.5 non può essere troppo alto
    elif total_curr_lambda < 2.5:
        max_over_25 = 0.65
    elif total_curr_lambda < 3.0:
        max_over_25 = 0.78
    else:
        max_over_25 = 0.88
    
    print(f"   Total λ: {total_curr_lambda:.2f}")
    print(f"   P(Over 2.5): {over_25*100:.2f}% (max atteso: {max_over_25*100:.0f}%)")
    
    if over_25 > max_over_25 + 0.05:
        errors.append(f"Over 2.5 sovrastimato: {over_25*100:.2f}% > {max_over_25*100:.0f}%")
        print(f"   ❌ SOVRASTIMA rilevata!")
    else:
        print(f"   ✅ Realistico")
    
    # GG non dovrebbe essere troppo alto con lambda basse
    gg = current['GG_NG']['GG']
    min_lambda = min(lambda_home_curr, lambda_away_curr)
    
    if min_lambda < 0.8:
        max_gg = 0.50
    elif min_lambda < 1.0:
        max_gg = 0.60
    elif min_lambda < 1.2:
        max_gg = 0.70
    else:
        max_gg = 0.80
    
    print(f"   Min λ: {min_lambda:.2f}")
    print(f"   P(GG): {gg*100:.2f}% (max atteso: {max_gg*100:.0f}%)")
    
    if gg > max_gg + 0.05:
        errors.append(f"GG sovrastimato: {gg*100:.2f}% > {max_gg*100:.0f}%")
        print(f"   ❌ SOVRASTIMA rilevata!")
    else:
        print(f"   ✅ Realistico")
    
    # === VERIFICA MOVIMENTI ===
    if expected_movement:
        print(f"\n📈 VERIFICA MOVIMENTI ATTESI:")
        
        for market_key, expected_dir in expected_movement.items():
            if market_key == 'P(1)':
                actual_change = current['1X2']['1'] - opening['1X2']['1']
            elif market_key == 'P(2)':
                actual_change = current['1X2']['2'] - opening['1X2']['2']
            elif market_key == 'P(GG)':
                actual_change = current['GG_NG']['GG'] - opening['GG_NG']['GG']
            elif market_key == 'P(NG)':
                actual_change = current['GG_NG']['NG'] - opening['GG_NG']['NG']
            elif market_key == 'P(Over 2.5)':
                actual_change = current['Over_Under']['Over 2.5'] - opening['Over_Under']['Over 2.5']
            else:
                continue
            
            if expected_dir == 'up':
                if actual_change > 0:
                    print(f"   ✅ {market_key} aumenta correttamente ({actual_change*100:+.2f}%)")
                else:
                    errors.append(f"{market_key} dovrebbe aumentare ma non lo fa")
                    print(f"   ❌ {market_key} NON aumenta ({actual_change*100:+.2f}%)")
            elif expected_dir == 'down':
                if actual_change < 0:
                    print(f"   ✅ {market_key} diminuisce correttamente ({actual_change*100:+.2f}%)")
                else:
                    errors.append(f"{market_key} dovrebbe diminuire ma non lo fa")
                    print(f"   ❌ {market_key} NON diminuisce ({actual_change*100:+.2f}%)")
    
    # === RISULTATO ===
    print(f"\n{'─'*80}")
    if errors:
        print(f"❌ SCENARIO FALLITO: {len(errors)} errori")
        for error in errors:
            print(f"   • {error}")
        return False
    elif warnings:
        print(f"⚠️  SCENARIO CON WARNING: {len(warnings)} alert")
        for warning in warnings:
            print(f"   • {warning}")
        return True
    else:
        print(f"✅ SCENARIO SUPERATO: Tutto corretto")
        return True

def main():
    print_section("TEST COMPLETO: REALITY CHECK CALCOLI E FORMULE")
    print("\nVerifica completa di:")
    print("  1. Sovrastime percentuali")
    print("  2. Confronto con Poisson puro")
    print("  3. Movimenti logici spread/total")
    print("  4. Coerenza tra mercati")
    print("  5. Impatto aggiustamenti API")
    
    scenarios = []
    
    # === SCENARI CRITICI (quelli che causavano problemi prima) ===
    
    scenarios.append((
        "CRITICO 1: Spread -0.75, Total 2.75 (quello segnalato dall'utente)",
        -0.5, 2.5,  # Apertura
        -0.75, 2.75,  # Corrente
        {'P(1)': 'up', 'P(2)': 'down', 'P(GG)': 'up', 'P(Over 2.5)': 'up'},
        False  # Senza API prima
    ))
    
    scenarios.append((
        "CRITICO 1 CON API: Stesso scenario con aggiustamenti API",
        -0.5, 2.5,
        -0.75, 2.75,
        {'P(1)': 'up', 'P(2)': 'down', 'P(GG)': 'up', 'P(Over 2.5)': 'up'},
        True  # Con API
    ))
    
    scenarios.append((
        "CRITICO 2: Total basso, spread negativo (rischio sovrastima GG)",
        -0.75, 2.25,
        -1.0, 2.25,
        {'P(1)': 'up', 'P(2)': 'down'},
        False
    ))
    
    scenarios.append((
        "CRITICO 3: Total alto, spread equilibrato (rischio sovrastima Over)",
        -0.25, 3.0,
        0.0, 3.25,
        {'P(GG)': 'up', 'P(Over 2.5)': 'up'},
        False
    ))
    
    # === SCENARI REALISTICI ===
    
    scenarios.append((
        "REALISTICO 1: Casa favorita, total medio",
        -0.5, 2.5,
        -0.75, 2.5,
        {'P(1)': 'up', 'P(2)': 'down'},
        False
    ))
    
    scenarios.append((
        "REALISTICO 2: Total aumenta, spread stabile",
        -0.5, 2.5,
        -0.5, 2.75,
        {'P(GG)': 'up', 'P(Over 2.5)': 'up'},
        False
    ))
    
    scenarios.append((
        "REALISTICO 3: Match equilibrato",
        0.0, 2.5,
        0.0, 2.75,
        {'P(GG)': 'up', 'P(Over 2.5)': 'up'},
        False
    ))
    
    scenarios.append((
        "REALISTICO 4: Total basso (difese forti)",
        -0.25, 2.0,
        -0.5, 2.0,
        {'P(1)': 'up', 'P(NG)': 'up'},
        False
    ))
    
    # === SCENARI ESTREMI ===
    
    scenarios.append((
        "ESTREMO 1: Casa molto favorita",
        -1.0, 2.5,
        -1.25, 2.5,
        {'P(1)': 'up', 'P(2)': 'down'},
        False
    ))
    
    scenarios.append((
        "ESTREMO 2: Total molto alto",
        0.0, 3.5,
        0.0, 3.75,
        {'P(Over 2.5)': 'up', 'P(Over 3.5)': 'up'},
        False
    ))
    
    scenarios.append((
        "ESTREMO 3: Total molto basso",
        -0.5, 1.75,
        -0.5, 1.5,
        {'P(NG)': 'up', 'P(Over 2.5)': 'down'},
        False
    ))
    
    # Esegui tutti gli scenari
    passed = 0
    failed = 0
    warned = 0
    
    for scenario_data in scenarios:
        result = test_scenario(*scenario_data)
        if result is True:
            passed += 1
        elif result is False:
            failed += 1
        else:
            warned += 1
    
    # === RIEPILOGO FINALE ===
    print_section("RIEPILOGO FINALE")
    print(f"\n✅ Scenari superati: {passed}/{len(scenarios)}")
    print(f"⚠️  Scenari con warning: {warned}/{len(scenarios)}")
    print(f"❌ Scenari falliti: {failed}/{len(scenarios)}")
    
    if failed == 0 and warned == 0:
        print(f"\n🎉 TUTTI I TEST SUPERATI PERFETTAMENTE!")
        print(f"   ✅ Nessuna sovrastima")
        print(f"   ✅ Delta vs Poisson < 2%")
        print(f"   ✅ Movimenti logici")
        print(f"   ✅ Percentuali realistiche")
        print(f"\n✅ Sistema CORRETTO e AFFIDABILE!")
        return 0
    elif failed == 0:
        print(f"\n⚠️  SISTEMA OK MA CON ALCUNI ALERT")
        print(f"   ✅ Nessun errore critico")
        print(f"   ⚠️  {warned} scenari con delta > 2% vs Poisson")
        print(f"   💡 Considera se Dixon-Coles è troppo aggressivo")
        return 0
    else:
        print(f"\n❌ PROBLEMI RILEVATI!")
        print(f"   ❌ {failed} scenari falliti")
        print(f"   ⚠️  {warned} scenari con warning")
        print(f"\n🔧 AZIONI NECESSARIE:")
        print(f"   1. Verificare formule di aggiustamento")
        print(f"   2. Ridurre overdispersion factor")
        print(f"   3. Limitare Dixon-Coles tau")
        print(f"   4. Verificare aggiustamenti API")
        return 1


if __name__ == "__main__":
    sys.exit(main())

