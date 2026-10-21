import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# 1. Configuración de página
st.set_page_config(
    page_title="Warren Dashboard - Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Estilos CSS Personalizados estilo Warren Dashboard (Tema Oscuro Neon)
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
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #131822;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid #232D42;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8;
        border-radius: 8px;
        padding: 8px 16px;
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
    /* Estilos para tarjetas de balances */
    .card-post {
        background: rgba(138, 43, 226, 0.15);
        border: 1px solid #8A2BE2;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .card-pre {
        background: rgba(255, 165, 0, 0.15);
        border: 1px solid #FFA500;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Warren Dashboard - Market Intelligence")

# 1. BANNER DE ALERTAS Y EVENTOS DEL DÍA (Cabecera)
st.markdown("""
<div style="background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%); border-left: 4px solid #00FF88; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px;">
    <span style="color: #00FF88; font-weight: bold;">🚨 DÍA CLAVE:</span> Reportan <b>META, TSLA y LRCX</b> entre otros. Monitoreá volatilidad y estimaciones de EPS en la solapa de balances[span_0](start_span)[span_0](end_span).
</div>
""", unsafe_allow_html=True)

# Pestañas principales actualizadas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌀 Rotación Sectorial", 
    "😱 Régimen & Miedo", 
    "🇺🇸 Mercado EE. UU.",
    "📅 Balances de la Semana",
    "🌐 Calendario Macro"
])

# Universo de Acciones
SECTORES = {
    "Tecnología 💻": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "AMD", "ORCL", "CRM", "INTC", "QCOM"],
    "Energía ⚡": ["XOM", "CVX", "COP", "SLB", "BP", "EOG", "MPC", "PSX", "VLO", "OXY"],
    "Salud 🏥": ["JNJ", "PFE", "UNH", "ABBV", "LLY", "MRK", "TMO", "DHR", "BMY", "AMGN"],
    "Financiero 🏦": ["JPM", "BAC", "WFC", "C", "MS", "GS", "BLK", "AXP", "V", "MA"],
    "Consumo Discrecional 🛒": ["TSLA", "NKE", "MCD", "HD", "SBUX", "LOW", "BKNG", "TJX"],
    "Industriales 🏗️": ["CAT", "DE", "GE", "LMT", "BA", "UNP", "HON", "MMM", "UPS"],
    "Comunicaciones 📡": ["NFLX", "DIS", "TMUS", "VZ", "T", "CMCSA", "EA"]
}

TODOS_TICKERS = sorted(list(set([t for lista in SECTORES.values() for t in lista])))

@st.cache_data(ttl=300)
def cargar_datos_mercado(tickers):
    try:
        df_download = yf.download(tickers + ["^VIX"], period="5d", interval="1d", progress=False)['Close']
        df_download = df_download.dropna(how='all')
        
        resultados = []
        for ticker in tickers:
            try:
                serie = df_download[ticker].dropna() if isinstance(df_download, pd.DataFrame) else df_download.dropna()
                if len(serie) >= 2:
                    p_actual = serie.iloc[-1]
                    p_previo = serie.iloc[-2]
                    var_pct = ((p_actual - p_previo) / p_previo) * 100
                    
                    resultados.append({
                        "Ticker": ticker,
                        "Precio": float(p_actual),
                        "Variacion": float(var_pct)
                    })
            except Exception:
                continue
        
        vix_val = 20.0
        try:
            vix_serie = df_download["^VIX"].dropna()
            if len(vix_serie) > 0:
                vix_val = float(vix_serie.iloc[-1])
        except Exception:
            pass

        return pd.DataFrame(resultados), vix_val
    except Exception:
        return pd.DataFrame(), 20.0

df_mercado, valor_vix = cargar_datos_mercado(TODOS_TICKERS)

# ==========================================
# PESTAÑA 1: ROTACIÓN SECTORIAL
# ==========================================
with tab1:
    st.header("Cuadro de Rotación de Sectores (RRG)")
    sectors_data = pd.DataFrame({
        'Sector': ['XLK (Tech)', 'XLE (Energía)', 'XLP (Consumo Def.)', 'XLV (Salud)', 'XLI (Industrial)'],
        'Fuerza_Relativa': [-1.5, 1.8, 1.2, 1.5, -0.8],
        'Momentum': [-1.8, 1.1, 1.9, 1.2, -0.5]
    })
    fig_rrg = px.scatter(
        sectors_data, x='Fuerza_Relativa', y='Momentum', text='Sector', color='Sector',
        color_discrete_sequence=["#FF3B69", "#00FF88", "#FFB800", "#00E5FF", "#A855F7"]
    )
    fig_rrg.add_hline(y=0, line_dash="dash", line_color="#334155")
    fig_rrg.add_vline(x=0, line_dash="dash", line_color="#334155")
    fig_rrg.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#131822',
        font=dict(color='#E2E8F0'), xaxis=dict(gridcolor='#1E293B', title="Fuerza Relativa vs SPY"),
        yaxis=dict(gridcolor='#1E293B', title="Momentum"), height=550
    )
    fig_rrg.update_traces(marker=dict(size=16))
    st.plotly_chart(fig_rrg, use_container_width=True)

# ==========================================
# PESTAÑA 2: ÍNDICE DE MIEDO Y RÉGIMEN
# ==========================================
with tab2:
    st.header("😱 Régimen & Índice de Miedo / Codicia")
    if not df_mercado.empty:
        total = len(df_mercado)
        alcistas = len(df_mercado[df_mercado["Variacion"] > 0])
        pct_alcista = (alcistas / total) * 100
        fear_greed_score = max(0, min(100, (pct_alcista * 0.6) + ((35 - valor_vix) * 2)))
        
        if fear_greed_score < 25:
            estado_texto, color_gauge = "🔴 MIEDO EXTREMO", "#FF3B69"
        elif fear_greed_score < 45:
            estado_texto, color_gauge = "🟠 MIEDO", "#FF8800"
        elif fear_greed_score < 55:
            estado_texto, color_gauge = "🟡 NEUTRAL", "#FFB800"
        elif fear_greed_score < 75:
            estado_texto, color_gauge = "🟢 CODICIA", "#00E5FF"
        else:
            estado_texto, color_gauge = "🔥 CODICIA EXTREMA", "#00FF88"

        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader(f"Estado Actual: {estado_texto}")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=fear_greed_score,
                number={'suffix': "/100", 'font': {'color': color_gauge, 'size': 48}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#334155"},
                    'bar': {'color': color_gauge, 'thickness': 0.3}, 'bgcolor': "#131822",
                    'borderwidth': 1, 'bordercolor': "#232D42",
                    'steps': [
                        {'range': [0, 25], 'color': '#2A121B'}, {'range': [25, 45], 'color': '#2A1C12'},
                        {'range': [45, 55], 'color': '#2A2612'}, {'range': [55, 75], 'color': '#12262A'},
                        {'range': [75, 100], 'color': '#122A1E'}
                    ],
                }
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), height=350, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
        with col2:
            st.subheader("📊 Indicadores Clave de Soporte")
            st.metric("Índice VIX (Volatilidad)", f"{valor_vix:.2f}", delta="- Miedo" if valor_vix < 20 else "+ Miedo", delta_color="inverse")
            st.metric("Acciones Verdes (Amplitud)", f"{alcistas} / {total}", f"{pct_alcista:.1f}% del mercado")
            st.metric("Acciones en Baja", f"{total - alcistas} / {total}")

# ==========================================
# PESTAÑA 3: ACCIONES EE. UU.
# ==========================================
with tab3:
    st.header("🇺🇸 Cotizaciones por Sector")
    if not df_mercado.empty:
        df_sorted = df_mercado.sort_values(by="Variacion", ascending=False)
        st.subheader("🔥 Top 10 Ganadores y Perdedores")
        c_g, c_p = st.columns(2)
        with c_g:
            st.markdown("#### 🟢 Top Ganadores")
            top_g = df_sorted.head(10).copy()
            top_g["Precio ($)"] = top_g["Precio"].apply(lambda x: f"${x:.2f}")
            top_g["Variación (%)"] = top_g["Variacion"].apply(lambda x: f"+{x:.2f}%")
            st.dataframe(top_g[["Ticker", "Precio ($)", "Variación (%)"]], use_container_width=True, hide_index=True)
        with c_p:
            st.markdown("#### 🔴 Top Perdedores")
            top_p = df_sorted.tail(10).iloc[::-1].copy()
            top_p["Precio ($)"] = top_p["Precio"].apply(lambda x: f"${x:.2f}")
            top_p["Variación (%)"] = top_p["Variacion"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(top_p[["Ticker", "Precio ($)", "Variación (%)"]], use_container_width=True, hide_index=True)
            
        st.divider()
        st.subheader("📂 Filtro por Sectores")
        for sector, tickers in SECTORES.items():
            with st.expander(f"📁 **{sector}**", expanded=False):
                df_sec = df_mercado[df_mercado["Ticker"].isin(tickers)].copy()
                if not df_sec.empty:
                    df_sec["Precio ($)"] = df_sec["Precio"].apply(lambda x: f"${x:.2f}")
                    df_sec["Variación (%)"] = df_sec["Variacion"].apply(lambda x: f"{'+' if x>=0 else ''}{x:.2f}%")
                    st.dataframe(df_sec[["Ticker", "Precio ($)", "Variación (%)"]], use_container_width=True, hide_index=True)

# ==========================================
# PESTAÑA 4: BALANCES DE LA SEMANA + BUSCADOR
# ==========================================
with tab4:
    st.header("📅 Calendario de Balances de la Semana")
    st.write("Resultados corporativos organizados por día con buscador rápido de tickers.")

    # 2. BUSCADOR RÁPIDO DE TICKERS
    busqueda_ticker = st.text_input("🔍 Buscar ticker específico (ej. META, TSLA, AAPL):", "").strip().upper()

    calendario_semana = {
        "Miércoles 21 de Octubre": [
            {"ticker": "META", "momento": "POST (Cierre)", "eps": "4.98"},
            {"ticker": "TSLA", "momento": "POST (Cierre)", "eps": "0.22"},
            {"ticker": "LRCX", "momento": "POST (Cierre)", "eps": "2.17"},
            {"ticker": "PM", "momento": "PRE (Apertura)", "eps": "2.30"},
            {"ticker": "IBM", "momento": "POST (Cierre)", "eps": "2.88"}
        ],
        "Jueves 22 de Octubre": [
            {"ticker": "AMZN", "momento": "POST (Cierre)", "eps": "1.14"},
            {"ticker": "AAPL", "momento": "POST (Cierre)", "eps": "1.40"},
            {"ticker": "INTC", "momento": "POST (Cierre)", "eps": "0.46"},
            {"ticker": "UPS", "momento": "PRE (Apertura)", "eps": "1.65"}
        ],
        "Viernes 23 de Octubre": [
            {"ticker": "XOM", "momento": "PRE (Apertura)", "eps": "2.10"},
            {"ticker": "CVX", "momento": "PRE (Apertura)", "eps": "2.45"}
        ]
    }

    encontrado = False
    for dia, empresas in calendario_semana.items():
        # Filtrar si el usuario usó el buscador
        empresas_filtradas = [e for e in empresas if not busqueda_ticker or busqueda_ticker in e['ticker']]
        
        if empresas_filtradas:
            encontrado = True
            with st.expander(f"🗓️ {dia} ({len(empresas_filtradas)} empresas)", expanded=True):
                for emp in empresas_filtradas:
                    is_post = "POST" in emp['momento']
                    css_class = "card-post" if is_post else "card-pre"
                    badge = "🟣 Cierre (Post)" if is_post else "🟠 Apertura (Pre)"
                    
                    # 4. TARJETAS DE BALANCES ESTILO MINI-PANEL
                    st.markdown(f"""
                    <div class="{css_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3 style="margin: 0; color: #FFFFFF;">{emp['ticker']}</h3>
                                <span style="font-size: 13px; color: #94A3B8;">{badge}</span>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 12px; color: #94A3B8; display: block;">EPS Estimado</span>
                                <strong style="font-size: 18px; color: #00FF88;">${emp['eps']}</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    if busqueda_ticker and not encontrado:
        st.warning(f"No se encontró el ticker '{busqueda_ticker}' en el calendario de balances de esta semana.")

# ==========================================
# PESTAÑA 5: CALENDARIO MACROECONÓMICO
# ==========================================
with tab5:
    st.header("🌐 Próximos Eventos Macroeconómicos (EE. UU.)")
    st.write("Indicadores y datos de alto impacto que mueven la volatilidad sistémica del mercado.")

    eventos_macro = [
        {"fecha": "Miércoles 21/10", "evento": "Inventarios de Petróleo Crudo (EIA)", "impacto": "🔴 Medio", "actual": "Pendiente"},
        {"fecha": "Jueves 22/10", "evento": "Peticiones Iniciales de Subsidio por Desempleo", "impacto": "🔴 Alto", "actual": "Pendiente"},
        {"fecha": "Jueves 22/10", "evento": "Venta de Viviendas Usadas (Existing Home Sales)", "impacto": "🟡 Moderado", "actual": "Pendiente"},
        {"fecha": "Viernes 23/10", "evento": "PMI Manufacturero y de Servicios (S&P Global)", "impacto": "🔥 Alto", "actual": "Pendiente"}
    ]

    for ev in eventos_macro:
        with st.container():
            col_f, col_ev, col_imp = st.columns([1, 2, 1])
            with col_f:
                st.markdown(f"**{ev['fecha']}**")
            with col_ev:
                st.markdown(f"📊 {ev['evento']}")
            with col_imp:
                st.markdown(f"Impacto: **{ev['impacto']}**")
            st.markdown("---")
        
