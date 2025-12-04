"""
Modelli Machine Learning per predizioni
XGBoost per migliorare accuratezza rispetto ai modelli statistici
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import pickle
from src.config import MODELS_DIR

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost non disponibile. Usa modelli statistici.")

class MLPredictor:
    """Wrapper per modelli ML"""
    
    def __init__(self):
        self.models = {}
        self.models_dir = MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._load_models()
    
    def _load_models(self):
        """Carica modelli ML salvati"""
        model_files = {
            "1x2": "model_1x2.pkl",
            "over_under": "model_over_under.pkl",
            "btts": "model_btts.pkl"
        }
        
        for model_name, filename in model_files.items():
            model_path = self.models_dir / filename
            if model_path.exists():
                try:
                    with open(model_path, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                except Exception as e:
                    print(f"Errore nel caricamento modello {model_name}: {e}")
    
    def _create_features(self, team_stats: Dict, h2h_stats: Dict, 
                        home_team_id: int, away_team_id: int) -> np.ndarray:
        """Crea feature vector per ML"""
        features = [
            team_stats["home"]["goals_scored_avg"],
            team_stats["home"]["goals_conceded_avg"],
            team_stats["away"]["goals_scored_avg"],
            team_stats["away"]["goals_conceded_avg"],
            team_stats["home"]["form_points"] / max(team_stats["home"]["matches_count"], 1),
            team_stats["away"]["form_points"] / max(team_stats["away"]["matches_count"], 1),
            h2h_stats.get("team1_wins", 0) / max(h2h_stats.get("total_matches", 1), 1),
            h2h_stats.get("draws", 0) / max(h2h_stats.get("total_matches", 1), 1),
            h2h_stats.get("team2_wins", 0) / max(h2h_stats.get("total_matches", 1), 1),
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict_1x2(self, features: np.ndarray) -> Optional[Dict[str, float]]:
        """Predice 1X2 con ML"""
        if "1x2" not in self.models or not XGBOOST_AVAILABLE:
            return None
        
        try:
            probs = self.models["1x2"].predict_proba(features)[0]
            return {
                "1": float(probs[0]),
                "X": float(probs[1]),
                "2": float(probs[2])
            }
        except Exception as e:
            print(f"Errore predizione ML 1X2: {e}")
            return None
    
    def predict_over_under(self, features: np.ndarray, threshold: float = 2.5) -> Optional[Dict[str, float]]:
        """Predice Over/Under con ML"""
        if "over_under" not in self.models or not XGBOOST_AVAILABLE:
            return None
        
        try:
            probs = self.models["over_under"].predict_proba(features)[0]
            return {
                "over": float(probs[1]),
                "under": float(probs[0])
            }
        except Exception as e:
            print(f"Errore predizione ML Over/Under: {e}")
            return None
    
    def predict_btts(self, features: np.ndarray) -> Optional[Dict[str, float]]:
        """Predice BTTS con ML"""
        if "btts" not in self.models or not XGBOOST_AVAILABLE:
            return None
        
        try:
            probs = self.models["btts"].predict_proba(features)[0]
            return {
                "yes": float(probs[1]),
                "no": float(probs[0])
            }
        except Exception as e:
            print(f"Errore predizione ML BTTS: {e}")
            return None
    
    def train_model(self, model_name: str, X: np.ndarray, y: np.ndarray):
        """
        Addestra un modello ML
        
        Args:
            model_name: "1x2", "over_under", "btts"
            X: Features (n_samples, n_features)
            y: Labels (n_samples,)
        """
        if not XGBOOST_AVAILABLE:
            print("XGBoost non disponibile per training")
            return
        
        try:
            if model_name == "1x2":
                model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                )
            else:
                model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=4,
                    learning_rate=0.1,
                    random_state=42
                )
            
            model.fit(X, y)
            
            # Salva modello
            model_path = self.models_dir / f"model_{model_name}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            self.models[model_name] = model
            print(f"Modello {model_name} addestrato e salvato")
        
        except Exception as e:
            print(f"Errore nel training modello {model_name}: {e}")





