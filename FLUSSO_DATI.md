# 🔄 Flusso Dati - Come Funziona Quando Inserisci i Nomi

## 📊 Flusso Attuale (Quando Inserisci "Juventus vs Inter")

### Step 1: Identificazione Squadre
```
Input: "Juventus vs Inter"
  ↓
[TeamIdentifier]
  ↓
Controlla cache: data/cache/teams_database.json
  ├─ Se ESISTE → Usa database locale ✅ (NESSUNA API)
  └─ Se NON ESISTE → Chiama API Football-Data.org per costruirlo
      ├─ API: GET /competitions/{league}/teams (per ogni lega)
      └─ Salva in cache locale ✅
```

**Chiamate API:** 0 (se database esiste) o ~15 (se deve costruirlo la prima volta)

---

### Step 2: Raccolta Statistiche Squadre

```
[PredictionGenerator.generate_prediction()]
  ↓
[DataCollector.calculate_team_stats(home_team_id, is_home=True)]
  ↓
Controlla cache: data/cache/team_{id}_matches_10.json
  ├─ Se ESISTE e < 6 ore → Usa cache ✅ (NESSUNA API)
  └─ Se NON ESISTE o > 6 ore → Chiama API
      ├─ API: GET /teams/{id}/matches?limit=10&status=FINISHED
      └─ Salva in cache ✅
```

**Chiamate API:** 0-2 (una per squadra, se non in cache)

---

### Step 3: Head-to-Head

```
[DataCollector.calculate_h2h_stats(team1_id, team2_id)]
  ↓
Controlla cache: data/cache/h2h_{id1}_{id2}.json
  ├─ Se ESISTE e < 6 ore → Usa cache ✅ (NESSUNA API)
  └─ Se NON ESISTE o > 6 ore → Chiama API
      ├─ API: GET /teams/{id1}/matches?limit=20&status=FINISHED
      ├─ Filtra match tra le due squadre
      └─ Salva in cache ✅
```

**Chiamate API:** 0-1 (se non in cache)

---

### Step 4: Calcolo Statistiche

```
[DataCollector.calculate_team_stats()]
  ↓
Analizza match recuperati (da cache o API)
  ├─ Calcola: gol fatti/subiti media
  ├─ Calcola: form (punti ultimi match)
  └─ Calcola: vittorie/pareggi/sconfitte
```

**Chiamate API:** 0 (usa dati già recuperati)

---

### Step 5: Generazione Pronostici

```
[PoissonModel + MLPredictor]
  ↓
Usa statistiche calcolate (NON chiama API)
  ├─ Calcola gol attesi
  ├─ Predice 1X2, Over/Under, BTTS, etc.
  └─ Combina modelli statistici + ML
```

**Chiamate API:** 0 (tutto locale)

---

## 📈 Riepilogo Chiamate API

### Primo Utilizzo (Database Non Esiste)
- Costruzione database squadre: ~15 chiamate (una tantum)
- Statistiche squadra casa: 1 chiamata
- Statistiche squadra trasferta: 1 chiamata
- Head-to-Head: 1 chiamata
- **TOTALE: ~18 chiamate** (solo la prima volta)

### Utilizzi Successivi (Con Cache)
- Database squadre: 0 (già in cache)
- Statistiche squadre: 0-2 (se cache valida, 0)
- Head-to-Head: 0-1 (se cache valida, 0)
- **TOTALE: 0-3 chiamate** (se cache valida, spesso 0!)

### Cache Duration
- **Database squadre:** Aggiornato solo se > 6 ore o mancante
- **Statistiche match:** Cache valida 6 ore
- **Head-to-Head:** Cache valida 6 ore

---

## ⚠️ Problemi Attuali

### 1. Troppe Chiamate API al Primo Avvio
- Costruisce database squadre chiamando API per ogni lega
- **Soluzione:** Pre-download database squadre o uso database statico

### 2. Cache Non Ottimale
- Cache per singola squadra, non per coppia
- **Soluzione:** Cache intelligente per coppie squadre

### 3. Nessun Fallback se API Fallisce
- Se API non risponde, sistema fallisce
- **Soluzione:** Fallback a dati mock o database locale

### 4. Rate Limiting Non Gestito
- Se fai molte richieste, potresti superare 10 req/min
- **Soluzione:** Rate limiter con queue

---

## 🚀 Miglioramenti da Implementare

### 1. Database Squadre Pre-costruito
- Includere database base nel repository
- Aggiornamento solo quando necessario

### 2. Cache Intelligente
- Cache per "statistiche squadra X in data Y"
- Cache per "H2H squadra X vs Y"

### 3. Batch API Calls
- Raccogliere tutte le chiamate necessarie
- Eseguirle in batch con rate limiting

### 4. Fallback System
- Se API fallisce, usa dati mock o ultimi dati disponibili
- Sistema continua a funzionare anche offline

### 5. Pre-fetching
- Pre-caricare statistiche squadre popolari
- Background job per aggiornare cache

---

## 📋 Cosa Viene Salvato in Cache

### `data/cache/teams_database.json`
```json
{
  "109": {
    "id": 109,
    "name": "Juventus",
    "short_name": "Juve",
    "tla": "JUV",
    "variants": ["Juventus", "Juve", "JUV"],
    "league": "Serie A",
    "league_code": "SA"
  }
}
```

### `data/cache/team_109_matches_10.json`
```json
[
  {
    "id": 12345,
    "homeTeam": {"id": 109, "name": "Juventus"},
    "awayTeam": {"id": 108, "name": "Inter"},
    "score": {"fullTime": {"home": 2, "away": 1}},
    "utcDate": "2024-01-15T20:00:00Z"
  }
]
```

### `data/cache/h2h_109_108.json`
```json
[
  // Match storici tra Juventus e Inter
]
```

---

## 🔧 Come Ridurre Chiamate API

### Opzione 1: Database Squadre Statico
Includere `teams_database.json` base nel repository (aggiornato periodicamente)

### Opzione 2: Cache Più Lunga
Aumentare `CACHE_DURATION_HOURS` in `config.py` (es: 24 ore invece di 6)

### Opzione 3: Pre-download Dati
Script che scarica dati per squadre popolari in anticipo

### Opzione 4: Database Locale Completo
Mantenere database locale con ultimi match di tutte le squadre

---

## ✅ Situazione Attuale

**Con Cache Valida:**
- ✅ 0-3 chiamate API per pronostico
- ✅ Cache dura 6 ore
- ✅ Sistema veloce

**Senza Cache:**
- ⚠️ 3-5 chiamate API per pronostico
- ⚠️ Potrebbe superare rate limit (10/min) se fai molte richieste

**Prima Volta:**
- ⚠️ ~18 chiamate API per costruire database
- ⚠️ Poi cache locale, nessuna chiamata

---

## 🎯 Raccomandazioni

1. **Prima esecuzione:** Lascia costruire database (una tantum)
2. **Utilizzi successivi:** Sistema usa cache, pochissime chiamate
3. **Per ridurre chiamate:** Aumenta `CACHE_DURATION_HOURS` in `config.py`
4. **Per offline:** Usa database squadre pre-costruito (da implementare)




