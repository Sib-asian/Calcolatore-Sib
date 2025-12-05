# 🤖 AI Assistant - Guida all'Uso

## 📋 Panoramica

L'AI Assistant è un sistema intelligente che ti aiuta ad analizzare partite di calcio, cercare news, spiegare calcoli e molto altro, **completamente gratuito**!

## 🚀 Funzionalità

### 1. **Analisi Partite**
Chiedi all'AI di analizzare una partita:
```
"Analizza Inter vs Milan"
"Fammi un'analisi di Juventus vs Napoli"
```

L'AI cercherà:
- News recenti sulle squadre
- Infortuni e formazioni
- Statistiche e form
- Calcoli probabilità (se hai inserito spread/total)

### 2. **Spiegazione Calcoli**
Chiedi perché un mercato ha una certa probabilità:
```
"Perché Under 2.5 è al 58%?"
"Spiegami il calcolo di GG/NG"
```

### 3. **Ricerca News**
Cerca news specifiche su squadre:
```
"Cerca news su Inter"
"Ci sono infortuni nel Milan?"
"Qual è la formazione probabile della Juventus?"
```

### 4. **Calcoli Probabilità**
L'AI può calcolare probabilità se fornisci spread e total:
```
"Calcola probabilità con spread -0.5 e total 2.5"
"Analizza spread -0.75, total 2.25"
```

## 💡 Esempi di Utilizzo

### Analisi Completa
```
Utente: "Analizza Inter vs Milan per domani"

AI: Cerca news, infortuni, formazioni, calcola probabilità
    e genera un report completo con insights.
```

### Q&A Contestuale
```
Utente: "Perché hai dato 58% a Under 2.5?"

AI: Spiega basandosi su:
    - Media gol ultime partite
    - News e formazioni
    - Modello statistico (Dixon-Coles)
    - Market movement
```

### Ricerca Pattern
```
Utente: "Inter in casa con total 2.5, come performa?"

AI: Analizza storico e pattern per rispondere.
```

## 🔧 Tecnologie Utilizzate

- **Groq API**: LLM gratuito (Llama 3.1 70B) - veloce e potente
- **DuckDuckGo**: Ricerca web gratuita
- **NewsAPI**: News strutturate (100 richieste/giorno gratis)
- **SQLite Cache**: Cache intelligente per ottimizzare chiamate

## 📱 Mobile-Friendly

L'interfaccia è ottimizzata per smartphone:
- Input text con font size corretto (previene zoom iOS)
- Chat responsive
- Risposte concise e leggibili

## ⚙️ Configurazione

Le API keys sono già configurate in `config.py`:
- Groq API Key: ✅ Configurata
- NewsAPI Key: ✅ Configurata

## 🎯 Limitazioni (Budget 0€)

- **NewsAPI**: 100 richieste/giorno (con cache intelligente, sufficiente per 50+ analisi)
- **DuckDuckGo**: Rate limit leggero (rispettato automaticamente)
- **Groq**: ~30 richieste/minuto (più che sufficiente)

## 💾 Cache

Il sistema usa cache SQLite per:
- **News**: Valide 24h (stessa squadra = stessa news)
- **Ricerche**: Valide 6h
- **Auto-cleanup**: Rimozione automatica entry scadute

## 🐛 Troubleshooting

### AI non risponde
1. Verifica connessione internet
2. Controlla che Groq API key sia valida in `config.py`
3. Prova a pulire la chat e riprovare

### News non trovate
1. NewsAPI potrebbe aver esaurito quota giornaliera (100/giorno)
2. Il sistema usa automaticamente DuckDuckGo come fallback
3. Cache riduce chiamate API (stessa squadra = cache hit)

### Lentezza
1. Prima chiamata può essere lenta (setup cache)
2. Chiamate successive più veloci (cache)
3. Groq è molto veloce (~1-2 secondi)

## 📊 Statistiche Cache

Puoi controllare statistiche cache (se implementato in futuro):
- Numero entry news in cache
- Numero entry ricerche in cache
- Tasso di cache hit

## 🔐 Privacy

- Tutte le chiamate API sono sicure (HTTPS)
- Cache locale (SQLite) - dati non inviati a terzi
- History conversazione solo in sessione Streamlit

## 🚀 Prossimi Sviluppi

Possibili miglioramenti futuri:
- Alert automatici (richiede polling, non sostenibile gratis)
- Storico avanzato multi-utente
- Integrazione con più fonti news
- Pattern recognition avanzato

---

**Buon utilizzo! 🎉**

