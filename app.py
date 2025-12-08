"""
Calcolatore SIB - Sistema di Calcolo Probabilità Scommesse Calcistiche
App Streamlit per calcolo avanzato di probabilità basato su spread e total
"""

import streamlit as st
import pandas as pd
from probability_calculator import AdvancedProbabilityCalculator
import plotly.graph_objects as go
import plotly.express as px
from ai_agent_groq import AIAgentGroq

# Configurazione pagina (mobile-friendly)
st.set_page_config(
    page_title="Calcolatore SIB",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS per mobile-friendly
st.markdown("""
<style>
    /* Mobile-friendly chat */
    @media (max-width: 768px) {
        .stTextInput > div > div > input {
            font-size: 16px !important; /* Previene zoom su iOS */
        }
        .chat-message {
            padding: 10px;
            margin: 5px 0;
            border-radius: 10px;
        }
    }
    .chat-user {
        background-color: #0e1117;
        color: white;
        text-align: right;
        margin-left: 20%;
    }
    .chat-assistant {
        background-color: #262730;
        color: white;
        text-align: left;
        margin-right: 20%;
    }
</style>
""", unsafe_allow_html=True)

# Titolo e descrizione
st.title("⚽ Calcolatore SIB - Probabilità Scommesse Calcistiche")
st.markdown("""
**Calcolatore avanzato basato su modelli Poisson bivariati e aggiustamenti Dixon-Coles**

Inserisci spread e total (apertura e corrente) per calcolare tutte le probabilità dei mercati.
- **Spread negativo** = Casa favorita
- **Spread positivo** = Trasferta favorita
""")

# Inizializza il calcolatore
@st.cache_resource
def get_calculator():
    return AdvancedProbabilityCalculator()

calculator = get_calculator()

# Inizializza AI Agent
@st.cache_resource
def get_ai_agent():
    try:
        return AIAgentGroq()
    except Exception as e:
        return None

ai_agent = get_ai_agent()

# Sidebar per input
st.sidebar.header("📊 Input Dati")

st.sidebar.subheader("Apertura")
spread_opening = st.sidebar.number_input(
    "Spread Apertura",
    value=-0.5,
    step=0.25,
    format="%.2f",
    help="Spread negativo = Casa favorita, positivo = Trasferta favorita"
)

total_opening = st.sidebar.number_input(
    "Total Apertura",
    value=2.5,
    min_value=0.5,
    step=0.25,
    format="%.2f",
    help="Total atteso (somma gol)"
)

st.sidebar.subheader("Corrente")
spread_current = st.sidebar.number_input(
    "Spread Corrente",
    value=-0.5,
    step=0.25,
    format="%.2f"
)

total_current = st.sidebar.number_input(
    "Total Corrente",
    value=2.5,
    min_value=0.5,
    step=0.25,
    format="%.2f"
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚽ Squadre (Opzionale)")
st.sidebar.markdown("*Inserisci i nomi per analisi AI automatica*")

team_home = st.sidebar.text_input(
    "Squadra Casa",
    value="",
    placeholder="Es: Inter, Milan, Juventus..."
)

team_away = st.sidebar.text_input(
    "Squadra Trasferta",
    value="",
    placeholder="Es: Inter, Milan, Juventus..."
)

# Calcolo probabilità
if st.sidebar.button("🔄 Analizza Partita", type="primary"):
        with st.spinner("Calcolo probabilità in corso..."):
            results = calculator.calculate_all_probabilities(
                spread_opening, total_opening,
                spread_current, total_current
            )
            st.session_state['results'] = results
            st.session_state['calculated'] = True
            # Salva context per AI
            st.session_state['ai_context'] = {
                'spread_opening': spread_opening,
                'total_opening': total_opening,
                'spread_current': spread_current,
                'total_current': total_current,
                'team_home': team_home,
                'team_away': team_away
            }
            
            # Analisi AI automatica delle probabilità (SEMPRE, anche senza nomi squadre)
            if ai_agent:
                with st.spinner("🤖 AI sta analizzando le probabilità..."):
                    try:
                        # Genera analisi probabilità usando il nuovo metodo
                        analysis = ai_agent.generate_probability_analysis(
                            results=results,
                            team_home=team_home if team_home else None,
                            team_away=team_away if team_away else None,
                            spread_opening=spread_opening,
                            total_opening=total_opening,
                            spread_current=spread_current,
                            total_current=total_current
                        )

                        if analysis and len(analysis) > 10:
                            st.session_state['ai_analysis'] = analysis
                        else:
                            st.session_state['ai_analysis'] = "⚠️ L'AI non ha generato un'analisi valida."
                    except Exception as e:
                        error_msg = str(e)
                        st.session_state['ai_analysis'] = f"⚠️ Errore durante analisi AI: {error_msg}"
                        print(f"Errore AI analisi: {error_msg}")
            else:
                # AI non disponibile
                st.session_state['ai_analysis'] = "⚠️ AI Agent non disponibile. Verifica le API keys in config.py o .env"

# Tabs principali
main_tab1, main_tab2, main_tab3 = st.tabs(["📊 Pre-Match", "⚡ Live", "🤖 AI Assistant"])

# Tab Calcolatore
with main_tab1:
    # Mostra risultati se calcolati
    if st.session_state.get('calculated', False):
        results = st.session_state['results']
        
        # Mostra analisi AI automatica se disponibile
        if st.session_state.get('ai_analysis'):
            st.success("🤖 Analisi AI completata!")
            with st.expander("📊 Analisi AI Automatica", expanded=True):
                st.markdown(st.session_state['ai_analysis'])
            st.markdown("---")
        elif st.session_state.get('ai_analysis') == "":
            # Analisi vuota (errore silenzioso)
            st.warning("⚠️ Analisi AI non disponibile. Verifica che le API keys siano configurate correttamente.")
        
        # Tabs per organizzare i risultati
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📈 Riepilogo", "1️⃣ 1X2", "⚽ GG/NG & Over/Under", 
            "⏱️ Primo Tempo", "🎯 Risultati Esatti", "🔄 Doppia Chance & Handicap",
            "🎲 Total Esatto & Win to Nil", "📊 Movimento Mercato"
        ])
        
        with tab1:
            st.header("📊 Riepilogo Generale")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Attese Gol Casa (Apertura)",
                f"{results['Opening']['Expected_Goals']['Home']:.2f}",
                delta=f"{results['Current']['Expected_Goals']['Home']:.2f} (Corrente)"
            )
        
        with col2:
            st.metric(
                "Attese Gol Trasferta (Apertura)",
                f"{results['Opening']['Expected_Goals']['Away']:.2f}",
                delta=f"{results['Current']['Expected_Goals']['Away']:.2f} (Corrente)"
            )
        
        with col3:
            st.metric(
                "Cambio Spread",
                f"{results['Movement']['Spread_Change']:+.2f}",
                help="Positivo = movimento verso trasferta"
            )
        
        with col4:
            st.metric(
                "Cambio Total",
                f"{results['Movement']['Total_Change']:+.2f}",
                help="Positivo = aumento total atteso"
            )
        
        # Grafico confronto attese gol
        fig_eg = go.Figure()
        fig_eg.add_trace(go.Bar(
            x=['Casa', 'Trasferta'],
            y=[
                results['Opening']['Expected_Goals']['Home'],
                results['Opening']['Expected_Goals']['Away']
            ],
            name='Apertura',
            marker_color='lightblue'
        ))
        fig_eg.add_trace(go.Bar(
            x=['Casa', 'Trasferta'],
            y=[
                results['Current']['Expected_Goals']['Home'],
                results['Current']['Expected_Goals']['Away']
            ],
            name='Corrente',
            marker_color='darkblue'
        ))
        fig_eg.update_layout(
            title='Confronto Attese Gol (Apertura vs Corrente)',
            xaxis_title='Squadra',
            yaxis_title='Attese Gol',
            barmode='group'
        )
        st.plotly_chart(fig_eg, use_container_width=True)
        
        with tab2:
            st.header("1️⃣ Probabilità 1X2")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Apertura")
            opening_1x2 = results['Opening']['1X2']
            
            # Grafico a torta
            fig_opening = go.Figure(data=[go.Pie(
                labels=['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
                values=[opening_1x2['1'], opening_1x2['X'], opening_1x2['2']],
                hole=0.3,
                marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c']
            )])
            fig_opening.update_layout(title="Probabilità 1X2 - Apertura")
            st.plotly_chart(fig_opening, use_container_width=True)
            
            # Tabella
            df_opening = pd.DataFrame({
                'Esito': ['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
                'Probabilità': [
                    opening_1x2['1'],
                    opening_1x2['X'],
                    opening_1x2['2']
                ],
                'Percentuale': [
                    f"{opening_1x2['1']*100:.2f}%",
                    f"{opening_1x2['X']*100:.2f}%",
                    f"{opening_1x2['2']*100:.2f}%"
                ],
                'Quote Implicite': [
                    f"{1/opening_1x2['1']:.2f}" if opening_1x2['1'] > 0 else "N/A",
                    f"{1/opening_1x2['X']:.2f}" if opening_1x2['X'] > 0 else "N/A",
                    f"{1/opening_1x2['2']:.2f}" if opening_1x2['2'] > 0 else "N/A"
                ]
            })
            st.dataframe(df_opening, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Corrente")
            current_1x2 = results['Current']['1X2']
            
            # Grafico a torta
            fig_current = go.Figure(data=[go.Pie(
                labels=['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
                values=[current_1x2['1'], current_1x2['X'], current_1x2['2']],
                hole=0.3,
                marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c']
            )])
            fig_current.update_layout(title="Probabilità 1X2 - Corrente")
            st.plotly_chart(fig_current, use_container_width=True)
            
            # Tabella
            df_current = pd.DataFrame({
                'Esito': ['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
                'Probabilità': [
                    current_1x2['1'],
                    current_1x2['X'],
                    current_1x2['2']
                ],
                'Percentuale': [
                    f"{current_1x2['1']*100:.2f}%",
                    f"{current_1x2['X']*100:.2f}%",
                    f"{current_1x2['2']*100:.2f}%"
                ],
                'Quote Implicite': [
                    f"{1/current_1x2['1']:.2f}" if current_1x2['1'] > 0 else "N/A",
                    f"{1/current_1x2['X']:.2f}" if current_1x2['X'] > 0 else "N/A",
                    f"{1/current_1x2['2']:.2f}" if current_1x2['2'] > 0 else "N/A"
                ]
            })
            st.dataframe(df_current, use_container_width=True, hide_index=True)
        
        # Confronto
        st.subheader("📈 Confronto Apertura vs Corrente")
        comparison_data = {
            'Esito': ['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
            'Apertura': [opening_1x2['1'], opening_1x2['X'], opening_1x2['2']],
            'Corrente': [current_1x2['1'], current_1x2['X'], current_1x2['2']],
            'Variazione': [
                current_1x2['1'] - opening_1x2['1'],
                current_1x2['X'] - opening_1x2['X'],
                current_1x2['2'] - opening_1x2['2']
            ]
        }
        df_comparison = pd.DataFrame(comparison_data)
        df_comparison['Variazione %'] = df_comparison['Variazione'].apply(
            lambda x: f"{x*100:+.2f}%"
        )
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        with tab3:
            st.header("⚽ GG/NG & Over/Under")
        
        # GG/NG
        st.subheader("🎯 Goal-Goal / No Goal")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Apertura**")
            opening_gg = results['Opening']['GG_NG']
            df_gg_opening = pd.DataFrame({
                'Mercato': ['GG (Entrambe segnano)', 'NG (Almeno una non segna)'],
                'Probabilità': [opening_gg['GG'], opening_gg['NG']],
                'Percentuale': [
                    f"{opening_gg['GG']*100:.2f}%",
                    f"{opening_gg['NG']*100:.2f}%"
                ]
            })
            st.dataframe(df_gg_opening, use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**Corrente**")
            current_gg = results['Current']['GG_NG']
            df_gg_current = pd.DataFrame({
                'Mercato': ['GG (Entrambe segnano)', 'NG (Almeno una non segna)'],
                'Probabilità': [current_gg['GG'], current_gg['NG']],
                'Percentuale': [
                    f"{current_gg['GG']*100:.2f}%",
                    f"{current_gg['NG']*100:.2f}%"
                ]
            })
            st.dataframe(df_gg_current, use_container_width=True, hide_index=True)
        
        # Over/Under
        st.subheader("📊 Over/Under")
        
        opening_ou = results['Opening']['Over_Under']
        current_ou = results['Current']['Over_Under']
        
        # Prepara dati per tabella
        ou_data = []
        for key in sorted(opening_ou.keys()):
            ou_data.append({
                'Mercato': key,
                'Prob. Apertura': opening_ou[key],
                'Prob. Corrente': current_ou[key],
                'Var. Assoluta': current_ou[key] - opening_ou[key],
                'Var. %': f"{(current_ou[key] - opening_ou[key])*100:+.2f}%"
            })
        
        df_ou = pd.DataFrame(ou_data)
        df_ou['Prob. Apertura'] = df_ou['Prob. Apertura'].apply(lambda x: f"{x*100:.2f}%")
        df_ou['Prob. Corrente'] = df_ou['Prob. Corrente'].apply(lambda x: f"{x*100:.2f}%")
        df_ou['Var. Assoluta'] = df_ou['Var. Assoluta'].apply(lambda x: f"{x*100:+.2f}%")
        
        st.dataframe(df_ou, use_container_width=True, hide_index=True)
        
        with tab4:
            st.header("⏱️ Mercati Primo Tempo (HT)")
        
        opening_ht = results['Opening']['HT']
        current_ht = results['Current']['HT']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 1X2 Primo Tempo - Apertura")
            df_ht_1x2_opening = pd.DataFrame({
                'Esito': ['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
                'Probabilità': [opening_ht['HT_1'], opening_ht['HT_X'], opening_ht['HT_2']],
                'Percentuale': [
                    f"{opening_ht['HT_1']*100:.2f}%",
                    f"{opening_ht['HT_X']*100:.2f}%",
                    f"{opening_ht['HT_2']*100:.2f}%"
                ]
            })
            st.dataframe(df_ht_1x2_opening, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 1X2 Primo Tempo - Corrente")
            df_ht_1x2_current = pd.DataFrame({
                'Esito': ['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
                'Probabilità': [current_ht['HT_1'], current_ht['HT_X'], current_ht['HT_2']],
                'Percentuale': [
                    f"{current_ht['HT_1']*100:.2f}%",
                    f"{current_ht['HT_X']*100:.2f}%",
                    f"{current_ht['HT_2']*100:.2f}%"
                ]
            })
            st.dataframe(df_ht_1x2_current, use_container_width=True, hide_index=True)
        
        st.subheader("📊 Over/Under Primo Tempo")
        ht_ou_data = []
        for key in ['Over 0.5', 'Under 0.5', 'Over 1.5', 'Under 1.5', 'Over 2.5', 'Under 2.5']:
            if key in opening_ht:
                ht_ou_data.append({
                    'Mercato': key,
                    'Prob. Apertura': f"{opening_ht[key]*100:.2f}%",
                    'Prob. Corrente': f"{current_ht[key]*100:.2f}%",
                    'Variazione': f"{(current_ht[key] - opening_ht[key])*100:+.2f}%"
                })
        
        df_ht_ou = pd.DataFrame(ht_ou_data)
        st.dataframe(df_ht_ou, use_container_width=True, hide_index=True)
        
        with tab5:
            st.header("🎯 Risultati Esatti")
        
        opening_scores = results['Opening']['Exact_Scores']
        current_scores = results['Current']['Exact_Scores']
        
        # Top 15 risultati più probabili
        st.subheader("🏆 Top 15 Risultati Esatti - Apertura")
        top_opening = dict(list(opening_scores.items())[:15])
        df_top_opening = pd.DataFrame({
            'Risultato': list(top_opening.keys()),
            'Probabilità': [f"{v*100:.2f}%" for v in top_opening.values()],
            'Quote Implicite': [f"{1/v:.2f}" if v > 0 else "N/A" for v in top_opening.values()]
        })
        st.dataframe(df_top_opening, use_container_width=True, hide_index=True)
        
        st.subheader("🏆 Top 15 Risultati Esatti - Corrente")
        top_current = dict(list(current_scores.items())[:15])
        df_top_current = pd.DataFrame({
            'Risultato': list(top_current.keys()),
            'Probabilità': [f"{v*100:.2f}%" for v in top_current.values()],
            'Quote Implicite': [f"{1/v:.2f}" if v > 0 else "N/A" for v in top_current.values()]
        })
        st.dataframe(df_top_current, use_container_width=True, hide_index=True)
        
        # Matrice risultati esatti
        st.subheader("📊 Matrice Risultati Esatti (0-3 gol)")
        max_display = 4
        matrix_opening = []
        matrix_current = []
        
        for home in range(max_display):
            row_opening = []
            row_current = []
            for away in range(max_display):
                score = f"{home}-{away}"
                row_opening.append(opening_scores.get(score, 0))
                row_current.append(current_scores.get(score, 0))
            matrix_opening.append(row_opening)
            matrix_current.append(row_current)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Apertura**")
            df_matrix_opening = pd.DataFrame(
                matrix_opening,
                index=[f"{i} gol casa" for i in range(max_display)],
                columns=[f"{i} gol trasferta" for i in range(max_display)]
            )
            df_matrix_opening = df_matrix_opening.applymap(lambda x: f"{x*100:.1f}%")
            st.dataframe(df_matrix_opening, use_container_width=True)
        
        with col2:
            st.write("**Corrente**")
            df_matrix_current = pd.DataFrame(
                matrix_current,
                index=[f"{i} gol casa" for i in range(max_display)],
                columns=[f"{i} gol trasferta" for i in range(max_display)]
            )
            df_matrix_current = df_matrix_current.applymap(lambda x: f"{x*100:.1f}%")
            st.dataframe(df_matrix_current, use_container_width=True)
        
        with tab6:
            st.header("🔄 Doppia Chance & Handicap Asiatico")
        
        opening_dc = results['Opening']['Double_Chance']
        current_dc = results['Current']['Double_Chance']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Doppia Chance - Apertura")
            df_dc_opening = pd.DataFrame({
                'Mercato': ['1X (Casa o Pareggio)', '12 (Casa o Trasferta)', 'X2 (Pareggio o Trasferta)'],
                'Probabilità': [opening_dc['1X'], opening_dc['12'], opening_dc['X2']],
                'Percentuale': [
                    f"{opening_dc['1X']*100:.2f}%",
                    f"{opening_dc['12']*100:.2f}%",
                    f"{opening_dc['X2']*100:.2f}%"
                ],
                'Quote Implicite': [
                    f"{1/opening_dc['1X']:.2f}" if opening_dc['1X'] > 0 else "N/A",
                    f"{1/opening_dc['12']:.2f}" if opening_dc['12'] > 0 else "N/A",
                    f"{1/opening_dc['X2']:.2f}" if opening_dc['X2'] > 0 else "N/A"
                ]
            })
            st.dataframe(df_dc_opening, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Doppia Chance - Corrente")
            df_dc_current = pd.DataFrame({
                'Mercato': ['1X (Casa o Pareggio)', '12 (Casa o Trasferta)', 'X2 (Pareggio o Trasferta)'],
                'Probabilità': [current_dc['1X'], current_dc['12'], current_dc['X2']],
                'Percentuale': [
                    f"{current_dc['1X']*100:.2f}%",
                    f"{current_dc['12']*100:.2f}%",
                    f"{current_dc['X2']*100:.2f}%"
                ],
                'Quote Implicite': [
                    f"{1/current_dc['1X']:.2f}" if current_dc['1X'] > 0 else "N/A",
                    f"{1/current_dc['12']:.2f}" if current_dc['12'] > 0 else "N/A",
                    f"{1/current_dc['X2']:.2f}" if current_dc['X2'] > 0 else "N/A"
                ]
            })
            st.dataframe(df_dc_current, use_container_width=True, hide_index=True)
        
        st.subheader("📊 Handicap Asiatico")
        opening_ah = results['Opening']['Handicap_Asiatico']
        current_ah = results['Current']['Handicap_Asiatico']
        
        # Mostra solo alcuni handicap principali
        ah_keys = [k for k in opening_ah.keys() if 'Casa' in k and any(h in k for h in ['-1.5', '-0.5', '0.0', '0.5', '1.5'])]
        
        # Ordina correttamente gli handicap (gestisce anche valori negativi)
        def extract_handicap(key):
            try:
                # Formato: "AH -1.5 Casa" -> estrai "-1.5"
                parts = key.split()
                if len(parts) >= 2:
                    return float(parts[1])
            except:
                return 0.0
            return 0.0
        
        ah_data = []
        for key in sorted(ah_keys, key=extract_handicap):
            handicap = key.split()[1] if len(key.split()) >= 2 else key
            trasferta_key = key.replace('Casa', 'Trasferta')
            ah_data.append({
                'Handicap': handicap,
                'Prob. Casa (Apertura)': f"{opening_ah[key]*100:.2f}%",
                'Prob. Casa (Corrente)': f"{current_ah[key]*100:.2f}%",
                'Prob. Trasferta (Apertura)': f"{opening_ah.get(trasferta_key, 0)*100:.2f}%",
                'Prob. Trasferta (Corrente)': f"{current_ah.get(trasferta_key, 0)*100:.2f}%"
            })
        
        df_ah = pd.DataFrame(ah_data)
        st.dataframe(df_ah, use_container_width=True, hide_index=True)
        
        with tab7:
            st.header("🎲 Total Esatto & Win to Nil")
        
        opening_et = results['Opening']['Exact_Total']
        current_et = results['Current']['Exact_Total']
        opening_wtn = results['Opening']['Win_to_Nil']
        current_wtn = results['Current']['Win_to_Nil']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Total Gol Esatto - Apertura")
            et_data = []
            for key in sorted(opening_et.keys(), key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 999):
                et_data.append({
                    'Total': key.replace('Esattamente ', ''),
                    'Probabilità': f"{opening_et[key]*100:.2f}%",
                    'Quote': f"{1/opening_et[key]:.2f}" if opening_et[key] > 0 else "N/A"
                })
            df_et_opening = pd.DataFrame(et_data)
            st.dataframe(df_et_opening, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Total Gol Esatto - Corrente")
            et_data = []
            for key in sorted(current_et.keys(), key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 999):
                et_data.append({
                    'Total': key.replace('Esattamente ', ''),
                    'Probabilità': f"{current_et[key]*100:.2f}%",
                    'Quote': f"{1/current_et[key]:.2f}" if current_et[key] > 0 else "N/A"
                })
            df_et_current = pd.DataFrame(et_data)
            st.dataframe(df_et_current, use_container_width=True, hide_index=True)
        
        st.subheader("🏆 Win to Nil")
        wtn_data = {
            'Mercato': ['Casa Win to Nil', 'Trasferta Win to Nil'],
            'Prob. Apertura': [
                f"{opening_wtn['Casa Win to Nil']*100:.2f}%",
                f"{opening_wtn['Trasferta Win to Nil']*100:.2f}%"
            ],
            'Prob. Corrente': [
                f"{current_wtn['Casa Win to Nil']*100:.2f}%",
                f"{current_wtn['Trasferta Win to Nil']*100:.2f}%"
            ],
            'Quote Apertura': [
                f"{1/opening_wtn['Casa Win to Nil']:.2f}" if opening_wtn['Casa Win to Nil'] > 0 else "N/A",
                f"{1/opening_wtn['Trasferta Win to Nil']:.2f}" if opening_wtn['Trasferta Win to Nil'] > 0 else "N/A"
            ]
        }
        df_wtn = pd.DataFrame(wtn_data)
        st.dataframe(df_wtn, use_container_width=True, hide_index=True)
        
        with tab8:
            st.header("📊 Analisi Movimento Mercato")
        
        movement = results['Movement']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Cambio Spread", f"{movement['Spread_Change']:+.2f}")
            st.metric("Cambio Total", f"{movement['Total_Change']:+.2f}")
        
        with col2:
            st.metric("Cambio Attese Gol Casa", f"{movement['Home_EG_Change']:+.2f}")
            st.metric("Cambio Attese Gol Trasferta", f"{movement['Away_EG_Change']:+.2f}")
        
        # Grafico movimento
        fig_movement = go.Figure()
        
        fig_movement.add_trace(go.Scatter(
            x=['Apertura', 'Corrente'],
            y=[results['Opening']['Expected_Goals']['Home'], 
               results['Current']['Expected_Goals']['Home']],
            mode='lines+markers',
            name='Attese Gol Casa',
            line=dict(color='blue', width=3)
        ))
        
        fig_movement.add_trace(go.Scatter(
            x=['Apertura', 'Corrente'],
            y=[results['Opening']['Expected_Goals']['Away'], 
               results['Current']['Expected_Goals']['Away']],
            mode='lines+markers',
            name='Attese Gol Trasferta',
            line=dict(color='red', width=3)
        ))
        
        fig_movement.update_layout(
            title='Movimento Attese Gol',
            xaxis_title='Momento',
            yaxis_title='Attese Gol',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_movement, use_container_width=True)
        
        # Analisi interpretativa
        st.subheader("🔍 Interpretazione Movimento")
        
        if movement['Spread_Change'] > 0:
            st.info("📈 Il mercato si è mosso verso la trasferta (spread aumentato)")
        elif movement['Spread_Change'] < 0:
            st.info("📉 Il mercato si è mosso verso la casa (spread diminuito)")
        else:
            st.info("➡️ Nessun movimento significativo nello spread")
        
        if movement['Total_Change'] > 0:
            st.info("⚽ Il total atteso è aumentato (più gol attesi)")
        elif movement['Total_Change'] < 0:
            st.info("🔒 Il total atteso è diminuito (meno gol attesi)")
        else:
            st.info("➡️ Nessun movimento significativo nel total")
    
    else:
        st.info("👈 Inserisci i dati nella sidebar e clicca '🔄 Analizza Partita' per iniziare")
        st.markdown("""
        **💡 Suggerimento**: Inserisci anche i nomi delle squadre per ottenere un'analisi AI automatica completa!
        """)

# Tab Live Betting
with main_tab2:
    st.header("⚡ Live Betting Analyzer")
    st.markdown("""
    **Analizza partite in corso per identificare le migliori opportunità live!**

    Inserisci il risultato attuale e il minutaggio. Opzionalmente puoi usare i dati del Pre-Match
    o inserire manualmente spread/total per un'analisi più accurata.
    """)

    # Layout a due colonne: inputs a sinistra, risultati a destra
    col_input, col_output = st.columns([1, 2])

    with col_input:
        st.subheader("📊 Dati Live")

        # Score attuale
        st.markdown("**Risultato Attuale:**")
        col_home, col_away = st.columns(2)
        with col_home:
            live_score_home = st.number_input(
                "Gol Casa",
                min_value=0,
                max_value=20,
                value=0,
                step=1,
                key="live_score_home"
            )
        with col_away:
            live_score_away = st.number_input(
                "Gol Trasferta",
                min_value=0,
                max_value=20,
                value=0,
                step=1,
                key="live_score_away"
            )

        # Minuto
        live_minute = st.number_input(
            "⏱️ Minuto",
            min_value=0,
            max_value=120,
            value=45,
            step=1,
            help="0-90 per tempi regolamentari, 91-120 per supplementari",
            key="live_minute"
        )

        st.markdown("---")

        # Opzione: usa pre-match
        use_prematch = st.checkbox(
            "✅ Usa dati Pre-Match",
            value=False,
            help="Se hai già analizzato la partita in Pre-Match, usa quei dati"
        )

        # Lambda source
        lambda_home_base = 1.5  # default
        lambda_away_base = 1.5  # default
        prematch_results = None

        if use_prematch:
            # Prova a usare dati pre-match
            if st.session_state.get('results'):
                prematch_results = st.session_state['results']
                lambda_home_base = prematch_results['Current']['Expected_Goals']['Home']
                lambda_away_base = prematch_results['Current']['Expected_Goals']['Away']

                st.success(f"✅ Usando λ Pre-Match: Casa={lambda_home_base:.2f}, Trasferta={lambda_away_base:.2f}")

                # Mostra anche spread/total pre-match se disponibili
                if st.session_state.get('ai_context'):
                    ctx = st.session_state['ai_context']
                    st.info(f"""
                    **Dati Pre-Match:**
                    - Spread: {ctx.get('spread_current', 'N/A')}
                    - Total: {ctx.get('total_current', 'N/A')}
                    """)
            else:
                st.warning("⚠️ Nessun dato Pre-Match disponibile. Analizza prima una partita nel tab Pre-Match.")
                use_prematch = False

        if not use_prematch:
            # Input manuali
            st.markdown("**📈 Dati Spread/Total (Opzionale):**")
            st.caption("Se non inserisci questi dati, userò valori generici")

            col_open, col_close = st.columns(2)

            with col_open:
                st.markdown("*Apertura*")
                live_spread_opening = st.number_input(
                    "Spread Apertura",
                    value=0.0,
                    step=0.25,
                    format="%.2f",
                    key="live_spread_opening"
                )
                live_total_opening = st.number_input(
                    "Total Apertura",
                    value=0.0,
                    min_value=0.0,
                    step=0.25,
                    format="%.2f",
                    key="live_total_opening"
                )

            with col_close:
                st.markdown("*Chiusura*")
                live_spread_closing = st.number_input(
                    "Spread Chiusura",
                    value=0.0,
                    step=0.25,
                    format="%.2f",
                    key="live_spread_closing"
                )
                live_total_closing = st.number_input(
                    "Total Chiusura",
                    value=0.0,
                    min_value=0.0,
                    step=0.25,
                    format="%.2f",
                    key="live_total_closing"
                )

            # Calcola lambda se spread/total sono forniti
            if live_spread_closing != 0.0 and live_total_closing != 0.0:
                lambda_home_base = (live_total_closing - live_spread_closing) * 0.5
                lambda_away_base = (live_total_closing + live_spread_closing) * 0.5
                st.info(f"✅ Calcolato λ da Spread/Total: Casa={lambda_home_base:.2f}, Trasferta={lambda_away_base:.2f}")
            else:
                st.warning("⚠️ Usando valori generici: λ Casa=1.5, λ Trasferta=1.5")

        st.markdown("---")

        # Squadre (opzionale)
        live_team_home = st.text_input(
            "Squadra Casa (opzionale)",
            value=st.session_state.get('ai_context', {}).get('team_home', '') if use_prematch else '',
            placeholder="Es: Inter",
            key="live_team_home"
        )
        live_team_away = st.text_input(
            "Squadra Trasferta (opzionale)",
            value=st.session_state.get('ai_context', {}).get('team_away', '') if use_prematch else '',
            placeholder="Es: Milan",
            key="live_team_away"
        )

        # Bottone analisi
        analyze_live = st.button("⚡ Analizza Live", type="primary", use_container_width=True)

    with col_output:
        if analyze_live:
            if ai_agent is None:
                st.error("⚠️ AI Agent non disponibile. Verifica le API keys in config.py")
            else:
                with st.spinner("🔄 Analisi live in corso..."):
                    try:
                        # Calcola probabilità live
                        live_probs = ai_agent.calculate_live_probabilities(
                            score_home=live_score_home,
                            score_away=live_score_away,
                            minute=live_minute,
                            lambda_home_base=lambda_home_base,
                            lambda_away_base=lambda_away_base
                        )

                        # Genera analisi AI
                        live_analysis = ai_agent.generate_live_betting_analysis(
                            score_home=live_score_home,
                            score_away=live_score_away,
                            minute=live_minute,
                            team_home=live_team_home if live_team_home else None,
                            team_away=live_team_away if live_team_away else None,
                            spread_opening=st.session_state.get('ai_context', {}).get('spread_opening') if use_prematch else (live_spread_opening if not use_prematch and live_spread_opening != 0.0 else None),
                            total_opening=st.session_state.get('ai_context', {}).get('total_opening') if use_prematch else (live_total_opening if not use_prematch and live_total_opening != 0.0 else None),
                            spread_closing=st.session_state.get('ai_context', {}).get('spread_current') if use_prematch else (live_spread_closing if not use_prematch and live_spread_closing != 0.0 else None),
                            total_closing=st.session_state.get('ai_context', {}).get('total_current') if use_prematch else (live_total_closing if not use_prematch and live_total_closing != 0.0 else None),
                            prematch_results=prematch_results if use_prematch else None
                        )

                        # Salva in session state
                        st.session_state['live_probs'] = live_probs
                        st.session_state['live_analysis'] = live_analysis

                    except Exception as e:
                        st.error(f"❌ Errore durante l'analisi live: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

        # Mostra risultati se disponibili
        if st.session_state.get('live_probs'):
            live_probs = st.session_state['live_probs']

            # Helper per confidence stars
            def get_confidence_stars(conf):
                if conf >= 0.80:
                    return "⭐⭐⭐⭐"
                elif conf >= 0.65:
                    return "⭐⭐⭐"
                elif conf >= 0.50:
                    return "⭐⭐"
                else:
                    return "⭐"

            # ===== BOX SITUAZIONE + MARKET ANALYSIS =====
            col_status1, col_status2 = st.columns([2, 1])

            with col_status1:
                urgency = live_probs.get('urgency_factor', 1.0)
                urgency_label = "🔥 CRITICO!" if urgency > 1.3 else "⚡ Decisivo" if urgency > 1.1 else "➡️ Normale"

                st.info(f"""
                **📊 SITUAZIONE LIVE**
                - Score: **{live_probs['current_score']['home']}-{live_probs['current_score']['away']}** | Minuto: **{live_probs['current_score']['minute']}'**
                - Tempo rimanente: **{live_probs['time_remaining']} minuti**
                - Urgency: **{urgency}x** {urgency_label}
                """)

            with col_status2:
                market_analysis = live_probs.get('market_analysis', {})
                market_conf = market_analysis.get('confidence', 1.0)
                market_dir = market_analysis.get('direction', 'neutral')

                conf_label = "✅ Alta" if market_conf > 1.05 else "⚠️ Bassa" if market_conf < 0.98 else "➖ Neutra"
                dir_label = "🏠 Casa" if market_dir == "home" else "✈️ Trasferta" if market_dir == "away" else "⚖️ Neutro"

                st.success(f"""
                **🎯 MARKET ANALYSIS**
                - Confidence: **{market_conf:.2f}** {conf_label}
                - Smart Money: {dir_label}
                """)

            # Analisi AI
            if st.session_state.get('live_analysis'):
                st.markdown("---")
                st.markdown(st.session_state['live_analysis'])

            st.markdown("---")

            # ===== TABS PER DATI DETTAGLIATI =====
            live_tab1, live_tab2, live_tab3, live_tab4, live_tab5, live_tab6 = st.tabs([
                "🎯 Next Goal", "🏆 Risultato Finale", "⚽ Over/Under & GG/NG",
                "📈 Delta Pre-Match", "🔮 Proiezioni", "📊 Dettagli Tecnici"
            ])

            with live_tab1:
                st.subheader("🎯 Prossimo Gol")

                next_goal = live_probs['next_goal']
                conf_next = next_goal.get('confidence', 0.5)
                stars_next = get_confidence_stars(conf_next)

                st.markdown(f"**Confidence: {conf_next:.0%} {stars_next}**")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Casa", f"{next_goal['home']*100:.1f}%")
                with col2:
                    st.metric("Trasferta", f"{next_goal['away']*100:.1f}%")
                with col3:
                    st.metric("Nessun Gol", f"{next_goal['none']*100:.1f}%")

                # Grafico
                fig_next_goal = go.Figure(data=[go.Bar(
                    x=['Casa', 'Trasferta', 'Nessun Gol'],
                    y=[next_goal['home']*100, next_goal['away']*100, next_goal['none']*100],
                    marker_color=['#1f77b4', '#2ca02c', '#ff7f0e']
                )])
                fig_next_goal.update_layout(
                    title="Probabilità Prossimo Gol",
                    yaxis_title="Probabilità (%)",
                    showlegend=False
                )
                st.plotly_chart(fig_next_goal, use_container_width=True)

            with live_tab2:
                st.subheader("🏆 Risultato Finale Previsto")

                final_result = live_probs['final_result']
                conf_1x2 = final_result.get('confidence', 0.5)
                stars_1x2 = get_confidence_stars(conf_1x2)

                st.markdown(f"**Confidence: {conf_1x2:.0%} {stars_1x2}**")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("1 (Casa)", f"{final_result['1']*100:.1f}%")
                with col2:
                    st.metric("X (Pareggio)", f"{final_result['X']*100:.1f}%")
                with col3:
                    st.metric("2 (Trasferta)", f"{final_result['2']*100:.1f}%")

                # Grafico
                fig_final = go.Figure(data=[go.Pie(
                    labels=['1 (Casa)', 'X (Pareggio)', '2 (Trasferta)'],
                    values=[final_result['1'], final_result['X'], final_result['2']],
                    hole=0.3,
                    marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c']
                )])
                fig_final.update_layout(title="Probabilità Risultato Finale")
                st.plotly_chart(fig_final, use_container_width=True)

            with live_tab3:
                st.subheader("⚽ Over/Under & GG/NG")

                over_under = live_probs['over_under']
                gg_ng = live_probs['gg_ng']
                conf_ou = over_under.get('confidence', 0.5)
                conf_gg = gg_ng.get('confidence', 0.5)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Over/Under 2.5** - Confidence: {conf_ou:.0%} {get_confidence_stars(conf_ou)}")
                    st.metric("Over 2.5", f"{over_under['Over 2.5']*100:.1f}%")
                    st.metric("Under 2.5", f"{over_under['Under 2.5']*100:.1f}%")

                with col2:
                    st.markdown(f"**Goal/No Goal** - Confidence: {conf_gg:.0%} {get_confidence_stars(conf_gg)}")
                    st.metric("GG", f"{gg_ng['GG']*100:.1f}%")
                    st.metric("NG", f"{gg_ng['NG']*100:.1f}%")

                    if gg_ng['gg_already']:
                        st.success("✅ Entrambe hanno già segnato!")

            with live_tab4:
                st.subheader("📈 Delta vs Pre-Match")

                delta = live_probs.get('delta_vs_prematch')

                if delta:
                    # Crea tabella comparativa
                    comparison_data = []

                    if 'home_win' in delta:
                        comparison_data.append({
                            'Mercato': '1 (Casa Win)',
                            'Pre-Match': f"{(live_probs['final_result']['1'] - delta['home_win'])*100:.1f}%",
                            'Live NOW': f"{live_probs['final_result']['1']*100:.1f}%",
                            'Delta': f"{delta['home_win']*100:+.1f}%",
                            'Trend': '📈' if delta['home_win'] > 0.05 else '📉' if delta['home_win'] < -0.05 else '➡️'
                        })

                    if 'away_win' in delta:
                        comparison_data.append({
                            'Mercato': '2 (Away Win)',
                            'Pre-Match': f"{(live_probs['final_result']['2'] - delta['away_win'])*100:.1f}%",
                            'Live NOW': f"{live_probs['final_result']['2']*100:.1f}%",
                            'Delta': f"{delta['away_win']*100:+.1f}%",
                            'Trend': '📈' if delta['away_win'] > 0.05 else '📉' if delta['away_win'] < -0.05 else '➡️'
                        })

                    if 'draw' in delta:
                        comparison_data.append({
                            'Mercato': 'X (Pareggio)',
                            'Pre-Match': f"{(live_probs['final_result']['X'] - delta['draw'])*100:.1f}%",
                            'Live NOW': f"{live_probs['final_result']['X']*100:.1f}%",
                            'Delta': f"{delta['draw']*100:+.1f}%",
                            'Trend': '📈' if delta['draw'] > 0.05 else '📉' if delta['draw'] < -0.05 else '➡️'
                        })

                    if 'over_25' in delta:
                        comparison_data.append({
                            'Mercato': 'Over 2.5',
                            'Pre-Match': f"{(live_probs['over_under']['Over 2.5'] - delta['over_25'])*100:.1f}%",
                            'Live NOW': f"{live_probs['over_under']['Over 2.5']*100:.1f}%",
                            'Delta': f"{delta['over_25']*100:+.1f}%",
                            'Trend': '📈' if delta['over_25'] > 0.05 else '📉' if delta['over_25'] < -0.05 else '➡️'
                        })

                    if 'under_25' in delta:
                        comparison_data.append({
                            'Mercato': 'Under 2.5',
                            'Pre-Match': f"{(live_probs['over_under']['Under 2.5'] - delta['under_25'])*100:.1f}%",
                            'Live NOW': f"{live_probs['over_under']['Under 2.5']*100:.1f}%",
                            'Delta': f"{delta['under_25']*100:+.1f}%",
                            'Trend': '📈' if delta['under_25'] > 0.05 else '📉' if delta['under_25'] < -0.05 else '➡️'
                        })

                    if 'gg' in delta:
                        comparison_data.append({
                            'Mercato': 'GG',
                            'Pre-Match': f"{(live_probs['gg_ng']['GG'] - delta['gg'])*100:.1f}%",
                            'Live NOW': f"{live_probs['gg_ng']['GG']*100:.1f}%",
                            'Delta': f"{delta['gg']*100:+.1f}%",
                            'Trend': '📈' if delta['gg'] > 0.05 else '📉' if delta['gg'] < -0.05 else '➡️'
                        })

                    df_comparison = pd.DataFrame(comparison_data)
                    st.dataframe(df_comparison, use_container_width=True, hide_index=True)

                    st.info("""
                    **💡 Come leggere:**
                    - 📈 = Probabilità SALITA rispetto al pre-match (>+5%)
                    - 📉 = Probabilità SCESA rispetto al pre-match (<-5%)
                    - ➡️ = Probabilità STABILE
                    """)
                else:
                    st.warning("⚠️ Nessun dato Pre-Match disponibile per confronto")

            with live_tab5:
                st.subheader("🔮 Proiezioni Future")

                projections = live_probs.get('projections', {})

                if projections:
                    st.markdown("**📊 Scenario: NESSUN GOL nei prossimi minuti**")

                    proj_data = []
                    for key, proj in projections.items():
                        over_now = live_probs['over_under']['Over 2.5']
                        under_now = live_probs['over_under']['Under 2.5']
                        over_change = proj['over_25'] - over_now
                        under_change = proj['under_25'] - under_now

                        proj_data.append({
                            'Minuto': f"{proj['minute']}'",
                            'Over 2.5': f"{proj['over_25']*100:.1f}%",
                            'Δ Over': f"{over_change*100:+.1f}%",
                            'Under 2.5': f"{proj['under_25']*100:.1f}%",
                            'Δ Under': f"{under_change*100:+.1f}%"
                        })

                    df_proj = pd.DataFrame(proj_data)
                    st.dataframe(df_proj, use_container_width=True, hide_index=True)

                    # Grafico trend
                    minutes = [live_probs['current_score']['minute']] + [proj['minute'] for proj in projections.values()]
                    over_values = [live_probs['over_under']['Over 2.5']*100] + [proj['over_25']*100 for proj in projections.values()]
                    under_values = [live_probs['over_under']['Under 2.5']*100] + [proj['under_25']*100 for proj in projections.values()]

                    fig_proj = go.Figure()
                    fig_proj.add_trace(go.Scatter(
                        x=minutes, y=over_values,
                        mode='lines+markers',
                        name='Over 2.5',
                        line=dict(color='red', width=3)
                    ))
                    fig_proj.add_trace(go.Scatter(
                        x=minutes, y=under_values,
                        mode='lines+markers',
                        name='Under 2.5',
                        line=dict(color='blue', width=3)
                    ))
                    fig_proj.update_layout(
                        title="Evoluzione Probabilità Over/Under 2.5",
                        xaxis_title="Minuto",
                        yaxis_title="Probabilità (%)",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig_proj, use_container_width=True)

                    st.info("""
                    **💡 Come usarla:**
                    - Se Under sta salendo → aspetta qualche minuto per bet Under (valore migliore)
                    - Se Over sta scendendo → bet Over ORA prima che scenda ancora
                    """)
                else:
                    st.warning("⚠️ Nessuna proiezione disponibile (partita quasi finita)")

            with live_tab6:
                st.subheader("📊 Dettagli Tecnici")

                expected_remaining = live_probs['expected_goals_remaining']

                st.markdown("**Gol Attesi Rimanenti:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Casa", f"{expected_remaining['home']:.3f}")
                with col2:
                    st.metric("Trasferta", f"{expected_remaining['away']:.3f}")
                with col3:
                    st.metric("Totale", f"{expected_remaining['total']:.3f}")

                # Mostra lambda base usati
                st.markdown("**Lambda Base Utilizzati:**")
                st.info(f"λ Casa = {lambda_home_base:.2f} | λ Trasferta = {lambda_away_base:.2f}")

                # Mostra adjustment factors
                st.markdown("**Adjustment Factors:**")
                st.info(f"Urgency Factor: {live_probs.get('urgency_factor', 1.0):.2f}x | Market Confidence: {market_analysis.get('confidence', 1.0):.2f}")

                # JSON completo per debug
                with st.expander("🔍 Dati Completi (JSON)"):
                    st.json(live_probs)

        else:
            st.info("👈 Inserisci i dati live e clicca '⚡ Analizza Live' per iniziare")
            st.markdown("""
            **💡 Suggerimenti:**
            - Se hai già analizzato la partita nel tab Pre-Match, attiva "Usa dati Pre-Match"
            - Altrimenti, inserisci manualmente spread/total per maggiore accuratezza
            - Puoi anche fare un'analisi rapida con solo score e minuto (valori generici)
            """)

# Tab AI Assistant
with main_tab3:
    st.header("🤖 AI Assistant - Analisi Intelligente")
    st.markdown("""
    **Chiedi all'AI di analizzare partite, cercare news, spiegare calcoli e molto altro!**
    
    Esempi:
    - "Analizza Inter vs Milan"
    - "Perché Under 2.5 è al 58%?"
    - "Cerca news su Juventus"
    - "Calcola probabilità con spread -0.5 e total 2.5"
    """)
    
    if ai_agent is None:
        st.error("⚠️ AI Agent non disponibile. Verifica le API keys in config.py")
    else:
        # Inizializza chat history
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []
        
        # Mostra chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state['chat_history']:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message chat-user">
                        <strong>Tu:</strong><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message chat-assistant">
                        <strong>AI:</strong><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Input chat
        st.markdown("---")
        user_input = st.text_input(
            "💬 Scrivi un messaggio...",
            key="chat_input",
            placeholder="Es: Analizza Inter vs Milan"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            send_button = st.button("📤 Invia", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("🗑️ Pulisci Chat", use_container_width=True)
        
        if clear_button:
            st.session_state['chat_history'] = []
            if ai_agent:
                ai_agent.clear_history()
            st.rerun()
        
        if send_button and user_input:
            # Verifica che AI agent sia disponibile
            if ai_agent is None:
                st.error("⚠️ AI Agent non disponibile. Verifica le API keys in config.py")
                st.stop()
            
            # Aggiungi messaggio utente alla history
            st.session_state['chat_history'].append({
                'role': 'user',
                'content': user_input
            })
            
            # Prepara context
            context = st.session_state.get('ai_context', {})
            
            # Chiama AI
            with st.spinner("🤔 AI sta pensando..."):
                try:
                    result = ai_agent.chat(user_input, context=context)
                    
                    if result.get('error'):
                        response = f"⚠️ Errore: {result['error']}"
                    else:
                        response = result.get('response', 'Nessuna risposta')
                    
                    # Aggiungi risposta alla history
                    st.session_state['chat_history'].append({
                        'role': 'assistant',
                        'content': response
                    })
                    
                    # Mostra tools usati (opzionale, solo se debug)
                    if result.get('tools_used') and st.session_state.get('debug_mode', False):
                        with st.expander("🔧 Tools utilizzati"):
                            for tool in result['tools_used']:
                                st.json(tool)
                    
                except Exception as e:
                    error_msg = f"Errore durante la chat: {str(e)}"
                    st.session_state['chat_history'].append({
                        'role': 'assistant',
                        'content': f"❌ {error_msg}"
                    })
            
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Calcolatore SIB - Sistema avanzato basato su modelli Poisson e Dixon-Coles</small>
</div>
""", unsafe_allow_html=True)

