#!/usr/bin/env python3
"""
Test con correzioni moderate per verificare se le percentuali sono più realistiche.

Confronta:
- Versione attuale (tutte le correzioni attive)
- Versione moderata (solo Dixon-Coles + overdispersion leggera)
- Poisson pura (baseline)
"""

from probability_calculator import AdvancedProbabilityCalculator
import math

# Caso specifico: spread -0.5 -> -0.75, total 2.5 -> 2.75
spread_opening = -0.5
total_opening = 2.5
spread_current = -0.75
total_current = 2.75

print('=' * 70)
print('CONFRONTO: Correzioni Attuali vs Moderate vs Poisson Pura')
print('=' * 70)
print(f'\nCaso: Spread {spread_opening} → {spread_current}, Total {total_opening} → {total_current}')

# 1. Versione attuale (tutte le correzioni)
print('\n' + '=' * 70)
print('1️⃣  VERSIONE ATTUALE (Tutte le correzioni attive)')
print('=' * 70)

calc_full = AdvancedProbabilityCalculator()
results_full = calc_full.calculate_all_probabilities(
    spread_opening, total_opening,
    spread_current, total_current
)

lambda_h_full = results_full['Current']['Expected_Goals']['Home']
lambda_a_full = results_full['Current']['Expected_Goals']['Away']
gg_full = results_full['Current']['GG_NG']['GG']
over25_full = results_full['Current']['Over_Under']['Over 2.5']
over35_full = results_full['Current']['Over_Under']['Over 3.5']

print(f'\nExpected Goals: Casa {lambda_h_full:.3f} - Trasferta {lambda_a_full:.3f}')
print(f'Total atteso: {lambda_h_full + lambda_a_full:.3f}')
print(f'\nGG: {gg_full*100:.2f}%')
print(f'Over 2.5: {over25_full*100:.2f}%')
print(f'Over 3.5: {over35_full*100:.2f}%')

# 2. Versione moderata (solo Dixon-Coles + overdispersion leggera)
print('\n' + '=' * 70)
print('2️⃣  VERSIONE MODERATA (Solo Dixon-Coles + Overdispersion leggera)')
print('=' * 70)

calc_moderate = AdvancedProbabilityCalculator()
# Disabilita correzioni aggressive
calc_moderate.use_ensemble_methods = False
calc_moderate.use_karlis_ntzoufras = False
calc_moderate.use_skewness_correction = False
calc_moderate.use_bias_correction = False
calc_moderate.use_market_efficiency = False
calc_moderate.use_dynamic_calibration = False
calc_moderate.use_bayesian_smoothing = False
calc_moderate.use_home_advantage_advanced = False
calc_moderate.use_negative_binomial = False
calc_moderate.use_zero_inflated = False
calc_moderate.use_lambda_regression = False
calc_moderate.use_copula_models = False
calc_moderate.use_variance_modeling = False
calc_moderate.use_market_consistency = False
calc_moderate.use_conditional_probabilities = False
calc_moderate.use_volatility_adjustment = False
# Mantieni solo Dixon-Coles base e overdispersion leggera
calc_moderate.overdispersion_factor_base = 1.05  # Ridotto da 1.1

results_moderate = calc_moderate.calculate_all_probabilities(
    spread_opening, total_opening,
    spread_current, total_current
)

lambda_h_mod = results_moderate['Current']['Expected_Goals']['Home']
lambda_a_mod = results_moderate['Current']['Expected_Goals']['Away']
gg_mod = results_moderate['Current']['GG_NG']['GG']
over25_mod = results_moderate['Current']['Over_Under']['Over 2.5']
over35_mod = results_moderate['Current']['Over_Under']['Over 3.5']

print(f'\nExpected Goals: Casa {lambda_h_mod:.3f} - Trasferta {lambda_a_mod:.3f}')
print(f'Total atteso: {lambda_h_mod + lambda_a_mod:.3f}')
print(f'\nGG: {gg_mod*100:.2f}%')
print(f'Over 2.5: {over25_mod*100:.2f}%')
print(f'Over 3.5: {over35_mod*100:.2f}%')

# 3. Poisson pura (baseline)
print('\n' + '=' * 70)
print('3️⃣  POISSON PURA (Baseline senza correzioni)')
print('=' * 70)

# Calcolo manuale Poisson pura
lambda_h_pure = (total_current - spread_current) * 0.5
lambda_a_pure = (total_current + spread_current) * 0.5

def poisson(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

# GG Poisson pura
prob_h_0 = poisson(0, lambda_h_pure)
prob_a_0 = poisson(0, lambda_a_pure)
gg_pure = (1 - prob_h_0) * (1 - prob_a_0)

# Over 2.5 Poisson pura (somma di tutte le combinazioni con total > 2)
over25_pure = 0.0
for h in range(15):
    for a in range(15):
        if h + a > 2:
            over25_pure += poisson(h, lambda_h_pure) * poisson(a, lambda_a_pure)

# Over 3.5 Poisson pura
over35_pure = 0.0
for h in range(15):
    for a in range(15):
        if h + a > 3:
            over35_pure += poisson(h, lambda_h_pure) * poisson(a, lambda_a_pure)

print(f'\nExpected Goals: Casa {lambda_h_pure:.3f} - Trasferta {lambda_a_pure:.3f}')
print(f'Total atteso: {lambda_h_pure + lambda_a_pure:.3f}')
print(f'\nGG: {gg_pure*100:.2f}%')
print(f'Over 2.5: {over25_pure*100:.2f}%')
print(f'Over 3.5: {over35_pure*100:.2f}%')

# Confronto finale
print('\n' + '=' * 70)
print('📊 CONFRONTO FINALE')
print('=' * 70)

print(f'\n{"Metrica":<20} {"Attuale":<15} {"Moderata":<15} {"Poisson Pura":<15} {"Differenza":<15}')
print('-' * 85)
print(f'{"Total atteso":<20} {lambda_h_full + lambda_a_full:<15.3f} {lambda_h_mod + lambda_a_mod:<15.3f} {lambda_h_pure + lambda_a_pure:<15.3f} {"":<15}')
print(f'{"GG %":<20} {gg_full*100:<15.2f} {gg_mod*100:<15.2f} {gg_pure*100:<15.2f} {(gg_full - gg_pure)*100:+.2f}%')
print(f'{"Over 2.5 %":<20} {over25_full*100:<15.2f} {over25_mod*100:<15.2f} {over25_pure*100:<15.2f} {(over25_full - over25_pure)*100:+.2f}%')
print(f'{"Over 3.5 %":<20} {over35_full*100:<15.2f} {over35_mod*100:<15.2f} {over35_pure*100:<15.2f} {(over35_full - over35_pure)*100:+.2f}%')

print('\n' + '=' * 70)
print('🔍 ANALISI')
print('=' * 70)

# Analisi GG
gg_diff = (gg_full - gg_pure) * 100
if abs(gg_diff) > 10:
    print(f'\n⚠️  GG: Differenza {gg_diff:+.1f}% è TROPPO ALTA (dovrebbe essere < 5%)')
else:
    print(f'\n✓ GG: Differenza {gg_diff:+.1f}% è accettabile')

# Analisi Over 2.5
over25_diff = (over25_full - over25_pure) * 100
if abs(over25_diff) > 10:
    print(f'⚠️  Over 2.5: Differenza {over25_diff:+.1f}% è TROPPO ALTA (dovrebbe essere < 8%)')
else:
    print(f'✓ Over 2.5: Differenza {over25_diff:+.1f}% è accettabile')

# Analisi Over 3.5
over35_diff = (over35_full - over35_pure) * 100
if abs(over35_diff) > 15:
    print(f'⚠️  Over 3.5: Differenza {over35_diff:+.1f}% è TROPPO ALTA (dovrebbe essere < 12%)')
else:
    print(f'✓ Over 3.5: Differenza {over35_diff:+.1f}% è accettabile')

# Raccomandazione
print('\n' + '=' * 70)
print('💡 RACCOMANDAZIONE')
print('=' * 70)

if abs(gg_diff) > 10 or abs(over25_diff) > 10 or abs(over35_diff) > 15:
    print('\n🚨 Le correzioni attuali stanno SOVRACORREGGENDO i risultati.')
    print('   Raccomando di usare la versione MODERATA per risultati più realistici.')
    print('\n   Modifiche consigliate:')
    print('   - Disabilitare ensemble (use_ensemble_methods = False)')
    print('   - Ridurre overdispersion_factor_base da 1.1 a 1.05')
    print('   - Disabilitare correzioni ridondanti (Karlis-Ntzoufras, Bayesian smoothing, ecc.)')
else:
    print('\n✓ Le correzioni attuali sono accettabili.')
    print('  I risultati sono sufficientemente vicini alla Poisson pura.')

