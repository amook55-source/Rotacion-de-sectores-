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
    /* Fondo principal */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Contenedores y Tarjetas */
    div[data-testid="stMetric"], .warren-card {
        background: linear-gradient(135deg, #131822 0%, #1A2130 100%);
        border: 1px solid #232D42;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    /* Títulos e indicadores */
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700;
    }
    
    /* Pestañas personalizadas */
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

    /* Tablas oscuras */
    .dataframe {
        background-color: #131822 !important;
        color: #E2E8F0 !important;
        border: 1px solid #232D42 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Warren Dashboard - Market Intelligence")

# 4 Pestañas principales (con la nueva pestaña de Balances incluida)
tab1, tab2, tab3, tab4 = st.tabs([
    "🌀 Rotación Sectorial", 
    "😱 Régimen & Índice de Miedo", 
    "🇺🇸 Mercado EE. UU. por Sector",
    "📅 Próximos Balances"
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
        
        # Obtener VIX
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
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#131822',
        font=dict(color='#E2E8F0'),
        xaxis=dict(gridcolor='#1E293B', title="Fuerza Relativa vs SPY"),
        yaxis=dict(gridcolor='#1E293B', title="Momentum"),
        height=550
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
            estado_texto = "🔴 MIEDO EXTREMO"
            color_gauge = "#FF3B69"
        elif fear_greed_score < 45:
            estado_texto = "🟠 MIEDO"
            color_gauge = "#FF8800"
        elif fear_greed_score < 55:
            estado_texto = "🟡 NEUTRAL"
            color_gauge = "#FFB800"
        elif fear_greed_score < 75:
            estado_texto = "🟢 CODICIA"
            color_gauge = "#00E5FF"
        else:
            estado_texto = "🔥 CODICIA EXTREMA"
            color_gauge = "#00FF88"

        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(f"Estado Actual: {estado_texto}")
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=fear_greed_score,
                number={'suffix': "/100", 'font': {'color': color_gauge, 'size': 48}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#334155"},
                    'bar': {'color': color_gauge, 'thickness': 0.3},
                    'bgcolor': "#131822",
                    'borderwidth': 1,
                    'bordercolor': "#232D42",
                    'steps': [
                        {'range': [0, 25], 'color': '#2A121B'},
                        {'range': [25, 45], 'color': '#2A1C12'},
                        {'range': [45, 55], 'color': '#2A2612'},
                        {'range': [55, 75], 'color': '#12262A'},
                        {'range': [75, 100], 'color': '#122A1E'}
                    ],
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E2E8F0'),
                height=350,
                margin=dict(l=20, r=20, t=30, b=20)
            )
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
# PESTAÑA 4: PRÓXIMOS BALANCES (AUTOMÁTICO)
# ==========================================
with tab4:
    st.header("📅 Calendario de Próximos Balances (Earnings)")
    st.write("Monitoreo automático de presentación de resultados y estimaciones de EPS para las principales acciones y CEDEARs.")

    @st.cache_data(ttl=3600)
    def obtener_balances_automaticos(tickers):
        datos = []
        ahora = datetime.now() - timedelta(days=1)
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                cal = t.get_earnings_dates(limit=3)
                if cal is not None and not cal.empty:
                    futuras = cal[cal.index >= ahora]
                    if not futuras.empty:
                        prox = futuras.index[0]
                        fila = futuras.iloc[0]
                        eps_est = fila.get('EPS Estimate', None)
                        
                        hora = prox.hour
                        if hora < 12:
                            momento = "PRE (Antes de la campana)"
                        elif hora >= 16:
                            momento = "POST (Después del cierre)"
                        else:
                            momento = "DURANTE / HORA NO ESPECIFICADA"

                        datos.append({
                            "Ticker": ticker,
                            "Fecha": prox.strftime('%Y-%m-%d'),
                            "Hora_dt": prox,
                            "Momento": momento,
                            "EPS Estimado": f"${eps_est:.2f}" if pd.notnull(eps_est) else "N/A"
                        })
            except Exception:
                continue
        return pd.DataFrame(datos)

    with st.spinner("Consultando próximos balances automáticamente..."):
        df_balances = obtener_balances_automaticos(TODOS_TICKERS)

    if df_balances.empty:
        st.warning("No se pudieron recuperar las fechas en este momento. Probá recargar la página.")
    else:
        df_balances = df_balances.sort_values(by="Hora_dt")
        fechas_unicas = df_balances["Fecha"].unique()

        for fecha in fechas_unicas:
            df_dia = df_balances[df_balances["Fecha"] == fecha]
            
            with st.expander(f"🗓️ Fecha de Reporte: {fecha} ({len(df_dia)} empresas)", expanded=True):
                for _, row in df_dia.iterrows():
                    col_t, col_m, col_e = st.columns([1, 2, 2])
                    with col_t:
                        st.markdown(f"### **{row['Ticker']}**")
                    with col_m:
                        st.write(f"📌 **{row['Momento']}**")
                    with col_e:
                        st.write(f"💵 **EPS Est:** {row['EPS Estimado']}")
                    st.markdown("---")
                    
