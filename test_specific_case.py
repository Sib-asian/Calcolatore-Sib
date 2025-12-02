#!/usr/bin/env python3
"""Test caso specifico: Spread -0.5 → -0.75, Total 2.5 → 2.75"""

from probability_calculator import AdvancedProbabilityCalculator

calc = AdvancedProbabilityCalculator()

# Caso specifico: spread -0.5 -> -0.75, total 2.5 -> 2.75
results = calc.calculate_all_probabilities(
    spread_opening=-0.5,
    total_opening=2.5,
    spread_current=-0.75,
    total_current=2.75
)

print('=' * 60)
print('CASO: Spread -0.5 → -0.75, Total 2.5 → 2.75')
print('=' * 60)

# Expected Goals
print('\n📊 EXPECTED GOALS:')
print(f'  Apertura: Casa {results["Opening"]["Expected_Goals"]["Home"]:.3f} - Trasferta {results["Opening"]["Expected_Goals"]["Away"]:.3f}')
print(f'  Corrente: Casa {results["Current"]["Expected_Goals"]["Home"]:.3f} - Trasferta {results["Current"]["Expected_Goals"]["Away"]:.3f}')

# 1X2
print('\n⚽ 1X2 CORRENTE:')
curr_1x2 = results['Current']['1X2']
print(f'  1 (Casa):      {curr_1x2["1"]*100:.2f}%')
print(f'  X (Pareggio):  {curr_1x2["X"]*100:.2f}%')
print(f'  2 (Trasferta): {curr_1x2["2"]*100:.2f}%')

# GG/NG
print('\n🎯 GG/NG CORRENTE:')
curr_gg = results['Current']['GG_NG']
print(f'  GG (Entrambe segnano): {curr_gg["GG"]*100:.2f}%')
print(f'  NG (Almeno una no):    {curr_gg["NG"]*100:.2f}%')

# Over/Under
print('\n📈 OVER/UNDER CORRENTE:')
curr_ou = results['Current']['Over_Under']
print(f'  Over 2.5:  {curr_ou["Over 2.5"]*100:.2f}%')
print(f'  Under 2.5: {curr_ou["Under 2.5"]*100:.2f}%')
print(f'  Over 3.5:  {curr_ou["Over 3.5"]*100:.2f}%')
print(f'  Under 3.5: {curr_ou["Under 3.5"]*100:.2f}%')

# Exact Scores top 10
print('\n🎲 TOP 10 RISULTATI ESATTI (Corrente):')
curr_scores = results['Current']['Exact_Scores']
for i, (score, prob) in enumerate(list(curr_scores.items())[:10], 1):
    print(f'  {i:2d}. {score:5s} → {prob*100:.2f}%')

print('\n' + '=' * 60)
print('ANALISI:')
print('=' * 60)
total_curr = results['Current']['Expected_Goals']['Home'] + results['Current']['Expected_Goals']['Away']
print(f'Total atteso corrente: {total_curr:.3f} gol')
print(f'Spread favorisce: Casa (spread negativo = Casa favorita)')
print(f'\nMovimento mercato:')
print(f'  Spread: -0.5 → -0.75 (Casa ancora più favorita)')
print(f'  Total: 2.5 → 2.75 (più gol attesi)')

# Verifica logica GG + Over
print('\n' + '=' * 60)
print('VERIFICA LOGICA GG + OVER:')
print('=' * 60)
print(f'\nTotal atteso: {total_curr:.3f} gol')
print(f'GG: {curr_gg["GG"]*100:.2f}% (entrambe segnano)')
print(f'Over 2.5: {curr_ou["Over 2.5"]*100:.2f}% (almeno 3 gol)')
print(f'Over 3.5: {curr_ou["Over 3.5"]*100:.2f}% (almeno 4 gol)')

print('\n🔍 INTERPRETAZIONE:')
if total_curr >= 2.75:
    print(f'✓ Total atteso {total_curr:.2f} > 2.75 → Over 2.5 e 3.5 hanno senso')
else:
    print(f'⚠ Total atteso {total_curr:.2f} < 2.75 → percentuali Over potrebbero essere alte')

if curr_gg["GG"] > 0.6:
    print(f'✓ GG {curr_gg["GG"]*100:.1f}% > 60% → entrambe segnano è probabile')
else:
    print(f'⚠ GG {curr_gg["GG"]*100:.1f}% < 60% → potrebbe essere basso per un consiglio')

# Calcolo manuale per verifica
print('\n' + '=' * 60)
print('CALCOLO MANUALE SEMPLIFICATO (Poisson pura):')
print('=' * 60)
import math

lambda_h = results['Current']['Expected_Goals']['Home']
lambda_a = results['Current']['Expected_Goals']['Away']

def poisson(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

# GG manuale (almeno 1 gol per parte)
prob_casa_0 = poisson(0, lambda_h)
prob_trasferta_0 = poisson(0, lambda_a)
gg_manual = (1 - prob_casa_0) * (1 - prob_trasferta_0)

print(f'\nPoisson pura (senza correzioni):')
print(f'  P(Casa = 0) = {prob_casa_0*100:.2f}%')
print(f'  P(Trasferta = 0) = {prob_trasferta_0*100:.2f}%')
print(f'  GG manuale = (1 - P(Casa=0)) × (1 - P(Trasferta=0)) = {gg_manual*100:.2f}%')
print(f'  GG calcolatore = {curr_gg["GG"]*100:.2f}%')
print(f'  Differenza = {abs(gg_manual - curr_gg["GG"])*100:.2f}% (dovuta a Dixon-Coles e correzioni)')

