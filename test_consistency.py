"""
Script di test per verificare coerenza e precisione dei calcoli
Verifica che spread/total siano abbinati correttamente ai mercati
"""

from probability_calculator import AdvancedProbabilityCalculator
import math

def test_spread_total_conversion():
    """Test conversione spread/total in attese gol"""
    calc = AdvancedProbabilityCalculator()
    
    print("=" * 60)
    print("TEST 1: Conversione Spread/Total -> Attese Gol")
    print("=" * 60)
    
    test_cases = [
        (-0.5, 2.5, "Casa leggermente favorita"),
        (-1.0, 2.5, "Casa favorita"),
        (-1.5, 2.5, "Casa molto favorita"),
        (0.0, 2.5, "Match equilibrato"),
        (0.5, 2.5, "Trasferta leggermente favorita"),
        (1.0, 2.5, "Trasferta favorita"),
        (-0.5, 1.5, "Casa favorita, match difensivo"),
        (-0.5, 3.5, "Casa favorita, match offensivo"),
    ]
    
    for spread, total, desc in test_cases:
        lambda_home, lambda_away = calc.spread_to_expected_goals(spread, total)
        
        # Verifica: lambda_home + lambda_away dovrebbe essere ~total
        actual_total = lambda_home + lambda_away
        total_diff = abs(actual_total - total)
        
        # Verifica: lambda_home - lambda_away dovrebbe essere ~-spread
        actual_spread = lambda_home - lambda_away
        spread_diff = abs(actual_spread - (-spread))
        
        # Verifica logica: se spread negativo, lambda_home > lambda_away
        if spread < 0:
            home_favored = lambda_home > lambda_away
        elif spread > 0:
            home_favored = lambda_home < lambda_away
        else:
            home_favored = abs(lambda_home - lambda_away) < 0.1
        
        status = "✓" if total_diff < 0.01 and spread_diff < 0.01 and home_favored else "✗"
        
        print(f"\n{status} {desc}")
        print(f"   Spread: {spread:+.2f}, Total: {total:.2f}")
        print(f"   Lambda Home: {lambda_home:.4f}, Lambda Away: {lambda_away:.4f}")
        print(f"   Total calcolato: {actual_total:.4f} (diff: {total_diff:.4f})")
        print(f"   Spread calcolato: {actual_spread:.4f} (diff: {spread_diff:.4f})")
        
        if total_diff >= 0.01 or spread_diff >= 0.01 or not home_favored:
            print(f"   ⚠️  PROBLEMA RILEVATO!")

def test_micro_changes():
    """Test che micro cambiamenti si riflettano correttamente"""
    calc = AdvancedProbabilityCalculator()
    
    print("\n" + "=" * 60)
    print("TEST 2: Sensibilità a Micro Cambiamenti")
    print("=" * 60)
    
    base_spread = -0.5
    base_total = 2.5
    
    lambda_home_base, lambda_away_base = calc.spread_to_expected_goals(base_spread, base_total)
    probs_base = calc.calculate_1x2_probabilities(lambda_home_base, lambda_away_base)
    
    print(f"\nBase: Spread={base_spread}, Total={base_total}")
    print(f"Probabilità base: 1={probs_base['1']:.4f}, X={probs_base['X']:.4f}, 2={probs_base['2']:.4f}")
    
    # Test cambiamenti spread
    print("\n--- Cambiamenti Spread ---")
    for delta_spread in [-0.25, -0.1, 0.1, 0.25]:
        new_spread = base_spread + delta_spread
        lambda_home, lambda_away = calc.spread_to_expected_goals(new_spread, base_total)
        probs = calc.calculate_1x2_probabilities(lambda_home, lambda_away)
        
        delta_1 = probs['1'] - probs_base['1']
        delta_X = probs['X'] - probs_base['X']
        delta_2 = probs['2'] - probs_base['2']
        
        print(f"\nSpread: {base_spread} -> {new_spread:+.2f} (Δ{delta_spread:+.2f})")
        print(f"  Δ1: {delta_1:+.4f}, ΔX: {delta_X:+.4f}, Δ2: {delta_2:+.4f}")
        
        # Verifica che il cambiamento sia sensato
        if delta_spread < 0:  # Spread più negativo = casa più favorita
            if delta_1 <= 0:
                print(f"  ⚠️  PROBLEMA: Casa dovrebbe essere più probabile!")
        else:  # Spread più positivo = trasferta più favorita
            if delta_2 <= 0:
                print(f"  ⚠️  PROBLEMA: Trasferta dovrebbe essere più probabile!")
    
    # Test cambiamenti total
    print("\n--- Cambiamenti Total ---")
    for delta_total in [-0.25, -0.1, 0.1, 0.25]:
        new_total = base_total + delta_total
        lambda_home, lambda_away = calc.spread_to_expected_goals(base_spread, new_total)
        probs = calc.calculate_1x2_probabilities(lambda_home, lambda_away)
        
        delta_1 = probs['1'] - probs_base['1']
        delta_X = probs['X'] - probs_base['X']
        delta_2 = probs['2'] - probs_base['2']
        
        print(f"\nTotal: {base_total} -> {new_total:.2f} (Δ{delta_total:+.2f})")
        print(f"  Δ1: {delta_1:+.4f}, ΔX: {delta_X:+.4f}, Δ2: {delta_2:+.4f}")
        
        # Verifica che il cambiamento sia sensato
        if delta_total > 0:  # Più gol attesi
            # Probabilità pareggio dovrebbe aumentare leggermente
            # Ma principalmente Over dovrebbe aumentare
            pass  # Verificheremo Over/Under separatamente

def test_market_consistency():
    """Test coerenza tra mercati"""
    calc = AdvancedProbabilityCalculator()
    
    print("\n" + "=" * 60)
    print("TEST 3: Coerenza tra Mercati")
    print("=" * 60)
    
    spread = -0.5
    total = 2.5
    
    lambda_home, lambda_away = calc.spread_to_expected_goals(spread, total)
    
    # Calcola tutti i mercati
    probs_1x2 = calc.calculate_1x2_probabilities(lambda_home, lambda_away)
    probs_gg_ng = calc.calculate_gg_ng_probabilities(lambda_home, lambda_away)
    probs_ou = calc.calculate_over_under_probabilities(lambda_home, lambda_away)
    probs_ht = calc.calculate_ht_probabilities(lambda_home, lambda_away)
    exact_scores = calc.calculate_exact_scores(lambda_home, lambda_away, max_goals=3)
    
    print(f"\nSpread: {spread}, Total: {total}")
    print(f"Lambda Home: {lambda_home:.4f}, Lambda Away: {lambda_away:.4f}")
    
    # Verifica 1X2 somma = 1
    sum_1x2 = probs_1x2['1'] + probs_1x2['X'] + probs_1x2['2']
    print(f"\n✓ 1X2 somma: {sum_1x2:.6f} (dovrebbe essere 1.0)")
    if abs(sum_1x2 - 1.0) > 0.001:
        print(f"  ⚠️  PROBLEMA: Somma non è 1.0!")
    
    # Verifica GG/NG somma = 1
    sum_gg_ng = probs_gg_ng['GG'] + probs_gg_ng['NG']
    print(f"✓ GG/NG somma: {sum_gg_ng:.6f} (dovrebbe essere 1.0)")
    if abs(sum_gg_ng - 1.0) > 0.001:
        print(f"  ⚠️  PROBLEMA: Somma non è 1.0!")
    
    # Verifica Over/Under somma = 1 per ogni soglia
    for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
        over_key = f'Over {threshold}'
        under_key = f'Under {threshold}'
        if over_key in probs_ou and under_key in probs_ou:
            sum_ou = probs_ou[over_key] + probs_ou[under_key]
            print(f"✓ Over/Under {threshold} somma: {sum_ou:.6f} (dovrebbe essere 1.0)")
            if abs(sum_ou - 1.0) > 0.001:
                print(f"  ⚠️  PROBLEMA: Somma non è 1.0!")
    
    # Verifica HT 1X2 somma = 1
    sum_ht_1x2 = probs_ht['HT_1'] + probs_ht['HT_X'] + probs_ht['HT_2']
    print(f"✓ HT 1X2 somma: {sum_ht_1x2:.6f} (dovrebbe essere 1.0)")
    if abs(sum_ht_1x2 - 1.0) > 0.001:
        print(f"  ⚠️  PROBLEMA: Somma non è 1.0!")
    
    # Verifica che risultati esatti sommino a ~1
    sum_exact = sum(exact_scores.values())
    print(f"✓ Risultati esatti (0-3) somma: {sum_exact:.6f} (dovrebbe essere ~1.0)")
    if abs(sum_exact - 1.0) > 0.1:
        print(f"  ⚠️  ATTENZIONE: Somma molto diversa da 1.0 (normale se max_goals limitato)")
    
    # Verifica logica: se casa favorita (spread negativo), prob 1 > prob 2
    if spread < 0:
        if probs_1x2['1'] <= probs_1x2['2']:
            print(f"\n⚠️  PROBLEMA LOGICO: Casa favorita ma prob 1 ({probs_1x2['1']:.4f}) <= prob 2 ({probs_1x2['2']:.4f})")
        else:
            print(f"\n✓ Logica corretta: Casa favorita, prob 1 ({probs_1x2['1']:.4f}) > prob 2 ({probs_1x2['2']:.4f})")

def test_edge_cases():
    """Test casi limite"""
    calc = AdvancedProbabilityCalculator()
    
    print("\n" + "=" * 60)
    print("TEST 4: Casi Limite")
    print("=" * 60)
    
    edge_cases = [
        (-2.0, 1.0, "Casa molto favorita, match difensivo"),
        (2.0, 1.0, "Trasferta molto favorita, match difensivo"),
        (-0.1, 4.5, "Match equilibrato, molto offensivo"),
        (0.0, 0.5, "Total molto basso"),
        (-1.0, 5.0, "Casa favorita, total molto alto"),
    ]
    
    for spread, total, desc in edge_cases:
        try:
            lambda_home, lambda_away = calc.spread_to_expected_goals(spread, total)
            probs = calc.calculate_1x2_probabilities(lambda_home, lambda_away)
            
            sum_probs = probs['1'] + probs['X'] + probs['2']
            
            status = "✓" if 0.99 <= sum_probs <= 1.01 else "✗"
            print(f"\n{status} {desc}")
            print(f"   Spread: {spread}, Total: {total}")
            print(f"   Lambda: Home={lambda_home:.4f}, Away={lambda_away:.4f}")
            print(f"   Somma prob: {sum_probs:.6f}")
            
            if not (0.99 <= sum_probs <= 1.01):
                print(f"   ⚠️  PROBLEMA: Somma probabilità non è ~1.0")
        except Exception as e:
            print(f"\n✗ {desc}: ERRORE - {e}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TEST DI COERENZA E PRECISIONE CALCOLATORE SIB")
    print("=" * 60)
    
    test_spread_total_conversion()
    test_micro_changes()
    test_market_consistency()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETATI")
    print("=" * 60)

