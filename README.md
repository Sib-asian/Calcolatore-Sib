# ⚽ Calcolatore Sib - Sistema IA per Pronostici Calcio

Sistema di intelligenza artificiale completamente autonomo per generare pronostici sportivi sul calcio.

## 🎯 Caratteristiche

- ✅ **Identificazione Automatica Squadre**: Riconosce squadre da nomi inseriti (fuzzy matching)
- ✅ **Raccolta Dati Automatica**: Recupera statistiche da API gratuite
- ✅ **Modelli Predittivi**: Combina modelli statistici (Poisson) e Machine Learning (XGBoost)
- ✅ **Pronostici Completi**: 1X2, Over/Under, BTTS, HT, HT/FT, Gol esatti
- ✅ **Confidence Scoring**: Valutazione affidabilità per ogni pronostico
- ✅ **Cache Intelligente**: Riduce chiamate API e migliora performance

## 🚀 Quick Start

### 1. Installazione

```bash
# Clona repository
git clone https://github.com/Sib-asian/Calcolatore-Sib.git
cd Calcolatore-Sib

# Crea ambiente virtuale (consigliato)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Configurazione API

Crea file `.env` nella root:
```env
FOOTBALL_DATA_API_KEY=il_tuo_token_qui
```

**Ottieni token gratuito:** https://www.football-data.org/

### 3. Primo Pronostico

```bash
python src/main.py "Juventus vs Inter"
```

## 📖 Documentazione Completa

Per setup dettagliato e rendere l'IA funzionante al 100%, leggi:
- **[SETUP_COMPLETO.md](SETUP_COMPLETO.md)** - Guida completa setup, database, training ML

## 🏗️ Architettura

```
Input: "Juventus vs Inter"
  ↓
[Team Identifier] → Identifica squadre con fuzzy matching
  ↓
[Data Collector] → Recupera statistiche, form, H2H da API
  ↓
[Feature Engineering] → Calcola features per ML
  ↓
[Statistical Models] → Poisson, Elo ratings
[ML Models] → XGBoost (se addestrato)
  ↓
[Prediction Generator] → Combina modelli, calcola confidence
  ↓
Output: Pronostico completo formattato
```

## 📊 Output Esempio

```
============================================================
PRONOSTICO: Juventus vs Inter
Lega: Serie A
============================================================

📊 GOL ATTESI
  Casa: 1.8
  Trasferta: 1.5
  Totale: 3.3

⚽ RISULTATO FINALE (1X2)
  1 (Juventus): 45.2% | Confidence: ⭐⭐⭐⭐
  X (Pareggio): 28.5% | Confidence: ⭐⭐⭐
  2 (Inter): 26.3% | Confidence: ⭐⭐⭐⭐

📈 OVER/UNDER 2.5
  Over 2.5: 65.8% | Confidence: ⭐⭐⭐⭐⭐
  Under 2.5: 34.2% | Confidence: ⭐⭐⭐

✅ BTTS (Both Teams To Score)
  Sì: 58.3% | Confidence: ⭐⭐⭐⭐
  No: 41.7% | Confidence: ⭐⭐⭐

⏱️ PRIMO TEMPO (HT)
  1: 42.1%
  X: 35.2%
  2: 22.7%

🔄 HT/FT (Più probabili)
  1/1: 18.5%
  X/1: 15.2%
  1/X: 12.8%

🎯 GOL TOTALI (Più probabili)
  3 gol: 28.5%
  2 gol: 25.3%
  4 gol: 18.2%
============================================================
```

## 📁 Struttura Progetto

```
calcolatore-Sib/
├── src/
│   ├── main.py                 # Entry point
│   ├── config.py               # Configurazione
│   ├── team_identifier.py      # Identificazione squadre
│   ├── data_collector.py       # Raccolta dati API
│   ├── prediction_generator.py # Generatore pronostici
│   └── models/
│       ├── statistical_models.py  # Poisson, Elo
│       └── ml_models.py            # XGBoost
├── scripts/
│   ├── download_historical_data.py  # Download dati storici
│   └── train_models.py              # Training ML
├── data/
│   ├── cache/                  # Cache API e database squadre
│   └── historical/             # Dati storici per training
├── models/                     # Modelli ML addestrati
├── requirements.txt
├── .env                        # API keys (non committare!)
└── README.md
```

## 🔑 Rendere l'IA Funzionante al 100%

### Livello Base (60-70%) - Funziona Subito
- ✅ Installazione dipendenze
- ✅ Configurazione API Football-Data.org
- ✅ Primo pronostico con modelli statistici

### Livello Intermedio (75-80%)
- ⚠️ Download dati storici (500+ match)
- ⚠️ Aggiornamento Elo ratings
- ⚠️ Cache ottimizzata

### Livello Avanzato (90-95%)
- ⚠️ Training modelli ML (2000+ match)
- ⚠️ Validazione modelli
- ⚠️ Fine-tuning parametri

### Livello Ottimale (95-100%)
- ⚠️ Ensemble modelli
- ⚠️ Feature engineering avanzato
- ⚠️ Retraining periodico

**Vedi [SETUP_COMPLETO.md](SETUP_COMPLETO.md) per dettagli.**

## 🛠️ Script Utili

### Download Dati Storici
```bash
python scripts/download_historical_data.py
```

### Training Modelli ML
```bash
python scripts/train_models.py
```

## 📋 Requisiti

- Python 3.8+
- Connessione Internet
- API Key Football-Data.org (gratuita)

## 🔒 API Gratuite Supportate

- **Football-Data.org** (principale): 10 req/min, dati completi leghe europee
- **TheSportsDB**: Nessuna key, dati base
- **OpenLigaDB**: Solo Bundesliga

## ⚠️ Limitazioni

- Rate limits API gratuite (10 req/min)
- Dati infortuni/squalifiche non disponibili gratuitamente
- Training ML richiede dataset storico (non incluso)

## 📝 License

Questo progetto è open source.

## 🤝 Contribuire

Contributi benvenuti! Apri una issue o pull request.

---

**Per domande o problemi, consulta [SETUP_COMPLETO.md](SETUP_COMPLETO.md)**
