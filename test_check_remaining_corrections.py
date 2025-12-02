#!/usr/bin/env python3
"""
Verifica se ci sono ancora correzioni cumulative attive nel core.
"""

from probability_calculator import AdvancedProbabilityCalculator

calc = AdvancedProbabilityCalculator()

print("="*80)
print("🔍 VERIFICA CORREZIONI ATTIVE NEL CORE")
print("="*80)

print("\n📋 Flag Correzioni:")
print(f"  use_ensemble_methods:           {calc.use_ensemble_methods}")
print(f"  use_overdispersion_correction:  {calc.use_overdispersion_correction}")
print(f"  use_skewness_correction:        {calc.use_skewness_correction}")
print(f"  use_karlis_ntzoufras:           {calc.use_karlis_ntzoufras}")
print(f"  use_bias_correction:            {calc.use_bias_correction}")
print(f"  use_market_efficiency:          {calc.use_market_efficiency}")
print(f"  use_dynamic_calibration:        {calc.use_dynamic_calibration}")
print(f"  use_bayesian_smoothing:         {calc.use_bayesian_smoothing}")
print(f"  use_home_advantage_advanced:    {calc.use_home_advantage_advanced}")
print(f"  use_negative_binomial:          {calc.use_negative_binomial}")
print(f"  use_zero_inflated:              {calc.use_zero_inflated}")
print(f"  use_lambda_regression:          {calc.use_lambda_regression}")
print(f"  use_copula_models:              {calc.use_copula_models}")
print(f"  use_variance_modeling:          {calc.use_variance_modeling}")

print("\n" + "="*80)
print("⚠️  PROBLEMA TROVATO!")
print("="*80)

print("""
Nel metodo _exact_score_probability_core(), le seguenti correzioni vengono
SEMPRE applicate, INDIPENDENTEMENTE dai flag:

1. lambda_regression_adjustment()      <- SEMPRE chiamata (riga 1508)
2. dynamic_calibration()                <- SEMPRE chiamata (riga 1511)
3. home_advantage_advanced()            <- SEMPRE chiamata (riga 1512)
4. negative_binomial (con if)           <- Controllata da flag ✓
5. zero_inflated_adjustment()           <- SEMPRE chiamata (riga 1539-1542)
6. dixon_coles_adjustment()             <- SEMPRE chiamata (riga 1545)
7. karlis_ntzoufras_correction()        <- SEMPRE chiamata (riga 1548)
8. get_skewness_correction()            <- SEMPRE chiamata (riga 1552-1554)
9. get_overdispersion_factor()          <- SEMPRE chiamata (riga 1557-1559)
10. get_bias_correction()               <- SEMPRE chiamata (riga 1562)
11. market_efficiency_adjustment()      <- SEMPRE chiamata (riga 1565)
12. copula_correlation_adjustment()     <- SEMPRE chiamata (riga 1568)
13. variance_modeling_advanced()        <- SEMPRE chiamata (riga 1571)
14. bayesian_smoothing()                <- SEMPRE chiamata (riga 1590)

TOTALE: 14 correzioni applicate SEMPRE, anche se i flag sono False!

Questo significa che i flag in __init__() NON controllano queste correzioni.
Sono solo "documentazione" ma non hanno effetto pratico.
""")

print("\n" + "="*80)
print("🔧 SOLUZIONE NECESSARIA")
print("="*80)

print("""
Dobbiamo modificare _exact_score_probability_core() per rispettare i flag:

1. Aggiungere if self.use_lambda_regression prima di lambda_regression_adjustment()
2. Aggiungere if self.use_dynamic_calibration prima di dynamic_calibration()
3. Aggiungere if self.use_home_advantage_advanced prima di home_advantage_advanced()
4. Aggiungere if self.use_zero_inflated prima di zero_inflated_adjustment()
5. Aggiungere if self.use_skewness_correction prima di get_skewness_correction()
6. Aggiungere if self.use_bias_correction prima di get_bias_correction()
7. Aggiungere if self.use_market_efficiency prima di market_efficiency_adjustment()
8. Aggiungere if self.use_copula_models prima di copula_correlation_adjustment()
9. Aggiungere if self.use_variance_modeling prima di variance_modeling_advanced()
10. Aggiungere if self.use_bayesian_smoothing prima di bayesian_smoothing()

Dixon-Coles e Karlis-Ntzoufras devono rimanere SEMPRE attivi (sono fondamentali).
Overdispersion deve rimanere SEMPRE attivo (è leggero e necessario).
""")

print("\n⚠️  Senza questo fix, il sistema sta ancora applicando TUTTE le correzioni!")
print("    I flag False in __init__() non hanno alcun effetto pratico.\n")

