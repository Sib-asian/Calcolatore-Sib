"""
Script per addestrare modelli ML con dati storici
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Aggiungi src al path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.ml_models import MLPredictor
from src.data_collector import DataCollector
from src.models.statistical_models import PoissonModel

HISTORICAL_DIR = BASE_DIR / "data" / "historical"

def load_historical_data():
    """Carica tutti i dati storici"""
    all_matches = []
    
    for csv_file in HISTORICAL_DIR.glob("matches_*.csv"):
        print(f"Caricando {csv_file.name}...")
        df = pd.read_csv(csv_file)
        all_matches.append(df)
    
    if not all_matches:
        print("❌ Nessun dato storico trovato!")
        print("   Esegui prima: python scripts/download_historical_data.py")
        return None
    
    df = pd.concat(all_matches, ignore_index=True)
    print(f"✓ Caricati {len(df)} match totali")
    return df

def create_features_from_match(row, data_collector, poisson_model):
    """Crea features per un match storico"""
    # Qui dovresti avere i team_id, ma nei CSV abbiamo solo nomi
    # Per semplicità, usiamo statistiche medie
    # In produzione, useresti i team_id reali
    
    # Features semplificate per training
    features = [
        1.5,  # home_goals_scored_avg (placeholder)
        1.5,  # home_goals_conceded_avg
        1.5,  # away_goals_scored_avg
        1.5,  # away_goals_conceded_avg
        1.5,  # home_form
        1.5,  # away_form
        0.33, # h2h_home_wins
        0.33, # h2h_draws
        0.33  # h2h_away_wins
    ]
    
    return np.array(features)

def prepare_training_data(df):
    """Prepara dati per training"""
    print("\nPreparazione dati per training...")
    
    # Crea labels per 1X2
    labels_1x2 = []
    for _, row in df.iterrows():
        home_score = row['home_score']
        away_score = row['away_score']
        
        if home_score > away_score:
            labels_1x2.append(0)  # Home win
        elif home_score == away_score:
            labels_1x2.append(1)  # Draw
        else:
            labels_1x2.append(2)  # Away win
    
    # Crea labels per Over/Under
    labels_over_under = []
    for _, row in df.iterrows():
        total_goals = row['home_score'] + row['away_score']
        labels_over_under.append(1 if total_goals > 2.5 else 0)
    
    # Crea labels per BTTS
    labels_btts = []
    for _, row in df.iterrows():
        home_score = row['home_score']
        away_score = row['away_score']
        labels_btts.append(1 if home_score > 0 and away_score > 0 else 0)
    
    # Features semplificate (in produzione, usa DataCollector)
    # Per ora usiamo features basate sui gol
    features = []
    for _, row in df.iterrows():
        feat = [
            row['home_score'] / 2.0,  # Approssimazione
            row['away_score'] / 2.0,
            row['away_score'] / 2.0,
            row['home_score'] / 2.0,
            1.5, 1.5, 0.33, 0.33, 0.33
        ]
        features.append(feat)
    
    X = np.array(features)
    y_1x2 = np.array(labels_1x2)
    y_over_under = np.array(labels_over_under)
    y_btts = np.array(labels_btts)
    
    print(f"✓ Features shape: {X.shape}")
    print(f"✓ Labels 1X2: {len(y_1x2)} (Home: {sum(y_1x2==0)}, Draw: {sum(y_1x2==1)}, Away: {sum(y_1x2==2)})")
    print(f"✓ Labels Over/Under: {len(y_over_under)} (Over: {sum(y_over_under==1)}, Under: {sum(y_over_under==0)})")
    print(f"✓ Labels BTTS: {len(y_btts)} (Yes: {sum(y_btts==1)}, No: {sum(y_btts==0)})")
    
    return X, y_1x2, y_over_under, y_btts

def main():
    """Funzione principale"""
    print("=" * 60)
    print("Training Modelli ML - Calcolatore Sib")
    print("=" * 60)
    
    # Carica dati
    df = load_historical_data()
    if df is None:
        return
    
    if len(df) < 100:
        print(f"⚠️  Solo {len(df)} match disponibili. Consigliati almeno 1000 per training efficace.")
        response = input("   Continuare comunque? (s/n): ")
        if response.lower() != 's':
            return
    
    # Prepara dati
    X, y_1x2, y_over_under, y_btts = prepare_training_data(df)
    
    # Split train/test
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_1x2_train, y_1x2_test = y_1x2[:split_idx], y_1x2[split_idx:]
    y_ou_train, y_ou_test = y_over_under[:split_idx], y_over_under[split_idx:]
    y_btts_train, y_btts_test = y_btts[:split_idx], y_btts[split_idx:]
    
    print(f"\nSplit: {len(X_train)} train, {len(X_test)} test")
    
    # Training
    predictor = MLPredictor()
    
    print("\n" + "=" * 60)
    print("Training modello 1X2...")
    predictor.train_model("1x2", X_train, y_1x2_train)
    
    print("\nTraining modello Over/Under...")
    predictor.train_model("over_under", X_train, y_ou_train)
    
    print("\nTraining modello BTTS...")
    predictor.train_model("btts", X_train, y_btts_train)
    
    print("\n" + "=" * 60)
    print("Training completato!")
    print(f"Modelli salvati in: {BASE_DIR / 'models'}")
    print("=" * 60)
    
    # Validazione base (opzionale)
    print("\nValidazione base...")
    if hasattr(predictor.models.get("1x2"), "score"):
        score_1x2 = predictor.models["1x2"].score(X_test, y_1x2_test)
        score_ou = predictor.models["over_under"].score(X_test, y_ou_test)
        score_btts = predictor.models["btts"].score(X_test, y_btts_test)
        
        print(f"  Accuratezza 1X2: {score_1x2:.2%}")
        print(f"  Accuratezza Over/Under: {score_ou:.2%}")
        print(f"  Accuratezza BTTS: {score_btts:.2%}")

if __name__ == "__main__":
    main()





