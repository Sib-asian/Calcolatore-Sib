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
main_tab1, main_tab2 = st.tabs(["📊 Calcolatore", "🤖 AI Assistant"])

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

# Tab AI Assistant
with main_tab2:
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

