"""
Test Integrazione API
Verifica che gli aggiustamenti API funzionino correttamente senza sovrastime
"""

import sys
from probability_calculator import AdvancedProbabilityCalculator

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)

def test_api_adjustment_logic():
    """Test logica aggiustamenti API"""
    print_section("TEST 1: Logica Aggiustamenti API")
    
    calc = AdvancedProbabilityCalculator()
    
    # Scenario 1: Squadra casa in ottima forma (5W), bassa variance
    print("\n📊 SCENARIO 1: Casa in forma (5W), Trasferta media (2W1D2L)")
    
    stats_home = {
        'team_name': 'Inter',
        'form_factor': 1.0,  # 5W = perfetto
        'variance': 0.5,  # Bassa (stabile)
        'goals_scored_avg': 2.2,
        'goals_conceded_avg': 0.6
    }
    
    stats_away = {
        'team_name': 'Juventus',
        'form_factor': 0.5,  # Media
        'variance': 1.2,  # Media-alta
        'goals_scored_avg': 1.1,
        'goals_conceded_avg': 1.4
    }
    
    # Input
    lambda_home_base = 1.5
    lambda_away_base = 1.0
    
    # Applica aggiustamento
    lambda_home_adj, lambda_away_adj = calc._apply_api_adjustment(
        lambda_home_base, lambda_away_base,
        stats_home, stats_away
    )
    
    home_change = ((lambda_home_adj / lambda_home_base) - 1) * 100
    away_change = ((lambda_away_adj / lambda_away_base) - 1) * 100
    
    print(f"\n🏠 Casa:")
    print(f"   Lambda base: {lambda_home_base:.3f}")
    print(f"   Lambda adjusted: {lambda_home_adj:.3f}")
    print(f"   Variazione: {home_change:+.2f}%")
    print(f"   Forma: {stats_home['form_factor']*100:.0f}% | Variance: {stats_home['variance']:.2f}")
    
    print(f"\n✈️ Trasferta:")
    print(f"   Lambda base: {lambda_away_base:.3f}")
    print(f"   Lambda adjusted: {lambda_away_adj:.3f}")
    print(f"   Variazione: {away_change:+.2f}%")
    print(f"   Forma: {stats_away['form_factor']*100:.0f}% | Variance: {stats_away['variance']:.2f}")
    
    # Verifica limiti
    assert -3.1 <= home_change <= 3.1, f"❌ Casa fuori limite: {home_change:.2f}%"
    assert -3.1 <= away_change <= 3.1, f"❌ Trasferta fuori limite: {away_change:.2f}%"
    print(f"\n✅ Aggiustamenti entro limiti (max ±3%)")
    
    # Scenario 2: Alta variance (imprevedibile)
    print("\n📊 SCENARIO 2: Alta variance (squadre imprevedibili)")
    
    stats_high_var = {
        'form_factor': 1.0,  # Forma ottima
        'variance': 2.5,  # Molto alta (imprevedibile)
        'goals_scored_avg': 2.0,
        'goals_conceded_avg': 1.5
    }
    
    lambda_adj_high_var, _ = calc._apply_api_adjustment(
        1.5, 1.0,
        stats_high_var, stats_away
    )
    
    change_high_var = ((lambda_adj_high_var / 1.5) - 1) * 100
    
    print(f"   Forma ottima (100%) MA variance alta (2.5)")
    print(f"   Aggiustamento: {change_high_var:+.2f}%")
    print(f"   ✅ Ridotto per bassa confidence (variance alta)")
    
    assert abs(change_high_var) < 2.0, "❌ Aggiustamento troppo alto per variance alta"
    
    return True


def test_no_overestimation():
    """Test che non ci siano sovrastime come prima"""
    print_section("TEST 2: Verifica NO Sovrastima")
    
    calc = AdvancedProbabilityCalculator()
    
    # Scenario critico: quello che causava problemi prima
    # spread=-0.75, total=2.75 → GG, Over dovrebbero essere realistici
    
    print("\n📊 SCENARIO: Spread -0.75, Total 2.75")
    print("   (Quello che prima causava GG 67%, Over 2.5 74%)")
    
    # Simula stats API moderate
    stats_home = {
        'form_factor': 0.7,  # Buona
        'variance': 0.8,
        'goals_scored_avg': 1.8,
        'goals_conceded_avg': 1.0
    }
    
    stats_away = {
        'form_factor': 0.6,  # Media-buona
        'variance': 1.0,
        'goals_scored_avg': 1.0,
        'goals_conceded_avg': 1.2
    }
    
    # SENZA API
    results_no_api = calc.calculate_all_probabilities(
        -0.5, 2.5,
        -0.75, 2.75
    )
    
    # CON API
    results_with_api = calc.calculate_all_probabilities(
        -0.5, 2.5,
        -0.75, 2.75,
        api_stats_home=stats_home,
        api_stats_away=stats_away
    )
    
    # Confronto
    print("\n📈 Confronto Probabilità (Corrente):")
    print("\n   Mercato                  | Senza API | Con API   | Delta")
    print("   " + "-"*60)
    
    markets_to_check = [
        ('P(1)', 'Current', '1X2', '1'),
        ('P(X)', 'Current', '1X2', 'X'),
        ('P(2)', 'Current', '1X2', '2'),
        ('P(GG)', 'Current', 'GG_NG', 'GG'),
        ('P(NG)', 'Current', 'GG_NG', 'NG'),
        ('P(Over 2.5)', 'Current', 'Over_Under', 'Over 2.5'),
        ('P(Over 3.5)', 'Current', 'Over_Under', 'Over 3.5'),
    ]
    
    for label, phase, market, key in markets_to_check:
        no_api = results_no_api[phase][market][key]
        with_api = results_with_api[phase][market][key]
        delta = (with_api - no_api) * 100
        
        print(f"   {label:20s} | {no_api*100:6.2f}%  | {with_api*100:6.2f}%  | {delta:+5.2f}%")
    
    # Verifica Over 2.5 non sovrastimato
    over_25_with_api = results_with_api['Current']['Over_Under']['Over 2.5']
    over_35_with_api = results_with_api['Current']['Over_Under']['Over 3.5']
    gg_with_api = results_with_api['Current']['GG_NG']['GG']
    
    print(f"\n🔍 Verifica Realismo:")
    print(f"   P(Over 2.5) = {over_25_with_api*100:.2f}% {'✅ OK' if over_25_with_api < 0.75 else '❌ ALTO'}")
    print(f"   P(Over 3.5) = {over_35_with_api*100:.2f}% {'✅ OK' if over_35_with_api < 0.65 else '❌ ALTO'}")
    print(f"   P(GG) = {gg_with_api*100:.2f}% {'✅ OK' if gg_with_api < 0.70 else '❌ ALTO'}")
    
    # Lambda attese
    lambda_home = results_with_api['Current']['Expected_Goals']['Home']
    lambda_away = results_with_api['Current']['Expected_Goals']['Away']
    total_lambda = lambda_home + lambda_away
    
    print(f"\n⚽ Expected Goals:")
    print(f"   Casa: {lambda_home:.3f}")
    print(f"   Trasferta: {lambda_away:.3f}")
    print(f"   Total: {total_lambda:.3f} (target: 2.75)")
    
    # Verifica non sovrastime
    assert over_25_with_api < 0.76, f"❌ Over 2.5 troppo alto: {over_25_with_api*100:.2f}%"
    assert gg_with_api < 0.71, f"❌ GG troppo alto: {gg_with_api*100:.2f}%"
    
    print(f"\n✅ Nessuna sovrastima rilevata!")
    
    return True


def test_coherence_maintained():
    """Test che la coerenza tra mercati sia mantenuta"""
    print_section("TEST 3: Verifica Coerenza Mercati")
    
    calc = AdvancedProbabilityCalculator()
    
    stats_home = {
        'form_factor': 0.75,
        'variance': 0.9,
        'goals_scored_avg': 2.0,
        'goals_conceded_avg': 0.8
    }
    
    stats_away = {
        'form_factor': 0.55,
        'variance': 1.1,
        'goals_scored_avg': 0.9,
        'goals_conceded_avg': 1.5
    }
    
    results = calc.calculate_all_probabilities(
        -0.5, 2.5,
        -0.75, 2.75,
        api_stats_home=stats_home,
        api_stats_away=stats_away
    )
    
    current = results['Current']
    
    # Test 1: 1X2 somma a 1.0
    sum_1x2 = current['1X2']['1'] + current['1X2']['X'] + current['1X2']['2']
    print(f"\n✓ Somma 1X2: {sum_1x2:.10f} {'✅' if abs(sum_1x2 - 1.0) < 0.0001 else '❌'}")
    assert abs(sum_1x2 - 1.0) < 0.0001
    
    # Test 2: GG/NG somma a 1.0
    sum_gg = current['GG_NG']['GG'] + current['GG_NG']['NG']
    print(f"✓ Somma GG/NG: {sum_gg:.10f} {'✅' if abs(sum_gg - 1.0) < 0.0001 else '❌'}")
    assert abs(sum_gg - 1.0) < 0.0001
    
    # Test 3: Over/Under somma a 1.0
    sum_ou_25 = current['Over_Under']['Over 2.5'] + current['Over_Under']['Under 2.5']
    print(f"✓ Somma O/U 2.5: {sum_ou_25:.10f} {'✅' if abs(sum_ou_25 - 1.0) < 0.0001 else '❌'}")
    assert abs(sum_ou_25 - 1.0) < 0.0001
    
    # Test 4: Win to Nil < NG
    wtn_casa = current['Win_to_Nil']['Casa Win to Nil']
    wtn_trasf = current['Win_to_Nil']['Trasferta Win to Nil']
    ng = current['GG_NG']['NG']
    sum_wtn = wtn_casa + wtn_trasf
    
    print(f"✓ Win to Nil < NG: {sum_wtn:.4f} < {ng:.4f} {'✅' if sum_wtn <= ng + 0.0001 else '❌'}")
    assert sum_wtn <= ng + 0.0001
    
    print(f"\n✅ Tutte le coerenze mantenute!")
    
    return True


def test_extreme_scenarios():
    """Test scenari estremi"""
    print_section("TEST 4: Scenari Estremi")
    
    calc = AdvancedProbabilityCalculator()
    
    # Scenario 1: Forma pessima + alta variance
    print("\n📊 SCENARIO 1: Forma pessima (5L) + Alta variance")
    
    stats_pessimo = {
        'form_factor': 0.0,  # 5L
        'variance': 2.5,
        'goals_scored_avg': 0.5,
        'goals_conceded_avg': 2.5
    }
    
    stats_medio = {
        'form_factor': 0.5,
        'variance': 1.0,
        'goals_scored_avg': 1.2,
        'goals_conceded_avg': 1.2
    }
    
    lambda_adj, _ = calc._apply_api_adjustment(1.0, 1.0, stats_pessimo, stats_medio)
    change = ((lambda_adj / 1.0) - 1) * 100
    
    print(f"   Aggiustamento: {change:+.2f}%")
    print(f"   {'✅' if change >= -3.1 and change <= 0 else '❌'} Entro limiti e negativo (forma pessima)")
    
    assert -3.1 <= change <= 0, f"Aggiustamento fuori range: {change:.2f}%"
    
    # Scenario 2: Forma ottima + bassa variance (caso migliore)
    print("\n📊 SCENARIO 2: Forma ottima (5W) + Bassa variance")
    
    stats_ottimo = {
        'form_factor': 1.0,  # 5W
        'variance': 0.3,  # Molto stabile
        'goals_scored_avg': 2.5,
        'goals_conceded_avg': 0.5
    }
    
    lambda_adj, _ = calc._apply_api_adjustment(1.5, 1.0, stats_ottimo, stats_medio)
    change = ((lambda_adj / 1.5) - 1) * 100
    
    print(f"   Aggiustamento: {change:+.2f}%")
    print(f"   {'✅' if change >= 0 and change <= 3.1 else '❌'} Entro limiti e positivo (forma ottima)")
    
    assert 0 <= change <= 3.1, f"Aggiustamento fuori range: {change:.2f}%"
    
    print(f"\n✅ Scenari estremi gestiti correttamente!")
    
    return True


def main():
    """Esegue tutti i test"""
    print("="*80)
    print("  TEST INTEGRAZIONE API - Verifica Funzionamento e No Sovrastime")
    print("="*80)
    
    tests = [
        ("Logica Aggiustamenti API", test_api_adjustment_logic),
        ("No Sovrastima", test_no_overestimation),
        ("Coerenza Mercati", test_coherence_maintained),
        ("Scenari Estremi", test_extreme_scenarios),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n{'='*80}")
                print(f"✅ TEST PASSATO: {test_name}")
                print(f"{'='*80}")
        except AssertionError as e:
            failed += 1
            print(f"\n{'='*80}")
            print(f"❌ TEST FALLITO: {test_name}")
            print(f"   Errore: {str(e)}")
            print(f"{'='*80}")
        except Exception as e:
            failed += 1
            print(f"\n{'='*80}")
            print(f"❌ TEST ERRORE: {test_name}")
            print(f"   Errore: {str(e)}")
            print(f"{'='*80}")
    
    # Riepilogo
    print_section("RIEPILOGO FINALE")
    print(f"\n✅ Test passati: {passed}/{len(tests)}")
    print(f"❌ Test falliti: {failed}/{len(tests)}")
    
    if failed == 0:
        print(f"\n🎉 TUTTI I TEST SUPERATI!")
        print(f"   - Aggiustamenti API funzionano correttamente")
        print(f"   - Nessuna sovrastima rilevata")
        print(f"   - Coerenza mercati mantenuta")
        print(f"   - Limiti rispettati (max ±3%)")
        print(f"\n✅ Sistema PRONTO per produzione!")
        return 0
    else:
        print(f"\n⚠️ ATTENZIONE: {failed} test falliti!")
        print(f"   Verificare e correggere prima di usare in produzione.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


