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
                    "description": "Calcola probabilità mercati scommesse basate su spread e total.",
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
            return {
                "success": True,
                "team": team_name,
                "news": news_data.get("news", [])[:5],
                "injuries": news_data.get("injuries", [])[:3],
                "lineup": news_data.get("lineup", [])[:3],
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
                return {
                    "success": True,
                    "results": results
                }
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
        base_prompt = """Sei un assistente esperto di scommesse calcistiche e analisi statistica.
Il tuo compito è aiutare l'utente ad analizzare partite di calcio, calcolare probabilità e fornire insights basati su dati reali.

REGOLE IMPORTANTI:
1. Risposte CONCISE e CHIARE (mobile-friendly)
2. Usa sempre dati concreti quando disponibili
3. Spiega i calcoli in modo semplice
4. Evita speculazioni senza dati
5. Se non hai dati, dillo chiaramente
6. Formatta risposte per essere leggibili su smartphone
7. **CRITICO**: Quando recuperi news/infortuni/formazioni con get_team_news, DEVI MOSTRARLI nel testo, non solo dire che esistono!

STRUMENTI DISPONIBILI:
- search_web: Cerca informazioni sul web
- get_team_news: Recupera news, infortuni, formazioni squadre
- calculate_probabilities: Calcola probabilità mercati scommesse

QUANDO USI get_team_news:
- Se trovi news: mostra titolo e breve descrizione di ogni news
- Se trovi infortuni: lista i giocatori infortunati
- Se trovi formazioni: descrivi la formazione probabile
- NON dire solo "ci sono news disponibili", MOSTRALE effettivamente!

Quando l'utente chiede analisi, usa gli strumenti disponibili per ottenere dati reali e MOSTRA i risultati nel testo."""
        
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
        
        # Mantieni solo ultimi 10 messaggi per performance
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Prepara messaggi per Groq
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(context)
            }
        ] + self.conversation_history[-10:]  # Ultimi 10 messaggi
        
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
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
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

