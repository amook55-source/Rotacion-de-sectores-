import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Terminal de Control S&P 500", layout="wide")

# Estilos OSCUROS tipo Control Center
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
    .badge-yellow { color: #fecb52; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

sectors = {
    "XLK": {"nombre": "Tecnología", "tickers": ["AAPL", "MSFT", "NVDA", "AVGO", "AMD", "QCOM"]},
    "XLY": {"nombre": "Consumo Discrecional", "tickers": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX"]},
    "XLC": {"nombre": "Comunicaciones", "tickers": ["GOOGL", "META", "NFLX", "DIS", "TMUS"]},
    "XLF": {"nombre": "Financieros", "tickers": ["BRK-B", "JPM", "V", "MA", "BAC", "MS"]},
    "XLI": {"nombre": "Industriales", "tickers": ["GE", "CAT", "UNP", "RTX", "HON", "BA"]},
    "XLE": {"nombre": "Energía", "tickers": ["XOM", "CVX", "COP", "SLB", "MPC"]},
    "XLB": {"nombre": "Materiales Básicos", "tickers": ["LIN", "FCX", "NEM", "DOW", "APD"]},
    "XLV": {"nombre": "Salud", "tickers": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE"]},
    "XLP": {"nombre": "Consumo Masivo", "tickers": ["WMT", "PG", "KO", "PEP", "COST", "MO"]},
    "XLU": {"nombre": "Servicios Públicos", "tickers": ["NEE", "SO", "DUK", "CEG", "AEP"]},
    "XLRE": {"nombre": "Real Estate", "tickers": ["PLD", "AMT", "EQIX", "CCI", "SPG"]}
}

top_stocks = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "WMT", "UNH", "XOM", "LLY", "PG", "COST", "MCD", "KO", "AMD", "BAC", "PEP"]

@st.cache_data(ttl=3600)
def fetch_data():
    all_tickers = list(set(["SPY", "^VIX"] + list(sectors.keys()) + top_stocks))
    df = yf.download(all_tickers, period="1y", interval="1d", progress=False)['Close']
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(0, axis=1)
    return df

try:
    df = fetch_data()

    # 1. DATOS DEL SPY
    spy = df["SPY"]
    spy_last = spy.iloc[-1]
    spy_1d = ((spy_last / spy.iloc[-2]) - 1) * 100
    spy_1w = ((spy_last / spy.iloc[-6]) - 1) * 100
    spy_1m = ((spy_last / spy.iloc[-22]) - 1) * 100

    # 2. DATOS DEL VIX
    vix_last = df["^VIX"].iloc[-1] if "^VIX" in df.columns else 20.0
    if vix_last < 15:
        vix_status = "🟢 Calma (Baja Volatilidad)"
    elif vix_last <= 22:
        vix_status = "🟡 Alerta Moderada"
    else:
        vix_status = "🔴 Pánico / Alta Volatilidad"

    # 3. CÁLCULO DE SECTORES Y SALUD REACTIVA
    sec_results = []
    positive_sec_today = 0

    for ticker, info in sectors.items():
        if ticker in df.columns:
            sec_price = df[ticker]
            # Cambio del día
            sec_1d = ((sec_price.iloc[-1] / sec_price.iloc[-2]) - 1) * 100
            if sec_1d > 0:
                positive_sec_today += 1

            # Rotación fuerza vs SPY
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
                "Var_1D": round(float(sec_1d), 2),
                "Tickers": info["tickers"]
            })
    df_sec = pd.DataFrame(sec_results)

    # CÁLCULO DE SALUD DEL MERCADO (REACTIVO A DÍAS CAÍDOS)
    # Ponderamos: 40% sectores en verde hoy + 30% impacto diario SPY + 30% nivel VIX
    sec_ratio = (positive_sec_today / len(df_sec)) * 100 if len(df_sec) > 0 else 50
    spy_score = max(0, min(100, (spy_1d + 3) * 16.6))  # -3% = 0, 0% = 50, +3% = 100
    vix_score = max(0, min(100, (35 - vix_last) * 4))   # VIX 35 = 0, VIX 10 = 100

    health_score = int((sec_ratio * 0.4) + (spy_score * 0.3) + (vix_score * 0.3))

    # 4. CÁLCULO DE STOCKS (MOVERS & MEDIAS MÓVILES)
    stock_changes = []
    above_sma50 = 0
    above_sma200 = 0
    valid_stocks = 0

    for s in top_stocks:
        if s in df.columns:
            s_series = df[s].dropna()
            if len(s_series) >= 200:
                valid_stocks += 1
                last_p = s_series.iloc[-1]
                prev_p = s_series.iloc[-2]
                pct = ((last_p / prev_p) - 1) * 100

                sma50 = s_series.rolling(50).mean().iloc[-1]
                sma200 = s_series.rolling(200).mean().iloc[-1]

                if last_p > sma50:
                    above_sma50 += 1
                if last_p > sma200:
                    above_sma200 += 1

                stock_changes.append({
                    "Ticker": s,
                    "Precio": round(float(last_p), 2),
                    "Variacion": round(float(pct), 2)
                })

    df_stocks = pd.DataFrame(stock_changes).sort_values(by="Variacion", ascending=False)
    pct_sma50 = int((above_sma50 / valid_stocks) * 100) if valid_stocks > 0 else 0
    pct_sma200 = int((above_sma200 / valid_stocks) * 100) if valid_stocks > 0 else 0

    # ------------------ ENCABEZADO Y TENDENCIA SPY ------------------
    st.title("🖥️ Terminal de Control & Mercado")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SPY Precio", f"${spy_last:.2f}", f"{spy_1d:.2f}% (1D)")
    c2.metric("Tendencia Semanal", "SPY 1W", f"{spy_1w:.2f}%")
    c3.metric("Tendencia Mensual", "SPY 1M", f"{spy_1m:.2f}%")
    c4.metric("VIX (Volatilidad)", f"{vix_last:.2f}", vix_status)

    st.markdown("---")

    # ------------------ PANEL EN DOS COLUMNAS ------------------
    col_izq, col_der = st.columns([1, 1])

    # ===== PANEL IZQUIERDO: RÉGIMEN & AMPLITUD =====
    with col_izq:
        st.subheader("⚡ Régimen & Amplitud de Mercado")

        # Gauge Chart Reactivo
        gauge_color = "#00cc96" if health_score >= 60 else ("#ffa15a" if health_score >= 40 else "#ef553b")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Salud del Mercado en Tiempo Real", 'font': {'size': 16, 'color': "white"}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': gauge_color},
                'bgcolor': "#1a1f2c",
                'borderwidth': 2,
                'bordercolor': "#2d3748",
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(239, 85, 59, 0.3)'},
                    {'range': [40, 60], 'color': 'rgba(255, 161, 90, 0.3)'},
                    {'range': [60, 100], 'color': 'rgba(0, 204, 150, 0.3)'}
                ]
            }
        ))
        fig_gauge.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Amplitud de Medias Móviles
        st.markdown("**Amplitud Táctica (Megacaps)**")
        a1, a2 = st.columns(2)
        a1.metric("Acciones > SMA 50", f"{pct_sma50}%")
        a2.metric("Acciones > SMA 200", f"{pct_sma200}%")

        st.markdown("---")
        st.subheader("📊 Rotación Sectorial Compacta")

        fig_bar = px.bar(
            df_sec.sort_values(by="Fuerza", ascending=True),
            x="Fuerza",
            y="ETF",
            color="Estado",
            hover_data=["Nombre", "Var_1D"],
            orientation='h',
            color_discrete_map={
                "Líderes": "#00cc96",
                "Debilitándose": "#ffa15a",
                "Rezagados": "#ef553b",
                "Mejorando": "#ab63fa"
            },
            title="Fuerza Relativa por Sector vs SPY"
        )
        fig_bar.update_layout(height=360, template="plotly_dark", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ===== PANEL DERECHO: CARTELERA & LUPA POR SECTOR =====
    with col_der:
        st.subheader("🔥 Cartelera del Día (Top Movers)")

        g_col, l_col = st.columns(2)

        with g_col:
            st.markdown("##### 🚀 Top Ganadoras")
            gainers = df_stocks.head(5)
            for r in gainers.itertuples():
                v = getattr(r, 'Variacion')
                st.markdown(f"""
                <div class="card">
                    <b>{r.Ticker}</b> | ${r.Precio}<br>
                    <span class="badge-green">+{v:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

        with l_col:
            st.markdown("##### 🔻 Top Perdedoras")
            losers = df_stocks.tail(5).iloc[::-1]
            for r in losers.itertuples():
                v = getattr(r, 'Variacion')
                st.markdown(f"""
                <div class="card">
                    <b>{r.Ticker}</b> | ${r.Precio}<br>
                    <span class="badge-red">{v:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🔍 Lupa Interactiva por Sector")

        # Selector para inspeccionar sector
        selected_etf = st.selectbox(
            "Selecciona un sector para ver sus componentes:",
            options=list(sectors.keys()),
            format_func=lambda x: f"{x} - {sectors[x]['nombre']}"
        )

        if selected_etf:
            sec_info = sectors[selected_etf]
            st.markdown(f"**Componentes Clave de {selected_etf} ({sec_info['nombre']}):**")
            
            comp_data = []
            for t in sec_info["tickers"]:
                if t in df.columns:
                    p = df[t].iloc[-1]
                    p_prev = df[t].iloc[-2]
                    var = ((p / p_prev) - 1) * 100
                    comp_data.append({"Acción": t, "Precio": round(float(p), 2), "Variación Día": round(float(var), 2)})
            
            if comp_data:
                st.dataframe(pd.DataFrame(comp_data), use_container_width=True)

except Exception as e:
    st.error(f"Error cargando datos: {e}")
    
