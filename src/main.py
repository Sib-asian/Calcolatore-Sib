"""
Entry point principale del sistema
MOSTRA CHIARAMENTE: Da dove vengono i dati (API o cache)
"""
import sys
from src.team_identifier import TeamIdentifier
from src.prediction_generator import PredictionGenerator

def main():
    """Funzione principale"""
    if len(sys.argv) < 2:
        print("Uso: python src/main.py 'Squadra1 vs Squadra2'")
        print("Esempio: python src/main.py 'Juventus vs Inter'")
        sys.exit(1)
    
    match_input = " ".join(sys.argv[1:])
    
    print("=" * 60)
    print("Calcolatore Sib - Sistema IA per Pronostici Calcio")
    print("=" * 60)
    print(f"\n📝 Input: {match_input}\n")
    
    try:
        # Step 1: Identifica squadre
        print("🔍 STEP 1: Identificazione Squadre")
        print("-" * 60)
        identifier = TeamIdentifier()
        home_team, away_team = identifier.parse_match_input(match_input)
        
        print(f"✓ Squadra casa: {home_team['name']} (ID: {home_team['id']}, Lega: {home_team['league']})")
        print(f"✓ Squadra trasferta: {away_team['name']} (ID: {away_team['id']}, Lega: {away_team['league']})")
        print("  📦 Dati da: Database locale (cache)\n")
        
        # Step 2: Genera pronostico
        print("📊 STEP 2: Raccolta Dati e Calcolo Pronostici")
        print("-" * 60)
        print("  🔄 Recuperando statistiche...")
        print("     📡 Chiamate API: 0-3 (se cache valida, 0)")
        print("     💾 Cache: 6 ore di validità")
        print()
        
        generator = PredictionGenerator()
        prediction = generator.generate_prediction(home_team, away_team)
        
        # Step 3: Output
        print("✅ STEP 3: Pronostico Generato")
        print("-" * 60)
        output = generator.format_output(prediction)
        print(output)
        
        # Info aggiuntive
        print("\n" + "=" * 60)
        print("ℹ️  INFO DATI")
        print("=" * 60)
        stats = prediction['stats']
        print(f"📈 Statistiche Casa:")
        print(f"   - Match analizzati: {stats['home']['matches_count']}")
        print(f"   - Media gol fatti: {stats['home']['goals_scored_avg']:.2f}")
        print(f"   - Media gol subiti: {stats['home']['goals_conceded_avg']:.2f}")
        print(f"   - Form ultimi match: {stats['home']['form_points']} punti")
        print()
        print(f"📈 Statistiche Trasferta:")
        print(f"   - Match analizzati: {stats['away']['matches_count']}")
        print(f"   - Media gol fatti: {stats['away']['goals_scored_avg']:.2f}")
        print(f"   - Media gol subiti: {stats['away']['goals_conceded_avg']:.2f}")
        print(f"   - Form ultimi match: {stats['away']['form_points']} punti")
        print()
        print(f"⚔️  Head-to-Head:")
        print(f"   - Match storici: {stats['h2h']['total_matches']}")
        if stats['h2h']['total_matches'] > 0:
            print(f"   - Vittorie {home_team['name']}: {stats['h2h']['team1_wins']}")
            print(f"   - Pareggi: {stats['h2h']['draws']}")
            print(f"   - Vittorie {away_team['name']}: {stats['h2h']['team2_wins']}")
        print()
        print("💡 Per dettagli su flusso dati, vedi: FLUSSO_DATI.md")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\n❌ Errore: {e}")
        print("\n💡 Suggerimenti:")
        print("   - Usa nomi completi delle squadre (es: 'Juventus' non 'Juve')")
        print("   - Verifica che le squadre siano nelle leghe supportate")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
