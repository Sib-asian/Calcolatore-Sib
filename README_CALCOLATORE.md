# ⚽ Calcolatore SIB - Sistema di Calcolo Probabilità Avanzato

Calcolatore professionale per scommesse calcistiche basato su **modelli matematici avanzati** (Poisson bivariato + aggiustamenti Dixon-Coles).

## 🎯 Caratteristiche

- ✅ **Input Semplice**: Solo spread e total (apertura e corrente)
- ✅ **Formule Matematiche Avanzate**: Modelli Poisson + Dixon-Coles
- ✅ **Calcolo Completo**: Tutti i mercati principali
  - 1X2 (Casa/Pareggio/Trasferta)
  - GG/NG (Goal-Goal/No Goal)
  - Over/Under (vari totali)
  - Mercati Primo Tempo (HT 1X2, HT Over/Under)
  - Risultati Esatti
- ✅ **Interfaccia Streamlit**: Moderna e intuitiva
- ✅ **Analisi Movimento Mercato**: Confronto apertura vs corrente
- ✅ **Visualizzazioni Interattive**: Grafici Plotly

## 🚀 Quick Start

### 1. Installazione

```bash
# Assicurati di essere nella directory del progetto
cd calcolatore-Sib

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Avvio Applicazione

```bash
streamlit run app.py
```

L'applicazione si aprirà automaticamente nel browser all'indirizzo `http://localhost:8501`

## 📊 Come Usare

### Input Richiesti

1. **Spread Apertura**: Spread iniziale del mercato
   - **Negativo** = Casa favorita (es. -0.5)
   - **Positivo** = Trasferta favorita (es. +0.5)

2. **Total Apertura**: Total iniziale (es. 2.5)

3. **Spread Corrente**: Spread attuale del mercato

4. **Total Corrente**: Total attuale

### Esempio

```
Spread Apertura: -0.5  (Casa favorita)
Total Apertura: 2.5
Spread Corrente: -0.75 (Casa ancora più favorita)
Total Corrente: 2.75   (Più gol attesi)
```

### Output

L'applicazione calcola e mostra:

- **Riepilogo**: Attese gol, movimenti mercato
- **1X2**: Probabilità Casa/Pareggio/Trasferta
- **GG/NG & Over/Under**: Probabilità per vari mercati
- **Primo Tempo**: Probabilità HT 1X2 e Over/Under HT
- **Risultati Esatti**: Top risultati più probabili
- **Movimento Mercato**: Analisi cambiamenti

## 🔬 Modelli Matematici

### 1. Conversione Spread/Total in Attese Gol

Il sistema converte spread e total in attese gol (lambda) per casa e trasferta:

```
lambda_home = (total + spread) / 2
lambda_away = (total - spread) / 2
```

**Esempio:**
- Spread: -0.5, Total: 2.5
- lambda_home = (2.5 + (-0.5)) / 2 = 1.0
- lambda_away = (2.5 - (-0.5)) / 2 = 1.5

### 2. Modello Poisson Bivariato

Per ogni risultato esatto (i, j), la probabilità è:

```
P(i, j) = P(i, lambda_home) × P(j, lambda_away) × tau(i, j)
```

Dove:
- `P(k, lambda) = (lambda^k × e^(-lambda)) / k!` è la distribuzione Poisson

### 3. Aggiustamento Dixon-Coles

Il fattore `tau(i, j)` corregge le probabilità di 0-0 e 1-1, che sono statisticamente più probabili:

```
tau(0,0) = 1 - lambda_home × lambda_away × rho
tau(1,0) = 1 + lambda_home × rho
tau(0,1) = 1 + lambda_away × rho
tau(1,1) = 1 - rho
tau(i,j) = 1  (altrimenti)
```

Dove `rho = 0.1` è il parametro di correlazione.

### 4. Calcolo Probabilità Mercati

- **1X2**: Somma probabilità risultati esatti dove casa vince/pareggio/trasferta vince
- **GG/NG**: Somma probabilità dove entrambe segnano/almeno una non segna
- **Over/Under**: Somma probabilità dove total gol >/< soglia
- **HT**: Usa lambda ridotte del 45% (statistica reale)

## 📁 Struttura File

```
calcolatore-Sib/
├── app.py                      # Applicazione Streamlit principale
├── probability_calculator.py   # Modulo calcolo probabilità
├── requirements.txt            # Dipendenze Python
└── README_CALCOLATORE.md       # Questa documentazione
```

## 🛠️ Dipendenze

- `streamlit>=1.28.0`: Framework web app
- `numpy>=1.24.0`: Calcoli numerici
- `scipy>=1.11.0`: Distribuzioni statistiche
- `pandas>=2.0.0`: Manipolazione dati
- `plotly>=5.17.0`: Grafici interattivi

## 📈 Esempio Output

### Probabilità 1X2
```
1 (Casa):     45.23%
X (Pareggio): 28.15%
2 (Trasferta): 26.62%
```

### Over/Under
```
Over 2.5:  65.84%
Under 2.5: 34.16%
```

### Risultati Esatti (Top 5)
```
1-1: 12.45%
1-0: 10.23%
2-1:  9.87%
0-1:  8.92%
2-0:  7.65%
```

## 🔍 Interpretazione Spread

- **Spread negativo** (es. -0.5): Casa favorita
  - Più negativo = Casa più favorita
  - Es. -1.5 = Casa deve vincere di almeno 2 gol

- **Spread positivo** (es. +0.5): Trasferta favorita
  - Più positivo = Trasferta più favorita
  - Es. +1.5 = Trasferta deve vincere di almeno 2 gol

- **Spread = 0**: Match equilibrato

## ⚙️ Parametri Modello

I parametri del modello possono essere modificati in `probability_calculator.py`:

```python
self.rho = 0.1   # Correlazione Dixon-Coles
self.xi = 0.1    # Aggiustamento basso scoring
ht_factor = 0.45 # Fattore riduzione primo tempo
```

## 🎓 Riferimenti Teorici

- **Poisson Distribution**: Modello standard per gol in calcio
- **Dixon-Coles Model**: Aggiustamento per correggere 0-0 e 1-1
- **Asian Handicap**: Sistema spread per bilanciare match

## 📝 Note

- Le probabilità sono calcolate fino a 10 gol per squadra (sufficiente per coprire >99.9% dei casi)
- I risultati esatti mostrati sono limitati a 5 gol per squadra per leggibilità
- Il modello assume indipendenza tra gol (corretta da Dixon-Coles per casi specifici)

## 🐛 Troubleshooting

### Errore: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### App non si avvia
```bash
# Verifica che streamlit sia installato
pip install streamlit
streamlit run app.py
```

### Calcoli sembrano errati
- Verifica che spread e total siano inseriti correttamente
- Ricorda: spread negativo = casa favorita
- Total deve essere positivo

## 📄 License

Questo progetto è open source.

## 🤝 Contribuire

Contributi benvenuti! Apri una issue o pull request.

---

**Sviluppato con formule matematiche avanzate per calcoli precisi e affidabili** ⚽📊

