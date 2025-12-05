# ⚡ Deploy Rapido su Streamlit Cloud

## 🚀 3 Passi Semplici

### 1️⃣ Connetti Repository
1. Vai su: **https://share.streamlit.io/**
2. Clicca **"New app"**
3. Seleziona:
   - Repository: `Sib-asian/Calcolatore-Sib`
   - Branch: `master`
   - Main file: `app.py`
4. Clicca **"Deploy!"**

### 2️⃣ Configura Secrets
1. Dopo il deploy, vai su **Settings** (⚙️)
2. Clicca su **"Secrets"**
3. Incolla questo (sostituisci con le tue API keys):

```toml
GROQ_API_KEY = "your_groq_api_key_here"
NEWS_API_KEY = "your_newsapi_key_here"
```

**Ottieni le tue API keys:**
- Groq: https://console.groq.com
- NewsAPI: https://newsapi.org/register

4. Clicca **"Save"**

### 3️⃣ Riavvia App
1. Vai su **"Manage app"**
2. Clicca **"Reboot app"**

## ✅ Fatto!

L'app sarà disponibile su: `https://[nome-app].streamlit.app`

---

**Nota**: Ogni push su `master` triggera un deploy automatico! 🎉

