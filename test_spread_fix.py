#!/usr/bin/env python3
"""Test fix spread"""
from probability_calculator import AdvancedProbabilityCalculator

calc = AdvancedProbabilityCalculator()
r = calc.calculate_all_probabilities(-0.75, 2.75, -0.75, 2.75)

print("Spread -0.75 (Casa favorita):")
print(f"  1 (Casa): {r['Current']['1X2']['1']*100:.2f}%")
print(f"  X (Pareggio): {r['Current']['1X2']['X']*100:.2f}%")
print(f"  2 (Trasferta): {r['Current']['1X2']['2']*100:.2f}%")

if r['Current']['1X2']['1'] > r['Current']['1X2']['2']:
    print("✓ Casa > Trasferta (CORRETTO)")
else:
    print("⚠️ ERRORE: Trasferta > Casa!")

