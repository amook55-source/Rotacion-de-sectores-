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

# ==========================================
# PESTAÑA 1 & 2 (Mantenemos tus gráficos RRG y Scores)
# ==========================================
with tab1:
    st.header("Cuadro de Rotación de Sectores")
    # Tu gráfico RRG aquí...

with tab2:
    st.header("Régimen & Top Scores")
    # Tu régimen y scores aquí...

# ==========================================
# PESTAÑA 3: ACCIONES EE. UU., GANADORES/PERDEDORES Y SECTORES
# ==========================================
with tab3:
    st.header("🇺🇸 Mercado de Acciones de EE. UU.")

    # Universo ampliado de acciones por sector
    sectores_ampliados = {
        "Tecnología 💻": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "AMD", "ORCL", "CRM", "INTC", "QCOM", "TXN", "IBM"],
        "Energía ⚡": ["XOM", "CVX", "COP", "SLB", "BP", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
        "Salud 🏥": ["JNJ", "PFE", "UNH", "ABBV", "LLY", "MRK", "TMO", "DHR", "BMY", "AMGN", "GILD"],
        "Financiero 🏦": ["JPM", "BAC", "WFC", "C", "MS", "GS", "BLK", "AXP", "V", "MA", "SCHW"],
        "Consumo Discrecional 🛒": ["TSLA", "NKE", "MCD", "HD", "SBUX", "LOW", "BKNG", "TJX", "TGT", "AMZN"],
        "Industriales & Servicios 🏗️": ["CAT", "DE", "GE", "LMT", "BA", "UNP", "HON", "MMM", "UPS", "RTX"],
        "Comunicaciones & Medios 📡": ["NFLX", "DIS", "TMUS", "VZ", "T", "CMCSA", "EA", "TTWO"]
    }

    # Función robusta para obtener cotizaciones sin error Nan
    @st.cache_data(ttl=300)  # Guarda datos en caché por 5 minutos para que sea ultrarrápido
    def obtener_cotizaciones(lista_tickers):
        resultados = []
        for ticker in lista_tickers:
            try:
                data = yf.Ticker(ticker).history(period="5d")
                if len(data) >= 2:
                    precio_actual = data['Close'].iloc[-1]
                    precio_anterior = data['Close'].iloc[-2]
                    var_pct = ((precio_actual - precio_anterior) / precio_anterior) * 100
                    
                    resultados.append({
                        "Ticker": ticker,
                        "Precio ($)": round(precio_actual, 2),
                        "Variación (%)": round(var_pct, 2),
                        "Estado": "🟢 Subida" if var_pct >= 0 else "🔴 Baja"
                    })
            except Exception:
                pass
        return pd.DataFrame(resultados)

    # 1. Cargar todas las acciones
    todos_los_tickers = list(set([t for lista in sectores_ampliados.values() for t in lista]))
    with st.spinner("Cargando cotizaciones en tiempo real..."):
        df_todos = obtener_cotizaciones(todos_los_tickers)

    if not df_todos.empty:
        # ----------------------------------------------------
        # SECCIÓN: TOP 10 GANADORES Y PERDEDORES
        # ----------------------------------------------------
        st.subheader("🔥 Top 10 Ganadores y Perdedores del Día")
        col_ganadores, col_perdedores = st.columns(2)

        df_sorted = df_todos.sort_values(by="Variación (%)", ascending=False)

        with col_ganadores:
            st.markdown("### 🟢 Top 10 Ganadores")
            top_ganadores = df_sorted.head(10).copy()
            top_ganadores["Variación (%)"] = top_ganadores["Variación (%)"].apply(lambda x: f"+{x:.2f}%")
            top_ganadores["Precio ($)"] = top_ganadores["Precio ($)"].apply(lambda x: f"${x:.2f}")
            st.dataframe(top_ganadores[["Ticker", "Precio ($)", "Variación (%)"]], use_container_width=True, hide_index=True)

        with col_perdedores:
            st.markdown("### 🔴 Top 10 Perdedores")
            top_perdedores = df_sorted.tail(10).iloc[::-1].copy()
            top_perdedores["Variación (%)"] = top_perdedores["Variación (%)"].apply(lambda x: f"{x:.2f}%")
            top_perdedores["Precio ($)"] = top_perdedores["Precio ($)"].apply(lambda x: f"${x:.2f}")
            st.dataframe(top_perdedores[["Ticker", "Precio ($)", "Variación (%)"]], use_container_width=True, hide_index=True)

        st.divider()

        # ----------------------------------------------------
        # SECCIÓN: ACCIONES DIVIDIDAS POR SECTOR
        # ----------------------------------------------------
        st.subheader("📂 Cotizaciones Detalladas por Sector")

        for sector, tickers in sectores_ampliados.items():
            with st.expander(f"📁 **{sector}**", expanded=True):
                df_sector = df_todos[df_todos["Ticker"].isin(tickers)].copy()
                if not df_sector.empty:
                    df_sector["Variación (%)"] = df_sector["Variación (%)"].apply(lambda x: f"{'+' if x >= 0 else ''}{x:.2f}%")
                    df_sector["Precio ($)"] = df_sector["Precio ($)"].apply(lambda x: f"${x:.2f}")
                    st.dataframe(df_sector[["Ticker", "Precio ($)", "Variación (%)", "Estado"]], use_container_width=True, hide_index=True)
    else:
        st.error("No se pudieron cargar los datos del mercado. Intenta refrescar en unos instantes.")
        
