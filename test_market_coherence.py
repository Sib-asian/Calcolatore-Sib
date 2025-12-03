"""
Test di Coerenza Movimenti Mercati

Verifica che tutti i mercati si muovano in modo logicamente coerente
quando cambiano spread e total (apertura vs corrente).
"""

import sys
from probability_calculator import AdvancedProbabilityCalculator

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)

def check_movement_logic(scenario_name, spread_opening, total_opening, spread_current, total_current):
    """
    Verifica la logica dei movimenti per uno scenario specifico.
    """
    calc = AdvancedProbabilityCalculator()
    results = calc.calculate_all_probabilities(
        spread_opening, total_opening,
        spread_current, total_current
    )
    
    opening = results['Opening']
    current = results['Current']
    movement = results['Movement']
    
    print(f"\n{'─'*80}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'─'*80}")
    print(f"Spread: {spread_opening:.2f} → {spread_current:.2f} (Δ = {movement['Spread_Change']:+.2f})")
    print(f"Total:  {total_opening:.2f} → {total_current:.2f} (Δ = {movement['Total_Change']:+.2f})")
    print(f"λ Casa: {opening['Expected_Goals']['Home']:.3f} → {current['Expected_Goals']['Home']:.3f} (Δ = {movement['Home_EG_Change']:+.3f})")
    print(f"λ Trasf: {opening['Expected_Goals']['Away']:.3f} → {current['Expected_Goals']['Away']:.3f} (Δ = {movement['Away_EG_Change']:+.3f})")
    
    errors = []
    warnings = []
    
    # ========== REGOLE DI COERENZA ==========
    
    # 1. SPREAD: Se diventa più NEGATIVO (Casa più favorita)
    if movement['Spread_Change'] < -0.01:  # Tolleranza
        print("\n🔍 SPREAD più NEGATIVO (Casa più favorita) → P(1) ↑, P(2) ↓")
        
        p1_change = current['1X2']['1'] - opening['1X2']['1']
        p2_change = current['1X2']['2'] - opening['1X2']['2']
        
        print(f"   P(1): {opening['1X2']['1']:.4f} → {current['1X2']['1']:.4f} ({p1_change:+.4f})")
        print(f"   P(2): {opening['1X2']['2']:.4f} → {current['1X2']['2']:.4f} ({p2_change:+.4f})")
        
        if p1_change <= 0:
            errors.append(f"❌ P(1) NON aumenta con spread più negativo! ({p1_change:+.4f})")
        else:
            print(f"   ✅ P(1) aumenta correttamente")
        
        if p2_change >= 0:
            errors.append(f"❌ P(2) NON diminuisce con spread più negativo! ({p2_change:+.4f})")
        else:
            print(f"   ✅ P(2) diminuisce correttamente")
        
        # Doppia Chance
        p1x_change = current['Double_Chance']['1X'] - opening['Double_Chance']['1X']
        px2_change = current['Double_Chance']['X2'] - opening['Double_Chance']['X2']
        
        print(f"   P(1X): {opening['Double_Chance']['1X']:.4f} → {current['Double_Chance']['1X']:.4f} ({p1x_change:+.4f})")
        print(f"   P(X2): {opening['Double_Chance']['X2']:.4f} → {current['Double_Chance']['X2']:.4f} ({px2_change:+.4f})")
        
        if p1x_change <= 0:
            errors.append(f"❌ P(1X) NON aumenta con spread più negativo! ({p1x_change:+.4f})")
        else:
            print(f"   ✅ P(1X) aumenta correttamente")
        
        if px2_change >= 0:
            errors.append(f"❌ P(X2) NON diminuisce con spread più negativo! ({px2_change:+.4f})")
        else:
            print(f"   ✅ P(X2) diminuisce correttamente")
    
    # 2. SPREAD: Se diventa più POSITIVO (Trasferta più favorita)
    elif movement['Spread_Change'] > 0.01:
        print("\n🔍 SPREAD più POSITIVO (Trasferta più favorita) → P(1) ↓, P(2) ↑")
        
        p1_change = current['1X2']['1'] - opening['1X2']['1']
        p2_change = current['1X2']['2'] - opening['1X2']['2']
        
        print(f"   P(1): {opening['1X2']['1']:.4f} → {current['1X2']['1']:.4f} ({p1_change:+.4f})")
        print(f"   P(2): {opening['1X2']['2']:.4f} → {current['1X2']['2']:.4f} ({p2_change:+.4f})")
        
        if p1_change >= 0:
            errors.append(f"❌ P(1) NON diminuisce con spread più positivo! ({p1_change:+.4f})")
        else:
            print(f"   ✅ P(1) diminuisce correttamente")
        
        if p2_change <= 0:
            errors.append(f"❌ P(2) NON aumenta con spread più positivo! ({p2_change:+.4f})")
        else:
            print(f"   ✅ P(2) aumenta correttamente")
        
        # Doppia Chance
        p1x_change = current['Double_Chance']['1X'] - opening['Double_Chance']['1X']
        px2_change = current['Double_Chance']['X2'] - opening['Double_Chance']['X2']
        
        print(f"   P(1X): {opening['Double_Chance']['1X']:.4f} → {current['Double_Chance']['1X']:.4f} ({p1x_change:+.4f})")
        print(f"   P(X2): {opening['Double_Chance']['X2']:.4f} → {current['Double_Chance']['X2']:.4f} ({px2_change:+.4f})")
        
        if p1x_change >= 0:
            errors.append(f"❌ P(1X) NON diminuisce con spread più positivo! ({p1x_change:+.4f})")
        else:
            print(f"   ✅ P(1X) diminuisce correttamente")
        
        if px2_change <= 0:
            errors.append(f"❌ P(X2) NON aumenta con spread più positivo! ({px2_change:+.4f})")
        else:
            print(f"   ✅ P(X2) aumenta correttamente")
    
    # 3. TOTAL: Se AUMENTA
    if movement['Total_Change'] > 0.01:
        print(f"\n🔍 TOTAL AUMENTA → Over ↑, Under ↓, GG ↑, NG ↓")
        
        # GG/NG
        pgg_change = current['GG_NG']['GG'] - opening['GG_NG']['GG']
        png_change = current['GG_NG']['NG'] - opening['GG_NG']['NG']
        
        print(f"   P(GG): {opening['GG_NG']['GG']:.4f} → {current['GG_NG']['GG']:.4f} ({pgg_change:+.4f})")
        print(f"   P(NG): {opening['GG_NG']['NG']:.4f} → {current['GG_NG']['NG']:.4f} ({png_change:+.4f})")
        
        if pgg_change <= 0:
            errors.append(f"❌ P(GG) NON aumenta con total aumentato! ({pgg_change:+.4f})")
        else:
            print(f"   ✅ P(GG) aumenta correttamente")
        
        if png_change >= 0:
            errors.append(f"❌ P(NG) NON diminuisce con total aumentato! ({png_change:+.4f})")
        else:
            print(f"   ✅ P(NG) diminuisce correttamente")
        
        # Over/Under
        test_thresholds = ['Over 1.5', 'Over 2.5', 'Over 3.5']
        for threshold in test_thresholds:
            if threshold in opening['Over_Under'] and threshold in current['Over_Under']:
                over_change = current['Over_Under'][threshold] - opening['Over_Under'][threshold]
                under_key = threshold.replace('Over', 'Under')
                under_change = current['Over_Under'][under_key] - opening['Over_Under'][under_key]
                
                print(f"   P({threshold}): {opening['Over_Under'][threshold]:.4f} → {current['Over_Under'][threshold]:.4f} ({over_change:+.4f})")
                
                if over_change <= 0:
                    errors.append(f"❌ P({threshold}) NON aumenta con total aumentato! ({over_change:+.4f})")
                else:
                    print(f"      ✅ {threshold} aumenta")
                
                if under_change >= 0:
                    errors.append(f"❌ P({under_key}) NON diminuisce con total aumentato! ({under_change:+.4f})")
    
    # 4. TOTAL: Se DIMINUISCE
    elif movement['Total_Change'] < -0.01:
        print(f"\n🔍 TOTAL DIMINUISCE → Over ↓, Under ↑, GG ↓, NG ↑")
        
        # GG/NG
        pgg_change = current['GG_NG']['GG'] - opening['GG_NG']['GG']
        png_change = current['GG_NG']['NG'] - opening['GG_NG']['NG']
        
        print(f"   P(GG): {opening['GG_NG']['GG']:.4f} → {current['GG_NG']['GG']:.4f} ({pgg_change:+.4f})")
        print(f"   P(NG): {opening['GG_NG']['NG']:.4f} → {current['GG_NG']['NG']:.4f} ({png_change:+.4f})")
        
        if pgg_change >= 0:
            errors.append(f"❌ P(GG) NON diminuisce con total diminuito! ({pgg_change:+.4f})")
        else:
            print(f"   ✅ P(GG) diminuisce correttamente")
        
        if png_change <= 0:
            errors.append(f"❌ P(NG) NON aumenta con total diminuito! ({png_change:+.4f})")
        else:
            print(f"   ✅ P(NG) aumenta correttamente")
        
        # Over/Under
        test_thresholds = ['Over 1.5', 'Over 2.5', 'Over 3.5']
        for threshold in test_thresholds:
            if threshold in opening['Over_Under'] and threshold in current['Over_Under']:
                over_change = current['Over_Under'][threshold] - opening['Over_Under'][threshold]
                under_key = threshold.replace('Over', 'Under')
                under_change = current['Over_Under'][under_key] - opening['Over_Under'][under_key]
                
                print(f"   P({threshold}): {opening['Over_Under'][threshold]:.4f} → {current['Over_Under'][threshold]:.4f} ({over_change:+.4f})")
                
                if over_change >= 0:
                    errors.append(f"❌ P({threshold}) NON diminuisce con total diminuito! ({over_change:+.4f})")
                else:
                    print(f"      ✅ {threshold} diminuisce")
                
                if under_change <= 0:
                    errors.append(f"❌ P({under_key}) NON aumenta con total diminuito! ({under_change:+.4f})")
    
    # 5. WIN TO NIL: Coerenza con NG
    print(f"\n🔍 WIN TO NIL: Deve essere coerente con NG")
    wtn_home = current['Win_to_Nil']['Casa Win to Nil']
    wtn_away = current['Win_to_Nil']['Trasferta Win to Nil']
    png = current['GG_NG']['NG']
    
    print(f"   P(Casa Win to Nil): {wtn_home:.4f}")
    print(f"   P(Trasferta Win to Nil): {wtn_away:.4f}")
    print(f"   P(NG): {png:.4f}")
    print(f"   Somma WtN: {wtn_home + wtn_away:.4f}")
    
    # Win to Nil è un sottoinsieme di NG
    if (wtn_home + wtn_away) > png + 0.001:  # Tolleranza
        errors.append(f"❌ Somma Win to Nil ({wtn_home + wtn_away:.4f}) > NG ({png:.4f})!")
    else:
        print(f"   ✅ Win to Nil coerente con NG")
    
    # 6. HANDICAP ASIATICO: Coerenza con 1X2
    print(f"\n🔍 ASIAN HANDICAP: Deve essere coerente con movimento spread")
    
    # Controlla AH 0.0 (circa equivalente a 1X2)
    ah_home_0 = current['Handicap_Asiatico'].get('AH 0.0 Casa', 0)
    ah_away_0 = current['Handicap_Asiatico'].get('AH 0.0 Trasferta', 0)
    p1 = current['1X2']['1']
    p2 = current['1X2']['2']
    
    print(f"   P(AH 0.0 Casa): {ah_home_0:.4f} vs P(1): {p1:.4f}")
    print(f"   P(AH 0.0 Trasferta): {ah_away_0:.4f} vs P(2): {p2:.4f}")
    
    # AH 0.0 dovrebbe essere simile a 1X2 (escludendo pareggio che viene rimborsato)
    if abs(ah_home_0 - (p1 + opening['1X2']['X'] * 0.5)) > 0.05:
        warnings.append(f"⚠️ AH 0.0 Casa ({ah_home_0:.4f}) diverge da 1X2 ({p1:.4f})")
    
    # 7. PRIMO TEMPO: Deve seguire stesso pattern del Full Time
    print(f"\n🔍 PRIMO TEMPO: Deve seguire pattern Full Time")
    
    if movement['Spread_Change'] < -0.01:
        ht_p1_change = current['HT']['HT_1'] - opening['HT']['HT_1']
        ht_p2_change = current['HT']['HT_2'] - opening['HT']['HT_2']
        
        print(f"   P(HT_1): {opening['HT']['HT_1']:.4f} → {current['HT']['HT_1']:.4f} ({ht_p1_change:+.4f})")
        print(f"   P(HT_2): {opening['HT']['HT_2']:.4f} → {current['HT']['HT_2']:.4f} ({ht_p2_change:+.4f})")
        
        if ht_p1_change <= 0:
            errors.append(f"❌ P(HT_1) NON aumenta con spread più negativo! ({ht_p1_change:+.4f})")
        else:
            print(f"   ✅ HT_1 aumenta come FT")
        
        if ht_p2_change >= 0:
            errors.append(f"❌ P(HT_2) NON diminuisce con spread più negativo! ({ht_p2_change:+.4f})")
        else:
            print(f"   ✅ HT_2 diminuisce come FT")
    
    # 8. NORMALIZZAZIONE: Tutti i mercati devono sommare a 1.0
    print(f"\n🔍 NORMALIZZAZIONE: Tutti i mercati devono sommare a 1.0")
    
    sum_1x2 = current['1X2']['1'] + current['1X2']['X'] + current['1X2']['2']
    sum_gg = current['GG_NG']['GG'] + current['GG_NG']['NG']
    sum_dc = current['Double_Chance']['1X'] + current['Double_Chance']['12'] + current['Double_Chance']['X2']
    
    print(f"   Somma 1X2: {sum_1x2:.10f}")
    print(f"   Somma GG/NG: {sum_gg:.10f}")
    print(f"   Somma Double Chance: {sum_dc:.10f}")
    
    if abs(sum_1x2 - 1.0) > 0.0001:
        errors.append(f"❌ 1X2 non normalizzato: {sum_1x2:.10f}")
    else:
        print(f"   ✅ 1X2 normalizzato")
    
    if abs(sum_gg - 1.0) > 0.0001:
        errors.append(f"❌ GG/NG non normalizzato: {sum_gg:.10f}")
    else:
        print(f"   ✅ GG/NG normalizzato")
    
    if abs(sum_dc - 2.0) > 0.0001:  # DC somma a 2.0 perché ogni esito copre 2 possibilità
        errors.append(f"❌ Double Chance non corretto: {sum_dc:.10f} (dovrebbe essere ~2.0)")
    else:
        print(f"   ✅ Double Chance corretto")
    
    # Over/Under per ogni soglia
    for threshold in ['Over 1.5', 'Over 2.5', 'Over 3.5']:
        if threshold in current['Over_Under']:
            under_key = threshold.replace('Over', 'Under')
            sum_ou = current['Over_Under'][threshold] + current['Over_Under'][under_key]
            print(f"   Somma {threshold}/{under_key}: {sum_ou:.10f}")
            
            if abs(sum_ou - 1.0) > 0.0001:
                errors.append(f"❌ {threshold}/{under_key} non normalizzato: {sum_ou:.10f}")
    
    # Stampa risultati
    print(f"\n{'─'*80}")
    if errors:
        print(f"❌ SCENARIO FALLITO: {len(errors)} errori critici")
        for error in errors:
            print(f"   {error}")
    else:
        print(f"✅ SCENARIO SUPERATO: Tutti i controlli passati")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"   {warning}")
    
    return len(errors) == 0


def main():
    print_section("TEST COERENZA MOVIMENTI MERCATI")
    print("\nQuesto test verifica che tutti i mercati si muovano in modo logicamente coerente")
    print("quando cambiano spread e total tra apertura e corrente.")
    
    scenarios = []
    
    # Scenario 1: Spread diventa più negativo (Casa più favorita), Total stabile
    scenarios.append((
        "Spread più negativo (Casa più favorita), Total stabile",
        -0.5, 2.5,  # Apertura
        -0.75, 2.5   # Corrente
    ))
    
    # Scenario 2: Spread diventa più positivo (Trasferta più favorita), Total stabile
    scenarios.append((
        "Spread più positivo (Trasferta più favorita), Total stabile",
        -0.5, 2.5,   # Apertura
        -0.25, 2.5   # Corrente
    ))
    
    # Scenario 3: Spread stabile, Total aumenta
    scenarios.append((
        "Spread stabile, Total aumenta",
        -0.5, 2.5,   # Apertura
        -0.5, 2.75   # Corrente
    ))
    
    # Scenario 4: Spread stabile, Total diminuisce
    scenarios.append((
        "Spread stabile, Total diminuisce",
        -0.5, 2.75,  # Apertura
        -0.5, 2.5    # Corrente
    ))
    
    # Scenario 5: Spread più negativo + Total aumenta (Casa più forte e più gol)
    scenarios.append((
        "Spread più negativo + Total aumenta",
        -0.5, 2.5,   # Apertura
        -0.75, 2.75  # Corrente
    ))
    
    # Scenario 6: Spread più positivo + Total aumenta (Trasferta più forte e più gol)
    scenarios.append((
        "Spread più positivo + Total aumenta",
        -0.75, 2.5,  # Apertura
        -0.5, 2.75   # Corrente
    ))
    
    # Scenario 7: Spread più negativo + Total diminuisce
    scenarios.append((
        "Spread più negativo + Total diminuisce",
        -0.5, 2.75,  # Apertura
        -0.75, 2.5   # Corrente
    ))
    
    # Scenario 8: Casa molto favorita
    scenarios.append((
        "Casa molto favorita diventa ancora più favorita",
        -1.0, 2.5,   # Apertura
        -1.25, 2.5   # Corrente
    ))
    
    # Scenario 9: Trasferta favorita
    scenarios.append((
        "Trasferta favorita diventa ancora più favorita",
        0.5, 2.5,    # Apertura
        0.75, 2.5    # Corrente
    ))
    
    # Scenario 10: Match equilibrato con total alto
    scenarios.append((
        "Match equilibrato, total aumenta significativamente",
        0.0, 2.5,    # Apertura
        0.0, 3.5     # Corrente
    ))
    
    # Scenario 11: Il caso dell'utente
    scenarios.append((
        "Caso specifico utente: spread da -0.5 a -0.75, total da 2.5 a 2.75",
        -0.5, 2.5,   # Apertura
        -0.75, 2.75  # Corrente
    ))
    
    passed = 0
    failed = 0
    
    for scenario in scenarios:
        result = check_movement_logic(*scenario)
        if result:
            passed += 1
        else:
            failed += 1
    
    # Riepilogo finale
    print_section("RIEPILOGO FINALE")
    print(f"\n✅ Scenari superati: {passed}/{len(scenarios)}")
    print(f"❌ Scenari falliti: {failed}/{len(scenarios)}")
    
    if failed == 0:
        print(f"\n🎉 TUTTI I TEST SUPERATI!")
        print(f"   Il sistema si muove in modo logicamente coerente per tutti gli scenari.")
    else:
        print(f"\n⚠️  ATTENZIONE: {failed} scenari con problemi di coerenza!")
        print(f"   Verificare la logica di calcolo dei mercati.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

