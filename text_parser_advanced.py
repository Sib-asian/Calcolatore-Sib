"""
Text Parser Avanzato
Estrae nomi giocatori, formazioni e infortuni da testi non strutturati
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

# Prova a importare spacy per NLP avanzato (opzionale)
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load('it_core_news_sm')
    except OSError:
        # Modello non installato, usa solo regex
        nlp = None
        SPACY_AVAILABLE = False
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None

class TextParserAdvanced:
    """Parser avanzato per estrarre informazioni strutturate da testi calcistici"""
    
    def __init__(self):
        # Pattern per nomi italiani/internazionali (Cognome Nome o Nome Cognome)
        self.name_patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',  # Nome Cognome
            r'\b([A-Z][a-z]+-[A-Z][a-z]+)\b',  # Nome-Cognome (con trattino)
        ]
        
        # Pattern per formazioni
        self.formation_patterns = [
            r'(?:formazione|lineup|probabile|schieramento)[\s:]+([0-9]-[0-9]-[0-9])',
            r'([0-9]-[0-9]-[0-9])(?:\s+con|\s+in)',
            r'(?:tattica|modulo)[\s:]+([0-9]-[0-9]-[0-9])',
        ]
        
        # Pattern per infortuni
        self.injury_keywords = [
            'infortunato', 'infortunio', 'stop', 'indisponibile', 'assente',
            'squalificato', 'sospeso', 'problema', 'lesione', 'trauma',
            'injury', 'injured', 'out', 'doubt', 'doubtful'
        ]
        
        # Pattern per estrarre infortuni con nomi
        self.injury_patterns = [
            r'(?:infortunato|stop|indisponibile|assente|squalificato)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s]+(?:infortunato|stop|indisponibile|assente)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s]+(?:subisce|ha subito|ha riportato)[\s]+(?:un\s+)?infortunio',
        ]
    
    def extract_player_names(self, text: str, max_names: int = 10) -> List[str]:
        """
        Estrae nomi di giocatori da un testo
        
        Args:
            text: Testo da analizzare
            max_names: Numero massimo di nomi da estrarre
            
        Returns:
            Lista di nomi trovati (unici)
        """
        names = set()
        
        # Metodo 1: Regex patterns (sempre disponibile)
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Filtra nomi troppo corti o comuni (es: "Il Calcio", "La Squadra")
                if len(match.split()) >= 2 and len(match) > 5:
                    # Rimuovi articoli comuni
                    if not any(word.lower() in ['il', 'la', 'lo', 'gli', 'le', 'un', 'una', 'del', 'della'] 
                              for word in match.split()):
                        names.add(match.strip())
        
        # Metodo 2: spacy NLP (se disponibile) - migliora accuratezza
        if SPACY_AVAILABLE and nlp is not None:
            try:
                doc = nlp(text)
                # Estrai entità di tipo PERSON
                for ent in doc.ents:
                    if ent.label_ == "PER" and len(ent.text.split()) >= 2:
                        # Filtra nomi troppo corti e rimuovi prefissi comuni
                        clean_name = ent.text.strip()
                        if len(clean_name) > 5:
                            # Rimuovi prefissi come "Infortunato", "Assente", ecc.
                            for prefix in ['infortunato', 'assente', 'squalificato', 'stop']:
                                if clean_name.lower().startswith(prefix):
                                    clean_name = clean_name[len(prefix):].strip()
                            if len(clean_name) > 5:
                                names.add(clean_name)
            except Exception:
                # Se spacy fallisce, continua con solo regex
                pass
        
        # Ordina per frequenza nel testo
        name_counts = Counter()
        for name in names:
            name_counts[name] = text.lower().count(name.lower())
        
        # Restituisci i nomi più frequenti
        sorted_names = [name for name, _ in name_counts.most_common(max_names)]
        return sorted_names
    
    def extract_formations(self, text: str) -> List[str]:
        """
        Estrae formazioni tattiche da un testo
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di formazioni trovate (es: ['4-3-3', '4-4-2'])
        """
        formations = set()
        
        # Cerca pattern formazioni
        for pattern in self.formation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Valida formato formazione (es: 4-3-3, 3-5-2)
                if re.match(r'^[0-9]-[0-9]-[0-9]$', match):
                    formations.add(match)
        
        # Cerca anche formazioni scritte in modo diverso
        alt_pattern = r'\b([0-9])\s*-\s*([0-9])\s*-\s*([0-9])\b'
        alt_matches = re.findall(alt_pattern, text)
        for match in alt_matches:
            formation = f"{match[0]}-{match[1]}-{match[2]}"
            formations.add(formation)
        
        return list(formations)
    
    def extract_injuries(self, text: str) -> List[Dict[str, Any]]:
        """
        Estrae informazioni su infortuni da un testo
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di dict con 'player', 'status', 'context'
        """
        injuries = []
        
        # Cerca pattern infortuni con nomi
        for pattern in self.injury_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                player_name = match.group(1) if match.groups() else None
                if player_name:
                    # Estrai contesto (frase completa)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    # Determina status
                    status = 'unknown'
                    if any(kw in context.lower() for kw in ['stop', 'fuori', 'out']):
                        status = 'out'
                    elif any(kw in context.lower() for kw in ['dubbio', 'doubt', 'doubtful']):
                        status = 'doubtful'
                    elif any(kw in context.lower() for kw in ['squalificato', 'sospeso']):
                        status = 'suspended'
                    
                    injuries.append({
                        'player': player_name,
                        'status': status,
                        'context': context
                    })
        
        # Rimuovi duplicati (stesso giocatore)
        seen_players = set()
        unique_injuries = []
        for injury in injuries:
            if injury['player'] not in seen_players:
                seen_players.add(injury['player'])
                unique_injuries.append(injury)
        
        return unique_injuries
    
    def extract_lineup_info(self, text: str) -> Dict[str, Any]:
        """
        Estrae informazioni su formazione probabile
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Dict con 'formation', 'players', 'notes'
        """
        result = {
            'formation': None,
            'players': [],
            'notes': []
        }
        
        # Estrai formazione
        formations = self.extract_formations(text)
        if formations:
            result['formation'] = formations[0]  # Prendi la prima
        
        # Estrai nomi giocatori menzionati
        players = self.extract_player_names(text, max_names=15)
        result['players'] = players[:11]  # Max 11 giocatori
        
        # Estrai note (frasi che contengono "probabile", "dubbio", ecc.)
        note_keywords = ['probabile', 'dubbio', 'indisponibile', 'infortunato', 'squalificato']
        sentences = re.split(r'[.!?]\s+', text)
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in note_keywords):
                if len(sentence) < 200:  # Solo frasi brevi
                    result['notes'].append(sentence.strip())
        
        return result
    
    def parse_news_article(self, title: str, snippet: str) -> Dict[str, Any]:
        """
        Analizza un articolo di news e estrae informazioni strutturate
        
        Args:
            title: Titolo dell'articolo
            snippet: Contenuto/descrizione
            
        Returns:
            Dict con informazioni estratte
        """
        full_text = f"{title} {snippet}"
        
        return {
            'players_mentioned': self.extract_player_names(full_text, max_names=10),
            'formations': self.extract_formations(full_text),
            'injuries': self.extract_injuries(full_text),
            'lineup_info': self.extract_lineup_info(full_text)
        }
    
    def enhance_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Arricchisce risultati di ricerca con informazioni estratte
        
        Args:
            results: Lista di risultati di ricerca (con 'title', 'snippet')
            
        Returns:
            Lista arricchita con campi 'parsed_info'
        """
        enhanced = []
        
        for result in results:
            title = result.get('title', '')
            snippet = result.get('snippet', '') or result.get('body', '')
            
            if title or snippet:
                parsed = self.parse_news_article(title, snippet)
                
                # Aggiungi info estratte al risultato
                enhanced_result = result.copy()
                enhanced_result['parsed_info'] = parsed
                enhanced.append(enhanced_result)
            else:
                enhanced.append(result)
        
        return enhanced

