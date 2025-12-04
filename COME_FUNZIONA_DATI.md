# 🔄 Come Funziona: Da Dove Vengono i Dati

## 📋 Risposta Diretta

**Quando inserisci "Juventus vs Inter", l'IA prende i dati da:**

### 1. **Database Squadre** (Locale - Nessuna API)
- **File:** `data/cache/teams_database.json`
- **Quando:** Sempre (prima cosa che controlla)
- **Chiamate API:** 0 (se database esiste)
- **Aggiornamento:** Solo se database non esiste o > 6 ore

### 2. **Statistiche Match** (API Football-Data.org)
- **API:** `GET /teams/{id}/matches?limit=10&status=FINISHED`
- **Quando:** Solo se non in cache o cache scaduta (> 6 ore)
- **Chiamate API:** 0-2 (una per squadra, se non in cache)
- **Cache:** `data/cache/team_{id}_matches_10.json`

### 3. **Head-to-Head** (API Football-Data.org)
- **API:** `GET /teams/{id}/matches?limit=20&status=FINISHED`
- **Quando:** Solo se non in cache o cache scaduta
- **Chiamate API:** 0-1 (se non in cache)
- **Cache:** `data/cache/h2h_{id1}_{id2}.json`

### 4. **Calcolo Statistiche** (Locale - Nessuna API)
- **Dove:** Nel codice Python
- **Quando:** Sempre (analizza dati già recuperati)
- **Chiamate API:** 0

---

## 🎯 Flusso Completo Esempio

```
Input: "Juventus vs Inter"
  ↓
[1] TeamIdentifier.identify_team("Juventus")
    ├─ Controlla: data/cache/teams_database.json
    ├─ Se ESISTE → Usa database locale ✅ (0 API)
    └─ Se NON ESISTE → Chiama API per costruirlo (15 API, una tantum)
  ↓
[2] DataCollector.get_team_matches(109)  # ID Juventus
    ├─ Controlla: data/cache/team_109_matches_10.json
    ├─ Se ESISTE e < 6 ore → Usa cache ✅ (0 API)
    └─ Se NON ESISTE o > 6 ore → API: GET /teams/109/matches (1 API)
  ↓
[3] DataCollector.get_team_matches(108)  # ID Inter
    ├─ Controlla: data/cache/team_108_matches_10.json
    ├─ Se ESISTE e < 6 ore → Usa cache ✅ (0 API)
    └─ Se NON ESISTE o > 6 ore → API: GET /teams/108/matches (1 API)
  ↓
[4] DataCollector.get_head_to_head(109, 108)
    ├─ Controlla: data/cache/h2h_109_108.json
    ├─ Se ESISTE e < 6 ore → Usa cache ✅ (0 API)
    └─ Se NON ESISTE o > 6 ore → API: GET /teams/109/matches (1 API)
  ↓
[5] DataCollector.calculate_team_stats()
    └─ Analizza match già recuperati (0 API)
  ↓
[6] PoissonModel + MLPredictor
    └─ Calcola pronostici (0 API)
```

---

## 📊 Chiamate API per Scenario

### Scenario 1: Primo Utilizzo (Database Non Esiste)
```
Costruzione database: ~15 chiamate (una tantum)
Statistiche Juventus: 1 chiamata
Statistiche Inter: 1 chiamata
Head-to-Head: 1 chiamata
─────────────────────────────
TOTALE: ~18 chiamate
```

### Scenario 2: Utilizzo Normale (Cache Valida)
```
Database squadre: 0 (cache)
Statistiche Juventus: 0 (cache)
Statistiche Inter: 0 (cache)
Head-to-Head: 0 (cache)
─────────────────────────────
TOTALE: 0 chiamate ✅
```

### Scenario 3: Cache Scaduta (Dopo 6 Ore)
```
Database squadre: 0 (ancora valido)
Statistiche Juventus: 1 chiamata
Statistiche Inter: 1 chiamata
Head-to-Head: 1 chiamata
─────────────────────────────
TOTALE: 3 chiamate
```

---

## 🔑 API Utilizzate

### Football-Data.org (Gratuita)
- **Base URL:** `https://api.football-data.org/v4`
- **Rate Limit:** 10 richieste/minuto
- **Autenticazione:** Header `X-Auth-Token` (gratuito)

### Endpoint Chiamati

1. **GET /competitions/{league}/teams**
   - Quando: Costruzione database squadre (una tantum)
   - Cache: `teams_database.json` (permanente)

2. **GET /teams/{id}/matches**
   - Quando: Recupero ultimi match squadra
   - Cache: `team_{id}_matches_10.json` (6 ore)

3. **GET /teams/{id}** (opzionale)
   - Quando: Info aggiuntive squadra
   - Cache: `team_info_{id}.json` (6 ore)

---

## 💾 Cosa Viene Salvato in Cache

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
**Durata:** Permanente (aggiornato solo se mancante)

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
**Durata:** 6 ore

### `data/cache/h2h_109_108.json`
```json
[
  // Match storici tra Juventus e Inter
]
```
**Durata:** 6 ore

---

## ⚡ Ottimizzazioni Implementate

### 1. Rate Limiting Automatico
- Pausa di 6.1 secondi tra chiamate API
- Evita superamento limite 10/min

### 2. Cache Intelligente
- Controlla cache prima di chiamare API
- Usa cache scaduta come fallback se API fallisce

### 3. Gestione Errori
- Se API fallisce, usa ultimi dati disponibili
- Sistema continua a funzionare anche con errori API

### 4. Batch Processing
- Raccoglie tutte le chiamate necessarie
- Esegue in sequenza con rate limiting

---

## 🎯 Risultato

**Con Cache Valida:**
- ✅ **0 chiamate API** per pronostico
- ✅ Risposta istantanea
- ✅ Nessun limite rate

**Senza Cache:**
- ⚠️ **3 chiamate API** per pronostico
- ⚠️ ~20 secondi (con rate limiting)
- ⚠️ Rispetta limite 10/min

**Prima Volta:**
- ⚠️ **~18 chiamate API** (costruzione database)
- ⚠️ ~2 minuti
- ⚠️ Poi cache locale, nessuna chiamata

---

## 📝 Riepilogo

**Domanda:** "Quando inserisci i nomi delle squadre, l'IA dove prende i dati?"

**Risposta:**
1. **Database squadre:** Cache locale (0 API se esiste)
2. **Statistiche match:** API Football-Data.org (0-2 chiamate se non in cache)
3. **Head-to-Head:** API Football-Data.org (0-1 chiamate se non in cache)
4. **Calcolo statistiche:** Locale, analizza dati già recuperati (0 API)
5. **Pronostici:** Locale, usa modelli statistici/ML (0 API)

**Totale chiamate API:**
- **Prima volta:** ~18 (costruzione database)
- **Con cache:** 0-3 (spesso 0!)
- **Cache valida 6 ore**

**Tutti i dati vengono salvati in cache locale per ridurre chiamate API!** ✅





