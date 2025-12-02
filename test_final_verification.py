#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test finale per verificare che i flag funzionino correttamente"""

from probability_calculator import AdvancedProbabilityCalculator

print("="*80)
print("TEST FINALE - Verifica Flag Correzioni")
print("="*80)

calc = AdvancedProbabilityCalculator()

# Test caso specifico
spread_curr = -0.75
total_curr = 2.75

results = calc.calculate_all_probabilities(
    -0.5, 2.5,
    spread_curr, total_curr
)

lambda_h = results['Current']['Expected_Goals']['Home']
lambda_a = results['Current']['Expected_Goals']['Away']
gg = results['Current']['GG_NG']['GG']
over25 = results['Current']['Over_Under']['Over 2.5']
over35 = results['Current']['Over_Under']['Over 3.5']

print(f"\nCaso: Spread -0.5 -> {spread_curr}, Total 2.5 -> {total_curr}")
print(f"Total atteso: {lambda_h + lambda_a:.3f}")
print(f"\nRisultati:")
print(f"  GG: {gg*100:.2f}%")
print(f"  Over 2.5: {over25*100:.2f}%")
print(f"  Over 3.5: {over35*100:.2f}%")

# Calcolo Poisson pura per confronto
import math
def poisson(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

prob_h_0 = poisson(0, lambda_h)
prob_a_0 = poisson(0, lambda_a)
gg_pure = (1 - prob_h_0) * (1 - prob_a_0)

over25_pure = 0.0
for h in range(15):
    for a in range(15):
        if h + a > 2:
            over25_pure += poisson(h, lambda_h) * poisson(a, lambda_a)

print(f"\nPoisson pura:")
print(f"  GG: {gg_pure*100:.2f}%")
print(f"  Over 2.5: {over25_pure*100:.2f}%")

print(f"\nDifferenze:")
diff_gg = (gg - gg_pure) * 100
diff_over25 = (over25 - over25_pure) * 100
print(f"  GG: {diff_gg:+.2f}%")
print(f"  Over 2.5: {diff_over25:+.2f}%")

print("\n" + "="*80)
if abs(diff_gg) < 5 and abs(diff_over25) < 5:
    print("SUCCESSO! I flag funzionano correttamente.")
    print("Le differenze sono minime (< 5%), come atteso con solo Dixon-Coles + Karlis-Ntzoufras.")
else:
    print("ATTENZIONE! Le differenze sono ancora alte.")
    print("Potrebbe esserci ancora qualche correzione attiva.")
print("="*80)

