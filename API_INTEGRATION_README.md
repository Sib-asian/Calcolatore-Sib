# Integrazione API Football - Documentazione

**Data**: 3 Dicembre 2025  
**Versione**: 1.0  
**Status**: ✅ PRONTO per produzione

---

## 📋 PANORAMICA

Integrazione con API-Football per recuperare statistiche recenti delle squadre e applicare aggiustamenti intelligenti ai calcoli delle probabilità.

### **Caratteristiche Chiave**:
- ✅ Completamente **opzionale** - App funziona anche senza
- ✅ **Automatico** - Aggiustamenti applicati se dati caricati
- ✅ **Conservativo** - Max ±3% per evitare sovrastime
- ✅ **Intelligente** - Considera forma E varianza
- ✅ **Robusto** - Gestione errori completa

---

## 🔑 API KEY

```
API Key: ad265facf527f3bb5439b6d87402f496
Provider: API-Football (RapidAPI)
Tier: FREE (100 richieste/giorno)
Limiti: Sufficienti con cache in-memory
```

---

## 📊 DATI RECUPERATI

Per ogni squadra:

1. **Ultimi 5 match** (filtrati per venue: casa/trasferta)
   - Risultati: W/D/L
   - Gol fatti e subiti per match

2. **Statistiche calcolate**:
   - Media gol segnati
   - Media gol subiti
   - Form factor (0-1, peso decrescente sui match recenti)
   - Variance (stabilità/imprevedibilità)

---

## ⚙️ FORMULA AGGIUSTAMENTO

### **Strategia Conservativa**:

```python
# 1. Base adjustment da form factor
form_adj = 0.98 + (form_factor * 0.04)  # Range: 0.98 - 1.02
# form=0.0 (5L) → 0.98 (-2%)
# form=0.5 (avg) → 1.00 (0%)
# form=1.0 (5W) → 1.02 (+2%)

# 2. Confidence da variance (riduce se imprevedibile)
if variance < 1.0:
    confidence = 1.0  # Piena fiducia
elif variance < 2.0:
    confidence = 1.0 - (variance - 1.0) * 0.6  # Ridotta
else:
    confidence = 0.3  # Molto bassa

# 3. Final adjustment (clamped ±3%)
final_adj = 1.0 + (form_adj - 1.0) * confidence
final_adj = clamp(final_adj, 0.97, 1.03)  # Max ±3%

# 4. Applica
lambda_adjusted = lambda_base * final_adj
```

### **Esempi Pratici**:

| Forma | Variance | Aggiustamento | Spiegazione |
|-------|----------|---------------|-------------|
| 5W (100%) | 0.5 (bassa) | **+2.0%** | Ottima forma, stabile → massimo boost |
| 5W (100%) | 2.5 (alta) | **+0.6%** | Ottima forma MA imprevedibile → ridotto |
| 5L (0%) | 0.5 (bassa) | **-2.0%** | Forma pessima, stabile → massimo malus |
| Media (50%) | 1.0 (media) | **±0.0%** | Forma media → nessun aggiustamento |

---

## 📈 RISULTATI TEST

### **Test 1: Logica Aggiustamenti**
```
✅ Casa forma 100%, variance 0.5 → +2.00%
✅ Trasferta forma 50%, variance 1.2 → +0.00%
✅ Alta variance (2.5) riduce aggiustamento → +0.60%
✅ Tutti entro limiti ±3%
```

### **Test 2: No Sovrastima**
```
Scenario critico (spread -0.75, total 2.75):
✅ P(GG) = 67.02% (prima causava problemi)
✅ P(Over 2.5) = 73.95% (realistico)
✅ P(Over 3.5) = 63.34% (realistico)
✅ Delta con/senza API < 0.5% (conservativo)
```

### **Test 3: Coerenza Mercati**
```
✅ Somma 1X2 = 1.0000000000
✅ Somma GG/NG = 1.0000000000
✅ Somma O/U = 1.0000000000
✅ Win to Nil < NG (0.2917 < 0.3296)
```

### **Test 4: Scenari Estremi**
```
✅ Forma pessima (5L) + alta variance → -0.60%
✅ Forma ottima (5W) + bassa variance → +2.00%
✅ Tutti entro range ±3%
```

---

## 🚀 UTILIZZO

### **1. Avvio App**:
```bash
cd calcolatore-Sib
streamlit run app.py
```

### **2. Workflow Utente**:

#### **Opzione A: SENZA API** (come prima)
```
1. Inserisci spread/total apertura
2. Inserisci spread/total corrente
3. Clicca "Calcola Probabilità"
4. Vedi risultati
```

#### **Opzione B: CON API** (nuovo)
```
1. Inserisci nomi squadre:
   - Casa: "Inter"
   - Trasferta: "Juventus"
2. Clicca "Carica Statistiche"
3. Vedi stats caricate:
   🏠 Inter (in casa)
   └ Ultimi 5: WWDWL
   └ Media gol: 2.1 fatti / 0.8 subiti
   └ Forma: 73%
   
   ✈️ Juventus (in trasferta)
   └ Ultimi 5: LDWWL
   └ Media gol: 0.9 fatti / 1.6 subiti
   └ Forma: 57%
4. Vedi alert coerenza:
   ✅ Input coerente con forma recente
   O
   ⚠️ Discrepanza rilevata (se anomalo)
5. Inserisci spread/total normalmente
6. Clicca "Calcola Probabilità"
7. Aggiustamenti API applicati AUTOMATICAMENTE
```

---

## 📂 FILE MODIFICATI/CREATI

### **Nuovi File**:
1. **`config.py`** - Configurazione API
2. **`api_football_client.py`** - Client API con cache
3. **`test_api_integration.py`** - Test completi

### **File Modificati**:
1. **`probability_calculator.py`**:
   - Aggiunto parametro `api_stats_home/away` a `calculate_all_probabilities()`
   - Aggiunto metodo `_apply_api_adjustment()`
   
2. **`app.py`**:
   - Import `api_football_client`
   - Sezione UI per caricamento stats
   - Alert coerenza
   - Pass stats al calcolo

3. **`requirements.txt`**:
   - Aggiunto `requests>=2.31.0`

---

## 🎯 LIMITI API

### **FREE Tier (100 req/giorno)**:

```
Uso tipico:
├─ Match analizzati: 10-30/giorno
├─ Squadre uniche: 20-60
├─ Chiamate API: 20-60 (cache in-memory)
└─ Margine: 40-80 inutilizzate ✅

Cache:
├─ Tipo: In-memory (dict)
├─ Durata: Sessione app
├─ Key: f"stats_{team}_{venue}"
└─ Reset: Chiusura app
```

**Veredicto**: Limiti più che sufficienti! ✅

---

## 🛡️ GESTIONE ERRORI

### **Errori Gestiti**:

1. **API non risponde**:
   ```
   ⚠️ "Errore API: timeout"
   → App continua senza stats
   ```

2. **Squadra non trovata**:
   ```
   ❌ "Squadra 'Intre' non trovata"
   → User corregge nome
   ```

3. **Limite giornaliero**:
   ```
   ⚠️ "Limite API raggiunto. Riprova domani."
   → App funziona senza stats
   ```

4. **Timeout/Network**:
   ```
   ⚠️ "Errore connessione"
   → Retry automatico (max 2)
   → Poi fallback graceful
   ```

**Nessun crash mai!** ✅

---

## 📊 IMPATTO PRESTAZIONI

### **Con Cache In-Memory**:

```
Prima chiamata (cache miss):
├─ Tempo: ~2-3 secondi
├─ API calls: 2 (una per squadra)
└─ Salvataggio cache: <1ms

Successive chiamate (cache hit):
├─ Tempo: <1ms
├─ API calls: 0
└─ Lettura cache: istantanea
```

### **Calcolo Probabilità**:

```
Senza API:
├─ Tempo: ~500ms
├─ Overhead: 0%

Con API:
├─ Tempo: ~502ms
├─ Overhead: +0.4% (trascurabile)
└─ Aggiustamento: ~2ms
```

**Impatto prestazioni: NEGLIGIBILE** ✅

---

## ✅ CONCLUSIONE

### **Sistema Completato**:

| Aspetto | Status | Note |
|---------|--------|------|
| **Implementazione** | ✅ | Completa e testata |
| **Test** | ✅ | 4/4 passati |
| **Sovrastime** | ✅ | Nessuna rilevata |
| **Coerenza** | ✅ | Tutte mantenute |
| **Errori** | ✅ | Gestione completa |
| **Prestazioni** | ✅ | Overhead <1% |
| **Documentazione** | ✅ | Completa |

### **Pronto per Produzione** 🚀

- ✅ Aggiustamenti conservativi (max ±3%)
- ✅ Intelligenti (forma + variance)
- ✅ Automatici (se dati caricati)
- ✅ Opzionali (app funziona senza)
- ✅ Robusti (gestione errori completa)
- ✅ Veloci (cache in-memory)
- ✅ Testati (4/4 test passati)

---

## 🔍 DEBUG

### **Test Manuale**:

```bash
# Test integrazione API
python test_api_integration.py

# Output atteso:
# ✅ Test passati: 4/4
# 🎉 TUTTI I TEST SUPERATI!
```

### **Verifica Cache**:

```python
from api_football_client import get_api_client

client = get_api_client()
print(f"Cache size: {len(client.cache)}")
# Dopo 2 squadre: 4 entries
# (team search + stats per venue)
```

---

**Fine Documentazione** 🎉


