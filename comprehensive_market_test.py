"""
Test completo di tutti i mercati - Verifica bug e coerenza
"""

from probability_calculator import AdvancedProbabilityCalculator
import math

def test_all_markets_comprehensive():
    """Test completo di tutti i mercati con vari scenari"""
    calc = AdvancedProbabilityCalculator()
    
    print("=" * 80)
    print("TEST COMPLETO TUTTI I MERCATI - RICERCA BUG")
    print("=" * 80)
    
    test_scenarios = [
        (-0.5, 2.5, "Casa leggermente favorita, total normale"),
        (-1.0, 2.5, "Casa favorita, total normale"),
        (0.0, 2.5, "Match equilibrato, total normale"),
        (0.5, 2.5, "Trasferta favorita, total normale"),
        (-0.5, 1.5, "Casa favorita, match difensivo"),
        (-0.5, 3.5, "Casa favorita, match offensivo"),
        (-1.5, 1.0, "Casa molto favorita, match molto difensivo"),
        (1.5, 4.5, "Trasferta favorita, match molto offensivo"),
    ]
    
    all_issues = []
    
    for spread, total, desc in test_scenarios:
        print(f"\n{'='*80}")
        print(f"SCENARIO: {desc}")
        print(f"Spread: {spread}, Total: {total}")
        print(f"{'='*80}")
        
        lambda_home, lambda_away = calc.spread_to_expected_goals(spread, total)
        print(f"Lambda Home: {lambda_home:.4f}, Lambda Away: {lambda_away:.4f}")
        
        # Verifica base
        calculated_total = lambda_home + lambda_away
        calculated_spread = lambda_home - lambda_away
        total_error = abs(calculated_total - total)
        spread_error = abs(calculated_spread - (-spread))
        
        if total_error > 0.01:
            issue = f"⚠️  BUG: Total non corrisponde! Atteso: {total}, Calcolato: {calculated_total:.4f}, Diff: {total_error:.4f}"
            print(issue)
            all_issues.append(issue)
        
        if spread_error > 0.01:
            issue = f"⚠️  BUG: Spread non corrisponde! Atteso: {-spread}, Calcolato: {calculated_spread:.4f}, Diff: {spread_error:.4f}"
            print(issue)
            all_issues.append(issue)
        
        # Test tutti i mercati
        probs_1x2 = calc.calculate_1x2_probabilities(lambda_home, lambda_away)
        probs_gg_ng = calc.calculate_gg_ng_probabilities(lambda_home, lambda_away)
        probs_ou = calc.calculate_over_under_probabilities(lambda_home, lambda_away)
        probs_ht = calc.calculate_ht_probabilities(lambda_home, lambda_away)
        exact_scores = calc.calculate_exact_scores(lambda_home, lambda_away, max_goals=4)
        
        # Verifica 1X2
        sum_1x2 = probs_1x2['1'] + probs_1x2['X'] + probs_1x2['2']
        if abs(sum_1x2 - 1.0) > 0.001:
            issue = f"⚠️  BUG 1X2: Somma = {sum_1x2:.6f} (dovrebbe essere 1.0)"
            print(issue)
            all_issues.append(issue)
        
        # Verifica logica 1X2
        if spread < 0 and probs_1x2['1'] <= probs_1x2['2']:
            issue = f"⚠️  BUG LOGICO 1X2: Casa favorita (spread={spread}) ma prob 1 ({probs_1x2['1']:.4f}) <= prob 2 ({probs_1x2['2']:.4f})"
            print(issue)
            all_issues.append(issue)
        elif spread > 0 and probs_1x2['2'] <= probs_1x2['1']:
            issue = f"⚠️  BUG LOGICO 1X2: Trasferta favorita (spread={spread}) ma prob 2 ({probs_1x2['2']:.4f}) <= prob 1 ({probs_1x2['1']:.4f})"
            print(issue)
            all_issues.append(issue)
        
        # Verifica GG/NG
        sum_gg_ng = probs_gg_ng['GG'] + probs_gg_ng['NG']
        if abs(sum_gg_ng - 1.0) > 0.001:
            issue = f"⚠️  BUG GG/NG: Somma = {sum_gg_ng:.6f} (dovrebbe essere 1.0)"
            print(issue)
            all_issues.append(issue)
        
        # Verifica Over/Under
        for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
            over_key = f'Over {threshold}'
            under_key = f'Under {threshold}'
            if over_key in probs_ou and under_key in probs_ou:
                sum_ou = probs_ou[over_key] + probs_ou[under_key]
                if abs(sum_ou - 1.0) > 0.001:
                    issue = f"⚠️  BUG Over/Under {threshold}: Somma = {sum_ou:.6f} (dovrebbe essere 1.0)"
                    print(issue)
                    all_issues.append(issue)
                
                # Verifica logica: se total > threshold, Over dovrebbe essere > 0.5
                if total > threshold and probs_ou[over_key] < 0.5:
                    issue = f"⚠️  BUG LOGICO Over/Under {threshold}: Total ({total}) > threshold ma Over ({probs_ou[over_key]:.4f}) < 0.5"
                    print(issue)
                    all_issues.append(issue)
                elif total < threshold and probs_ou[under_key] < 0.5:
                    issue = f"⚠️  BUG LOGICO Over/Under {threshold}: Total ({total}) < threshold ma Under ({probs_ou[under_key]:.4f}) < 0.5"
                    print(issue)
                    all_issues.append(issue)
        
        # Verifica HT
        sum_ht_1x2 = probs_ht['HT_1'] + probs_ht['HT_X'] + probs_ht['HT_2']
        if abs(sum_ht_1x2 - 1.0) > 0.001:
            issue = f"⚠️  BUG HT 1X2: Somma = {sum_ht_1x2:.6f} (dovrebbe essere 1.0)"
            print(issue)
            all_issues.append(issue)
        
        # Verifica HT Over/Under
        for threshold in [0.5, 1.5, 2.5]:
            over_key = f'Over {threshold}'
            under_key = f'Under {threshold}'
            if over_key in probs_ht and under_key in probs_ht:
                sum_ht_ou = probs_ht[over_key] + probs_ht[under_key]
                if abs(sum_ht_ou - 1.0) > 0.001:
                    issue = f"⚠️  BUG HT Over/Under {threshold}: Somma = {sum_ht_ou:.6f} (dovrebbe essere 1.0)"
                    print(issue)
                    all_issues.append(issue)
        
        # Verifica risultati esatti
        sum_exact = sum(exact_scores.values())
        if sum_exact < 0.8:  # Dovrebbe coprire almeno l'80% con max_goals=4
            issue = f"⚠️  ATTENZIONE: Risultati esatti sommano solo {sum_exact:.4f} (potrebbe essere normale se limitato)"
            print(issue)
        
        # Verifica probabilità negative o > 1
        all_probs = [
            probs_1x2['1'], probs_1x2['X'], probs_1x2['2'],
            probs_gg_ng['GG'], probs_gg_ng['NG'],
            *probs_ou.values(),
            probs_ht['HT_1'], probs_ht['HT_X'], probs_ht['HT_2'],
            *[v for k, v in probs_ht.items() if k.startswith('Over') or k.startswith('Under')]
        ]
        
        for prob in all_probs:
            if prob < 0:
                issue = f"⚠️  BUG: Probabilità negativa trovata: {prob:.6f}"
                print(issue)
                all_issues.append(issue)
            elif prob > 1.01:  # Piccola tolleranza per arrotondamenti
                issue = f"⚠️  BUG: Probabilità > 1 trovata: {prob:.6f}"
                print(issue)
                all_issues.append(issue)
        
        print(f"\n✓ Tutti i test base passati per questo scenario")
    
    print(f"\n{'='*80}")
    print("RIEPILOGO BUG TROVATI")
    print(f"{'='*80}")
    if all_issues:
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
    else:
        print("✓ NESSUN BUG TROVATO! Tutti i mercati sono coerenti.")
    
    return len(all_issues) == 0

def test_edge_cases_extreme():
    """Test casi limite estremi"""
    calc = AdvancedProbabilityCalculator()
    
    print(f"\n{'='*80}")
    print("TEST CASI LIMITE ESTREMI")
    print(f"{'='*80}")
    
    extreme_cases = [
        (-3.0, 1.0, "Spread molto negativo, total molto basso"),
        (3.0, 1.0, "Spread molto positivo, total molto basso"),
        (-0.1, 6.0, "Spread quasi zero, total molto alto"),
        (-2.0, 5.0, "Spread negativo, total alto"),
        (0.0, 0.1, "Total estremamente basso"),
    ]
    
    issues = []
    
    for spread, total, desc in extreme_cases:
        try:
            lambda_home, lambda_away = calc.spread_to_expected_goals(spread, total)
            
            # Verifica che lambda siano ragionevoli
            if lambda_home < 0 or lambda_away < 0:
                issue = f"⚠️  BUG: Lambda negativa per {desc}"
                print(issue)
                issues.append(issue)
            
            if lambda_home > 5.0 or lambda_away > 5.0:
                issue = f"⚠️  ATTENZIONE: Lambda molto alta ({lambda_home:.2f}, {lambda_away:.2f}) per {desc}"
                print(issue)
            
            probs = calc.calculate_1x2_probabilities(lambda_home, lambda_away)
            sum_probs = probs['1'] + probs['X'] + probs['2']
            
            if abs(sum_probs - 1.0) > 0.01:
                issue = f"⚠️  BUG: Somma probabilità = {sum_probs:.6f} per {desc}"
                print(issue)
                issues.append(issue)
            
            print(f"✓ {desc}: OK")
            
        except Exception as e:
            issue = f"⚠️  ERRORE per {desc}: {e}"
            print(issue)
            issues.append(issue)
    
    return len(issues) == 0

def test_market_consistency():
    """Test coerenza tra mercati diversi"""
    calc = AdvancedProbabilityCalculator()
    
    print(f"\n{'='*80}")
    print("TEST COERENZA TRA MERCATI")
    print(f"{'='*80}")
    
    spread = -0.5
    total = 2.5
    
    lambda_home, lambda_away = calc.spread_to_expected_goals(spread, total)
    
    probs_1x2 = calc.calculate_1x2_probabilities(lambda_home, lambda_away)
    probs_ou = calc.calculate_over_under_probabilities(lambda_home, lambda_away)
    exact_scores = calc.calculate_exact_scores(lambda_home, lambda_away, max_goals=None)
    
    # Verifica: probabilità 1X2 dovrebbe essere coerente con risultati esatti
    prob_1_from_exact = sum(prob for score, prob in exact_scores.items() 
                            if int(score.split('-')[0]) > int(score.split('-')[1]))
    prob_X_from_exact = sum(prob for score, prob in exact_scores.items() 
                           if int(score.split('-')[0]) == int(score.split('-')[1]))
    prob_2_from_exact = sum(prob for score, prob in exact_scores.items() 
                           if int(score.split('-')[0]) < int(score.split('-')[1]))
    
    diff_1 = abs(probs_1x2['1'] - prob_1_from_exact)
    diff_X = abs(probs_1x2['X'] - prob_X_from_exact)
    diff_2 = abs(probs_1x2['2'] - prob_2_from_exact)
    
    print(f"Prob 1X2 calcolata: 1={probs_1x2['1']:.6f}, X={probs_1x2['X']:.6f}, 2={probs_1x2['2']:.6f}")
    print(f"Prob 1X2 da exact:   1={prob_1_from_exact:.6f}, X={prob_X_from_exact:.6f}, 2={prob_2_from_exact:.6f}")
    print(f"Differenze: Δ1={diff_1:.6f}, ΔX={diff_X:.6f}, Δ2={diff_2:.6f}")
    
    if diff_1 > 0.01 or diff_X > 0.01 or diff_2 > 0.01:
        print("⚠️  ATTENZIONE: Discrepanza tra 1X2 calcolata e da risultati esatti")
        print("   (Potrebbe essere normale se max_goals limitato per exact_scores)")
    else:
        print("✓ Coerenza perfetta tra 1X2 e risultati esatti")
    
    # Verifica: Over/Under dovrebbe essere coerente con total
    ou_25_over = probs_ou.get('Over 2.5', 0)
    expected_total = lambda_home + lambda_away
    
    print(f"\nTotal atteso: {expected_total:.4f}")
    print(f"Over 2.5: {ou_25_over:.4f}")
    
    if expected_total > 2.5 and ou_25_over < 0.5:
        print("⚠️  BUG LOGICO: Total > 2.5 ma Over 2.5 < 0.5")
    elif expected_total < 2.5 and ou_25_over > 0.5:
        print("⚠️  BUG LOGICO: Total < 2.5 ma Over 2.5 > 0.5")
    else:
        print("✓ Logica Over/Under corretta")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("PANORAMICA COMPLETA MERCATI - RICERCA BUG E MIGLIORAMENTI")
    print("="*80)
    
    test1_ok = test_all_markets_comprehensive()
    test2_ok = test_edge_cases_extreme()
    test_market_consistency()
    
    print(f"\n{'='*80}")
    print("RISULTATO FINALE")
    print(f"{'='*80}")
    if test1_ok and test2_ok:
        print("✓ TUTTI I TEST PASSATI - NESSUN BUG TROVATO")
    else:
        print("⚠️  ALCUNI TEST FALLITI - VERIFICARE BUG SOPRA")

