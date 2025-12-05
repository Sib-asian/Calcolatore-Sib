# 🚀 Deploy su Streamlit Cloud

## ✅ Repository Pronto per Deploy!

Il repository è configurato e pronto per il deploy automatico su Streamlit Cloud.

## 📋 Passi per Deploy

### 1. Connetti Repository a Streamlit Cloud

1. Vai su: https://share.streamlit.io/
2. Clicca su **"New app"**
3. Seleziona:
   - **Repository**: `Sib-asian/Calcolatore-Sib`
   - **Branch**: `master`
   - **Main file path**: `app.py`
4. Clicca su **"Deploy!"**

### 2. Configura Secrets (IMPORTANTE!)

Dopo il primo deploy, configura le API keys:

1. Vai su: https://share.streamlit.io/
2. Seleziona la tua app
3. Clicca su **"Settings"** (⚙️ in alto a destra)
4. Vai su **"Secrets"**
5. Clicca su **"Edit secrets"**
6. Incolla questo contenuto (sostituisci con le tue API keys):

```toml
GROQ_API_KEY = "your_groq_api_key_here"
NEWS_API_KEY = "your_newsapi_key_here"
```

**Nota**: Ottieni le tue API keys da:
- Groq: https://console.groq.com
- NewsAPI: https://newsapi.org/register

7. Clicca su **"Save"**

### 3. Riavvia l'App

Dopo aver salvato i secrets:

1. Vai su **"Manage app"**
2. Clicca su **"Reboot app"**
3. L'app si riavvierà con le API keys configurate

## ✅ Verifica Deploy

Dopo il deploy, verifica che:

1. ✅ L'app si carica senza errori
2. ✅ Il tab "Calcolatore" funziona
3. ✅ Il tab "AI Assistant" è visibile
4. ✅ La chat AI risponde (testa con "Ciao")

## 🔧 Configurazione Automatica

Il file `config.py` legge automaticamente:
1. **Secrets di Streamlit Cloud** (variabili d'ambiente)
2. **File .env** (se presente, per sviluppo locale)

Quindi funziona sia in locale che su Streamlit Cloud!

## 📝 Note Importanti

- **Deploy Automatico**: Ogni push su `master` triggera un nuovo deploy
- **Secrets Sicuri**: Le API keys sono salvate in modo sicuro su Streamlit Cloud
- **Cache**: Il database SQLite (`ai_cache.db`) viene creato automaticamente
- **Rate Limits**: 
  - Groq: 30 req/min (sufficiente)
  - NewsAPI: 100 req/giorno (sufficiente con cache)

## 🐛 Troubleshooting

### App non si avvia
- Verifica che `app.py` sia nella root
- Controlla i logs in Streamlit Cloud dashboard

### AI non risponde
- Verifica che i secrets siano configurati correttamente
- Controlla i logs per errori API

### Errori di import
- Verifica che `requirements.txt` contenga tutte le dipendenze
- Streamlit Cloud installa automaticamente da `requirements.txt`

## 🎉 Deploy Completato!

Una volta configurato, l'app sarà disponibile su:
```
https://[your-app-name].streamlit.app
```

---

**Nota**: Il repository è già pronto. Basta connetterlo a Streamlit Cloud e configurare i secrets! 🚀

