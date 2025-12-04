"""
Generatore di pronostici completo
Combina modelli statistici e ML per output finale
"""
from typing import Dict, Tuple
from src.models.statistical_models import PoissonModel
from src.models.ml_models import MLPredictor
from src.data_collector import DataCollector

class PredictionGenerator:
    """Genera pronostici completi combinando tutti i modelli"""
    
    def __init__(self):
        self.poisson_model = PoissonModel()
        self.ml_predictor = MLPredictor()
        self.data_collector = DataCollector()
    
    def generate_prediction(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Genera pronostico completo per una partita
        
        Args:
            home_team: Dict con info squadra casa
            away_team: Dict con info squadra trasferta
        
        Returns:
            Dict completo con tutti i pronostici
        """
        # Raccogli statistiche
        home_stats = self.data_collector.calculate_team_stats(home_team["id"], is_home=True)
        away_stats = self.data_collector.calculate_team_stats(away_team["id"], is_home=False)
        
        h2h_stats = self.data_collector.calculate_h2h_stats(home_team["id"], away_team["id"])
        
        # Calcola gol attesi con Poisson
        home_goals_exp, away_goals_exp = self.poisson_model.predict_goals(
            home_attack=home_stats["goals_scored_avg"],
            away_attack=away_stats["goals_scored_avg"],
            home_defense=home_stats["goals_conceded_avg"],
            away_defense=away_stats["goals_conceded_avg"]
        )
        
        # Predizioni statistiche
        stat_1x2 = self.poisson_model.predict_1x2(home_goals_exp, away_goals_exp)
        stat_over_under = self.poisson_model.predict_over_under(home_goals_exp, away_goals_exp)
        stat_btts = self.poisson_model.predict_btts(home_goals_exp, away_goals_exp)
        stat_ht = self.poisson_model.predict_ht(home_goals_exp, away_goals_exp)
        stat_ht_ft = self.poisson_model.predict_ht_ft(home_goals_exp, away_goals_exp)
        stat_exact_goals = self.poisson_model.predict_exact_goals(home_goals_exp, away_goals_exp)
        
        # Predizioni ML (se disponibili)
        team_stats_dict = {
            "home": home_stats,
            "away": away_stats
        }
        features = self.ml_predictor._create_features(
            team_stats_dict, h2h_stats, home_team["id"], away_team["id"]
        )
        
        ml_1x2 = self.ml_predictor.predict_1x2(features)
        ml_over_under = self.ml_predictor.predict_over_under(features)
        ml_btts = self.ml_predictor.predict_btts(features)
        
        # Combina predizioni statistiche e ML (media pesata)
        final_1x2 = self._combine_predictions(stat_1x2, ml_1x2, ml_weight=0.3)
        final_over_under = self._combine_predictions(stat_over_under, ml_over_under, ml_weight=0.3)
        final_btts = self._combine_predictions(stat_btts, ml_btts, ml_weight=0.3)
        
        # Calcola confidence scores
        confidence_1x2 = self._calculate_confidence(final_1x2, home_stats, away_stats, h2h_stats)
        confidence_over_under = self._calculate_confidence(final_over_under, home_stats, away_stats, h2h_stats)
        confidence_btts = self._calculate_confidence(final_btts, home_stats, away_stats, h2h_stats)
        
        # Prepara output
        prediction = {
            "match": {
                "home_team": home_team["name"],
                "away_team": away_team["name"],
                "league": home_team.get("league", "Unknown")
            },
            "expected_goals": {
                "home": round(home_goals_exp, 2),
                "away": round(away_goals_exp, 2),
                "total": round(home_goals_exp + away_goals_exp, 2)
            },
            "1x2": {
                "1": round(final_1x2["1"] * 100, 1),
                "X": round(final_1x2["X"] * 100, 1),
                "2": round(final_1x2["2"] * 100, 1),
                "confidence": confidence_1x2
            },
            "over_under": {
                "over_2.5": round(final_over_under["over"] * 100, 1),
                "under_2.5": round(final_over_under["under"] * 100, 1),
                "confidence": confidence_over_under
            },
            "btts": {
                "yes": round(final_btts["yes"] * 100, 1),
                "no": round(final_btts["no"] * 100, 1),
                "confidence": confidence_btts
            },
            "half_time": {
                "1": round(stat_ht["1"] * 100, 1),
                "X": round(stat_ht["X"] * 100, 1),
                "2": round(stat_ht["2"] * 100, 1)
            },
            "ht_ft": {
                "most_likely": max(stat_ht_ft.items(), key=lambda x: x[1]),
                "all_combinations": {k: round(v * 100, 1) for k, v in stat_ht_ft.items()}
            },
            "exact_goals": {
                k: round(v * 100, 1) for k, v in sorted(stat_exact_goals.items(), 
                                                         key=lambda x: x[1], reverse=True)[:5]
            },
            "stats": {
                "home": home_stats,
                "away": away_stats,
                "h2h": h2h_stats
            }
        }
        
        return prediction
    
    def _combine_predictions(self, stat_pred: Dict, ml_pred: Optional[Dict], 
                            ml_weight: float = 0.3) -> Dict:
        """Combina predizioni statistiche e ML"""
        if ml_pred is None:
            return stat_pred
        
        combined = {}
        for key in stat_pred.keys():
            combined[key] = (1 - ml_weight) * stat_pred[key] + ml_weight * ml_pred.get(key, stat_pred[key])
        
        # Normalizza
        total = sum(combined.values())
        if total > 0:
            combined = {k: v/total for k, v in combined.items()}
        
        return combined
    
    def _calculate_confidence(self, prediction: Dict, home_stats: Dict, 
                             away_stats: Dict, h2h_stats: Dict) -> int:
        """
        Calcola confidence score (1-5 stelle)
        Basato su:
        - Qualità dati disponibili
        - Coerenza statistiche
        - Numero match storici
        """
        confidence = 3  # Base
        
        # Più match = più confidence
        if home_stats["matches_count"] >= 8 and away_stats["matches_count"] >= 8:
            confidence += 1
        
        # H2H disponibili
        if h2h_stats.get("total_matches", 0) >= 3:
            confidence += 1
        
        # Dati completi
        if all([home_stats["goals_scored_avg"] > 0, away_stats["goals_scored_avg"] > 0]):
            confidence += 1
        
        # Limita a 5
        return min(5, confidence)
    
    def format_output(self, prediction: Dict) -> str:
        """Formatta output per visualizzazione"""
        output = []
        output.append("=" * 60)
        output.append(f"PRONOSTICO: {prediction['match']['home_team']} vs {prediction['match']['away_team']}")
        output.append(f"Lega: {prediction['match']['league']}")
        output.append("=" * 60)
        output.append("")
        
        # Gol attesi
        output.append("📊 GOL ATTESI")
        output.append(f"  Casa: {prediction['expected_goals']['home']}")
        output.append(f"  Trasferta: {prediction['expected_goals']['away']}")
        output.append(f"  Totale: {prediction['expected_goals']['total']}")
        output.append("")
        
        # 1X2
        output.append("⚽ RISULTATO FINALE (1X2)")
        conf_stars = "⭐" * prediction['1x2']['confidence']
        output.append(f"  1 ({prediction['match']['home_team']}): {prediction['1x2']['1']}% | Confidence: {conf_stars}")
        output.append(f"  X (Pareggio): {prediction['1x2']['X']}% | Confidence: {conf_stars}")
        output.append(f"  2 ({prediction['match']['away_team']}): {prediction['1x2']['2']}% | Confidence: {conf_stars}")
        output.append("")
        
        # Over/Under
        output.append("📈 OVER/UNDER 2.5")
        conf_stars = "⭐" * prediction['over_under']['confidence']
        output.append(f"  Over 2.5: {prediction['over_under']['over_2.5']}% | Confidence: {conf_stars}")
        output.append(f"  Under 2.5: {prediction['over_under']['under_2.5']}% | Confidence: {conf_stars}")
        output.append("")
        
        # BTTS
        output.append("✅ BTTS (Both Teams To Score)")
        conf_stars = "⭐" * prediction['btts']['confidence']
        output.append(f"  Sì: {prediction['btts']['yes']}% | Confidence: {conf_stars}")
        output.append(f"  No: {prediction['btts']['no']}% | Confidence: {conf_stars}")
        output.append("")
        
        # HT
        output.append("⏱️ PRIMO TEMPO (HT)")
        output.append(f"  1: {prediction['half_time']['1']}%")
        output.append(f"  X: {prediction['half_time']['X']}%")
        output.append(f"  2: {prediction['half_time']['2']}%")
        output.append("")
        
        # HT/FT
        output.append("🔄 HT/FT (Più probabili)")
        ht_ft_sorted = sorted(prediction['ht_ft']['all_combinations'].items(), 
                             key=lambda x: x[1], reverse=True)[:3]
        for combo, prob in ht_ft_sorted:
            output.append(f"  {combo}: {prob}%")
        output.append("")
        
        # Gol esatti
        output.append("🎯 GOL TOTALI (Più probabili)")
        for goals, prob in list(prediction['exact_goals'].items())[:3]:
            output.append(f"  {goals} gol: {prob}%")
        output.append("")
        
        output.append("=" * 60)
        
        return "\n".join(output)





