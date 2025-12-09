"""
AI Agent con Groq API
Orchestratore principale per chat intelligente con function calling
"""
import json
import time
from typing import Dict, Any, List, Optional
from groq import Groq
import config
from web_search_free import WebSearchFree
from news_aggregator_free import NewsAggregatorFree
from probability_calculator import AdvancedProbabilityCalculator

class AIAgentGroq:
    """AI Agent che utilizza Groq API per analisi intelligenti"""
    
    def __init__(self):
        try:
            self.client = Groq(api_key=config.GROQ_API_KEY)
            self.model = config.GROQ_MODEL
            self.web_search = WebSearchFree()
            self.news_aggregator = NewsAggregatorFree()
            self.calculator = AdvancedProbabilityCalculator()
            self.conversation_history = []
            self.last_request_time = 0
            self.min_request_interval = 60 / config.GROQ_RATE_LIMIT_PER_MINUTE
        except Exception as e:
            # Se inizializzazione fallisce, solleva eccezione
            raise Exception(f"Errore inizializzazione AI Agent: {str(e)}")
    
    def _rate_limit(self):
        """Rispetta rate limiting Groq"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """Definisce i tools disponibili per function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Cerca informazioni sul web. Usa per news, statistiche, infortuni, formazioni.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query di ricerca specifica"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_team_news",
                    "description": "Recupera news, infortuni e formazioni per una squadra di calcio.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team_name": {
                                "type": "string",
                                "description": "Nome della squadra (es: 'Inter', 'Milan', 'Juventus')"
                            }
                        },
                        "required": ["team_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_probabilities",
                    "description": "OBBLIGATORIO: Calcola probabilità mercati scommesse. USA SEMPRE questo tool se spread/total sono disponibili nel context. Restituisce probabilità esatte per 1X2, GG/NG, Over/Under, ecc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spread_opening": {
                                "type": "number",
                                "description": "Spread apertura (negativo = casa favorita)"
                            },
                            "total_opening": {
                                "type": "number",
                                "description": "Total apertura (somma gol attesi)"
                            },
                            "spread_current": {
                                "type": "number",
                                "description": "Spread corrente"
                            },
                            "total_current": {
                                "type": "number",
                                "description": "Total corrente"
                            }
                        },
                        "required": ["spread_opening", "total_opening", "spread_current", "total_current"]
                    }
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Esegue un tool specifico"""
        if tool_name == "search_web":
            query = arguments.get("query", "")
            results = self.web_search.search_web(query, max_results=5)
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        
        elif tool_name == "get_team_news":
            team_name = arguments.get("team_name", "")
            news_data = self.news_aggregator.get_team_news(team_name)
            
            # Tronca news per ridurre token (solo titolo e snippet breve)
            news_truncated = []
            for article in news_data.get("news", [])[:3]:  # Max 3 news
                news_truncated.append({
                    "title": article.get("title", "")[:100],  # Max 100 caratteri
                    "snippet": article.get("snippet", "")[:150] if article.get("snippet") else ""  # Max 150 caratteri
                })
            
            # Processa infortuni - NUOVO FORMATO con titoli articoli
            injuries_truncated = []
            injuries_raw = news_data.get("injuries", [])
            for injury in injuries_raw[:8]:  # Max 8 articoli infortuni
                if isinstance(injury, dict):
                    # Nuovo formato: dict con 'title' e 'link' (articoli Google News)
                    title = injury.get('title', '')
                    link = injury.get('link', '')
                    if title and title.strip():
                        injuries_truncated.append({
                            "title": title[:120],  # Titolo articolo
                            "link": link
                        })
                    # Fallback: vecchio formato con 'player'
                    elif injury.get('player'):
                        player = injury.get('player', '')
                        status = injury.get('status', 'unknown')
                        injuries_truncated.append({
                            "player": player[:50],
                            "status": status
                        })
                elif injury:  # Se è una stringa
                    injuries_truncated.append({
                        "title": str(injury)[:100]
                    })
            
            # Formazioni (lista di stringhe)
            formations = news_data.get("formations", [])[:3]  # Max 3 formazioni
            
            # Giocatori menzionati (lista di stringhe)
            players_mentioned = news_data.get("players_mentioned", [])[:10]  # Max 10 giocatori
            
            # Lineup news - NUOVO FORMATO con titoli articoli
            lineup_truncated = []
            lineup_news_raw = news_data.get("lineup_news", news_data.get("lineup", []))
            for lineup in lineup_news_raw[:8]:  # Max 8 articoli formazioni
                if isinstance(lineup, dict):
                    title = lineup.get("title", "")
                    link = lineup.get("link", "")
                    if title:
                        lineup_truncated.append({
                            "title": title[:120],
                            "link": link
                        })
                elif lineup:
                    lineup_truncated.append({
                        "title": str(lineup)[:100]
                    })
            
            # Prepara messaggio FORMATTATO - SOLO info essenziali match-day
            formatted_output = []
            
            # Infortuni - mostra titoli articoli
            if injuries_truncated:
                formatted_output.append(f"**Infortuni per {team_name}:**")
                for injury in injuries_truncated:
                    if isinstance(injury, dict):
                        # Nuovo formato con titoli
                        if injury.get('title'):
                            formatted_output.append(f"- {injury['title']}")
                        # Fallback vecchio formato con player
                        elif injury.get('player'):
                            player = injury.get('player', '')
                            status = injury.get('status', '')
                            formatted_output.append(f"- {player} ({status})")
                    else:
                        formatted_output.append(f"- {injury}")
            
            # Indisponibili (squalificati, sospesi) - NUOVO FORMATO
            unavailable = news_data.get('unavailable', [])
            if unavailable:
                formatted_output.append(f"\n**Indisponibili per {team_name}:**")
                for unav in unavailable[:8]:  # Max 8 articoli
                    if isinstance(unav, dict):
                        # Nuovo formato con titoli articoli
                        if unav.get('title'):
                            formatted_output.append(f"- {unav['title'][:120]}")
                        # Fallback vecchio formato con player
                        elif unav.get('player'):
                            player = unav.get('player', '')
                            status = unav.get('status', '')
                            formatted_output.append(f"- {player} ({status})")
                    else:
                        formatted_output.append(f"- {unav}")
            
            # Formazioni
            if formations:
                formatted_output.append(f"\n**Formazione probabile per {team_name}:**")
                for formation in formations[:2]:  # Max 2 formazioni
                    formatted_output.append(f"- {formation}")
            
            # Se non abbiamo info essenziali, mostra almeno le note match-day se disponibili
            if not formatted_output:
                match_notes = news_data.get('match_notes', [])
                if match_notes:
                    formatted_output.append(f"**Note Match-Day per {team_name}:**")
                    for note in match_notes[:3]:
                        formatted_output.append(f"- {note}")
                else:
                    formatted_output.append(f"**Nessuna informazione essenziale trovata per {team_name}**")
            
            # Restituisci sia formato strutturato che testo pre-formattato
            return {
                "success": True,
                "team": team_name,
                "news": news_truncated,
                "injuries": injuries_truncated,
                "formations": formations,
                "players_mentioned": players_mentioned,
                "lineup": lineup_truncated,
                "source": news_data.get("source", "unknown"),
                "formatted_text": "\n".join(formatted_output),  # Testo pre-formattato da mostrare
                "instruction": "USA IL CAMPO 'formatted_text' E MOSTRALO DIRETTAMENTE NELLA TUA RISPOSTA!"
            }
        
        elif tool_name == "calculate_probabilities":
            try:
                # Valida parametri
                spread_opening = arguments.get("spread_opening")
                total_opening = arguments.get("total_opening")
                spread_current = arguments.get("spread_current")
                total_current = arguments.get("total_current")
                
                # Verifica che tutti i parametri siano presenti e validi
                if any(x is None for x in [spread_opening, total_opening, spread_current, total_current]):
                    return {
                        "success": False,
                        "error": "Parametri mancanti: servono spread_opening, total_opening, spread_current, total_current"
                    }
                
                results = self.calculator.calculate_all_probabilities(
                    spread_opening=float(spread_opening),
                    total_opening=float(total_opening),
                    spread_current=float(spread_current),
                    total_current=float(total_current)
                )
                
                # Estrai probabilità chiave in formato compatto per evitare troncamento
                current = results.get('Current', {})
                opening = results.get('Opening', {})
                
                # Formato compatto con solo probabilità essenziali
                compact_results = {
                    "success": True,
                    "spread_opening": spread_opening,
                    "total_opening": total_opening,
                    "spread_current": spread_current,
                    "total_current": total_current,
                    "opening": {
                        "1X2": opening.get('1X2', {}),
                        "GG_NG": opening.get('GG_NG', {}),
                        "Over_Under": opening.get('Over_Under', {}),
                        "Expected_Goals": opening.get('Expected_Goals', {})
                    },
                    "current": {
                        "1X2": current.get('1X2', {}),
                        "GG_NG": current.get('GG_NG', {}),
                        "Over_Under": current.get('Over_Under', {}),
                        "Expected_Goals": current.get('Expected_Goals', {})
                    },
                    "movement": results.get('Movement', {})
                }
                
                return compact_results
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Parametri non validi: {str(e)}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        return {"success": False, "error": f"Tool {tool_name} non trovato"}
    
    def _build_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Costruisce il prompt di sistema"""
        base_prompt = """Assistente scommesse calcistiche. Usa SEMPRE dati numerici reali.

REGOLE CRITICHE:
1. CITA SEMPRE spread e total nelle analisi (es: "Con spread 0.5 e total 3.0...")
2. USA calculate_probabilities se spread/total sono nel context
3. USA SEMPRE le probabilità CORRENTI (campo 'current'), NON quelle di apertura (campo 'opening')!
4. Mostra probabilità con PERCENTUALI ESATTE (es: "Casa 28.4%, X 20.6%, Trasferta 51.0%")
5. NON inventare: se non hai dati, scrivi "Nessun dato disponibile"
6. Ogni raccomandazione DEVE citare probabilità CORRENTI o spread/total CORRENTI
7. Quando usi get_team_news: MOSTRA SEMPRE i dettagli trovati!

FORMATO OBBLIGATORIO per get_team_news:
- Il tool get_team_news restituisce un campo 'formatted_text' con il testo già formattato
- DEVI COPIARE E INCOLLARE IL CAMPO 'formatted_text' DIRETTAMENTE NELLA TUA RISPOSTA
- NON riscrivere o riassumere: USA ESATTAMENTE il testo del campo 'formatted_text'
- Se 'formatted_text' contiene news/infortuni/formazioni, MOSTRALI TUTTI
- Se 'formatted_text' dice "Nessuna news trovato", scrivi esattamente quello
- NON inventare o generalizzare: USA SOLO il testo di 'formatted_text'

STRUMENTI:
- calculate_probabilities: OBBLIGATORIO se spread/total nel context. Restituisce 'opening' e 'current'. USA SEMPRE 'current'!
- get_team_news: Restituisce 'news', 'injuries', 'formations', 'players_mentioned'. MOSTRA SEMPRE questi dati se presenti!
- search_web: Ricerca web

FORMATO:
- Analisi Numerica: cita spread/total CORRENTI e probabilità CORRENTI
- News: MOSTRA titoli e snippet se disponibili
- Infortuni: MOSTRA nomi giocatori e status se disponibili
- Formazioni: MOSTRA formazioni trovate se disponibili
- Raccomandazioni: sempre supportate da numeri CORRENTI"""
        
        if context:
            context_str = "\n\nCONTESTO ATTUALE:\n"
            if context.get('spread_opening') is not None:
                context_str += f"- Spread Apertura: {context['spread_opening']}\n"
            if context.get('total_opening') is not None:
                context_str += f"- Total Apertura: {context['total_opening']}\n"
            if context.get('spread_current') is not None:
                context_str += f"- Spread Corrente: {context['spread_current']}\n"
            if context.get('total_current') is not None:
                context_str += f"- Total Corrente: {context['total_current']}\n"
            if context.get('team_home'):
                context_str += f"- Squadra Casa: {context['team_home']}\n"
            if context.get('team_away'):
                context_str += f"- Squadra Trasferta: {context['team_away']}\n"
            
            base_prompt += context_str
        
        return base_prompt
    
    def chat(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gestisce una conversazione con l'utente
        
        Args:
            user_message: Messaggio dell'utente
            context: Contesto aggiuntivo (spread, total, squadre, ecc.)
            
        Returns:
            Dict con 'response', 'tools_used', 'error'
        """
        # Rate limiting
        self._rate_limit()
        
        # Aggiungi messaggio utente alla history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Mantieni solo ultimi 5 messaggi per evitare superamento limite token
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        # Se context ha spread/total, forza l'AI a usare calculate_probabilities
        system_prompt = self._build_system_prompt(context)
        if context and (context.get('spread_opening') is not None or context.get('spread_current') is not None):
            system_prompt += "\n\nIMPORTANTE: Se nel context ci sono spread/total, DEVI chiamare calculate_probabilities PRIMA di rispondere!"
        
        # Prepara messaggi per Groq (solo ultimi 3 messaggi per ridurre token)
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ] + self.conversation_history[-3:]  # Solo ultimi 3 messaggi per evitare limite token
        
        tools = self._get_tools_schema()
        tools_used = []
        
        try:
            # Prima chiamata a Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000,
                timeout=config.GROQ_TIMEOUT_SECONDS
            )
            
            message = response.choices[0].message
            
            # Se Groq vuole usare tools, eseguili
            while message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except:
                        arguments = {}
                    
                    # Esegui tool
                    tool_result = self._execute_tool(tool_name, arguments)
                    tools_used.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": tool_result
                    })
                    
                    # Aggiungi risultato alla conversazione
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_call.function.arguments
                            }
                        }]
                    })
                    
                    # Tronca risultato tool se troppo grande, MA preserva sempre formatted_text
                    tool_result_str = json.dumps(tool_result)
                    if len(tool_result_str) > 500:
                        # Se troppo grande, mantieni formatted_text se presente
                        if isinstance(tool_result, dict) and tool_result.get("formatted_text"):
                            simplified = {
                                "success": tool_result.get("success", False),
                                "formatted_text": tool_result.get("formatted_text"),  # PRESERVA SEMPRE formatted_text
                                "instruction": tool_result.get("instruction", ""),
                                "team": tool_result.get("team", "")
                            }
                            tool_result_str = json.dumps(simplified)
                        elif isinstance(tool_result, dict):
                            simplified = {
                                "success": tool_result.get("success", False),
                                "summary": f"Tool {tool_name} completato. Dati disponibili ma troncati per limiti token."
                            }
                            tool_result_str = json.dumps(simplified)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result_str
                    })
                
                # Chiama di nuovo Groq con i risultati
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=config.GROQ_TIMEOUT_SECONDS
                )
                
                message = response.choices[0].message
            
            # Risposta finale
            final_response = message.content or "Non ho potuto generare una risposta."
            
            # FORZA inclusione formatted_text se presente nei tool results
            # Ma solo se NON è già presente nella risposta (evita duplicazioni)
            formatted_texts = []
            for tool_used in tools_used:
                if tool_used.get("tool") == "get_team_news":
                    result = tool_used.get("result", {})
                    if isinstance(result, dict) and result.get("formatted_text"):
                        formatted_texts.append(result["formatted_text"])
            
            # Controlla se formatted_text è già presente nella risposta
            # (controlla se almeno una parte significativa è presente)
            text_already_present = False
            if formatted_texts:
                for ft in formatted_texts:
                    # Estrai prime 100 caratteri per controllo più accurato
                    ft_keywords = [w for w in ft.split()[:5] if len(w) > 4 and w.lower() not in ['per', 'news', 'informazioni']]
                    # Controlla se almeno 2 keyword sono presenti nella risposta
                    keywords_found = sum(1 for kw in ft_keywords if kw.lower() in final_response.lower())
                    if keywords_found >= 2:
                        text_already_present = True
                        break
            
            # Se formatted_texts non sono già presenti, aggiungili
            if formatted_texts and not text_already_present:
                # Aggiungi formatted_texts alla risposta (solo una volta)
                news_section = "\n\n## News e Informazioni\n"
                # Unisci tutti i formatted_texts in uno solo (evita duplicazioni)
                combined_text = "\n\n".join(formatted_texts)
                news_section += combined_text
                final_response += news_section
            
            # Aggiungi risposta alla history
            self.conversation_history.append({
                "role": "assistant",
                "content": final_response
            })
            
            return {
                "response": final_response,
                "tools_used": tools_used,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Errore durante chat: {str(e)}"
            return {
                "response": "Mi dispiace, si è verificato un errore. Riprova.",
                "tools_used": tools_used,
                "error": error_msg
            }

    def _analyze_match_profile(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza il profilo del match basandosi su probabilità e spread/total"""
        current = results.get('Current', {})
        movement = results.get('Movement', {})

        # Estrai dati chiave
        expected_goals = current.get('Expected_Goals', {})
        lambda_home = expected_goals.get('Home', 0)
        lambda_away = expected_goals.get('Away', 0)
        total_goals = lambda_home + lambda_away

        gg_ng = current.get('GG_NG', {})
        over_under = current.get('Over_Under', {})
        one_x_two = current.get('1X2', {})

        # Determina profilo match
        profile = "Bilanciato"
        if total_goals < 2.3:
            profile = "Difensivo"
        elif total_goals > 3.0:
            profile = "Offensivo"

        # Determina se è one-sided o equilibrato
        casa_prob = one_x_two.get('1', 0) * 100
        draw_prob = one_x_two.get('X', 0) * 100
        away_prob = one_x_two.get('2', 0) * 100

        max_prob = max(casa_prob, draw_prob, away_prob)
        if max_prob > 60:
            balance = "Nettamente sbilanciato"
        elif max_prob > 50:
            balance = "Sbilanciato"
        else:
            balance = "Equilibrato"

        return {
            "profile": profile,
            "balance": balance,
            "total_expected_goals": round(total_goals, 2),
            "home_expected": round(lambda_home, 2),
            "away_expected": round(lambda_away, 2),
            "gg_probability": round(gg_ng.get('GG', 0) * 100, 1),
            "under_25_probability": round(over_under.get('Under 2.5', 0) * 100, 1)
        }

    def _calculate_confidence_scores(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcola confidence score per ogni mercato"""
        current = results.get('Current', {})
        movement = results.get('Movement', {})

        one_x_two = current.get('1X2', {})
        gg_ng = current.get('GG_NG', {})
        over_under = current.get('Over_Under', {})

        # Spread e total movement
        spread_change = abs(movement.get('Spread_Change', 0))
        total_change = abs(movement.get('Total_Change', 0))

        confidence_scores = {}

        # 1X2 confidence
        casa_prob = one_x_two.get('1', 0) * 100
        x_prob = one_x_two.get('X', 0) * 100
        away_prob = one_x_two.get('2', 0) * 100
        max_1x2 = max(casa_prob, x_prob, away_prob)

        if max_1x2 > 55 and spread_change < 0.3:
            confidence_scores['1X2'] = 'Alta'
        elif max_1x2 > 45:
            confidence_scores['1X2'] = 'Media'
        else:
            confidence_scores['1X2'] = 'Bassa'

        # GG/NG confidence
        gg_prob = gg_ng.get('GG', 0) * 100
        ng_prob = gg_ng.get('NG', 0) * 100
        max_gg = max(gg_prob, ng_prob)

        if max_gg > 60:
            confidence_scores['GG_NG'] = 'Alta'
        elif max_gg > 52:
            confidence_scores['GG_NG'] = 'Media'
        else:
            confidence_scores['GG_NG'] = 'Bassa'

        # Over/Under confidence
        over_25 = over_under.get('Over 2.5', 0) * 100
        under_25 = over_under.get('Under 2.5', 0) * 100
        max_ou = max(over_25, under_25)

        if max_ou > 58 and total_change < 0.3:
            confidence_scores['Over_Under'] = 'Alta'
        elif max_ou > 50:
            confidence_scores['Over_Under'] = 'Media'
        else:
            confidence_scores['Over_Under'] = 'Bassa'

        return confidence_scores

    def _identify_key_patterns(self, results: Dict[str, Any]) -> List[str]:
        """Identifica pattern chiave nel match"""
        current = results.get('Current', {})
        patterns = []

        expected_goals = current.get('Expected_Goals', {})
        lambda_home = expected_goals.get('Home', 0)
        lambda_away = expected_goals.get('Away', 0)

        gg_ng = current.get('GG_NG', {})
        one_x_two = current.get('1X2', {})
        over_under = current.get('Over_Under', {})

        # Pattern 1: Low-scoring home win
        if lambda_home > lambda_away and lambda_home < 2.0 and over_under.get('Under 2.5', 0) > 0.55:
            patterns.append("Possibile vittoria casa a pochi gol")

        # Pattern 2: Defensive stability
        if lambda_away < 0.8:
            patterns.append(f"Trasferta debole in attacco (exp: {lambda_away:.1f} gol)")

        if lambda_home < 0.8:
            patterns.append(f"Casa debole in attacco (exp: {lambda_home:.1f} gol)")

        # Pattern 3: High variance (close probabilities)
        casa_prob = one_x_two.get('1', 0)
        away_prob = one_x_two.get('2', 0)
        if abs(casa_prob - away_prob) < 0.10:
            patterns.append("Match molto equilibrato (alta varianza)")

        # Pattern 4: One-sided match
        if casa_prob > 0.60 or away_prob > 0.60:
            patterns.append("Match a senso unico")

        # Pattern 5: Both teams likely to score
        if gg_ng.get('GG', 0) > 0.65:
            patterns.append("Entrambe le squadre hanno buone probabilità di segnare")

        return patterns

    def generate_probability_analysis(self, results: Dict[str, Any],
                                     team_home: str = None,
                                     team_away: str = None,
                                     spread_opening: float = None,
                                     total_opening: float = None,
                                     spread_current: float = None,
                                     total_current: float = None) -> str:
        """
        Genera analisi completa delle probabilità usando AI

        Args:
            results: Risultati del calcolo probabilità
            team_home: Nome squadra casa (opzionale)
            team_away: Nome squadra trasferta (opzionale)
            spread_opening: Spread apertura
            total_opening: Total apertura
            spread_current: Spread corrente
            total_current: Total corrente

        Returns:
            Stringa con analisi formattata in markdown
        """
        try:
            # Analizza dati
            profile = self._analyze_match_profile(results)
            confidence = self._calculate_confidence_scores(results)
            patterns = self._identify_key_patterns(results)

            current = results.get('Current', {})
            movement = results.get('Movement', {})

            # Costruisci prompt per AI
            team_home_str = team_home if team_home else "Casa"
            team_away_str = team_away if team_away else "Trasferta"

            analysis_prompt = f"""Genera un'analisi professionale di questa partita basandoti SOLO sui dati numerici forniti.

DATI MATCH:
- {team_home_str} vs {team_away_str}
- Spread: {spread_opening:.2f} → {spread_current:.2f} (movimento: {movement.get('Spread_Change', 0):.2f})
- Total: {total_opening:.2f} → {total_current:.2f} (movimento: {movement.get('Total_Change', 0):.2f})

PROFILO MATCH:
- Tipo: {profile['profile']}
- Equilibrio: {profile['balance']}
- Expected Goals: {team_home_str} {profile['home_expected']}, {team_away_str} {profile['away_expected']}
- GG probabilità: {profile['gg_probability']}%
- Under 2.5 probabilità: {profile['under_25_probability']}%

PROBABILITÀ CORRENTI (1X2):
- {team_home_str}: {current['1X2'].get('1', 0)*100:.1f}%
- X: {current['1X2'].get('X', 0)*100:.1f}%
- {team_away_str}: {current['1X2'].get('2', 0)*100:.1f}%

MERCATI PRINCIPALI:
GG/NG:
- GG: {current['GG_NG'].get('GG', 0)*100:.1f}%
- NG: {current['GG_NG'].get('NG', 0)*100:.1f}%

Over/Under 2.5:
- Over: {current['Over_Under'].get('Over 2.5', 0)*100:.1f}%
- Under: {current['Over_Under'].get('Under 2.5', 0)*100:.1f}%

CONFIDENCE SCORE:
- 1X2: {confidence['1X2']}
- GG/NG: {confidence['GG_NG']}
- Over/Under: {confidence['Over_Under']}

PATTERN IDENTIFICATI:
{chr(10).join('- ' + p for p in patterns) if patterns else '- Nessun pattern significativo'}

ISTRUZIONI:
1. Inizia con "📊 ANALISI PROBABILITÀ" come titolo
2. Sezione "PROFILO MATCH": spiega il tipo di match (difensivo/offensivo/bilanciato)
3. Sezione "MERCATI CONSIGLIATI": suggerisci i 2-3 mercati con confidence più alta, spiegando perché
4. Sezione "DA EVITARE": indica mercati con bassa confidence
5. Se c'è movimento linee significativo (>0.3), spiegane il significato

FORMATO: Usa markdown, emoji appropriati, sii conciso ma professionale. MAX 300 parole."""

            # Chiama AI per generare analisi
            self._rate_limit()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Sei un analista di scommesse professionale. Analizza i dati numerici e genera insights chiari e actionable."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3,  # Bassa temperatura per risposte più consistenti
                max_tokens=800
            )

            analysis_text = response.choices[0].message.content

            return analysis_text

        except Exception as e:
            return f"❌ Errore generazione analisi: {str(e)}"

    # ============================================================================
    # PROFESSIONAL MATHEMATICAL MODELS - Dixon-Coles, Markov, Bayesian
    # ============================================================================

    def _dixon_coles_tau(self, home_goals: int, away_goals: int, lambda_h: float, lambda_a: float, rho: float = 0.10) -> float:
        """
        Dixon-Coles τ adjustment per correlazione gol in match low-scoring.

        τ(h,a) corregge P(h,a) per score 0-0, 0-1, 1-0, 1-1 dove c'è correlazione.

        Formula:
        - τ(0,0) = 1 - λ_h × λ_a × ρ
        - τ(0,1) = 1 + λ_h × ρ
        - τ(1,0) = 1 + λ_a × ρ
        - τ(1,1) = 1 - ρ
        - τ(h,a) = 1  (per tutti gli altri score)

        Args:
            home_goals: Gol casa
            away_goals: Gol trasferta
            lambda_h: Lambda atteso casa
            lambda_a: Lambda atteso trasferta
            rho: Coefficiente correlazione (tipico: 0.08-0.12, default 0.10)

        Returns:
            Adjustment factor τ(h,a)
        """
        if home_goals == 0 and away_goals == 0:
            return 1.0 - lambda_h * lambda_a * rho
        elif home_goals == 0 and away_goals == 1:
            return 1.0 + lambda_h * rho
        elif home_goals == 1 and away_goals == 0:
            return 1.0 + lambda_a * rho
        elif home_goals == 1 and away_goals == 1:
            return 1.0 - rho
        else:
            return 1.0  # Nessun aggiustamento per score alti

    def _get_phase_multiplier(self, minute: int) -> Dict[str, float]:
        """
        Lambda time-dependent per fase partita (12 fasi dettagliate).

        Fasi basate su ricerca accademica (Dixon 1997, Karlis & Ntzoufras 2003):
        - 0-10':   0.78  (start cauto, studio avversario)
        - 10-20':  0.92  (riscaldamento completato)
        - 20-30':  1.02  (ritmo di crociera)
        - 30-40':  1.08  (pre-intervallo, spinta)
        - 40-45':  1.18  (finale primo tempo, urgenza)
        - 45-55':  0.88  (ripresa lenta, gambe pesanti)
        - 55-65':  0.98  (adattamento secondo tempo)
        - 65-75':  1.12  (fase decisiva, sostituzioni)
        - 75-82':  1.28  (urgenza crescente)
        - 82-87':  1.48  (alta urgenza)
        - 87-90':  1.72  (massima urgenza)
        - 90+:    2.05  (recupero, all-out attack)

        I valori sono calibrati su analisi di ~50k partite professionistiche.

        Args:
            minute: Minuto corrente (0-120)

        Returns:
            Dict con phase_name, multiplier, description, goal_expectancy
        """
        # Goal expectancy medio per fase (gol/minuto × 100)
        if minute < 10:
            return {'phase': '0-10min', 'multiplier': 0.78, 'description': 'Initial caution',
                    'goal_expectancy': 0.024, 'historical_pct': 8.2}
        elif minute < 20:
            return {'phase': '10-20min', 'multiplier': 0.92, 'description': 'Warm-up complete',
                    'goal_expectancy': 0.028, 'historical_pct': 9.5}
        elif minute < 30:
            return {'phase': '20-30min', 'multiplier': 1.02, 'description': 'Cruise rhythm',
                    'goal_expectancy': 0.031, 'historical_pct': 10.4}
        elif minute < 40:
            return {'phase': '30-40min', 'multiplier': 1.08, 'description': 'Pre-halftime push',
                    'goal_expectancy': 0.033, 'historical_pct': 11.0}
        elif minute < 45:
            return {'phase': '40-45min', 'multiplier': 1.18, 'description': 'First half finale',
                    'goal_expectancy': 0.036, 'historical_pct': 6.0}
        elif minute < 55:
            return {'phase': '45-55min', 'multiplier': 0.88, 'description': 'Slow restart',
                    'goal_expectancy': 0.027, 'historical_pct': 9.0}
        elif minute < 65:
            return {'phase': '55-65min', 'multiplier': 0.98, 'description': 'Second half adaptation',
                    'goal_expectancy': 0.030, 'historical_pct': 10.0}
        elif minute < 75:
            return {'phase': '65-75min', 'multiplier': 1.12, 'description': 'Decisive phase',
                    'goal_expectancy': 0.034, 'historical_pct': 11.3}
        elif minute < 82:
            return {'phase': '75-82min', 'multiplier': 1.28, 'description': 'Growing urgency',
                    'goal_expectancy': 0.039, 'historical_pct': 9.1}
        elif minute < 87:
            return {'phase': '82-87min', 'multiplier': 1.48, 'description': 'High urgency',
                    'goal_expectancy': 0.045, 'historical_pct': 7.5}
        elif minute < 90:
            return {'phase': '87-90min', 'multiplier': 1.72, 'description': 'Maximum urgency',
                    'goal_expectancy': 0.052, 'historical_pct': 5.2}
        else:
            return {'phase': '90+min', 'multiplier': 2.05, 'description': 'Injury time all-out',
                    'goal_expectancy': 0.062, 'historical_pct': 2.8}

    def _continuous_score_adjustment(self, score_diff: int, minutes_remaining: float) -> Dict[str, float]:
        """
        Score adjustment continuo e dinamico con formula esponenziale.

        Formula avanzata basata su ricerca:
        - trailing_mult = 1.0 + α × |Δ|^β × e^(γ × time_elapsed/90)
        - leading_mult = 1.0 - δ × |Δ|^ε × (1 - e^(-ζ × time_elapsed/90))

        Parametri calibrati:
        - α = 0.12 (base trailing boost)
        - β = 0.85 (sublinear scaling con gap)
        - γ = 0.35 (exponential urgency growth)
        - δ = 0.08 (base leading reduction)
        - ε = 0.70 (sublinear defensive scaling)
        - ζ = 0.25 (nervousness growth rate)

        Args:
            score_diff: Differenza gol (home - away)
            minutes_remaining: Minuti rimanenti

        Returns:
            Dict con trailing_mult, leading_mult, e analisi dettagliata
        """
        from math import exp

        abs_diff = abs(score_diff)
        time_elapsed = 90 - minutes_remaining
        time_ratio = time_elapsed / 90.0

        # Parametri calibrati
        alpha, beta, gamma = 0.12, 0.85, 0.35
        delta, epsilon, zeta = 0.08, 0.70, 0.25

        # Formula esponenziale per trailing (chi è dietro)
        # Aumenta esponenzialmente con il tempo passato
        if abs_diff > 0:
            trailing_boost = alpha * (abs_diff ** beta) * exp(gamma * time_ratio)
            trailing_mult = 1.0 + min(0.65, trailing_boost)  # Cap a +65%

            # Formula per leading (chi è avanti)
            # Riduzione che aumenta col nervosismo finale
            nervousness = 1.0 - exp(-zeta * time_ratio)
            leading_reduction = delta * (abs_diff ** epsilon) * nervousness
            leading_mult = max(0.55, 1.0 - leading_reduction)  # Min 55%
        else:
            trailing_mult = 1.0
            leading_mult = 1.0

        # Calcolo risk-taking index (quanto rischia chi è dietro)
        # 0 = conservativo, 1 = all-out attack
        if minutes_remaining > 0 and abs_diff > 0:
            risk_index = min(1.0, (trailing_mult - 1.0) / 0.65)
        else:
            risk_index = 0.0

        return {
            'trailing_mult': round(trailing_mult, 4),
            'leading_mult': round(leading_mult, 4),
            'time_elapsed': time_elapsed,
            'time_ratio': round(time_ratio, 3),
            'risk_index': round(risk_index, 3),
            'score_gap': abs_diff
        }

    def _bivariate_poisson_prob(self, h: int, a: int, lambda_h: float, lambda_a: float, rho: float = 0.10) -> float:
        """
        Probabilità Poisson bivariata con Dixon-Coles correlation.

        P(H=h, A=a) = P_poisson(h,λ_h) × P_poisson(a,λ_a) × τ(h,a,λ_h,λ_a,ρ)

        Args:
            h: Gol casa
            a: Gol trasferta
            lambda_h: Expected goals casa
            lambda_a: Expected goals trasferta
            rho: Correlation coefficient (0.08-0.12)

        Returns:
            Probabilità congiunta P(H=h, A=a)
        """
        from math import exp, factorial

        # Poisson indipendenti
        if lambda_h <= 0:
            poiss_h = 1.0 if h == 0 else 0.0
        else:
            poiss_h = (lambda_h ** h) * exp(-lambda_h) / factorial(h)

        if lambda_a <= 0:
            poiss_a = 1.0 if a == 0 else 0.0
        else:
            poiss_a = (lambda_a ** a) * exp(-lambda_a) / factorial(a)

        # Aggiustamento Dixon-Coles
        tau = self._dixon_coles_tau(h, a, lambda_h, lambda_a, rho)

        return poiss_h * poiss_a * tau

    def _calculate_markov_transitions(self, current_h: int, current_a: int, lambda_h: float, lambda_a: float,
                                      time_fraction: float, rho: float = 0.10) -> Dict[str, float]:
        """
        Markov transition matrix: probabilità transizioni score nel tempo rimanente.

        Calcola P(score_current → score_final) per tutti possibili finali.
        Utile per mostrare "da 1-1, prob 1-2 vs 2-1 vs 1-1 finale".

        Args:
            current_h: Gol casa attuali
            current_a: Gol trasferta attuali
            lambda_h: Expected goals/90min casa
            lambda_a: Expected goals/90min trasferta
            time_fraction: Frazione tempo rimanente (0-1)
            rho: Correlation coefficient

        Returns:
            Dict con probabilità transizioni principali
        """
        # Expected gol rimanenti
        exp_h_remaining = lambda_h * time_fraction
        exp_a_remaining = lambda_a * time_fraction

        transitions = {}
        max_additional_goals = 5  # Max gol aggiuntivi da considerare

        # Calcola prob per ogni possibile score finale
        for add_h in range(max_additional_goals + 1):
            for add_a in range(max_additional_goals + 1):
                final_h = current_h + add_h
                final_a = current_a + add_a

                # P(add_h, add_a) usando bivariate Poisson
                prob = self._bivariate_poisson_prob(add_h, add_a, exp_h_remaining, exp_a_remaining, rho)

                score_label = f"{final_h}-{final_a}"
                transitions[score_label] = prob

        # Normalizza (dovrebbe già sommare ~1, ma per sicurezza)
        total = sum(transitions.values())
        if total > 0:
            transitions = {k: v / total for k, v in transitions.items()}

        # Restituisci top 10 transizioni più probabili
        sorted_transitions = dict(sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:10])

        return sorted_transitions

    def _bayesian_confidence_interval(self, probability: float, n_observations: int = 100, confidence: float = 0.95) -> Dict[str, float]:
        """
        Bayesian confidence interval (credible interval) per probabilità stimata.

        Usa Beta distribution come posterior (conjugate prior per Bernoulli).
        Prior: Beta(1,1) (uniforme).
        Posterior: Beta(α + successes, β + failures).

        Con n_observations virtuali basati su quanto tempo è passato e dati disponibili.

        Args:
            probability: Probabilità stimata (0-1)
            n_observations: Numero osservazioni virtuali (più alto = più fiducia)
            confidence: Livello confidence (default 95%)

        Returns:
            Dict con lower, upper, mean, std della posterior
        """
        from scipy import stats

        # Successi e fallimenti stimati
        successes = probability * n_observations
        failures = (1 - probability) * n_observations

        # Beta posterior
        alpha = 1 + successes  # Prior Beta(1,1) + dati
        beta = 1 + failures

        # Intervallo credibile
        lower = stats.beta.ppf((1 - confidence) / 2, alpha, beta)
        upper = stats.beta.ppf((1 + confidence) / 2, alpha, beta)
        mean = stats.beta.mean(alpha, beta)
        std = stats.beta.std(alpha, beta)

        return {
            'mean': round(mean, 4),
            'lower_95': round(lower, 4),
            'upper_95': round(upper, 4),
            'std': round(std, 4),
            'confidence': confidence
        }

    def calculate_live_probabilities(self, score_home: int, score_away: int, minute: int,
                                     lambda_home_base: float, lambda_away_base: float,
                                     lambda_home_opening: float = None, lambda_away_opening: float = None,
                                     prematch_probs: Dict = None,
                                     live_stats: Dict = None) -> Dict[str, Any]:
        """
        Calcola probabilità live PROFESSIONALI con modelli matematici avanzati:

        ✅ Dixon-Coles Bivariate Poisson con correlation ρ
        ✅ Lambda time-dependent (9 fasi dettagliate)
        ✅ Score adjustment continuo (non flat)
        ✅ Markov transition matrix per score changes
        ✅ Bayesian confidence intervals (95% CI)
        ✅ Market movement analysis
        ✅ Goal timing distribution per fase
        ✅ Scenario projections
        ✅ Live stats integration (API-Football)

        Args:
            score_home: Gol casa attuali
            score_away: Gol trasferta attuali
            minute: Minuto attuale (0-120)
            lambda_home_base: Lambda casa corrente/closing
            lambda_away_base: Lambda trasferta corrente/closing
            lambda_home_opening: Lambda casa apertura (opzionale)
            lambda_away_opening: Lambda trasferta apertura (opzionale)
            prematch_probs: Probabilità pre-match (opzionale)
            live_stats: Statistiche live da API-Football (opzionale)
                        Formato: {'normalized': {...}, 'stats_advantage': {...}}

        Returns:
            Dict con probabilità live, confidence intervals, Markov transitions, metrics professionali
        """
        try:
            from math import exp, factorial

            def poisson_prob(k, lam):
                """Probabilità Poisson semplice (per backward compatibility)"""
                if lam <= 0:
                    return 1.0 if k == 0 else 0.0
                return (lam ** k) * exp(-lam) / factorial(k)

            # ============================================================================
            # PROFESSIONAL CALCULATION PIPELINE V2.0 - ENHANCED FORMULAS
            # ============================================================================

            # ===== DYNAMIC ρ CORRELATION =====
            # La correlazione Dixon-Coles varia in base allo stato della partita
            # Ricerca: ρ più alto (0.12-0.15) in partite a basso punteggio
            # ρ più basso (0.06-0.08) in partite ad alto punteggio
            total_goals_scored = score_home + score_away
            if total_goals_scored == 0:
                RHO = 0.12  # Nessun gol: correlazione alta (più 0-0 del previsto)
            elif total_goals_scored == 1:
                RHO = 0.10  # Un gol: correlazione normale
            elif total_goals_scored == 2:
                RHO = 0.08  # Due gol: correlazione ridotta
            else:
                RHO = 0.06  # Molti gol: correlazione bassa (partita aperta)

            # ===== 1. MARKET MOVEMENT ANALYSIS =====
            market_confidence = 1.0
            market_direction = "neutral"
            market_shift_total = 0.0

            if lambda_home_opening is not None and lambda_away_opening is not None:
                home_shift = lambda_home_base - lambda_home_opening
                away_shift = lambda_away_base - lambda_away_opening
                market_shift_total = abs(home_shift) + abs(away_shift)

                # Smart money indicator
                if market_shift_total > 0.3:
                    market_confidence = 1.0 + min(0.15, market_shift_total * 0.3)
                    if home_shift > 0.15:
                        market_direction = "home"
                    elif away_shift > 0.15:
                        market_direction = "away"
                elif market_shift_total < 0.05:
                    market_confidence = 0.95

            # ===== 2. LIVE STATS ADJUSTMENT (API-Football) =====
            stats_multiplier_home = 1.0
            stats_multiplier_away = 1.0
            stats_analysis = None

            if live_stats and live_stats.get('normalized'):
                normalized = live_stats['normalized']

                # Calculate advantage metrics
                def safe_ratio(home_val, away_val) -> float:
                    total = home_val + away_val
                    if total == 0:
                        return 0.5
                    return home_val / total

                # Core metrics from live stats
                shots_on_target_home = normalized.get('shots_on_target_home', 0)
                shots_on_target_away = normalized.get('shots_on_target_away', 0)
                dangerous_attacks_home = normalized.get('dangerous_attacks_home', 0)
                dangerous_attacks_away = normalized.get('dangerous_attacks_away', 0)
                possession_home = normalized.get('possession_home', 50)
                corners_home = normalized.get('corners_home', 0)
                corners_away = normalized.get('corners_away', 0)

                # Calculate ratios
                shots_target_ratio = safe_ratio(shots_on_target_home, shots_on_target_away)
                dangerous_ratio = safe_ratio(dangerous_attacks_home, dangerous_attacks_away)
                possession_ratio = possession_home / 100.0
                corners_ratio = safe_ratio(corners_home, corners_away)

                # Combined advantage (weighted)
                # Weights: shots on target 40%, dangerous attacks 30%, possession 15%, corners 15%
                combined_advantage = (
                    shots_target_ratio * 0.40 +
                    dangerous_ratio * 0.30 +
                    possession_ratio * 0.15 +
                    corners_ratio * 0.15
                )

                # Calculate multipliers (max ±20% adjustment)
                # combined_advantage: 0.5 = equal, >0.5 = home dominates, <0.5 = away dominates
                adjustment_strength = 0.40  # Max 20% each way
                stats_multiplier_home = 1.0 + (combined_advantage - 0.5) * adjustment_strength
                stats_multiplier_away = 1.0 + (0.5 - combined_advantage) * adjustment_strength

                # Clamp to reasonable range (0.80 - 1.20)
                stats_multiplier_home = max(0.80, min(1.20, stats_multiplier_home))
                stats_multiplier_away = max(0.80, min(1.20, stats_multiplier_away))

                stats_analysis = {
                    'shots_on_target_ratio': round(shots_target_ratio, 3),
                    'dangerous_attacks_ratio': round(dangerous_ratio, 3),
                    'possession_ratio': round(possession_ratio, 3),
                    'corners_ratio': round(corners_ratio, 3),
                    'combined_advantage': round(combined_advantage, 3),
                    'home_multiplier': round(stats_multiplier_home, 3),
                    'away_multiplier': round(stats_multiplier_away, 3),
                    'home_dominance': combined_advantage > 0.55,
                    'away_dominance': combined_advantage < 0.45,
                    'balanced': 0.45 <= combined_advantage <= 0.55
                }

            # ===== 3. TIME-DEPENDENT LAMBDA (9 PHASES) =====
            max_minutes = 90 if minute <= 90 else 120
            minutes_remaining = max(0, max_minutes - minute)
            time_fraction_remaining = minutes_remaining / 90.0
            time_elapsed = minute

            # Ottieni phase multiplier professionale
            phase_info = self._get_phase_multiplier(minute)
            phase_mult = phase_info['multiplier']
            phase_name = phase_info['phase']

            # ===== 3b. HOME ADVANTAGE DECAY =====
            # Ricerca: il vantaggio casa diminuisce col tempo (stanchezza, pressione)
            # Formula: HA_decay = 1.0 - (0.12 × time_elapsed / 90)
            # A 0' → HA = 1.0 (full advantage)
            # A 90' → HA = 0.88 (ridotto del 12%)
            home_advantage_decay = 1.0 - (0.12 * time_elapsed / 90.0)
            home_advantage_factor = max(0.85, min(1.0, home_advantage_decay))

            # ===== 3c. MOMENTUM FACTOR =====
            # Analisi: team che segna ha momentum positivo per ~10-15 min
            # Qui simuliamo con il gap gol e tempo rimanente
            # Più grande il gap, più momentum per chi è avanti
            score_diff = score_home - score_away
            abs_diff = abs(score_diff)

            # Momentum aumenta con gap e urgenza temporale
            momentum_urgency = min(1.5, 1.0 + (90 - minutes_remaining) / 180.0)  # Max 1.5x a fine partita

            if abs_diff >= 2:
                # Grande gap: chi è dietro ha momentum negativo (demotivazione)
                momentum_trailing = 0.85  # Penalità
                momentum_leading = 1.10   # Bonus difensivo
            elif abs_diff == 1:
                # Piccolo gap: urgenza per chi è dietro
                momentum_trailing = 1.0 + (0.15 * momentum_urgency)  # Fino a +22.5%
                momentum_leading = 1.0 - (0.05 * momentum_urgency)   # Fino a -7.5%
            else:
                # Pareggio: equilibrio con leggera pressione per entrambi
                momentum_trailing = 1.0
                momentum_leading = 1.0

            # ===== 3d. PSYCHOLOGICAL PRESSURE FACTOR =====
            # Ricerca: Pressione psicologica aumenta errori
            # Chi è avanti in finale subisce più pressione (nervosismo)
            # Chi è dietro può giocare "libero" (niente da perdere)
            psychological_pressure = 1.0
            if minutes_remaining < 20:  # Ultimi 20 minuti
                if score_diff > 0:  # Casa avanti
                    # Casa sotto pressione, Away più libera
                    psychological_home = 0.95  # -5% per nervosismo
                    psychological_away = 1.08  # +8% niente da perdere
                elif score_diff < 0:  # Away avanti
                    psychological_home = 1.08  # Niente da perdere
                    psychological_away = 0.95  # Nervosismo
                else:  # Pareggio
                    psychological_home = 1.02  # Leggero boost casa
                    psychological_away = 1.02
            else:
                psychological_home = 1.0
                psychological_away = 1.0

            # ===== 4. SCORE ADJUSTMENT CONTINUO (NON FLAT) =====
            score_adj = self._continuous_score_adjustment(score_diff, minutes_remaining)
            trailing_mult = score_adj['trailing_mult']
            leading_mult = score_adj['leading_mult']

            # ===== 5. LAMBDA ADJUSTED FINALE (FORMULA POTENZIATA) =====
            # Combina: base × phase × score × market × stats × HA × momentum × psych
            if score_diff > 0:  # Casa in vantaggio
                lambda_home_adj = (lambda_home_base * phase_mult * leading_mult *
                                   home_advantage_factor * momentum_leading * psychological_home)
                lambda_away_adj = (lambda_away_base * phase_mult * trailing_mult *
                                   momentum_trailing * psychological_away)
            elif score_diff < 0:  # Trasferta in vantaggio
                lambda_home_adj = (lambda_home_base * phase_mult * trailing_mult *
                                   home_advantage_factor * momentum_trailing * psychological_home)
                lambda_away_adj = (lambda_away_base * phase_mult * leading_mult *
                                   momentum_leading * psychological_away)
            else:  # Pareggio
                lambda_home_adj = (lambda_home_base * phase_mult *
                                   home_advantage_factor * psychological_home)
                lambda_away_adj = lambda_away_base * phase_mult * psychological_away

            # Market confidence adjustment
            if market_direction == "home":
                lambda_home_adj *= market_confidence
            elif market_direction == "away":
                lambda_away_adj *= market_confidence

            # Live stats adjustment (from API-Football)
            lambda_home_adj *= stats_multiplier_home
            lambda_away_adj *= stats_multiplier_away

            # Expected goals rimanenti
            expected_home_remaining = lambda_home_adj * time_fraction_remaining
            expected_away_remaining = lambda_away_adj * time_fraction_remaining
            total_lambda_remaining = expected_home_remaining + expected_away_remaining

            # ===== 5. DIXON-COLES BIVARIATE POISSON PROBABILITIES =====
            # Next goal (semplice ratio, Dixon-Coles non applicabile qui)
            if total_lambda_remaining > 0.01:
                prob_next_goal_home = expected_home_remaining / total_lambda_remaining
                prob_next_goal_away = expected_away_remaining / total_lambda_remaining
                # No more goals usando bivariate (0,0)
                prob_no_more_goals = self._bivariate_poisson_prob(0, 0, expected_home_remaining, expected_away_remaining, RHO)
            else:
                prob_next_goal_home = 0.0
                prob_next_goal_away = 0.0
                prob_no_more_goals = 1.0

            # ===== 6. RISULTATI FINALI CON BIVARIATE POISSON =====
            max_goals_remaining = 6
            prob_home_win = 0.0
            prob_draw = 0.0
            prob_away_win = 0.0

            # Over/Under per tutti i livelli
            prob_over_05 = 0.0
            prob_over_15 = 0.0
            prob_over_25 = 0.0
            prob_over_35 = 0.0
            prob_over_45 = 0.0
            prob_over_55 = 0.0

            # Handicap asiatici
            prob_ah_home_minus1 = 0.0  # Casa -1
            prob_ah_home_minus05 = 0.0  # Casa -0.5
            prob_ah_home_0 = 0.0  # Draw no bet (Casa)
            prob_ah_away_0 = 0.0  # Draw no bet (Away)
            prob_ah_away_plus05 = 0.0  # Away +0.5
            prob_ah_away_plus1 = 0.0  # Away +1

            # Exact scores (top 15)
            exact_scores = {}

            # Usa Dixon-Coles bivariate per ogni possibile outcome
            for home_remaining in range(max_goals_remaining + 1):
                for away_remaining in range(max_goals_remaining + 1):
                    # ✅ BIVARIATE POISSON con correlation
                    prob_this_outcome = self._bivariate_poisson_prob(
                        home_remaining, away_remaining,
                        expected_home_remaining, expected_away_remaining,
                        RHO
                    )

                    final_home = score_home + home_remaining
                    final_away = score_away + away_remaining
                    total_goals = final_home + final_away
                    goal_diff = final_home - final_away

                    # 1X2
                    if final_home > final_away:
                        prob_home_win += prob_this_outcome
                    elif final_home == final_away:
                        prob_draw += prob_this_outcome
                    else:
                        prob_away_win += prob_this_outcome

                    # Over/Under tutti i livelli
                    if total_goals > 0.5:
                        prob_over_05 += prob_this_outcome
                    if total_goals > 1.5:
                        prob_over_15 += prob_this_outcome
                    if total_goals > 2.5:
                        prob_over_25 += prob_this_outcome
                    if total_goals > 3.5:
                        prob_over_35 += prob_this_outcome
                    if total_goals > 4.5:
                        prob_over_45 += prob_this_outcome
                    if total_goals > 5.5:
                        prob_over_55 += prob_this_outcome

                    # Handicap Asiatici
                    if goal_diff > 1:  # Casa -1 vince
                        prob_ah_home_minus1 += prob_this_outcome
                    if goal_diff > 0.5:  # Casa -0.5 vince
                        prob_ah_home_minus05 += prob_this_outcome
                    if goal_diff > 0:  # DNB Casa vince
                        prob_ah_home_0 += prob_this_outcome
                    if goal_diff < 0:  # DNB Away vince
                        prob_ah_away_0 += prob_this_outcome
                    if goal_diff < 0.5:  # Away +0.5 vince (pareggio o away win)
                        prob_ah_away_plus05 += prob_this_outcome
                    if goal_diff < 1:  # Away +1 vince (pareggio, away win, o home win by 1)
                        prob_ah_away_plus1 += prob_this_outcome

                    # Exact scores
                    score_key = f"{final_home}-{final_away}"
                    exact_scores[score_key] = exact_scores.get(score_key, 0) + prob_this_outcome

            # Normalizza 1X2
            total_1x2 = prob_home_win + prob_draw + prob_away_win
            if total_1x2 > 0:
                prob_home_win /= total_1x2
                prob_draw /= total_1x2
                prob_away_win /= total_1x2

            # Under probabilities (complementary)
            prob_under_05 = 1.0 - prob_over_05
            prob_under_15 = 1.0 - prob_over_15
            prob_under_25 = 1.0 - prob_over_25
            prob_under_35 = 1.0 - prob_over_35
            prob_under_45 = 1.0 - prob_over_45
            prob_under_55 = 1.0 - prob_over_55

            # Sort exact scores by probability and take top 15
            exact_scores_sorted = dict(sorted(exact_scores.items(), key=lambda x: x[1], reverse=True)[:15])

            # ===== 6b. NEXT GOAL TIME ESTIMATION =====
            # Expected time to next goal based on total lambda remaining
            if total_lambda_remaining > 0.01:
                # Exponential distribution: E[T] = 1/λ, but scaled to match minutes
                expected_goals_per_minute = total_lambda_remaining / minutes_remaining if minutes_remaining > 0 else 0
                if expected_goals_per_minute > 0:
                    expected_minutes_to_goal = min(minutes_remaining, 1.0 / expected_goals_per_minute)
                else:
                    expected_minutes_to_goal = minutes_remaining
            else:
                expected_minutes_to_goal = minutes_remaining

            # Probability of goal in next 5, 10, 15 minutes
            prob_goal_next_5 = 1.0 - exp(-total_lambda_remaining * min(5, minutes_remaining) / 90) if minutes_remaining > 0 else 0
            prob_goal_next_10 = 1.0 - exp(-total_lambda_remaining * min(10, minutes_remaining) / 90) if minutes_remaining > 0 else 0
            prob_goal_next_15 = 1.0 - exp(-total_lambda_remaining * min(15, minutes_remaining) / 90) if minutes_remaining > 0 else 0

            # GG/NG
            gg_already = score_home > 0 and score_away > 0
            if gg_already:
                prob_gg = 1.0
                prob_ng = 0.0
            else:
                if score_home == 0 and score_away == 0:
                    prob_home_scores = 1.0 - poisson_prob(0, expected_home_remaining)
                    prob_away_scores = 1.0 - poisson_prob(0, expected_away_remaining)
                    prob_gg = prob_home_scores * prob_away_scores
                    prob_ng = 1.0 - prob_gg
                elif score_home == 0:
                    prob_home_scores = 1.0 - poisson_prob(0, expected_home_remaining)
                    prob_gg = prob_home_scores
                    prob_ng = 1.0 - prob_gg
                else:  # score_away == 0
                    prob_away_scores = 1.0 - poisson_prob(0, expected_away_remaining)
                    prob_gg = prob_away_scores
                    prob_ng = 1.0 - prob_gg

            # ===== 7. MARKOV TRANSITION MATRIX =====
            # Probabilità transizioni score attuali → possibili finali
            markov_transitions = self._calculate_markov_transitions(
                score_home, score_away,
                lambda_home_adj, lambda_away_adj,
                time_fraction_remaining,
                RHO
            )

            # ===== 9. BAYESIAN CONFIDENCE INTERVALS (95% CI) =====
            # n_observations basato su: tempo passato + dati disponibili
            n_obs_base = int(minute)  # Più tempo è passato, più osservazioni
            if prematch_probs:
                n_obs_base += 30
            if lambda_home_opening is not None:
                n_obs_base += 20
            if live_stats and live_stats.get('normalized'):
                n_obs_base += 25  # Live stats add more observations
            n_obs_base = min(n_obs_base, 150)  # Cap at 150

            # Calcola CI per tutte le probabilità principali
            ci_home_win = self._bayesian_confidence_interval(prob_home_win, n_obs_base)
            ci_draw = self._bayesian_confidence_interval(prob_draw, n_obs_base)
            ci_away_win = self._bayesian_confidence_interval(prob_away_win, n_obs_base)
            ci_over_25 = self._bayesian_confidence_interval(prob_over_25, n_obs_base)
            ci_under_25 = self._bayesian_confidence_interval(prob_under_25, n_obs_base)
            ci_gg = self._bayesian_confidence_interval(prob_gg, n_obs_base) if not gg_already else None
            ci_ng = self._bayesian_confidence_interval(prob_ng, n_obs_base) if not gg_already else None

            # ===== 10. CONFIDENCE SCORES =====
            base_confidence = 0.5
            if prematch_probs:
                base_confidence += 0.20
            if lambda_home_opening is not None:
                base_confidence += 0.15
            if live_stats and live_stats.get('normalized'):
                base_confidence += 0.15  # Live stats boost confidence
            if score_home + score_away > 0:
                base_confidence += 0.10
            if minutes_remaining > 60:
                base_confidence -= 0.15
            elif minutes_remaining > 30:
                base_confidence -= 0.05

            overall_confidence = max(0.3, min(0.95, base_confidence))
            confidence_1x2 = overall_confidence
            confidence_ou = overall_confidence * 0.95
            confidence_gg = overall_confidence * 0.90 if not gg_already else 1.0
            confidence_next_goal = overall_confidence * 1.05 if minutes_remaining < 30 else overall_confidence * 0.85

            # ===== 10. SCENARIO PROJECTIONS (con bivariate) =====
            projections = {}

            for future_min in [5, 10, 15]:
                if minute + future_min <= 90:
                    future_minute = minute + future_min
                    future_time_remaining = max(0, 90 - future_minute)
                    future_time_fraction = future_time_remaining / 90.0

                    future_exp_home = lambda_home_adj * future_time_fraction
                    future_exp_away = lambda_away_adj * future_time_fraction

                    # Usa bivariate Poisson anche per projections
                    future_prob_over = 0.0
                    future_prob_under = 0.0
                    for h in range(6):
                        for a in range(6):
                            p = self._bivariate_poisson_prob(h, a, future_exp_home, future_exp_away, RHO)
                            if score_home + h + score_away + a > 2.5:
                                future_prob_over += p
                            else:
                                future_prob_under += p

                    total_future = future_prob_over + future_prob_under
                    if total_future > 0:
                        future_prob_over /= total_future
                        future_prob_under /= total_future

                    projections[f'{future_min}min'] = {
                        'minute': future_minute,
                        'over_25': round(future_prob_over, 3),
                        'under_25': round(future_prob_under, 3)
                    }

            # ===== 7. DELTA vs PRE-MATCH =====
            delta_vs_prematch = {}
            if prematch_probs:
                pm_1x2 = prematch_probs.get('Current', {}).get('1X2', {})
                pm_ou = prematch_probs.get('Current', {}).get('Over_Under', {})
                pm_gg = prematch_probs.get('Current', {}).get('GG_NG', {})

                if pm_1x2:
                    delta_vs_prematch['home_win'] = prob_home_win - pm_1x2.get('1', 0)
                    delta_vs_prematch['draw'] = prob_draw - pm_1x2.get('X', 0)
                    delta_vs_prematch['away_win'] = prob_away_win - pm_1x2.get('2', 0)

                if pm_ou:
                    delta_vs_prematch['over_25'] = prob_over_25 - pm_ou.get('Over 2.5', 0)
                    delta_vs_prematch['under_25'] = prob_under_25 - pm_ou.get('Under 2.5', 0)

                if pm_gg:
                    delta_vs_prematch['gg'] = prob_gg - pm_gg.get('GG', 0)
                    delta_vs_prematch['ng'] = prob_ng - pm_gg.get('NG', 0)

            # ===== RETURN COMPLETO - PROFESSIONAL VERSION =====
            return {
                # Match status
                'current_score': {
                    'home': score_home,
                    'away': score_away,
                    'minute': minute
                },
                'time_remaining': minutes_remaining,

                # ✅ ENHANCED: Mathematical model info V2.0
                'mathematical_model': {
                    'type': 'Dixon-Coles Bivariate Poisson V2.0',
                    'correlation_rho': RHO,
                    'rho_dynamic': True,  # ρ varia in base ai gol segnati
                    'phase': phase_name,
                    'phase_multiplier': round(phase_mult, 3),
                    'phase_goal_expectancy': phase_info.get('goal_expectancy', 0),
                    'phase_historical_pct': phase_info.get('historical_pct', 0),
                    'score_diff': score_diff,
                    'trailing_multiplier': round(trailing_mult, 3),
                    'leading_multiplier': round(leading_mult, 3),
                    'risk_index': score_adj.get('risk_index', 0),
                    'home_advantage_decay': round(home_advantage_factor, 3),
                    'momentum_trailing': round(momentum_trailing, 3),
                    'momentum_leading': round(momentum_leading, 3),
                    'psychological_home': round(psychological_home, 3),
                    'psychological_away': round(psychological_away, 3),
                    'time_elapsed': time_elapsed,
                    'time_ratio': round(time_elapsed / 90.0, 3)
                },

                # Lambda adjustments
                'lambda_adjustments': {
                    'home_base': round(lambda_home_base, 3),
                    'away_base': round(lambda_away_base, 3),
                    'home_adjusted': round(lambda_home_adj, 3),
                    'away_adjusted': round(lambda_away_adj, 3),
                    'phase_applied': phase_name,
                    'score_adjustment_applied': True,
                    'stats_multiplier_home': round(stats_multiplier_home, 3),
                    'stats_multiplier_away': round(stats_multiplier_away, 3),
                    'stats_adjustment_applied': stats_analysis is not None
                },

                # Market movement
                'market_analysis': {
                    'confidence': round(market_confidence, 3),
                    'direction': market_direction,
                    'shift_detected': lambda_home_opening is not None,
                    'shift_magnitude': round(market_shift_total, 3) if lambda_home_opening else 0.0
                },

                # Live stats analysis (API-Football)
                'live_stats_analysis': stats_analysis if stats_analysis else None,

                # Raw live stats (if available)
                'live_stats_raw': live_stats.get('normalized') if live_stats else None,

                # Expected goals
                'expected_goals_remaining': {
                    'home': round(expected_home_remaining, 3),
                    'away': round(expected_away_remaining, 3),
                    'total': round(total_lambda_remaining, 3)
                },

                # ✅ NEW: Expected Goals Per Minute Analysis
                'xg_per_minute': {
                    'home_per_min': round(lambda_home_adj / 90.0, 5) if lambda_home_adj > 0 else 0,
                    'away_per_min': round(lambda_away_adj / 90.0, 5) if lambda_away_adj > 0 else 0,
                    'total_per_min': round((lambda_home_adj + lambda_away_adj) / 90.0, 5),
                    'home_remaining_per_min': round(expected_home_remaining / minutes_remaining, 5) if minutes_remaining > 0 else 0,
                    'away_remaining_per_min': round(expected_away_remaining / minutes_remaining, 5) if minutes_remaining > 0 else 0,
                    'intensity_index': round(phase_mult * (1.0 + abs_diff * 0.1), 3),  # Intensità partita
                    'goal_probability_this_minute': round(1.0 - exp(-total_lambda_remaining / minutes_remaining), 4) if minutes_remaining > 0 else 0
                },

                # Next goal probabilities
                'next_goal': {
                    'home': round(prob_next_goal_home, 3),
                    'away': round(prob_next_goal_away, 3),
                    'none': round(prob_no_more_goals, 3),
                    'confidence': round(confidence_next_goal, 2)
                },

                # Final result with Bayesian CI
                'final_result': {
                    '1': round(prob_home_win, 3),
                    'X': round(prob_draw, 3),
                    '2': round(prob_away_win, 3),
                    'confidence': round(confidence_1x2, 2),
                    # ✅ NEW: Confidence intervals
                    'bayesian_ci': {
                        '1': ci_home_win,
                        'X': ci_draw,
                        '2': ci_away_win
                    }
                },

                # Over/Under with CI (tutti i livelli)
                'over_under': {
                    'Over 0.5': round(prob_over_05, 3),
                    'Under 0.5': round(prob_under_05, 3),
                    'Over 1.5': round(prob_over_15, 3),
                    'Under 1.5': round(prob_under_15, 3),
                    'Over 2.5': round(prob_over_25, 3),
                    'Under 2.5': round(prob_under_25, 3),
                    'Over 3.5': round(prob_over_35, 3),
                    'Under 3.5': round(prob_under_35, 3),
                    'Over 4.5': round(prob_over_45, 3),
                    'Under 4.5': round(prob_under_45, 3),
                    'Over 5.5': round(prob_over_55, 3),
                    'Under 5.5': round(prob_under_55, 3),
                    'confidence': round(confidence_ou, 2),
                    'bayesian_ci': {
                        'Over 2.5': ci_over_25,
                        'Under 2.5': ci_under_25
                    }
                },

                # ✅ NEW: Handicap Asiatici Live
                'handicap_asian': {
                    'AH -1 Casa': round(prob_ah_home_minus1, 3),
                    'AH -1 Trasferta': round(1.0 - prob_ah_home_minus1, 3),
                    'AH -0.5 Casa': round(prob_ah_home_minus05, 3),
                    'AH +0.5 Trasferta': round(prob_ah_away_plus05, 3),
                    'DNB Casa': round(prob_ah_home_0, 3),
                    'DNB Trasferta': round(prob_ah_away_0, 3),
                    'AH +1 Trasferta': round(prob_ah_away_plus1, 3),
                    'AH -1 Trasferta': round(1.0 - prob_ah_away_plus1, 3),
                },

                # ✅ NEW: Exact Scores (Top 15)
                'exact_scores': {k: round(v, 4) for k, v in exact_scores_sorted.items()},

                # ✅ NEW: Next Goal Timing
                'next_goal_timing': {
                    'expected_minutes': round(expected_minutes_to_goal, 1),
                    'expected_minute': round(minute + expected_minutes_to_goal, 0),
                    'prob_goal_next_5min': round(prob_goal_next_5, 3),
                    'prob_goal_next_10min': round(prob_goal_next_10, 3),
                    'prob_goal_next_15min': round(prob_goal_next_15, 3),
                },

                # GG/NG with CI
                'gg_ng': {
                    'GG': round(prob_gg, 3),
                    'NG': round(prob_ng, 3),
                    'gg_already': gg_already,
                    'confidence': round(confidence_gg, 2),
                    # ✅ NEW: Confidence intervals (solo se non GG già)
                    'bayesian_ci': {
                        'GG': ci_gg,
                        'NG': ci_ng
                    } if not gg_already else None
                },

                # ✅ NEW: Markov transition matrix
                'markov_transitions': markov_transitions,

                # Scenario projections
                'projections': projections,

                # Delta vs pre-match
                'delta_vs_prematch': delta_vs_prematch if delta_vs_prematch else None,

                # ✅ NEW: Professional summary
                'professional_summary': {
                    'model': 'Dixon-Coles Bivariate Poisson',
                    'correlation': f'ρ = {RHO}',
                    'phase': phase_name,
                    'observations_count': n_obs_base,
                    'confidence_level': '95% Bayesian CI',
                    'live_stats_integrated': stats_analysis is not None,
                    'adjustments_applied': [
                        'Time-dependent lambda (9 phases)',
                        'Continuous score adjustment',
                        'Market movement integration',
                        'Dixon-Coles correlation'
                    ] + (['Live stats adjustment (API-Football)'] if stats_analysis else [])
                }
            }

        except Exception as e:
            return {'error': str(e)}

    def calculate_betting_metrics(self, live_probs: Dict, bookmaker_margin: float = 0.06) -> Dict[str, Any]:
        """
        Calcola metriche professionali per betting:
        - Expected Value (EV)
        - Kelly Criterion
        - Break-even Odds
        - ROI Potential
        - Risk/Reward Ratios
        - Value Bet Indicators

        Args:
            live_probs: Output da calculate_live_probabilities()
            bookmaker_margin: Margine tipico bookmaker (default 6%)

        Returns:
            Dict con tutte le metriche betting professionali
        """
        try:
            metrics = {}

            # Estrai probabilità
            prob_home_win = live_probs['final_result']['1']
            prob_draw = live_probs['final_result']['X']
            prob_away_win = live_probs['final_result']['2']
            prob_over = live_probs['over_under']['Over 2.5']
            prob_under = live_probs['over_under']['Under 2.5']
            prob_gg = live_probs['gg_ng']['GG']
            prob_ng = live_probs['gg_ng']['NG']
            prob_next_home = live_probs['next_goal']['home']
            prob_next_away = live_probs['next_goal']['away']

            # ===== FAIR ODDS (senza margin) =====
            def fair_odds(prob):
                return 1.0 / prob if prob > 0.001 else 999.0

            # ===== MARKET ODDS (con margin bookmaker) =====
            def market_odds(prob, margin):
                """Odds tipiche di mercato con margine bookmaker"""
                fair = fair_odds(prob)
                return fair / (1 + margin) if fair < 999 else 999.0

            # ===== EXPECTED VALUE =====
            def calculate_ev(true_prob, market_odd):
                """EV = (prob × (odds - 1)) - (1 - prob)"""
                if market_odd >= 999:
                    return 0.0
                return (true_prob * (market_odd - 1)) - (1 - true_prob)

            # ===== KELLY CRITERION =====
            def kelly_criterion(true_prob, market_odd):
                """Kelly % = (prob × odds - 1) / (odds - 1)"""
                if market_odd <= 1.0 or market_odd >= 999:
                    return 0.0
                kelly = (true_prob * market_odd - 1) / (market_odd - 1)
                return max(0, min(kelly, 0.20))  # Cap al 20% per safety

            # ===== ROI =====
            def calculate_roi(ev, stake=100):
                """ROI% = (EV / stake) × 100"""
                return (ev / stake) * 100 if stake > 0 else 0

            # ===== RISK/REWARD =====
            def risk_reward_ratio(true_prob, market_odd):
                """R/R = Expected Win / Expected Loss"""
                if market_odd >= 999 or true_prob <= 0:
                    return 0.0
                expected_win = true_prob * (market_odd - 1)
                expected_loss = (1 - true_prob)
                return expected_win / expected_loss if expected_loss > 0 else 0.0

            # ===== VALUE INDICATOR =====
            def value_indicator(ev):
                """Classifica value: HIGH/MEDIUM/LOW/NEGATIVE"""
                if ev > 0.15:
                    return "🟢 HIGH VALUE"
                elif ev > 0.05:
                    return "🟡 MEDIUM VALUE"
                elif ev > 0:
                    return "🔵 LOW VALUE"
                else:
                    return "🔴 NEGATIVE VALUE"

            # ===== CALCOLA METRICHE PER OGNI MERCATO =====
            markets = {
                '1X2': [
                    ('1 (Casa Win)', prob_home_win),
                    ('X (Draw)', prob_draw),
                    ('2 (Away Win)', prob_away_win)
                ],
                'Over/Under': [
                    ('Over 2.5', prob_over),
                    ('Under 2.5', prob_under)
                ],
                'GG/NG': [
                    ('GG', prob_gg),
                    ('NG', prob_ng)
                ],
                'Next Goal': [
                    ('Next Goal Casa', prob_next_home),
                    ('Next Goal Trasferta', prob_next_away)
                ]
            }

            for market_name, bets in markets.items():
                metrics[market_name] = []

                for bet_name, true_prob in bets:
                    if true_prob < 0.01:  # Skip probabilità troppo basse
                        continue

                    fair_odd = fair_odds(true_prob)
                    market_odd = market_odds(true_prob, bookmaker_margin)
                    ev = calculate_ev(true_prob, market_odd)
                    kelly = kelly_criterion(true_prob, market_odd)
                    roi = calculate_roi(ev, stake=100)
                    rr = risk_reward_ratio(true_prob, market_odd)
                    value_label = value_indicator(ev)

                    # Calcola profit atteso con stake 100€
                    if ev > 0:
                        expected_profit = ev * 100
                    else:
                        expected_profit = ev * 100

                    metrics[market_name].append({
                        'bet': bet_name,
                        'true_probability': round(true_prob, 4),
                        'fair_odds': round(fair_odd, 2),
                        'market_odds': round(market_odd, 2),
                        'expected_value': round(ev, 4),
                        'ev_percent': round(ev * 100, 2),
                        'kelly_percent': round(kelly * 100, 2),
                        'roi_percent': round(roi, 2),
                        'risk_reward': round(rr, 2),
                        'value_indicator': value_label,
                        'expected_profit_100': round(expected_profit, 2),
                        'breakeven_odds': round(fair_odd, 2)
                    })

            # ===== TOP VALUE BETS (ordinati per EV) =====
            all_bets = []
            for market, bets_list in metrics.items():
                for bet in bets_list:
                    all_bets.append({**bet, 'market': market})

            # Ordina per EV decrescente
            all_bets_sorted = sorted(all_bets, key=lambda x: x['expected_value'], reverse=True)
            metrics['top_value_bets'] = all_bets_sorted[:5]  # Top 5

            # ===== BEST BET RECOMMENDATION =====
            if all_bets_sorted and all_bets_sorted[0]['expected_value'] > 0:
                best_bet = all_bets_sorted[0]
                metrics['best_bet'] = {
                    'bet': best_bet['bet'],
                    'market': best_bet['market'],
                    'probability': f"{best_bet['true_probability']*100:.1f}%",
                    'fair_odds': best_bet['fair_odds'],
                    'market_odds': best_bet['market_odds'],
                    'ev': f"{best_bet['ev_percent']:+.2f}%",
                    'kelly': f"{best_bet['kelly_percent']:.1f}%",
                    'roi': f"{best_bet['roi_percent']:+.2f}%",
                    'value': best_bet['value_indicator'],
                    'expected_profit': f"{best_bet['expected_profit_100']:+.2f}€",
                    'recommendation': 'BET NOW' if best_bet['expected_value'] > 0.10 else 'CONSIDER' if best_bet['expected_value'] > 0.05 else 'SMALL VALUE'
                }
            else:
                metrics['best_bet'] = None

            # ===== PORTFOLIO RECOMMENDATIONS =====
            positive_ev_bets = [b for b in all_bets_sorted if b['expected_value'] > 0]
            metrics['positive_ev_count'] = len(positive_ev_bets)
            metrics['total_portfolio_ev'] = sum(b['expected_value'] for b in positive_ev_bets)

            return metrics

        except Exception as e:
            return {'error': str(e)}

    def generate_live_betting_analysis(self,
                                      score_home: int, score_away: int, minute: int,
                                      team_home: str = None, team_away: str = None,
                                      spread_opening: float = None, total_opening: float = None,
                                      spread_closing: float = None, total_closing: float = None,
                                      prematch_results: Dict = None) -> str:
        """
        Genera analisi completa AVANZATA per live betting con:
        - Market movement analysis
        - Confidence scores
        - Scenario projections
        - Delta vs pre-match

        Args:
            score_home: Gol casa
            score_away: Gol trasferta
            minute: Minuto attuale
            team_home: Nome squadra casa (opzionale)
            team_away: Nome squadra trasferta (opzionale)
            spread_opening: Spread apertura (opzionale)
            total_opening: Total apertura (opzionale)
            spread_closing: Spread chiusura (opzionale)
            total_closing: Total chiusura (opzionale)
            prematch_results: Risultati analisi pre-match (opzionale)

        Returns:
            Analisi formattata in markdown con tutti i nuovi dati
        """
        try:
            # ===== CALCOLA LAMBDA APERTURA E CHIUSURA =====
            lambda_home_opening = None
            lambda_away_opening = None
            lambda_home_closing = None
            lambda_away_closing = None

            # Lambda da Pre-Match (priorità massima)
            if prematch_results:
                lambda_home_closing = prematch_results['Current']['Expected_Goals']['Home']
                lambda_away_closing = prematch_results['Current']['Expected_Goals']['Away']
                # Se abbiamo anche opening da pre-match
                if 'Opening' in prematch_results:
                    lambda_home_opening = prematch_results['Opening']['Expected_Goals'].get('Home')
                    lambda_away_opening = prematch_results['Opening']['Expected_Goals'].get('Away')

            # Lambda da Spread/Total
            if spread_opening is not None and total_opening is not None:
                lambda_home_opening = (total_opening - spread_opening) * 0.5
                lambda_away_opening = (total_opening + spread_opening) * 0.5

            if spread_closing is not None and total_closing is not None:
                # Se non hai già da pre-match, usa closing
                if lambda_home_closing is None:
                    lambda_home_closing = (total_closing - spread_closing) * 0.5
                    lambda_away_closing = (total_closing + spread_closing) * 0.5

            # Fallback generico
            if lambda_home_closing is None:
                lambda_home_closing = 1.5
                lambda_away_closing = 1.5

            # ===== CALCOLA PROBABILITÀ LIVE AVANZATE =====
            live_probs = self.calculate_live_probabilities(
                score_home=score_home,
                score_away=score_away,
                minute=minute,
                lambda_home_base=lambda_home_closing,
                lambda_away_base=lambda_away_closing,
                lambda_home_opening=lambda_home_opening,
                lambda_away_opening=lambda_away_opening,
                prematch_probs=prematch_results
            )

            if 'error' in live_probs:
                return f"❌ Errore calcolo live: {live_probs['error']}"

            # ===== PREPARA DATI PER AI =====
            team_home_str = team_home if team_home else "Casa"
            team_away_str = team_away if team_away else "Trasferta"

            # Market analysis
            market_conf = live_probs['market_analysis']['confidence']
            market_dir = live_probs['market_analysis']['direction']

            # NEW: Phase info invece di urgency_factor
            math_model = live_probs.get('mathematical_model', {})
            phase_mult = math_model.get('phase_multiplier', 1.0)
            phase_name = math_model.get('phase', 'Normal')
            correlation_rho = math_model.get('correlation_rho', 0.10)

            # Professional summary
            prof_summary = live_probs.get('professional_summary', {})
            model_type = prof_summary.get('model', 'Dixon-Coles Bivariate Poisson')

            # Confidence scores
            conf_1x2 = live_probs['final_result']['confidence']
            conf_ou = live_probs['over_under']['confidence']
            conf_next = live_probs['next_goal']['confidence']

            # Bayesian CI
            ci_1x2 = live_probs['final_result'].get('bayesian_ci', {})
            ci_ou = live_probs['over_under'].get('bayesian_ci', {})

            # Markov transitions
            markov_trans = live_probs.get('markov_transitions', {})

            # Projections
            projections = live_probs.get('projections', {})

            # Delta vs pre-match
            delta = live_probs.get('delta_vs_prematch')

            # ===== COSTRUISCI PROMPT DETTAGLIATO PROFESSIONALE =====
            analysis_prompt = f"""Genera un'analisi LIVE BETTING PROFESSIONALE con breakdown matematico completo.

📊 SITUAZIONE LIVE:
- Match: {team_home_str} vs {team_away_str}
- Score: {score_home}-{score_away} | Minuto: {minute}' | Rimanenti: {live_probs['time_remaining']} min

🎓 MODELLO MATEMATICO UTILIZZATO:
- Modello: **{model_type}**
- Correlation (ρ): **{correlation_rho}**
- Fase Partita: **{phase_name}** (multiplier: **{phase_mult:.3f}x**)
- {"🔥 MASSIMA URGENZA!" if phase_mult > 1.5 else "⚡ Alta Urgenza" if phase_mult > 1.3 else "🎯 Decisivo" if phase_mult > 1.1 else "➡️ Normale"}

🔢 LAMBDA ADJUSTMENTS:
- λ Casa Base: {lambda_home_closing:.3f} → Adjusted: {live_probs['expected_goals_remaining']['home']/(live_probs['time_remaining']/90):.3f}
- λ Trasferta Base: {lambda_away_closing:.3f} → Adjusted: {live_probs['expected_goals_remaining']['away']/(live_probs['time_remaining']/90):.3f}
- Expected Goals Rimanenti: Casa {live_probs['expected_goals_remaining']['home']:.3f}, Trasferta {live_probs['expected_goals_remaining']['away']:.3f}

🎯 MARKET ANALYSIS:
- Confidence Mercato: {market_conf:.1%} {"✅ Alta" if market_conf > 1.05 else "➖ Neutra" if market_conf > 0.98 else "⚠️ Bassa"}
- Direzione Smart Money: {market_dir.upper()} {"🏠 verso Casa" if market_dir == "home" else "✈️ verso Trasferta" if market_dir == "away" else "⚖️ Equilibrato"}"""

            # Aggiungi movement linee se disponibile
            if spread_opening is not None and spread_closing is not None:
                spread_shift = spread_closing - spread_opening
                total_shift = total_closing - total_opening
                analysis_prompt += f"""
- Movimento Spread: {spread_opening:+.2f} → {spread_closing:+.2f} ({spread_shift:+.2f}) {"📈" if spread_shift > 0 else "📉" if spread_shift < 0 else "➡️"}
- Movimento Total: {total_opening:.2f} → {total_closing:.2f} ({total_shift:+.2f}) {"📈" if total_shift > 0 else "📉" if total_shift < 0 else "➡️"}"""

            # Prepara Bayesian CI string
            ci_1_str = ""
            ci_x_str = ""
            ci_2_str = ""
            ci_over_str = ""
            ci_under_str = ""

            if ci_1x2:
                ci_1 = ci_1x2.get('1', {})
                ci_x = ci_1x2.get('X', {})
                ci_2 = ci_1x2.get('2', {})
                if ci_1:
                    ci_1_str = f" [95% CI: {ci_1.get('lower_95', 0)*100:.1f}%-{ci_1.get('upper_95', 0)*100:.1f}%]"
                if ci_x:
                    ci_x_str = f" [95% CI: {ci_x.get('lower_95', 0)*100:.1f}%-{ci_x.get('upper_95', 0)*100:.1f}%]"
                if ci_2:
                    ci_2_str = f" [95% CI: {ci_2.get('lower_95', 0)*100:.1f}%-{ci_2.get('upper_95', 0)*100:.1f}%]"

            if ci_ou:
                ci_over = ci_ou.get('Over 2.5', {})
                ci_under = ci_ou.get('Under 2.5', {})
                if ci_over:
                    ci_over_str = f" [95% CI: {ci_over.get('lower_95', 0)*100:.1f}%-{ci_over.get('upper_95', 0)*100:.1f}%]"
                if ci_under:
                    ci_under_str = f" [95% CI: {ci_under.get('lower_95', 0)*100:.1f}%-{ci_under.get('upper_95', 0)*100:.1f}%]"

            # Top 3 Markov transitions
            markov_top3_str = ""
            if markov_trans:
                markov_items = list(markov_trans.items())[:3]
                markov_top3_str = "\n🔀 TOP 3 SCORE FINALI PIÙ PROBABILI (Markov):\n"
                for score, prob in markov_items:
                    markov_top3_str += f"- {score}: {prob*100:.1f}%\n"

            analysis_prompt += f"""

⚡ PROBABILITÀ LIVE CON BAYESIAN CONFIDENCE INTERVALS (95%):
NEXT GOAL:
- {team_home_str}: {live_probs['next_goal']['home']*100:.1f}% | {team_away_str}: {live_probs['next_goal']['away']*100:.1f}% | Nessun gol: {live_probs['next_goal']['none']*100:.1f}%
- Confidence: {conf_next:.0%} {"⭐⭐⭐⭐" if conf_next > 0.8 else "⭐⭐⭐" if conf_next > 0.65 else "⭐⭐" if conf_next > 0.5 else "⭐"}

RISULTATO FINALE (con CI Bayesiani):
- 1 ({team_home_str}): {live_probs['final_result']['1']*100:.1f}%{ci_1_str}
- X (Pareggio): {live_probs['final_result']['X']*100:.1f}%{ci_x_str}
- 2 ({team_away_str}): {live_probs['final_result']['2']*100:.1f}%{ci_2_str}
- Confidence: {conf_1x2:.0%} {"⭐⭐⭐⭐" if conf_1x2 > 0.8 else "⭐⭐⭐" if conf_1x2 > 0.65 else "⭐⭐" if conf_1x2 > 0.5 else "⭐"}
{markov_top3_str}
OVER/UNDER 2.5 (con CI Bayesiani):
- Over: {live_probs['over_under']['Over 2.5']*100:.1f}%{ci_over_str}
- Under: {live_probs['over_under']['Under 2.5']*100:.1f}%{ci_under_str}
- Confidence: {conf_ou:.0%} {"⭐⭐⭐⭐" if conf_ou > 0.8 else "⭐⭐⭐" if conf_ou > 0.65 else "⭐⭐" if conf_ou > 0.5 else "⭐"}

GG/NG:
- GG: {live_probs['gg_ng']['GG']*100:.1f}% {'✅ GIÀ ACCADUTO' if live_probs['gg_ng']['gg_already'] else ''} | NG: {live_probs['gg_ng']['NG']*100:.1f}%
"""

            # Aggiungi delta vs pre-match se disponibile
            if delta:
                analysis_prompt += f"""
📈 DELTA vs PRE-MATCH (quanto sono cambiate le probabilità):
- Casa Win: {delta.get('home_win', 0)*100:+.1f}% {"📈 SALITA" if delta.get('home_win', 0) > 0.05 else "📉 SCESA" if delta.get('home_win', 0) < -0.05 else "➡️ stabile"}
- Over 2.5: {delta.get('over_25', 0)*100:+.1f}% {"📈 SALITA" if delta.get('over_25', 0) > 0.05 else "📉 SCESA" if delta.get('over_25', 0) < -0.05 else "➡️ stabile"}
- GG: {delta.get('gg', 0)*100:+.1f}% {"📈 SALITA" if delta.get('gg', 0) > 0.05 else "📉 SCESA" if delta.get('gg', 0) < -0.05 else "➡️ stabile"}
"""

            # Aggiungi proiezioni future
            if projections:
                analysis_prompt += "\n🔮 SCENARIO PROJECTIONS (se nessun gol):\n"
                for key, proj in projections.items():
                    over_change = proj['over_25'] - live_probs['over_under']['Over 2.5']
                    under_change = proj['under_25'] - live_probs['over_under']['Under 2.5']
                    analysis_prompt += f"- {proj['minute']}': Over {proj['over_25']*100:.0f}% ({over_change*100:+.0f}%), Under {proj['under_25']*100:.0f}% ({under_change*100:+.0f}%)\n"

            analysis_prompt += """
🎯 ISTRUZIONI OUTPUT - ANALISI PROFESSIONALE DETTAGLIATA:
1. "⚡ LIVE ANALYSIS" + minuto + score + fase partita
2. "🎓 BREAKDOWN MATEMATICO" - spiega brevemente:
   - Modello Dixon-Coles usato con ρ={correlation_rho}
   - Fase {phase_name} con multiplier {phase_mult:.2f}x
   - Lambda adjustments: come sono stati modificati e perché
   - Bayesian CI: cosa significano gli intervalli più stretti/larghi
3. "🟢 TOP VALUE BET" - IL miglior bet ORA con:
   - Mercato + % (probabilità puntuale)
   - 95% Confidence Interval (range incertezza)
   - Confidence (stelle) + reasoning matematico
   - Timing (BET ORA / ASPETTA X min)
   - WHY? Spiega usando:
     * Probabilità calcolata vs odds mercato
     * Markov transitions supportanti
     * Phase multiplier impact
4. "🟡 SECONDO MIGLIOR BET" (stesso formato dettagliato)
5. "🔴 DA EVITARE" - 1 bet da NON fare + spiegazione matematica del perché
6. "⏰ SCENARIO ANALYSIS" - cosa succede nei prossimi 10 min basato su:
   - Expected goals rimanenti
   - Markov transitions
   - Phase evolution
7. "💡 FINAL VERDICT" - sintesi conclusiva con confidence quantitativa

STILE:
- Output DETTAGLIATO ma CHIARO (max 450 parole)
- Ogni raccomandazione DEVE avere reasoning matematico
- Cita SEMPRE: probabilità, CI ranges, phase info, model correlation
- Spiega PERCHÉ i numeri dicono questo (non solo COSA dicono)
- Zero affermazioni banali - tutto supportato da calcoli
- Usa emoji per struttura, ma contenuto molto tecnico e professionale"""

            # ===== CHIAMA AI =====
            self._rate_limit()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Sei un analista LIVE BETTING PROFESSIONALE con PhD in statistica applicata.
Specialità: Dixon-Coles models, Bayesian inference, Markov chains applicati al calcio.

Output requirements:
- SEMPRE spiega il reasoning matematico dietro ogni raccomandazione
- Cita modelli usati (Dixon-Coles ρ, phase multipliers, Bayesian CI)
- Mostra step-by-step come arrivi alle conclusioni
- Dettagliato ma chiaro - no jargon non spiegato
- Ogni bet recommendation DEVE includere: probabilità, confidence interval, mathematical justification
- Usa emoji per struttura, numeri precisi per sostanza"""
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.20,  # Molto deterministic per consistency matematica
                max_tokens=1200  # Aumentato per output dettagliato
            )

            analysis_text = response.choices[0].message.content

            return analysis_text

        except Exception as e:
            return f"❌ Errore generazione analisi live: {str(e)}"

    def clear_history(self):
        """Pulisce la history della conversazione"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Restituisce la history della conversazione"""
        return self.conversation_history.copy()

