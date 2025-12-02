#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test finale per verificare tutti i fix"""

from probability_calculator import AdvancedProbabilityCalculator

print("="*80)
print("TEST FINALE - VERIFICA TUTTI I FIX")
print("="*80)

calc = AdvancedProbabilityCalculator()

# Test 1: Spread rispettato
print("\n1. VERIFICA SPREAD RISPETTATO")
print("-"*80)

test_cases = [
    {"name": "Casa molto favorita", "spread": -1.5, "total": 2.5},
    {"name": "Casa favorita", "spread": -0.75, "total": 2.75},
    {"name": "Match equilibrato", "spread": 0.0, "total": 3.0},
    {"name": "Trasferta favorita", "spread": 0.75, "total": 2.75},
]

all_spread_ok = True
for tc in test_cases:
    lh, la = calc.spread_to_expected_goals(tc["spread"], tc["total"])
    
    # CONVENZIONE: spread negativo = Casa favorita
    # Quindi con spread negativo, lambda_home > lambda_away
    # Ma lo spread NON è lambda_h - lambda_a!
    # È una convenzione delle scommesse
    
    total_calc = lh + la
    total_error = abs(total_calc - tc["total"])
    
    # Verifica coerenza con spread
    if tc["spread"] < -0.1:  # Casa favorita
        spread_ok = lh > la
        status = "✓" if spread_ok else "⚠️"
    elif tc["spread"] > 0.1:  # Trasferta favorita
        spread_ok = la > lh
        status = "✓" if spread_ok else "⚠️"
    else:  # Equilibrato
        spread_ok = abs(lh - la) < 0.1
        status = "✓" if spread_ok else "⚠️"
    
    print(f"{tc['name']} (Spread {tc['spread']:+.2f}):")
    print(f"  Lambda: Casa {lh:.3f}, Trasferta {la:.3f}")
    print(f"  Total: {total_calc:.3f} (atteso {tc['total']:.2f}) {status}")
    
    if not spread_ok or total_error > 0.01:
        all_spread_ok = False

if all_spread_ok:
    print("\n✅ Spread rispettato in tutti i casi!")
else:
    print("\n⚠️ Problemi con lo spread!")

# Test 2: Exact Scores normalizzati
print("\n\n2. VERIFICA EXACT SCORES NORMALIZZATI")
print("-"*80)

results = calc.calculate_all_probabilities(-0.75, 2.75, -0.75, 2.75)
exact_scores = results['Current']['Exact_Scores']
sum_exact = sum(exact_scores.values())

print(f"Somma Exact Scores: {sum_exact:.15f}")
if abs(sum_exact - 1.0) < 1e-10:
    print("✅ Exact Scores perfettamente normalizzati!")
else:
    print(f"⚠️ Errore: {abs(sum_exact - 1.0):.10f}")

# Test 3: 1X2 coerente con Exact Scores
print("\n\n3. VERIFICA COERENZA 1X2 vs EXACT SCORES")
print("-"*80)

sum_1 = 0.0
sum_X = 0.0
sum_2 = 0.0

for score, prob in exact_scores.items():
    parts = score.split('-')
    if len(parts) == 2:
        h, a = int(parts[0]), int(parts[1])
        if h > a:
            sum_1 += prob
        elif h == a:
            sum_X += prob
        else:
            sum_2 += prob

_1x2 = results['Current']['1X2']
print(f"1X2 da Exact Scores:")
print(f"  1: {sum_1*100:.2f}% (1X2: {_1x2['1']*100:.2f}%)")
print(f"  X: {sum_X*100:.2f}% (1X2: {_1x2['X']*100:.2f}%)")
print(f"  2: {sum_2*100:.2f}% (1X2: {_1x2['2']*100:.2f}%)")

diff_1 = abs(sum_1 - _1x2['1']) * 100
diff_X = abs(sum_X - _1x2['X']) * 100
diff_2 = abs(sum_2 - _1x2['2']) * 100

if diff_1 < 1 and diff_X < 1 and diff_2 < 1:
    print("✅ Coerenza perfetta (< 1%)!")
else:
    print(f"⚠️ Differenze: 1={diff_1:.2f}%, X={diff_X:.2f}%, 2={diff_2:.2f}%")

# Test 4: Aggiustamenti cumulativi
print("\n\n4. VERIFICA AGGIUSTAMENTI CUMULATIVI")
print("-"*80)

import math
def poisson(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

lh = results['Current']['Expected_Goals']['Home']
la = results['Current']['Expected_Goals']['Away']

gg_calc = results['Current']['GG_NG']['GG']
prob_h_0 = poisson(0, lh)
prob_a_0 = poisson(0, la)
gg_pure = (1 - prob_h_0) * (1 - prob_a_0)

diff_gg = (gg_calc - gg_pure) * 100

print(f"GG: {gg_calc*100:.2f}% (Poisson: {gg_pure*100:.2f}%, diff: {diff_gg:+.2f}%)")

if abs(diff_gg) < 5:
    print("✅ Aggiustamenti entro limiti accettabili!")
else:
    print("⚠️ Aggiustamenti troppo alti!")

# Riepilogo
print("\n\n" + "="*80)
print("RIEPILOGO FINALE")
print("="*80)

issues = []
if not all_spread_ok:
    issues.append("Spread non rispettato")
if abs(sum_exact - 1.0) > 1e-10:
    issues.append("Exact Scores non normalizzati")
if diff_1 >= 1 or diff_X >= 1 or diff_2 >= 1:
    issues.append("Incoerenza 1X2 vs Exact Scores")
if abs(diff_gg) >= 5:
    issues.append("Aggiustamenti cumulativi troppo alti")

if issues:
    print("\n⚠️ PROBLEMI TROVATI:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✅ TUTTI I FIX APPLICATI CORRETTAMENTE!")
    print("   - Spread rispettato")
    print("   - Exact Scores normalizzati (somma = 1.0)")
    print("   - Coerenza tra mercati")
    print("   - Aggiustamenti entro limiti")
    print("\n🚀 Sistema pronto per produzione!")

print("="*80)

