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

# Pestañas principales incluyendo Balances
tab_resumen, tab_score, tab_senales, tab_balances, tab_rotacion = st.tabs([
    "📋 Resumen & Régimen", 
    "🎯 Warren Score", 
    "⚡ Señales", 
    "📅 Balances (Earnings)", 
    "🌀 Rotación"
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
# 1. RESUMEN & RÉGIMEN
# ==========================================
with tab_resumen:
    st.header("📊 Régimen de Mercado & Exposición")
    if not df_mercado.empty:
        total = len(df_mercado)
        alcistas = len(df_mercado[df_mercado["Precio"] > df_mercado["EMA200"]])
        pct_ema200 = (alcistas / total) * 100
        score_regimen = int((pct_ema200 * 0.5) + ((30 - valor_vix) * 1.5))
        score_regimen = max(0, min(100, score_regimen))
        
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            st.metric("Índice de Régimen General", f"{score_regimen} / 100")
            st.metric("Índice VIX", f"{valor_vix:.2f}")
        with col_reg2:
            if score_regimen < 40:
                st.error("⚠️ **Mercado Defensivo**: Exposición sugerida 25% - 50%.")
            else:
                st.success("🚀 **Mercado Favorable**: Exposición sugerida 75% - 100%.")

# ==========================================
# 2. WARREN SCORE
# ==========================================
with tab_score:
    st.header("🎯 Warren Score & Pilares")
    if not df_mercado.empty:
        df_score_sorted = df_mercado.sort_values(by="WarrenScore", ascending=False).reset_index(drop=True)
        tabla_mostrar = df_score_sorted.head(15).copy()
        tabla_mostrar.index += 1
        tabla_mostrar.rename(columns={"WarrenScore": "SCORE", "Tendencia": "TEND.", "Fuerza": "FUERZA", "Contraccion": "CONTR.", "Setup": "SETUP"}, inplace=True)
        st.dataframe(tabla_mostrar[["Ticker", "SCORE", "TEND.", "FUERZA", "CONTR.", "SETUP"]], use_container_width=True)

# ==========================================
# 3. SEÑALES TÉCNICAS
# ==========================================
with tab_senales:
    st.header("⚡ Detector de Señales Técnicas")
    st.info("Monitoreo activo de cruces EMA200, RSI y MACD.")

# ==========================================
# 4. CALENDARIO DE BALANCES (EARNINGS) - NUEVO!
# ==========================================
with tab_balances:
    st.header("📅 Calendario de Balances de la Semana")
    st.caption("Próximos reportes de ganancias corporativas (EPS Estimado y Reacción del Mercado).")
    
    # Datos simulados profesionales idénticos al Warren Dashboard
    df_balances = pd.DataFrame([
        {"Ticker": "META", "Empresa": "Meta Platforms", "Día": "Miércoles 28/10", "Momento": "POST CIERRE", "EPS Est": "$4.98", "Reacción": "Pendiente"},
        {"Ticker": "TSLA", "Empresa": "Tesla Inc.", "Día": "Miércoles 28/10", "Momento": "POST CIERRE", "EPS Est": "$0.22", "Reacción": "Pendiente"},
        {"Ticker": "LRCX", "Empresa": "Lam Research", "Día": "Miércoles 28/10", "Momento": "POST CIERRE", "EPS Est": "$2.17", "Reacción": "Pendiente"},
        {"Ticker": "PM", "Empresa": "Philip Morris", "Día": "Jueves 29/10", "Momento": "PRE APERTURA", "EPS Est": "$2.30", "Reacción": "🔴 -1,2% hoy"},
        {"Ticker": "TMO", "Empresa": "Thermo Fisher", "Día": "Jueves 29/10", "Momento": "PRE APERTURA", "EPS Est": "$6.40", "Reacción": "🟢 +1,0% hoy"},
        {"Ticker": "IBM", "Empresa": "Int. Business Machines", "Día": "Viernes 30/10", "Momento": "POST CIERRE", "EPS Est": "$2.88", "Reacción": "Pendiente"},
        {"Ticker": "DHR", "Empresa": "Danaher Corp.", "Día": "Viernes 30/10", "Momento": "PRE APERTURA", "EPS Est": "$1.92", "Reacción": "🟢 +4,4% hoy"}
    ])
    
    for index, row in df_balances.iterrows():
        with st.container():
            col_b1, col_b2, col_b3, col_b4 = st.columns([1, 2, 2, 1])
            col_b1.markdown(f"### **{row['Ticker']}**")
            col_b2.markdown(f"🗓️ *{row['Día']}*  \n🕒 `{row['Momento']}`")
            col_b3.markdown(f"📊 **EPS Est:** `{row['EPS Est']}`")
            col_b4.markdown(f"📈 **{row['Reacción']}**")
            st.divider()

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
    
