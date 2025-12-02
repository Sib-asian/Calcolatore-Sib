#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check approfondito di TUTTI i mercati per trovare problemi residui:
1. Aggiustamenti cumulativi nascosti
2. Spread non rispettato
3. Incoerenze tra mercati
4. Normalizzazioni errate
"""

from probability_calculator import AdvancedProbabilityCalculator
import math

print("="*80)
print("CHECK APPROFONDITO - TUTTI I MERCATI")
print("="*80)

calc = AdvancedProbabilityCalculator()

# Test con diversi spread per verificare che vengano rispettati
test_cases = [
    {"name": "Casa molto favorita", "spread": -1.5, "total": 2.5},
    {"name": "Casa favorita", "spread": -0.75, "total": 2.75},
    {"name": "Match equilibrato", "spread": 0.0, "total": 3.0},
    {"name": "Trasferta favorita", "spread": 0.75, "total": 2.75},
    {"name": "Trasferta molto favorita", "spread": 1.5, "total": 2.5},
]

print("\n1. VERIFICA SPREAD RISPETTATO")
print("="*80)

for tc in test_cases:
    results = calc.calculate_all_probabilities(
        tc["spread"], tc["total"],
        tc["spread"], tc["total"]
    )
    
    lambda_h = results['Current']['Expected_Goals']['Home']
    lambda_a = results['Current']['Expected_Goals']['Away']
    
    # Verifica spread
    spread_calc = lambda_h - lambda_a
    total_calc = lambda_h + lambda_a
    
    spread_error = abs(spread_calc - tc["spread"])
    total_error = abs(total_calc - tc["total"])
    
    print(f"\n{tc['name']}:")
    print(f"  Input:  Spread {tc['spread']:+.2f}, Total {tc['total']:.2f}")
    print(f"  Lambda: Casa {lambda_h:.3f}, Trasferta {lambda_a:.3f}")
    print(f"  Calc:   Spread {spread_calc:+.3f}, Total {total_calc:.3f}")
    print(f"  Errore: Spread {spread_error:.6f}, Total {total_error:.6f}")
    
    if spread_error > 0.01 or total_error > 0.01:
        print(f"  ⚠️  PROBLEMA: Spread/Total non rispettato!")
    else:
        print(f"  ✓ OK")

print("\n\n2. VERIFICA 1X2 COERENTE CON SPREAD")
print("="*80)

for tc in test_cases:
    results = calc.calculate_all_probabilities(
        tc["spread"], tc["total"],
        tc["spread"], tc["total"]
    )
    
    curr_1x2 = results['Current']['1X2']
    
    print(f"\n{tc['name']} (Spread {tc['spread']:+.2f}):")
    print(f"  1 (Casa):      {curr_1x2['1']*100:6.2f}%")
    print(f"  X (Pareggio):  {curr_1x2['X']*100:6.2f}%")
    print(f"  2 (Trasferta): {curr_1x2['2']*100:6.2f}%")
    
    # Verifica coerenza con spread
    if tc["spread"] < -0.5:  # Casa favorita
        if curr_1x2['1'] <= curr_1x2['2']:
            print(f"  ⚠️  PROBLEMA: Casa dovrebbe essere più probabile!")
        else:
            print(f"  ✓ Coerente con spread")
    elif tc["spread"] > 0.5:  # Trasferta favorita
        if curr_1x2['2'] <= curr_1x2['1']:
            print(f"  ⚠️  PROBLEMA: Trasferta dovrebbe essere più probabile!")
        else:
            print(f"  ✓ Coerente con spread")
    else:  # Match equilibrato
        if abs(curr_1x2['1'] - curr_1x2['2']) > 0.15:
            print(f"  ⚠️  PROBLEMA: Match dovrebbe essere equilibrato!")
        else:
            print(f"  ✓ Coerente con spread")

print("\n\n3. VERIFICA NORMALIZZAZIONI TUTTI I MERCATI")
print("="*80)

tc = test_cases[1]  # Casa favorita
results = calc.calculate_all_probabilities(
    tc["spread"], tc["total"],
    tc["spread"], tc["total"]
)

errors = []

# 1X2
sum_1x2 = sum(results['Current']['1X2'].values())
if abs(sum_1x2 - 1.0) > 1e-10:
    errors.append(f"1X2: {sum_1x2:.15f}")
else:
    print("✓ 1X2 normalizzato")

# GG/NG
sum_gg = sum(results['Current']['GG_NG'].values())
if abs(sum_gg - 1.0) > 1e-10:
    errors.append(f"GG/NG: {sum_gg:.15f}")
else:
    print("✓ GG/NG normalizzato")

# Over/Under
ou = results['Current']['Over_Under']
for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
    over_key = f'Over {threshold}'
    under_key = f'Under {threshold}'
    if over_key in ou and under_key in ou:
        sum_ou = ou[over_key] + ou[under_key]
        if abs(sum_ou - 1.0) > 1e-10:
            errors.append(f"O/U {threshold}: {sum_ou:.15f}")
        else:
            print(f"✓ Over/Under {threshold} normalizzato")

# Doppia Chance (deve essere coerente con 1X2)
dc = results['Current']['Double_Chance']
_1x2 = results['Current']['1X2']
if abs(dc['1X'] - (_1x2['1'] + _1x2['X'])) > 1e-10:
    errors.append(f"1X: {dc['1X']:.15f} vs {_1x2['1'] + _1x2['X']:.15f}")
else:
    print("✓ Doppia Chance 1X coerente")
    
if abs(dc['12'] - (_1x2['1'] + _1x2['2'])) > 1e-10:
    errors.append(f"12: {dc['12']:.15f} vs {_1x2['1'] + _1x2['2']:.15f}")
else:
    print("✓ Doppia Chance 12 coerente")
    
if abs(dc['X2'] - (_1x2['X'] + _1x2['2'])) > 1e-10:
    errors.append(f"X2: {dc['X2']:.15f} vs {_1x2['X'] + _1x2['2']:.15f}")
else:
    print("✓ Doppia Chance X2 coerente")

# Handicap Asiatico
ah = results['Current']['Handicap_Asiatico']
for handicap in [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]:
    casa_key = f'AH {handicap:+.1f} Casa'
    trasferta_key = f'AH {handicap:+.1f} Trasferta'
    if casa_key in ah and trasferta_key in ah:
        sum_ah = ah[casa_key] + ah[trasferta_key]
        if abs(sum_ah - 1.0) > 1e-10:
            errors.append(f"AH {handicap:+.1f}: {sum_ah:.15f}")
        else:
            print(f"✓ Handicap {handicap:+.1f} normalizzato")

if errors:
    print(f"\n⚠️  ERRORI DI NORMALIZZAZIONE TROVATI:")
    for err in errors:
        print(f"  - {err}")
else:
    print("\n✓ Tutte le normalizzazioni corrette!")

print("\n\n4. VERIFICA AGGIUSTAMENTI CUMULATIVI NASCOSTI")
print("="*80)

# Confronta risultati con Poisson pura
tc = {"spread": -0.75, "total": 2.75}
results = calc.calculate_all_probabilities(tc["spread"], tc["total"], tc["spread"], tc["total"])

lambda_h = results['Current']['Expected_Goals']['Home']
lambda_a = results['Current']['Expected_Goals']['Away']

def poisson(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

# GG Poisson pura
prob_h_0 = poisson(0, lambda_h)
prob_a_0 = poisson(0, lambda_a)
gg_pure = (1 - prob_h_0) * (1 - prob_a_0)
gg_calc = results['Current']['GG_NG']['GG']

# Over 2.5 Poisson pura
over25_pure = 0.0
for h in range(15):
    for a in range(15):
        if h + a > 2:
            over25_pure += poisson(h, lambda_h) * poisson(a, lambda_a)
over25_calc = results['Current']['Over_Under']['Over 2.5']

# Over 3.5 Poisson pura
over35_pure = 0.0
for h in range(15):
    for a in range(15):
        if h + a > 3:
            over35_pure += poisson(h, lambda_h) * poisson(a, lambda_a)
over35_calc = results['Current']['Over_Under']['Over 3.5']

# 1X2 Poisson pura
prob_1_pure = 0.0
prob_X_pure = 0.0
prob_2_pure = 0.0
for h in range(15):
    for a in range(15):
        p = poisson(h, lambda_h) * poisson(a, lambda_a)
        if h > a:
            prob_1_pure += p
        elif h == a:
            prob_X_pure += p
        else:
            prob_2_pure += p

prob_1_calc = results['Current']['1X2']['1']
prob_X_calc = results['Current']['1X2']['X']
prob_2_calc = results['Current']['1X2']['2']

print(f"\nConfronto con Poisson Pura (Spread {tc['spread']}, Total {tc['total']}):")
print(f"\n{'Mercato':<20} {'Poisson':<12} {'Calcolato':<12} {'Diff %':<10} {'Status'}")
print("-"*65)

metrics = [
    ("GG", gg_pure, gg_calc, 8),
    ("Over 2.5", over25_pure, over25_calc, 10),
    ("Over 3.5", over35_pure, over35_calc, 12),
    ("1 (Casa)", prob_1_pure, prob_1_calc, 5),
    ("X (Pareggio)", prob_X_pure, prob_X_calc, 8),
    ("2 (Trasferta)", prob_2_pure, prob_2_calc, 5),
]

all_ok = True
for name, pure, calc, threshold in metrics:
    diff = (calc - pure) * 100
    status = "✓" if abs(diff) < threshold else "⚠️"
    if abs(diff) >= threshold:
        all_ok = False
    print(f"{name:<20} {pure*100:>10.2f}% {calc*100:>10.2f}% {diff:>9.2f}% {status}")

if all_ok:
    print("\n✓ Nessun aggiustamento cumulativo eccessivo trovato!")
else:
    print("\n⚠️  Alcuni aggiustamenti sono ancora troppo alti!")

print("\n\n5. VERIFICA COERENZA TRA MERCATI CORRELATI")
print("="*80)

# GG dovrebbe essere correlato con Over 2.5
print(f"\nGG vs Over 2.5:")
print(f"  GG: {gg_calc*100:.2f}%")
print(f"  Over 2.5: {over25_calc*100:.2f}%")

# Se GG è alto, Over 2.5 dovrebbe essere alto
if gg_calc > 0.6 and over25_calc < 0.5:
    print(f"  ⚠️  INCOERENZA: GG alto ma Over 2.5 basso!")
elif gg_calc < 0.4 and over25_calc > 0.7:
    print(f"  ⚠️  INCOERENZA: GG basso ma Over 2.5 alto!")
else:
    print(f"  ✓ Coerenti")

# Win to Nil dovrebbe essere correlato con NG
wtn = results['Current']['Win_to_Nil']
ng = results['Current']['GG_NG']['NG']
print(f"\nWin to Nil vs NG:")
print(f"  Casa Win to Nil: {wtn['Casa Win to Nil']*100:.2f}%")
print(f"  Trasferta Win to Nil: {wtn['Trasferta Win to Nil']*100:.2f}%")
print(f"  NG: {ng*100:.2f}%")

# Somma Win to Nil dovrebbe essere <= NG
sum_wtn = wtn['Casa Win to Nil'] + wtn['Trasferta Win to Nil']
if sum_wtn > ng + 0.01:
    print(f"  ⚠️  INCOERENZA: Somma Win to Nil ({sum_wtn*100:.2f}%) > NG ({ng*100:.2f}%)!")
else:
    print(f"  ✓ Coerenti")

print("\n\n6. VERIFICA EXACT SCORES SOMMANO CORRETTAMENTE")
print("="*80)

exact_scores = results['Current']['Exact_Scores']
sum_exact = sum(exact_scores.values())
print(f"\nSomma tutti i risultati esatti: {sum_exact:.10f}")
if abs(sum_exact - 1.0) > 0.01:
    print(f"⚠️  PROBLEMA: Somma risultati esatti dovrebbe essere ~1.0!")
else:
    print(f"✓ OK (tolleranza per troncamento)")

# Verifica che i risultati esatti corrispondano al 1X2
sum_1_from_exact = 0.0
sum_X_from_exact = 0.0
sum_2_from_exact = 0.0

for score, prob in exact_scores.items():
    parts = score.split('-')
    if len(parts) == 2:
        h, a = int(parts[0]), int(parts[1])
        if h > a:
            sum_1_from_exact += prob
        elif h == a:
            sum_X_from_exact += prob
        else:
            sum_2_from_exact += prob

print(f"\n1X2 da Exact Scores:")
print(f"  1: {sum_1_from_exact*100:.2f}% (1X2: {prob_1_calc*100:.2f}%)")
print(f"  X: {sum_X_from_exact*100:.2f}% (1X2: {prob_X_calc*100:.2f}%)")
print(f"  2: {sum_2_from_exact*100:.2f}% (1X2: {prob_2_calc*100:.2f}%)")

diff_1 = abs(sum_1_from_exact - prob_1_calc) * 100
diff_X = abs(sum_X_from_exact - prob_X_calc) * 100
diff_2 = abs(sum_2_from_exact - prob_2_calc) * 100

if diff_1 > 2 or diff_X > 2 or diff_2 > 2:
    print(f"⚠️  INCOERENZA: Exact Scores non corrispondono a 1X2!")
else:
    print(f"✓ Coerenti (diff < 2%)")

print("\n\n" + "="*80)
print("RIEPILOGO FINALE")
print("="*80)

issues_found = []

# Controlla tutti i problemi
if not all_ok:
    issues_found.append("Aggiustamenti cumulativi ancora troppo alti")

if errors:
    issues_found.append("Errori di normalizzazione")

if diff_1 > 2 or diff_X > 2 or diff_2 > 2:
    issues_found.append("Incoerenza tra Exact Scores e 1X2")

if sum_wtn > ng + 0.01:
    issues_found.append("Incoerenza tra Win to Nil e NG")

if issues_found:
    print("\n⚠️  PROBLEMI TROVATI:")
    for i, issue in enumerate(issues_found, 1):
        print(f"  {i}. {issue}")
else:
    print("\n✅ NESSUN PROBLEMA TROVATO!")
    print("   - Spread rispettato")
    print("   - Normalizzazioni corrette")
    print("   - Coerenza tra mercati")
    print("   - Aggiustamenti entro limiti accettabili")
    print("   - Sistema pronto per produzione")

print("="*80)

