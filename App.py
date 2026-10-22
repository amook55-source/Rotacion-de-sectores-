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

# 2. Estilos CSS Globales (Tema Neón Oscuro)
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
    
    /* Estilos para Balances */
    .card-post {
        background-color: #120D1D;
        border: 1px solid #7C3AED;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .card-pre {
        background-color: #1A160C;
        border: 1px solid #D97706;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-post { color: #A78BFA; font-weight: 600; font-size: 0.9rem; }
    .badge-pre { color: #FBBF24; font-weight: 600; font-size: 0.9rem; }
    .eps-val { color: #10B981; font-size: 1.3rem; font-weight: 700; text-align: right; }
    .eps-lbl { color: #9CA3AF; font-size: 0.8rem; text-align: right; }

    /* Estilos para Warren Score Cards */
    .score-card {
        background: linear-gradient(135deg, #131822 0%, #1A2130 100%);
        border: 1px solid #1E293B;
        border-left: 4px solid #00FF88;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    .ticker-title { color: #FFFFFF; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .score-badge {
        background-color: #052E16;
        color: #00FF88;
        border: 1px solid #059669;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 1.2rem;
        font-weight: 700;
        text-align: center;
    }
    .pillar-box {
        background-color: #0B0E14;
        border: 1px solid #232D42;
        border-radius: 6px;
        padding: 6px;
        text-align: center;
        color: #94A3B8;
        font-size: 0.8rem;
    }
    .pillar-val { color: #00FF88; font-weight: 700; font-size: 1rem; }

    /* Estilos para Señales */
    .signal-card {
        background: linear-gradient(135deg, #131822 0%, #1A2130 100%);
        border: 1px solid #232D42;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .signal-badge-bull {
        background-color: #052E16;
        color: #00FF88;
        border: 1px solid #059669;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .signal-badge-bear {
        background-color: #311218;
        color: #FF3B69;
        border: 1px solid #9F1239;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Warren Dashboard - Market Intelligence Pro")

# Pestañas principales de navegación
tab_resumen, tab_score, tab_senales, tab_balances, tab_rotacion = st.tabs([
    "📋 Resumen & Régimen", 
    "🎯 Warren Score", 
    "⚡ Señales", 
    "📅 Balances (Earnings)", 
    "🌀 Rotación"
])

# Universo de Tickers
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
                
        vix_val = float(data["^VIX"].dropna().iloc[-1]) if "^VIX" in data else 18.26
        return pd.DataFrame(resultados), vix_val
    except Exception:
        return pd.DataFrame(), 18.26

df_mercado, valor_vix = cargar_datos_completos(TICKERS_UNIVERSO)

# ==========================================
# 1. RESUMEN & RÉGIMEN (CON GRÁFICO DE AGUJA)
# ==========================================
with tab_resumen:
    st.header("📊 Régimen de Mercado & Exposición")
    if not df_mercado.empty:
        total = len(df_mercado)
        alcistas = len(df_mercado[df_mercado["Precio"] > df_mercado["EMA200"]])
        pct_ema200 = (alcistas / total) * 100
        score_regimen = int((pct_ema200 * 0.5) + ((30 - valor_vix) * 1.5))
        score_regimen = max(0, min(100, score_regimen))
        
        col_reg1, col_reg2 = st.columns([1, 1])
        
        with col_reg1:
            st.markdown("### 🎛️ Índice de Régimen General")
            color_gauge = "#FF3B69" if score_regimen < 40 else ("#FFB800" if score_regimen < 60 else "#00FF88")
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score_regimen,
                number={'suffix': " / 100", 'font': {'color': color_gauge, 'size': 38}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#334155"},
                    'bar': {'color': color_gauge, 'thickness': 0.3},
                    'bgcolor': "#131822",
                    'borderwidth': 1,
                    'bordercolor': "#232D42",
                    'steps': [
                        {'range': [0, 40], 'color': '#2A121B'},
                        {'range': [40, 60], 'color': '#2A2612'},
                        {'range': [60, 100], 'color': '#122A1E'}
                    ],
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E2E8F0'),
                height=260,
                margin=dict(l=20, r=20, t=10, b=10)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_reg2:
            st.markdown("### 💡 Diagnóstico del Mercado")
            st.metric("Índice VIX (Volatilidad)", f"{valor_vix:.2f}")
            st.metric("Acciones sobre EMA200", f"{alcistas} de {total} ({pct_ema200:.1f}%)")
            
            if score_regimen < 40:
                st.error("⚠️ **Mercado Defensivo**: Exposición sugerida 25% - 50%. Posiciones chicas y stops cortos.")
            elif score_regimen < 60:
                st.warning("⚠️ **Mercado Neutral**: Exposición sugerida 50% - 75%. Operar selectivamente.")
            else:
                st.success("🚀 **Mercado Favorable**: Exposición sugerida 75% - 100%. Acompañar la tendencia.")

# ==========================================
# 2. WARREN SCORE (TARJETAS DINÁMICAS)
# ==========================================
with tab_score:
    st.header("🎯 Podio del Warren Score")
    st.caption("Los papeles con mayor puntaje compuesto según tendencia, fuerza, contracción y setup.")

    if not df_mercado.empty:
        df_score_sorted = df_mercado.sort_values(by="WarrenScore", ascending=False).reset_index(drop=True)
        
        for idx, row in df_score_sorted.head(10).iterrows():
            posicion = idx + 1
            
            # Contenedor con estilo de tarjeta oscura
            with st.container():
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #131822 0%, #1A2130 100%); border: 1px solid #1E293B; border-left: 4px solid #00FF88; border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <span style="color: #64748B; font-weight: 700; font-size: 1.2rem;">#{posicion}</span>
                            <div>
                                <div style="color: #FFFFFF; font-size: 1.5rem; font-weight: 700; margin: 0;">{row['Ticker']}</div>
                                <div style="color: #64748B; font-size: 0.85rem;">Precio: ${row['Precio']:.2f} &nbsp;|&nbsp; Var: <span style="color: {'#00FF88' if row['Variacion'] >= 0 else '#FF3B69'};">{row['Variacion']:+.2f}%</span></div>
                            </div>
                        </div>
                        <div style="background-color: #052E16; color: #00FF88; border: 1px solid #059669; border-radius: 8px; padding: 6px 12px; font-size: 1.2rem; font-weight: 700; text-align: center;">
                            {row['WarrenScore']} <span style="font-size: 0.7rem; color: #94A3B8;">pts</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Columnas nativas para los pilares (evita problemas de renderizado HTML en Streamlit)
                p1, p2, p3, p4 = st.columns(4)
                with p1:
                    st.metric("TEND.", f"{row['Tendencia']} / 20")
                with p2:
                    st.metric("FUERZA", f"{row['Fuerza']} / 25")
                with p3:
                    st.metric("CONTR.", f"{row['Contraccion']} / 35")
                with p4:
                    st.metric("SETUP", f"{row['Setup']} / 20")
                
                st.divider()


# ==========================================
# 3. SEÑALES TÉCNICAS
# ==========================================
with tab_senales:
    st.header("⚡ Detector de Señales Técnicas")
    st.caption("Filtro en tiempo real de rebotes en medias clave y cruces de momentum.")

    col_sig1, col_sig2 = st.columns(2)

    with col_sig1:
        st.subheader("🎯 Cerca / Rebote en EMA200")
        if not df_mercado.empty:
            df_ema_cerca = df_mercado[abs((df_mercado["Precio"] - df_mercado["EMA200"]) / df_mercado["EMA200"]) <= 0.03].copy()
            if not df_ema_cerca.empty:
                for _, row in df_ema_cerca.iterrows():
                    dist_pct = ((row['Precio'] - row['EMA200']) / row['EMA200']) * 100
                    badge_cls = "signal-badge-bull" if dist_pct >= 0 else "signal-badge-bear"
                    estado_txt = "🟢 Sobre EMA200" if dist_pct >= 0 else "🔴 Bajo EMA200"
                    
                    st.markdown(f"""
                    <div class="signal-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 1.2rem; color: #FFF;">{row['Ticker']}</strong>
                                <span style="color: #94A3B8; font-size: 0.85rem; margin-left: 10px;">${row['Precio']:.2f}</span>
                            </div>
                            <div>
                                <span class="{badge_cls}">{estado_txt} ({dist_pct:+.1f}%)</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay activos testeando la EMA200 en este momento.")

    with col_sig2:
        st.subheader("📈 Cruces de Momentum")
        if not df_mercado.empty:
            top_momentum = df_mercado.sort_values(by="Fuerza", ascending=False).head(5)
            for _, row in top_momentum.iterrows():
                st.markdown(f"""
                <div class="signal-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="font-size: 1.2rem; color: #FFF;">{row['Ticker']}</strong>
                            <span style="color: #94A3B8; font-size: 0.85rem; margin-left: 10px;">Score Fuerza: {row['Fuerza']}/25</span>
                        </div>
                        <div>
                            <span class="signal-badge-bull">⚡ Cruce Alcista MACD</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 4. CALENDARIO DE BALANCES (EARNINGS)
# ==========================================
with tab_balances:
    st.subheader("📅 Resultados Corporativos de la Semana")
    st.caption("Resultados corporativos organizados por día con buscador rápido de tickers.")

    ticker_buscado = st.text_input("🔍 Buscar ticker específico (ej. META, TSLA, AAPL, AMZN, GOOGL):", "").strip().upper()

    dias_earnings = {
        "🗓️ Lunes 19 de Octubre (4 empresas)": [
            {"ticker": "NFLX", "momento": "Cierre (Post)", "tipo": "post", "eps": "$5.40"},
            {"ticker": "UAL", "momento": "Cierre (Post)", "tipo": "post", "eps": "-$2.10"},
            {"ticker": "HAL", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$0.15"},
            {"ticker": "JBHT", "momento": "Cierre (Post)", "tipo": "post", "eps": "$1.45"}
        ],
        "🗓️ Martes 20 de Octubre (6 empresas)": [
            {"ticker": "JNJ", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$2.20"},
            {"ticker": "PG", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$1.63"},
            {"ticker": "TRV", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$2.90"},
            {"ticker": "LMT", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$6.05"},
            {"ticker": "SNAP", "momento": "Cierre (Post)", "tipo": "post", "eps": "-$0.05"},
            {"ticker": "TXT", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$0.65"}
        ],
        "🗓️ Miércoles 21 de Octubre (5 empresas)": [
            {"ticker": "META", "momento": "Cierre (Post)", "tipo": "post", "eps": "$4.98"},
            {"ticker": "TSLA", "momento": "Cierre (Post)", "tipo": "post", "eps": "$0.22"},
            {"ticker": "LRCX", "momento": "Cierre (Post)", "tipo": "post", "eps": "$2.17"},
            {"ticker": "PM", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$2.30"},
            {"ticker": "IBM", "momento": "Cierre (Post)", "tipo": "post", "eps": "$2.88"}
        ],
        "🗓️ Jueves 22 de Octubre (7 empresas)": [
            {"ticker": "AAPL", "momento": "Cierre (Post)", "tipo": "post", "eps": "$1.25"},
            {"ticker": "AMZN", "momento": "Cierre (Post)", "tipo": "post", "eps": "$7.38"},
            {"ticker": "GOOGL", "momento": "Cierre (Post)", "tipo": "post", "eps": "$11.20"},
            {"ticker": "MSFT", "momento": "Cierre (Post)", "tipo": "post", "eps": "$2.65"},
            {"ticker": "INTC", "momento": "Cierre (Post)", "tipo": "post", "eps": "$1.10"},
            {"ticker": "CMCSA", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$0.65"},
            {"ticker": "UPS", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$2.25"}
        ],
        "🗓️ Viernes 23 de Octubre (3 empresas)": [
            {"ticker": "XOM", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$0.20"},
            {"ticker": "CVX", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$0.35"},
            {"ticker": "ABBV", "momento": "Apertura (Pre)", "tipo": "pre", "eps": "$2.85"}
        ]
    }

    for dia_label, lista_empresas in dias_earnings.items():
        if ticker_buscado:
            lista_filtrada = [e for e in lista_empresas if ticker_buscado in e["ticker"]]
        else:
            lista_filtrada = lista_empresas

        if lista_filtrada:
            with st.expander(dia_label, expanded=True):
                for emp in lista_filtrada:
                    clase_card = "card-post" if emp["tipo"] == "post" else "card-pre"
                    clase_badge = "badge-post" if emp["tipo"] == "post" else "badge-pre"
                    icono = "🟣" if emp["tipo"] == "post" else "🟠"

                    html_card = f"""
                    <div class="{clase_card}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h2 style="margin: 0; color: #FFFFFF; font-size: 1.8rem; font-weight: 700;">{emp['ticker']}</h2>
                                <span class="{clase_badge}">{icono} {emp['momento']}</span>
                            </div>
                            <div>
                                <div class="eps-lbl">EPS Estimado</div>
                                <div class="eps-val">{emp['eps']}</div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)

# ==========================================
# 5. ROTACIÓN SECTORIAL
# ==========================================
with tab_rotacion:
    st.header("🌀 Cuadrantes de Rotación Sectorial")
    sectors_data = pd.DataFrame({
        'Sector': ['XLK (Tech)', 'XLE (Energía)', 'XLP (Consumo Def.)', 'XLV (Salud)', 'XLI (Industrial)'],
        'Fuerza_Relativa': [-1.2, 1.9, 1.4, 1.6, -0.5],
        'Momentum': [-1.5, 1.2, 2.1, 1.3, -0.2]
    })
    fig_rrg = px.scatter(sectors_data, x='Fuerza_Relativa', y='Momentum', text='Sector', color='Sector', color_discrete_sequence=["#FF3B69", "#00FF88", "#FFB800", "#00E5FF", "#A855F7"])
    fig_rrg.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#131822', font=dict(color='#E2E8F0'), height=500)
    st.plotly_chart(fig_rrg, use_container_width=True)
                
