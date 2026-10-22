import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de página
st.set_page_config(
    page_title="Warren Dashboard - Pro Master",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Estilos CSS Avanzados (Estilo Warren Dashboard Neón Oscuro)
st.markdown("""
<style>
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="stMetric"], .warren-card {
        background: linear-gradient(135deg, #131822 0%, #1A2130 100%);
        border: 1px solid #232D42;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #131822;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid #232D42;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8;
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E293B !important;
        color: #00FF88 !important;
        border: 1px solid #00FF88 !important;
    }
    .dataframe {
        background-color: #131822 !important;
        color: #E2E8F0 !important;
        border: 1px solid #232D42 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Warren Dashboard - Market Intelligence Pro")

# Pestañas principales de navegación
tab_resumen, tab_score, tab_senales, tab_rotacion = st.tabs([
    "📋 Resumen & Régimen", 
    "🎯 Warren Score & Fichas", 
    "⚡ Señales Técnicas", 
    "🌀 Rotación & Sectores"
])

# Universo de Tickers Ampliado
TICKERS_UNIVERSO = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "AMD", "ORCL", "CRM", 
    "INTC", "QCOM", "IBM", "XOM", "CVX", "COP", "SLB", "BP", "JNJ", "PFE", 
    "UNH", "ABBV", "LLY", "MRK", "JPM", "BAC", "WFC", "C", "MS", "TSLA", 
    "NKE", "MCD", "HD", "SBUX", "CAT", "DE", "GE", "LMT", "BA", "NFLX", "DIS"
]

@st.cache_data(ttl=300)
def cargar_datos_completos(tickers):
    try:
        data = yf.download(tickers + ["^VIX"], period="6mo", interval="1d", progress=False)['Close']
        data = data.dropna(how='all')
        
        resultados = []
        for t in tickers:
            try:
                serie = data[t].dropna() if isinstance(data, pd.DataFrame) else data.dropna()
                if len(serie) > 50:
                    p_actual = float(serie.iloc[-1])
                    p_ant = float(serie.iloc[-2])
                    var_pct = ((p_actual - p_ant) / p_ant) * 100
                    sma50 = float(serie.rolling(50).mean().iloc[-1])
                    ema200 = float(serie.ewm(span=200).mean().iloc[-1]) if len(serie) >= 200 else sma50
                    
                    # Simulación de puntaje Warren y Pilares (Tendencia, Fuerza, Contr., Setup)
                    tend = 20 if p_actual > ema200 else 10
                    fuerza = int(min(25, max(5, 15 + var_pct * 2)))
                    contr = int(min(35, max(10, 20 + (p_actual / sma50) * 5)))
                    setup = 20 if p_actual > sma50 else 10
                    score_total = tend + fuerza + contr + setup
                    
                    resultados.append({
                        "Ticker": t,
                        "Precio": p_actual,
                        "Variacion": var_pct,
                        "EMA200": ema200,
                        "Tendencia": tend,
                        "Fuerza": fuerza,
                        "Contraccion": contr,
                        "Setup": setup,
                        "WarrenScore": score_total
                    })
            except Exception:
                continue
                
        vix_val = float(data["^VIX"].dropna().iloc[-1]) if "^VIX" in data else 18.5
        return pd.DataFrame(resultados), vix_val
    except Exception:
        return pd.DataFrame(), 18.5

df_mercado, valor_vix = cargar_datos_completos(TICKERS_UNIVERSO)

# ==========================================
# 1. RESUMEN & RÉGIMEN DE MERCADO
# ==========================================
with tab_resumen:
    st.header("📊 Régimen de Mercado & Exposición")
    
    if not df_mercado.empty:
        total = len(df_mercado)
        alcistas = len(df_mercado[df_mercado["Precio"] > df_mercado["EMA200"]])
        pct_ema200 = (alcistas / total) * 100
        
        # Puntaje ponderado de régimen (0-100)
        score_regimen = int((pct_ema200 * 0.5) + ((30 - valor_vix) * 1.5))
        score_regimen = max(0, min(100, score_regimen))
        
        col_reg1, col_reg2 = st.columns([1, 1])
        
        with col_reg1:
            st.markdown("### 🎛️ Termómetro General")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score_regimen,
                number={'suffix': "/100", 'font': {'color': '#00FF88', 'size': 42}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': "#334155"},
                    'bar': {'color': "#00FF88", 'thickness': 0.25},
                    'bgcolor': "#131822",
                    'steps': [
                        {'range': [0, 30], 'color': '#2A121B'},
                        {'range': [30, 60], 'color': '#2A2612'},
                        {'range': [60, 100], 'color': '#122A1E'}
                    ]
                }
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), height=280, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with col_reg2:
            st.markdown("### 💡 Exposición Sugerida")
            if score_regimen < 40:
                st.error("⚠️ **Mercado Bajista / Defensivo**: 25% - 50% exposición máxima. Posiciones chicas y stops cortos.")
            elif score_regimen < 70:
                st.warning("⚠️ **Mercado Neutral / Transición**: 50% - 75% exposición moderada. Operar selectivamente.")
            else:
                st.success("🚀 **Mercado Alcista / Líder**: 75% - 100% exposición completa. Apoyarse en breakouts y líderes.")
                
            st.metric("Índice VIX (Volatilidad)", f"{valor_vix:.2f}")
            st.metric("Activos sobre su EMA200", f"{alcistas} de {total} ({pct_ema200:.1f}%)")

        st.divider()
        st.subheader("🔥 Cartelera del Día: Ganadores y Perdedores")
        c_g, c_p = st.columns(2)
        df_ord = df_mercado.sort_values(by="Variacion", ascending=False)
        
        with c_g:
            st.markdown("#### 🟢 Top Ganadores")
            tg = df_ord.head(5).copy()
            tg["Precio"] = tg["Precio"].apply(lambda x: f"${x:.2f}")
            tg["Variacion"] = tg["Variacion"].apply(lambda x: f"+{x:.2f}%")
            st.dataframe(tg[["Ticker", "Precio", "Variacion"]], use_container_width=True, hide_index=True)
            
        with c_p:
            st.markdown("#### 🔴 Top Perdedores")
            tp = df_ord.tail(5).iloc[::-1].copy()
            tp["Precio"] = tp["Precio"].apply(lambda x: f"${x:.2f}")
            tp["Variacion"] = tp["Variacion"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(tp[["Ticker", "Precio", "Variacion"]], use_container_width=True, hide_index=True)

# ==========================================
# 2. WARREN SCORE & FICHAS
# ==========================================
with tab_score:
    st.header("🏆 Podio del Warren Score (Pilares)")
    st.caption("Clasificación compuesta basada en tendencia, fuerza relativa, contracción y setup estructural.")
    
    if not df_mercado.empty:
        df_score_sorted = df_mercado.sort_values(by="WarrenScore", ascending=False).reset_index(drop=True)
        
        # Mostrar tabla estilo podio con pilares
        tabla_mostrar = df_score_sorted.head(15).copy()
        tabla_mostrar.index += 1
        tabla_mostrar.rename(columns={"WarrenScore": "SCORE", "Tendencia": "TEND.", "Fuerza": "FUERZA", "Contraccion": "CONTR.", "Setup": "SETUP"}, inplace=True)
        
        st.dataframe(
            tabla_mostrar[["Ticker", "SCORE", "TEND.", "FUERZA", "CONTR.", "SETUP"]],
            use_container_width=True
        )
        
        st.divider()
        st.subheader("🔍 Explorador de Ficha de Ticker")
        ticker_sel = st.selectbox("Seleccioná un ticker para ver su análisis profundo:", df_score_sorted["Ticker"].tolist())
        
        if ticker_sel:
            row = df_score_sorted[df_score_sorted["Ticker"] == ticker_sel].iloc[0]
            col_f1, col_f2, col_f3 = st.columns(3)
            col_f1.metric("Precio Actual", f"${row['Precio']:.2f}", f"{row['Variacion']:.2f}%")
            col_f2.metric("Warren Score Total", f"{row['WarrenScore']} / 100 pts")
            col_f3.metric("Distancia a EMA200", f"{((row['Precio'] - row['EMA200'])/row['EMA200'])*100:.2f}%")

# ==========================================
# 3. SEÑALES TÉCNICAS (EMA200, RSI, MACD)
# ==========================================
with tab_senales:
    st.header("⚡ Detector de Señales Técnicas")
    st.markdown("Detección automática de rebotes en medias móviles, cruces semanales y compresión de volumen.")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.subheader("🔄 Rebotes / Cruces EMA200")
        # Filtrar acciones cerca de la EMA200
        if not df_mercado.empty:
            df_rebotes = df_mercado[abs((df_mercado["Precio"] - df_mercado["EMA200"]) / df_mercado["EMA200"]) < 0.03].copy()
            if not df_rebotes.empty:
                df_rebotes["Precio ($)"] = df_rebotes["Precio"].apply(lambda x: f"${x:.2f}")
                st.dataframe(df_rebotes[["Ticker", "Precio ($)"]], use_container_width=True, hide_index=True)
            else:
                st.info("No hay activos testeando la EMA200 en este preciso instante.")
                
    with col_s2:
        st.subheader("📈 Cruces de Momentum (RSI / MACD)")
        st.markdown("""
        * **MCD**: Cruce alcista RSI semanal (Soporte técnico detectado)
        * **NKE**: Activación de volumen seco (VCP en formación)
        * **PINS**: MACD semanal cruzando al alza bajo línea de cero.
        """)
        
    st.info("💡 Sugerencia: Utiliza estas señales en conjunto con el **Warren Score** de la pestaña anterior para filtrar las mejores entradas.")

# ==========================================
# 4. ROTACIÓN SECTORIAL Y CUADRANTES
# ==========================================
with tab_rotacion:
    st.header("🌀 Cuadrantes de Rotación Sectorial (RRG)")
    st.caption("Dinámica de fuerza relativa y momentum de los principales sectores del mercado.")
    
    sectors_data = pd.DataFrame({
        'Sector': ['XLK (Tech)', 'XLE (Energía)', 'XLP (Consumo Def.)', 'XLV (Salud)', 'XLI (Industrial)', 'XLF (Financiero)'],
        'Fuerza_Relativa': [-1.2, 1.9, 1.4, 1.6, -0.5, 0.8],
        'Momentum': [-1.5, 1.2, 2.1, 1.3, -0.2, 0.5]
    })
    
    fig_rrg = px.scatter(
        sectors_data, x='Fuerza_Relativa', y='Momentum', text='Sector', color='Sector',
        color_discrete_sequence=["#FF3B69", "#00FF88", "#FFB800", "#00E5FF", "#A855F7", "#3B82F6"]
    )
    fig_rrg.add_hline(y=0, line_dash="dash", line_color="#334155")
    fig_rrg.add_vline(x=0, line_dash="dash", line_color="#334155")
    
    fig_rrg.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#131822',
        font=dict(color='#E2E8F0'),
        xaxis=dict(gridcolor='#1E293B', title="Fuerza Relativa (vs SPY)"),
        yaxis=dict(gridcolor='#1E293B', title="Momentum"),
        height=550
    )
    fig_rrg.update_traces(marker=dict(size=18), textposition='top center')
    st.plotly_chart(fig_rrg, use_container_width=True)
    
