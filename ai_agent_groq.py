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
            
            # Processa infortuni (può essere lista di dict o lista di stringhe)
            injuries_truncated = []
            injuries_raw = news_data.get("injuries", [])
            for injury in injuries_raw[:2]:  # Max 2 infortuni
                if isinstance(injury, dict):
                    # Nuovo formato: dict con 'player', 'status', 'context'
                    player = injury.get('player', '')
                    status = injury.get('status', 'unknown')
                    injuries_truncated.append({
                        "player": player[:50],
                        "status": status,
                        "info": injury.get('context', '')[:100] if injury.get('context') else ""
                    })
                else:
                    # Vecchio formato: dict con 'title'
                    injuries_truncated.append({
                        "title": str(injury.get("title", ""))[:100] if isinstance(injury, dict) else str(injury)[:100]
                    })
            
            # Formazioni (lista di stringhe)
            formations = news_data.get("formations", [])[:3]  # Max 3 formazioni
            
            # Giocatori menzionati (lista di stringhe)
            players_mentioned = news_data.get("players_mentioned", [])[:10]  # Max 10 giocatori
            
            # Lineup (mantenuto per compatibilità)
            lineup_truncated = []
            for lineup in news_data.get("lineup", [])[:2]:  # Max 2 formazioni
                lineup_truncated.append({
                    "title": lineup.get("title", "")[:100] if isinstance(lineup, dict) else str(lineup)[:100]
                })
            
            return {
                "success": True,
                "team": team_name,
                "news": news_truncated,
                "injuries": injuries_truncated,
                "formations": formations,  # Nuovo campo
                "players_mentioned": players_mentioned,  # Nuovo campo
                "lineup": lineup_truncated,
                "source": news_data.get("source", "unknown")
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
7. Quando usi get_team_news: mostra SOLO dati reali trovati, NON generalizzare

STRUMENTI:
- calculate_probabilities: OBBLIGATORIO se spread/total nel context. Restituisce 'opening' e 'current'. USA SEMPRE 'current'!
- get_team_news: News/infortuni/formazioni (solo dati reali)
- search_web: Ricerca web

FORMATO:
- Analisi Numerica: cita spread/total CORRENTI e probabilità CORRENTI
- News: solo se trovate realmente
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
                    
                    # Tronca risultato tool se troppo grande (max 500 caratteri JSON)
                    tool_result_str = json.dumps(tool_result)
                    if len(tool_result_str) > 500:
                        # Se troppo grande, mantieni solo info essenziali
                        if isinstance(tool_result, dict):
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
    
    def clear_history(self):
        """Pulisce la history della conversazione"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Restituisce la history della conversazione"""
        return self.conversation_history.copy()

