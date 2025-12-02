#!/usr/bin/env python3
"""
Test completo con diversi scenari per verificare la correttezza dei calcoli
dopo l'applicazione del fix conservativo.

Testa:
1. Diversi spread (negativo, zero, positivo)
2. Diversi total (basso, medio, alto)
3. Movimenti di mercato (apertura vs corrente)
4. Coerenza tra mercati
5. Limiti matematici (somme = 1.0)
"""

from probability_calculator import AdvancedProbabilityCalculator
import math

def test_scenario(name, spread_open, total_open, spread_curr, total_curr):
    """Testa un singolo scenario e verifica coerenza"""
    print(f"\n{'='*80}")
    print(f"📊 SCENARIO: {name}")
    print(f"{'='*80}")
    print(f"Apertura: Spread {spread_open:+.2f}, Total {total_open:.2f}")
    print(f"Corrente: Spread {spread_curr:+.2f}, Total {total_curr:.2f}")
    
    calc = AdvancedProbabilityCalculator()
    results = calc.calculate_all_probabilities(
        spread_open, total_open,
        spread_curr, total_curr
    )
    
    # Expected Goals
    lambda_h = results['Current']['Expected_Goals']['Home']
    lambda_a = results['Current']['Expected_Goals']['Away']
    total_lambda = lambda_h + lambda_a
    
    print(f"\n🎯 Expected Goals: Casa {lambda_h:.3f} - Trasferta {lambda_a:.3f}")
    print(f"   Total atteso: {total_lambda:.3f}")
    
    # 1X2
    curr_1x2 = results['Current']['1X2']
    sum_1x2 = curr_1x2['1'] + curr_1x2['X'] + curr_1x2['2']
    print(f"\n⚽ 1X2:")
    print(f"   1 (Casa):      {curr_1x2['1']*100:6.2f}%")
    print(f"   X (Pareggio):  {curr_1x2['X']*100:6.2f}%")
    print(f"   2 (Trasferta): {curr_1x2['2']*100:6.2f}%")
    print(f"   Somma:         {sum_1x2*100:6.2f}% {'✓' if abs(sum_1x2 - 1.0) < 1e-6 else '⚠️ ERRORE'}")
    
    # GG/NG
    curr_gg = results['Current']['GG_NG']
    sum_gg = curr_gg['GG'] + curr_gg['NG']
    print(f"\n🎯 GG/NG:")
    print(f"   GG (Entrambe segnano): {curr_gg['GG']*100:6.2f}%")
    print(f"   NG (Almeno una no):    {curr_gg['NG']*100:6.2f}%")
    print(f"   Somma:                 {sum_gg*100:6.2f}% {'✓' if abs(sum_gg - 1.0) < 1e-6 else '⚠️ ERRORE'}")
    
    # Over/Under
    curr_ou = results['Current']['Over_Under']
    print(f"\n📈 Over/Under:")
    for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
        over_key = f'Over {threshold}'
        under_key = f'Under {threshold}'
        if over_key in curr_ou and under_key in curr_ou:
            over = curr_ou[over_key]
            under = curr_ou[under_key]
            sum_ou = over + under
            print(f"   {threshold}: Over {over*100:6.2f}% | Under {under*100:6.2f}% | Sum {sum_ou*100:6.2f}% {'✓' if abs(sum_ou - 1.0) < 1e-6 else '⚠️'}")
    
    # Doppia Chance
    curr_dc = results['Current']['Double_Chance']
    print(f"\n🔄 Doppia Chance:")
    print(f"   1X: {curr_dc['1X']*100:6.2f}% (dovrebbe essere 1+X = {(curr_1x2['1']+curr_1x2['X'])*100:.2f}%) {'✓' if abs(curr_dc['1X'] - (curr_1x2['1']+curr_1x2['X'])) < 1e-6 else '⚠️'}")
    print(f"   12: {curr_dc['12']*100:6.2f}% (dovrebbe essere 1+2 = {(curr_1x2['1']+curr_1x2['2'])*100:.2f}%) {'✓' if abs(curr_dc['12'] - (curr_1x2['1']+curr_1x2['2'])) < 1e-6 else '⚠️'}")
    print(f"   X2: {curr_dc['X2']*100:6.2f}% (dovrebbe essere X+2 = {(curr_1x2['X']+curr_1x2['2'])*100:.2f}%) {'✓' if abs(curr_dc['X2'] - (curr_1x2['X']+curr_1x2['2'])) < 1e-6 else '⚠️'}")
    
    # Verifica realismo Over/Under rispetto al total atteso
    print(f"\n🔍 Verifica Realismo:")
    
    # Calcolo Poisson pura per confronto
    def poisson(k, lam):
        return (lam ** k) * math.exp(-lam) / math.factorial(k)
    
    # Over 2.5 Poisson pura
    over25_pure = 0.0
    for h in range(15):
        for a in range(15):
            if h + a > 2:
                over25_pure += poisson(h, lambda_h) * poisson(a, lambda_a)
    
    over25_calc = curr_ou['Over 2.5']
    diff_over25 = (over25_calc - over25_pure) * 100
    
    print(f"   Over 2.5: {over25_calc*100:.2f}% (Poisson pura: {over25_pure*100:.2f}%, diff: {diff_over25:+.2f}%)")
    if abs(diff_over25) > 10:
        print(f"   ⚠️  Differenza troppo alta! Dovrebbe essere < 10%")
    else:
        print(f"   ✓ Differenza accettabile")
    
    # GG Poisson pura
    prob_h_0 = poisson(0, lambda_h)
    prob_a_0 = poisson(0, lambda_a)
    gg_pure = (1 - prob_h_0) * (1 - prob_a_0)
    
    gg_calc = curr_gg['GG']
    diff_gg = (gg_calc - gg_pure) * 100
    
    print(f"   GG: {gg_calc*100:.2f}% (Poisson pura: {gg_pure*100:.2f}%, diff: {diff_gg:+.2f}%)")
    if abs(diff_gg) > 8:
        print(f"   ⚠️  Differenza troppo alta! Dovrebbe essere < 8%")
    else:
        print(f"   ✓ Differenza accettabile")
    
    # Verifica coerenza 1X2 con risultati esatti
    print(f"\n📋 Top 5 Risultati Esatti:")
    curr_scores = results['Current']['Exact_Scores']
    for i, (score, prob) in enumerate(list(curr_scores.items())[:5], 1):
        print(f"   {i}. {score:5s} → {prob*100:6.2f}%")
    
    # Ritorna metriche per confronto
    return {
        'name': name,
        'total_lambda': total_lambda,
        'gg': gg_calc * 100,
        'over25': over25_calc * 100,
        'over35': curr_ou['Over 3.5'] * 100,
        'diff_gg': diff_gg,
        'diff_over25': diff_over25,
        'sum_1x2_ok': abs(sum_1x2 - 1.0) < 1e-6,
        'sum_gg_ok': abs(sum_gg - 1.0) < 1e-6
    }

# Test diversi scenari
print("="*80)
print("🧪 TEST COMPLETO - DIVERSI SCENARI")
print("="*80)

scenarios = []

# Scenario 1: Casa molto favorita, total basso
scenarios.append(test_scenario(
    "Casa molto favorita, total basso",
    spread_open=-1.5, total_open=2.0,
    spread_curr=-1.75, total_curr=2.25
))

# Scenario 2: Casa leggermente favorita, total medio
scenarios.append(test_scenario(
    "Casa leggermente favorita, total medio",
    spread_open=-0.5, total_open=2.5,
    spread_curr=-0.75, total_curr=2.75
))

# Scenario 3: Match equilibrato, total alto
scenarios.append(test_scenario(
    "Match equilibrato, total alto",
    spread_open=0.0, total_open=3.5,
    spread_curr=0.0, total_curr=3.75
))

# Scenario 4: Trasferta favorita, total basso
scenarios.append(test_scenario(
    "Trasferta favorita, total basso",
    spread_open=0.75, total_open=2.0,
    spread_curr=1.0, total_curr=2.25
))

# Scenario 5: Casa favorita, total molto alto
scenarios.append(test_scenario(
    "Casa favorita, total molto alto",
    spread_open=-0.5, total_open=4.0,
    spread_curr=-0.75, total_curr=4.25
))

# Scenario 6: Match equilibrato, total molto basso
scenarios.append(test_scenario(
    "Match equilibrato, total molto basso",
    spread_open=0.0, total_open=1.5,
    spread_curr=0.0, total_curr=1.75
))

# Scenario 7: Grande movimento spread (casa diventa più favorita)
scenarios.append(test_scenario(
    "Grande movimento spread (casa più favorita)",
    spread_open=-0.25, total_open=2.5,
    spread_curr=-1.25, total_curr=2.5
))

# Scenario 8: Grande movimento total (da basso ad alto)
scenarios.append(test_scenario(
    "Grande movimento total (da basso ad alto)",
    spread_open=-0.5, total_open=2.0,
    spread_curr=-0.5, total_curr=3.5
))

# Riepilogo finale
print(f"\n{'='*80}")
print("📊 RIEPILOGO FINALE")
print(f"{'='*80}")

print(f"\n{'Scenario':<45} {'Total':<8} {'GG%':<8} {'O2.5%':<8} {'O3.5%':<8} {'ΔGG':<8} {'ΔO2.5':<8}")
print('-'*95)

all_ok = True
for s in scenarios:
    status_gg = '✓' if abs(s['diff_gg']) < 8 else '⚠️'
    status_o25 = '✓' if abs(s['diff_over25']) < 10 else '⚠️'
    
    if abs(s['diff_gg']) >= 8 or abs(s['diff_over25']) >= 10:
        all_ok = False
    
    print(f"{s['name']:<45} {s['total_lambda']:<8.2f} {s['gg']:<8.2f} {s['over25']:<8.2f} {s['over35']:<8.2f} {s['diff_gg']:+7.2f}{status_gg} {s['diff_over25']:+7.2f}{status_o25}")

print(f"\n{'='*80}")
if all_ok:
    print("✅ TUTTI I TEST PASSATI - Il sistema è corretto e realistico!")
else:
    print("⚠️  ALCUNI TEST FALLITI - Verificare le correzioni")
print(f"{'='*80}")

# Verifica normalizzazioni
print(f"\n🔍 Verifica Normalizzazioni:")
all_normalized = all(s['sum_1x2_ok'] and s['sum_gg_ok'] for s in scenarios)
if all_normalized:
    print("✅ Tutte le probabilità sono correttamente normalizzate (somma = 1.0)")
else:
    print("⚠️  Alcune probabilità non sono normalizzate correttamente")

