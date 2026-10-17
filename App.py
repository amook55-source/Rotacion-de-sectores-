import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Terminal de Mercado S&P 500", layout="wide")

# Estilo oscuro tipo Terminal
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .card {
        background-color: #1a1f2c;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #2d3748;
        margin-bottom: 8px;
    }
    .badge-green { color: #00cc96; font-weight: bold; }
    .badge-red { color: #ef553b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

sectors = {
    "XLK": {"nombre": "Tecnología", "tickers": "AAPL, MSFT, NVDA"},
    "XLY": {"nombre": "Consumo Discr.", "tickers": "AMZN, TSLA, MCD"},
    "XLC": {"nombre": "Comunicaciones", "tickers": "GOOGL, META, NFLX"},
    "XLF": {"nombre": "Financieros", "tickers": "JPM, BRK.B, V"},
    "XLI": {"nombre": "Industriales", "tickers": "GE, CAT, UNP"},
    "XLE": {"nombre": "Energía", "tickers": "XOM, CVX, COP"},
    "XLB": {"nombre": "Materiales", "tickers": "LIN, FCX, NEM"},
    "XLV": {"nombre": "Salud", "tickers": "LLY, UNH, JNJ"},
    "XLP": {"nombre": "Consumo Masivo", "tickers": "WMT, PG, KO"},
    "XLU": {"nombre": "Utilities", "tickers": "NEE, SO, DUK"},
    "XLRE": {"nombre": "Real Estate", "tickers": "PLD, AMT, EQIX"}
}

top_stocks = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "WMT", "UNH", "XOM", "LLY", "PG", "COST"]

@st.cache_data(ttl=3600)
def fetch_all_data():
    all_tickers = list(set(["SPY"] + list(sectors.keys()) + top_stocks))
    df = yf.download(all_tickers, period="6mo", interval="1d", progress=False)['Close']
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(0, axis=1)
    return df

try:
    df = fetch_all_data()
    spy = df["SPY"]
    spy_last = spy.iloc[-1]
    spy_prev = spy.iloc[-2]
    spy_pct = ((spy_last / spy_prev) - 1) * 100

    # CÁLCULO DE SECTORES
    sec_results = []
    for ticker, info in sectors.items():
        if ticker in df.columns:
            sec_price = df[ticker]
            r = sec_price / spy
            sma_r = r.rolling(window=14).mean()
            x = ((r / sma_r) - 1) * 100
            y = x.pct_change(periods=10) * 100
            lx, ly = x.iloc[-1], y.iloc[-1]
            
            if lx >= 0 and ly >= 0:
                cat = "Líderes"
            elif lx >= 0 and ly < 0:
                cat = "Debilitándose"
            elif lx < 0 and ly < 0:
                cat = "Rezagados"
            else:
                cat = "Mejorando"

            sec_results.append({
                "ETF": ticker,
                "Nombre": info["nombre"],
                "Fuerza": round(float(lx), 2),
                "Momentum": round(float(ly), 2),
                "Estado": cat,
                "Componentes": info["tickers"]
            })
    df_sec = pd.DataFrame(sec_results)

    # CÁLCULO DE STOCKS (MOVERS DEL DÍA)
    stock_changes = []
    for s in top_stocks:
        if s in df.columns:
            last = df[s].iloc[-1]
            prev = df[s].iloc[-2]
            pct = ((last / prev) - 1) * 100
            stock_changes.append({
                "Ticker": s, 
                "Precio": round(float(last), 2), 
                "Variacion": round(float(pct), 2)
            })
    df_stocks = pd.DataFrame(stock_changes).sort_values(by="Variacion", ascending=False)

    # TÍTULO PRINCIPAL
    st.title("🖥️ Terminal de Control & Rotación Sectorial")
    st.markdown("---")

    # PANEL EN DOS COLUMNAS PRINCIPALES
    col_izq, col_der = st.columns([1, 1])

    # ------------------ PANEL IZQUIERDO ------------------
    with col_izq:
        st.subheader("⚡ Régimen de Mercado")
        
        # Puntaje continuo de salud basado en la Fuerza Relativa promedio
        avg_fuerza = df_sec["Fuerza"].mean()
        # Normalizamos el puntaje entre 0 y 100
        score = int(max(0, min(100, (avg_fuerza + 5) * 10)))
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Salud Sectorial", 'font': {'size': 16, 'color': "white"}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#00cc96" if score >= 50 else "#ef553b"},
                'bgcolor': "#1a1f2c",
                'borderwidth': 2,
                'bordercolor': "#2d3748",
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(239, 85, 59, 0.3)'},
                    {'range': [40, 70], 'color': 'rgba(255, 161, 90, 0.3)'},
                    {'range': [70, 100], 'color': 'rgba(0, 204, 150, 0.3)'}
                ]
            }
        ))
        fig_gauge.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.metric(label="SPY (S&P 500)", value=f"${spy_last:.2f}", delta=f"{spy_pct:.2f}%")

        st.markdown("---")
        st.subheader("📊 Rotación Sectorial (Resumen Compacto)")
        
        fig_bar = px.bar(
            df_sec.sort_values(by="Fuerza", ascending=True),
            x="Fuerza",
            y="ETF",
            color="Estado",
            hover_data=["Nombre", "Componentes"],
            orientation='h',
            color_discrete_map={
                "Líderes": "#00cc96",
                "Debilitándose": "#ffa15a",
                "Rezagados": "#ef553b",
                "Mejorando": "#ab63fa"
            },
            title="Fuerza Relativa por Sector vs SPY"
        )
        fig_bar.update_layout(height=380, template="plotly_dark", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ------------------ PANEL DERECHO ------------------
    with col_der:
        st.subheader("🔥 Cartelera del Día (Top Movers)")
        
        col_g, col_l = st.columns(2)
        
        with col_g:
            st.markdown("##### 🚀 Top Ganadoras")
            gainers = df_stocks.head(5)
            for r in gainers.itertuples():
                var_val = getattr(r, 'Variacion')
                st.markdown(f"""
                <div class="card">
                    <b>{r.Ticker}</b> | ${r.Precio}<br>
                    <span class="badge-green">+{var_val:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

        with col_l:
            st.markdown("##### 🔻 Top Perdedoras")
            losers = df_stocks.tail(5).iloc[::-1]
            for r in losers.itertuples():
                var_val = getattr(r, 'Variacion')
                st.markdown(f"""
                <div class="card">
                    <b>{r.Ticker}</b> | ${r.Precio}<br>
                    <span class="badge-red">{var_val:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🗂️ Resumen por Categorías")
        
        for cat in ["Líderes", "Debilitándose", "Mejorando", "Rezagados"]:
            sub = df_sec[df_sec["Estado"] == cat]
            if len(sub) > 0:
                tickers_str = ", ".join([f"**{row.ETF}** ({row.Nombre})" for row in sub.itertuples()])
                st.markdown(f"**{cat}:** {tickers_str}")

except Exception as e:
    st.error(f"Error cargando datos: {e}")
    
