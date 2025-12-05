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
        
        # Lista di parole comuni da escludere (italiano + inglese)
        common_words = {
            'il', 'la', 'lo', 'gli', 'le', 'un', 'una', 'uno', 'del', 'della', 'dei', 'delle',
            'per', 'con', 'che', 'chi', 'cui', 'dove', 'quando', 'come', 'perché',
            'ha', 'hanno', 'era', 'erano', 'stato', 'stati', 'stata', 'state',
            'anni', 'anno', 'uno', 'due', 'tre', 'sei', 'sette', 'otto', 'nove', 'dieci',
            'anche', 'pure', 'solo', 'sempre', 'mai', 'già', 'ancora', 'poi', 'dopo',
            'tonfo', 'rilasciato', 'occup', 'noccup', 'sage', 'in', 'stato',
            'zidane', 'allegri', 'de', 'zerbi', 'rabiot', 'hojbjerg', 'henrique',
            'calcio', 'squadra', 'partita', 'match', 'gol', 'goal', 'campo', 'stadio',
            # Escludi nomi prodotti/videogiochi
            'victory', 'road', 'standard', 'edition', 'inazuma', 'eleven', 'sports', 'fc',
            'ea', 'sports', 'amazon', 'disponibile', 'sconto', 'gioco', 'completo', 'include',
            'germania', 'trentanove', 'colombia', 'nuova', 'zelanda', 'australia'
        }
        
        # Pattern per escludere nomi prodotti/videogiochi
        product_patterns = [
            r'victory\s+road', r'standard\s+edition', r'inazuma\s+eleven',
            r'ea\s+sports', r'sports\s+fc', r'edition\s+per', r'disponibile\s+su',
            r'germania\s+trentanove', r'colombia.*nuova\s+zelanda'
        ]
        
        # Metodo 1: Regex patterns (sempre disponibile)
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                words = match.split()
                # Deve avere almeno 2 parole, entrambe con iniziale maiuscola
                if len(words) >= 2:
                    # Verifica che entrambe le parole inizino con maiuscola
                    if all(word[0].isupper() for word in words if word):
                        # Filtra parole comuni
                        if not any(word.lower() in common_words for word in words):
                            # Filtra nomi troppo corti (ogni parola almeno 3 caratteri)
                            if all(len(word) >= 3 for word in words):
                                # Filtra se contiene numeri o caratteri speciali (tranne trattino)
                                if all(re.match(r'^[A-Za-zÀ-ÿ-]+$', word) for word in words):
                                    # Filtra se è una frase comune o nome prodotto
                                    excluded_phrases = [
                                        'che tonfo', 'anche allegri', 'zidane anche', 'per sei', 'anni uno',
                                        'ha rilasciato', 'stato noccup', 'victory road', 'standard edition',
                                        'inazuma eleven', 'ea sports', 'sports fc', 'edition per',
                                        'germania trentanove', 'nuova zelanda', 'manuel neuer'  # Neuer è un giocatore ma qui è false positive
                                    ]
                                    # Escludi se matcha pattern prodotti
                                    is_product = any(re.search(pattern, match.lower()) for pattern in product_patterns)
                                    if not is_product and not any(phrase in match.lower() for phrase in excluded_phrases):
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
                        words = clean_name.split()
                        
                        # Verifica che non contenga parole comuni
                        if not any(word.lower() in common_words for word in words):
                            # Verifica che ogni parola sia almeno 3 caratteri
                            if all(len(word) >= 3 for word in words):
                                # Rimuovi prefissi come "Infortunato", "Assente", ecc.
                                for prefix in ['infortunato', 'assente', 'squalificato', 'stop', 'squalificato']:
                                    if clean_name.lower().startswith(prefix):
                                        clean_name = clean_name[len(prefix):].strip()
                                
                                # Verifica formato finale
                                if len(clean_name) > 5 and len(clean_name.split()) >= 2:
                                    # Filtra se contiene parole comuni dopo pulizia
                                    if not any(word.lower() in common_words for word in clean_name.split()):
                                        names.add(clean_name)
            except Exception:
                # Se spacy fallisce, continua con solo regex
                pass
        
        # Filtra ulteriormente: rimuovi nomi che sono chiaramente false positives
        filtered_names = set()
        for name in names:
            words = name.split()
            # Escludi se contiene solo parole comuni o troppo corte
            if all(len(word) >= 3 for word in words):
                if not any(word.lower() in common_words for word in words):
                    # Escludi se sembra una frase (troppe parole o pattern sospetti)
                    if len(words) <= 3:  # Max 3 parole per un nome
                        filtered_names.add(name)
        
        # Ordina per frequenza nel testo
        name_counts = Counter()
        for name in filtered_names:
            name_counts[name] = text.lower().count(name.lower())
        
        # Restituisci i nomi più frequenti (almeno menzionati 2 volte per essere più sicuri)
        sorted_names = []
        for name, count in name_counts.most_common(max_names * 2):  # Prendi più candidati
            if count >= 1:  # Almeno menzionato 1 volta
                sorted_names.append(name)
                if len(sorted_names) >= max_names:
                    break
        
        return sorted_names
    
    def extract_formations(self, text: str) -> List[str]:
        """
        Estrae formazioni tattiche da un testo - MIGLIORATO per multilingua
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di formazioni trovate (es: ['4-3-3', '4-4-2'])
        """
        formations = set()
        
        # Pattern multilingua per formazioni
        formation_keywords = [
            'formazione', 'lineup', 'formation', 'formação', 'alineación',
            'composition', 'aufstellung', 'probable', 'probable', 'ufficiale',
            'official', 'starting', 'xi', '11'
        ]
        
        # Cerca pattern formazioni (pattern originali)
        for pattern in self.formation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Valida formato formazione (es: 4-3-3, 3-5-2)
                if re.match(r'^[0-9]-[0-9]-[0-9]$', match):
                    formations.add(match)
        
        # Cerca anche formazioni scritte in modo diverso (con/senza spazi)
        alt_patterns = [
            r'\b([0-9])\s*-\s*([0-9])\s*-\s*([0-9])\b',  # 4 - 3 - 3
            r'\b([0-9])-([0-9])-([0-9])\b',  # 4-3-3
            r'\b([0-9])\s+([0-9])\s+([0-9])\b',  # 4 3 3 (senza trattini)
        ]
        
        for alt_pattern in alt_patterns:
            alt_matches = re.findall(alt_pattern, text)
            for match in alt_matches:
                if len(match) == 3:
                    formation = f"{match[0]}-{match[1]}-{match[2]}"
                    # Valida che sia una formazione valida (somma = 10 o 11)
                    try:
                        total = int(match[0]) + int(match[1]) + int(match[2])
                        if 8 <= total <= 11:  # Formazioni valide
                            formations.add(formation)
                    except:
                        pass
        
        # Cerca formazioni vicine a keywords (es: "formazione 4-3-3")
        for keyword in formation_keywords:
            pattern = rf'{keyword}[\s:]+([0-9]-[0-9]-[0-9])'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if re.match(r'^[0-9]-[0-9]-[0-9]$', match):
                    formations.add(match)
        
        return list(formations)
    
    def extract_injuries(self, text: str) -> List[Dict[str, Any]]:
        """
        Estrae informazioni su infortuni da un testo - MIGLIORATO per multilingua
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di dict con 'player', 'status', 'context'
        """
        injuries = []
        
        # Keywords multilingua per infortuni
        injury_keywords_multilang = [
            'infortunato', 'infortunio', 'stop', 'indisponibile', 'assente',
            'squalificato', 'sospeso', 'problema', 'lesione', 'trauma',
            'injury', 'injured', 'out', 'doubt', 'doubtful', 'hurt',
            'lesão', 'lesionado', 'lesión', 'blessé', 'verletzt',
            'suspended', 'banned', 'suspenso', 'suspendido', 'suspendu', 'gesperrt'
        ]
        
        # Pattern multilingua migliorati
        injury_patterns_enhanced = [
            # Italiano
            r'(?:infortunato|stop|indisponibile|assente|squalificato)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s]+(?:infortunato|stop|indisponibile|assente)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s]+(?:subisce|ha subito|ha riportato)[\s]+(?:un\s+)?infortunio',
            # Inglese
            r'(?:injured|out|hurt|suspended|banned)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s]+(?:injured|out|hurt|suspended|banned)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s]+(?:suffered|sustained)[\s]+(?:an?\s+)?injury',
            # Portoghese/Spagnolo
            r'(?:lesionado|lesionado|suspenso|suspendido)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s]+(?:lesionado|suspenso)',
        ]
        
        # Cerca pattern infortuni con nomi (pattern originali + enhanced)
        all_patterns = self.injury_patterns + injury_patterns_enhanced
        for pattern in all_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                player_name = match.group(1) if match.groups() else None
                if player_name and len(player_name.split()) >= 2:  # Almeno 2 parole
                    # Estrai contesto (frase completa)
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    # Determina status (multilingua)
                    status = 'unknown'
                    context_lower = context.lower()
                    if any(kw in context_lower for kw in ['stop', 'fuori', 'out', 'ausente', 'ausente']):
                        status = 'out'
                    elif any(kw in context_lower for kw in ['dubbio', 'doubt', 'doubtful', 'dúvida']):
                        status = 'doubtful'
                    elif any(kw in context_lower for kw in ['squalificato', 'sospeso', 'suspended', 'banned', 'suspenso', 'suspendido', 'gesperrt']):
                        status = 'suspended'
                    elif any(kw in context_lower for kw in ['infortunato', 'injured', 'hurt', 'lesionado', 'blessé', 'verletzt']):
                        status = 'injured'
                    
                    injuries.append({
                        'player': player_name.strip(),
                        'status': status,
                        'context': context
                    })
        
        # Rimuovi duplicati (stesso giocatore)
        seen_players = set()
        unique_injuries = []
        for injury in injuries:
            player = injury['player'].lower()
            if player not in seen_players:
                seen_players.add(player)
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

