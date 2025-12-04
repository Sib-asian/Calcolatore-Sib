# 📖 Esempi di Utilizzo - Calcolatore Sib

## 🚀 Uso Base

### Pronostico Semplice
```bash
python src/main.py "Juventus vs Inter"
```

### Pronostico con Varianti Nome
```bash
# Funziona anche con varianti
python src/main.py "Juve vs Inter Milan"
python src/main.py "Real Madrid - Barcelona"
python src/main.py "Manchester United vs Liverpool"
```

## 🔧 Uso Programmato

### Esempio Python
```python
from src.team_identifier import TeamIdentifier
from src.prediction_generator import PredictionGenerator

# Identifica squadre
identifier = TeamIdentifier()
home_team, away_team = identifier.parse_match_input("Juventus vs Inter")

# Genera pronostico
generator = PredictionGenerator()
prediction = generator.generate_prediction(home_team, away_team)

# Accedi ai risultati
print(f"Probabilità vittoria casa: {prediction['1x2']['1']}%")
print(f"Confidence: {prediction['1x2']['confidence']} stelle")
```

### Esempio con Dati Personalizzati
```python
from src.data_collector import DataCollector
from src.models.statistical_models import PoissonModel

# Raccogli statistiche
collector = DataCollector()
home_stats = collector.calculate_team_stats(109, is_home=True)  # ID Juventus
away_stats = collector.calculate_team_stats(108, is_home=False)  # ID Inter

# Calcola gol attesi
poisson = PoissonModel()
home_exp, away_exp = poisson.predict_goals(
    home_attack=home_stats["goals_scored_avg"],
    away_attack=away_stats["goals_scored_avg"],
    home_defense=home_stats["goals_conceded_avg"],
    away_defense=away_stats["goals_conceded_avg"]
)

print(f"Gol attesi: Casa {home_exp:.2f}, Trasferta {away_exp:.2f}")
```

## 📊 Output Personalizzato

### Solo 1X2
```python
prediction = generator.generate_prediction(home_team, away_team)
print(f"1: {prediction['1x2']['1']}%")
print(f"X: {prediction['1x2']['X']}%")
print(f"2: {prediction['1x2']['2']}%")
```

### Solo Over/Under
```python
print(f"Over 2.5: {prediction['over_under']['over_2.5']}%")
print(f"Under 2.5: {prediction['over_under']['under_2.5']}%")
```

### Statistiche Dettagliate
```python
stats = prediction['stats']
print(f"Form casa (ultimi 5): {stats['home']['form_points']} punti")
print(f"H2H: {stats['h2h']['team1_wins']}-{stats['h2h']['draws']}-{stats['h2h']['team2_wins']}")
```

## 🔄 Batch Processing

### Analizza Multiple Partite
```python
matches = [
    "Juventus vs Inter",
    "Milan vs Napoli",
    "Roma vs Lazio"
]

for match in matches:
    try:
        home, away = identifier.parse_match_input(match)
        pred = generator.generate_prediction(home, away)
        print(f"\n{match}: {pred['1x2']['1']:.1f}% - {pred['1x2']['X']:.1f}% - {pred['1x2']['2']:.1f}%")
    except Exception as e:
        print(f"Errore {match}: {e}")
```

## 📈 Training Personalizzato

### Addestra con Tuoi Dati
```python
from src.models.ml_models import MLPredictor
import numpy as np

# Prepara features e labels
X = np.array([[features...]])  # Tua matrice features
y = np.array([0, 1, 2])  # Labels: 0=home, 1=draw, 2=away

# Addestra
predictor = MLPredictor()
predictor.train_model("1x2", X, y)
```

## 🎯 Filtraggio per Confidence

### Solo Pronostici ad Alta Confidence
```python
prediction = generator.generate_prediction(home_team, away_team)

# Filtra solo pronostici con confidence >= 4
if prediction['1x2']['confidence'] >= 4:
    print("Pronostico ad alta confidence!")
    print(prediction)
```

## 📝 Export Risultati

### Salva in JSON
```python
import json

prediction = generator.generate_prediction(home_team, away_team)
with open('pronostico.json', 'w') as f:
    json.dump(prediction, f, indent=2, default=str)
```

### Salva in CSV
```python
import pandas as pd

predictions = []
# ... genera multiple predizioni ...

df = pd.DataFrame(predictions)
df.to_csv('pronostici.csv', index=False)
```





