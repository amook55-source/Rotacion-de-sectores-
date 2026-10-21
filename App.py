import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Market & Sector Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Dashboard de Análisis de Mercado & Sectores")

tab1, tab2, tab3 = st.tabs([
    "🌀 Rotación Sectorial", 
    "🎯 Régimen & Top Scores", 
    "🇺🇸 Acciones EE. UU. por Sector"
])

# Lista unificada de acciones por sector
SECTORES = {
    "Tecnología 💻": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "AMD", "ORCL", "CRM", "INTC", "QCOM", "IBM"],
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
        # Descargamos todo de un solo paquete (mucho más rápido y sin bloqueos de API)
        df_download = yf.download(tickers, period="5d", interval="1d", progress=False)['Close']
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
        return pd.DataFrame(resultados)
    except Exception as e:
        return pd.DataFrame()

df_mercado = cargar_datos_mercado(TODOS_TICKERS)

# ==========================================
# PESTAÑA 1: ROTACIÓN SECTORIAL
# ==========================================
with tab1:
    st.header("Cuadro de Rotación de Sectores")
    sectors_data = pd.DataFrame({
        'Sector': ['XLK (Tech)', 'XLE (Energía)', 'XLP (Consumo Def.)', 'XLV (Salud)', 'XLI (Industrial)'],
        'Fuerza_Relativa': [-1.5, 1.8, 1.2, 1.5, -0.8],
        'Momentum': [-1.8, 1.1, 1.9, 1.2, -0.5]
    })
    
    fig_rrg = px.scatter(
        sectors_data, x='Fuerza_Relativa', y='Momentum', text='Sector', color='Sector'
    )
    fig_rrg.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_rrg.add_vline(x=0, line_dash="dash", line_color="gray")
    fig_rrg.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig_rrg, use_container_width=True)

# ==========================================
# PESTAÑA 2: RÉGIMEN & METRICAS REALES
# ==========================================
with tab2:
    st.header("🎯 Régimen de Mercado e Indicadores de Amplitud")
    
    if not df_mercado.empty:
        total_activos = len(df_mercado)
        alcistas = len(df_mercado[df_mercado["Variacion"] > 0])
        bajistas = len(df_mercado[df_mercado["Variacion"] < 0])
        pct_alcistas = (alcistas / total_activos) * 100 if total_activos > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Acciones en Subida 🟢", f"{alcistas} / {total_activos}")
        c2.metric("Acciones en Baja 🔴", f"{bajistas} / {total_activos}")
        c3.metric("Amplitud de Mercado (% Alcista)", f"{pct_alcistas:.1f}%")
        
        # Tacómetro basado en la amplitud real
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pct_alcistas,
            title={'text': "Salud del Mercado (% Activos Verdes)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#00FF7F"},
                'steps': [
                    {'range': [0, 40], 'color': "#8B0000"},
                    {'range': [40, 60], 'color': "#4682B4"},
                    {'range': [60, 100], 'color': "#006400"}
                ]
            }
        ))
        fig_gauge.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    else:
        st.info("Cargando métricas de régimen...")

# ==========================================
# PESTAÑA 3: ACCIONES EE. UU. Y GANADORES/PERDEDORES
# ==========================================
with tab3:
    st.header("🇺🇸 Mercado de Acciones de EE. UU.")
    
    if not df_mercado.empty:
        # Top 10 Ganadores y Perdedores
        st.subheader("🔥 Top 10 Ganadores y Perdedores del Día")
        col_g, col_p = st.columns(2)
        
        df_ord = df_mercado.sort_values(by="Variacion", ascending=False)
        
        with col_g:
            st.markdown("#### 🟢 Top 10 Ganadores")
            top_g = df_ord.head(10).copy()
            top_g["Precio ($)"] = top_g["Precio"].apply(lambda x: f"${x:.2f}")
            top_g["Variación (%)"] = top_g["Variacion"].apply(lambda x: f"+{x:.2f}%")
            st.dataframe(top_g[["Ticker", "Precio ($)", "Variación (%)"]], use_container_width=True, hide_index=True)
            
        with col_p:
            st.markdown("#### 🔴 Top 10 Perdedores")
            top_p = df_ord.tail(10).iloc[::-1].copy()
            top_p["Precio ($)"] = top_p["Precio"].apply(lambda x: f"${x:.2f}")
            top_p["Variación (%)"] = top_p["Variacion"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(top_p[["Ticker", "Precio ($)", "Variación (%)"]], use_container_width=True, hide_index=True)
            
        st.divider()
        
        # Sectores
        st.subheader("📂 Cotizaciones Detalladas por Sector")
        for sector, tickers in SECTORES.items():
            with st.expander(f"📁 **{sector}**", expanded=True):
                df_sec = df_mercado[df_mercado["Ticker"].isin(tickers)].copy()
                if not df_sec.empty:
                    df_sec["Precio ($)"] = df_sec["Precio"].apply(lambda x: f"${x:.2f}")
                    df_sec["Variación (%)"] = df_sec["Variacion"].apply(lambda x: f"{'+' if x>=0 else ''}{x:.2f}%")
                    df_sec["Estado"] = df_sec["Variacion"].apply(lambda x: "🟢 Subida" if x>=0 else "🔴 Baja")
                    st.dataframe(df_sec[["Ticker", "Precio ($)", "Variación (%)", "Estado"]], use_container_width=True, hide_index=True)
    else:
        st.error("No se pudieron consultar los datos en este momento. Reintenta actualizando la página.")
