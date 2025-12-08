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

    def clear_history(self):
        """Pulisce la history della conversazione"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Restituisce la history della conversazione"""
        return self.conversation_history.copy()

