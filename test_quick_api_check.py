"""
Quick API Check
Test rapido per verificare che l'API funzioni correttamente
"""

from api_football_client import get_api_client
from probability_calculator import AdvancedProbabilityCalculator

def test_api_connection():
    """Test connessione API"""
    print("\n" + "="*60)
    print("  TEST 1: Connessione API")
    print("="*60)
    
    try:
        client = get_api_client()
        print("✅ Client API inizializzato")
        
        # Test search squadra famosa
        print("\n🔍 Cerco 'Inter'...")
        team = client.search_team("Inter")
        
        if team:
            print(f"✅ Squadra trovata: {team['team_name']} (ID: {team['team_id']})")
            return True
        else:
            print("❌ Squadra non trovata")
            return False
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False


def test_team_stats():
    """Test recupero statistiche"""
    print("\n" + "="*60)
    print("  TEST 2: Recupero Statistiche")
    print("="*60)
    
    try:
        client = get_api_client()
        
        print("\n📊 Carico stats Inter (casa)...")
        stats = client.get_team_stats("Inter", venue="home")
        
        if stats:
            print(f"\n✅ Stats caricate per: {stats['team_name']}")
            print(f"   └ Ultimi 5: {''.join(stats['results'])}")
            print(f"   └ Media gol fatti: {stats['goals_scored_avg']:.1f}")
            print(f"   └ Media gol subiti: {stats['goals_conceded_avg']:.1f}")
            print(f"   └ Forma: {stats['form_factor']*100:.0f}%")
            print(f"   └ Variance: {stats['variance']:.2f}")
            return True
        else:
            print("❌ Nessuna statistica recuperata")
            return False
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False


def test_full_calculation():
    """Test calcolo completo con API"""
    print("\n" + "="*60)
    print("  TEST 3: Calcolo Completo con API")
    print("="*60)
    
    try:
        client = get_api_client()
        calc = AdvancedProbabilityCalculator()
        
        print("\n📊 Carico stats...")
        stats_home = client.get_team_stats("Inter", venue="home")
        stats_away = client.get_team_stats("Juventus", venue="away")
        
        if not stats_home or not stats_away:
            print("⚠️ Una o entrambe le squadre non trovate")
            return False
        
        print(f"✅ {stats_home['team_name']} vs {stats_away['team_name']}")
        
        print("\n⚽ Calcolo probabilità...")
        
        # SENZA API
        results_no_api = calc.calculate_all_probabilities(
            -0.5, 2.5,
            -0.75, 2.75
        )
        
        # CON API
        results_with_api = calc.calculate_all_probabilities(
            -0.5, 2.5,
            -0.75, 2.75,
            api_stats_home=stats_home,
            api_stats_away=stats_away
        )
        
        # Confronto
        print("\n📈 Confronto Risultati:")
        print(f"   {'Mercato':<15} {'Senza API':>10} {'Con API':>10} {'Delta':>8}")
        print("   " + "-"*45)
        
        markets = [
            ('P(1)', '1X2', '1'),
            ('P(GG)', 'GG_NG', 'GG'),
            ('P(Over 2.5)', 'Over_Under', 'Over 2.5'),
        ]
        
        for label, market, key in markets:
            no_api = results_no_api['Current'][market][key]
            with_api = results_with_api['Current'][market][key]
            delta = (with_api - no_api) * 100
            
            print(f"   {label:<15} {no_api*100:>9.2f}% {with_api*100:>9.2f}% {delta:>+7.2f}%")
        
        print("\n✅ Calcolo completato con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Esegue tutti i test"""
    print("\n" + "="*60)
    print("  QUICK API CHECK")
    print("  Verifica rapida funzionamento API")
    print("="*60)
    
    tests = [
        ("Connessione API", test_api_connection),
        ("Recupero Stats", test_team_stats),
        ("Calcolo Completo", test_full_calculation),
    ]
    
    passed = 0
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test '{name}' fallito: {str(e)}")
    
    # Riepilogo
    print("\n" + "="*60)
    print(f"  RISULTATO: {passed}/{len(tests)} test passati")
    print("="*60)
    
    if passed == len(tests):
        print("\n🎉 TUTTO FUNZIONA!")
        print("   L'API è configurata correttamente.")
        print("   Puoi usare l'app con le statistiche squadre!")
    else:
        print("\n⚠️ ALCUNI TEST FALLITI")
        print("   Possibili cause:")
        print("   - API key non valida o scaduta")
        print("   - Limite giornaliero raggiunto (100 req)")
        print("   - Problemi di connessione internet")
        print("   - Rate limiting attivo")
        print("\n   L'app funziona comunque senza API!")


if __name__ == "__main__":
    main()

