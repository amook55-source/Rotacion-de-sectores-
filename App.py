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
    .info-card {
        background-color: #161b22;
        padding: 10px;
        border-radius: 6px;
        border-left: 3px solid #00cc96;
        font-size: 12px;
        color: #c9d1d9;
        margin-bottom: 12px;
    }
    .badge-green { color: #00cc96; font-weight: bold; }
    .badge-red { color: #ef553b; font-weight: bold; }
    .badge-outperform { background-color: rgba(0, 204, 150, 0.2); color: #00cc96; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
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
    spy_5d_ret = (spy.iloc[-1] / spy.iloc[-6]) - 1

    # 2. DATOS DEL VIX
    vix_last = df["^VIX"].iloc[-1] if "^VIX" in df.columns else 20.0
    if vix_last < 15:
        vix_status = "🟢 Calma (Baja Volatilidad)"
    elif vix_last <= 22:
        vix_status = "🟡 Alerta Moderada"
    else:
        vix_status = "🔴 Pánico / Alta Volatilidad"

    # 3. CÁLCULO DE SECTORES Y SALUD REACTIVA
    sec_results = {}
    positive_sec_today = 0

    for ticker, info in sectors.items():
        if ticker in df.columns:
            sec_price = df[ticker]
            sec_1d = ((sec_price.iloc[-1] / sec_price.iloc[-2]) - 1) * 100
            if sec_1d > 0:
                positive_sec_today += 1

            r = sec_price / spy
            sma_r = r.rolling(window=14).mean()
            x = ((r / sma_r) - 1) * 100
            lx = x.iloc[-1]

            sec_results[ticker] = {
                "fuerza": round(float(lx), 2),
                "var_1d": round(float(sec_1d), 2),
                "nombre": info["nombre"]
            }

    # 4. CÁLCULO DE STOCKS (MOVERS, OUTPERFORM & SCORING)
    stock_analysis = []
    above_sma50 = 0
    above_sma200 = 0
    valid_stocks = 0

    stock_to_sector = {}
    for etf, info in sectors.items():
        for t in info["tickers"]:
            stock_to_sector[t] = etf

    for s in top_stocks:
        if s in df.columns:
            s_series = df[s].dropna()
            if len(s_series) >= 200:
                valid_stocks += 1
                last_p = s_series.iloc[-1]
                prev_p = s_series.iloc[-2]
                pct_1d = ((last_p / prev_p) - 1) * 100
                
                s_5d_ret = (s_series.iloc[-1] / s_series.iloc[-6]) - 1
                is_outperformer = s_5d_ret > spy_5d_ret

                sma50 = s_series.rolling(50).mean().iloc[-1]
                sma200 = s_series.rolling(200).mean().iloc[-1]

                if last_p > sma50:
                    above_sma50 += 1
                if last_p > sma200:
                    above_sma200 += 1

                # Scoring de Oportunidad (0 a 10)
                score = 5
                sec_key = stock_to_sector.get(s)
                if sec_key and sec_key in sec_results:
                    sec_fuerza = sec_results[sec_key]["fuerza"]
                    if sec_fuerza > 2: score += 3
                    elif sec_fuerza > 0: score += 1
                    else: score -= 2
                
                if is_outperformer: score += 2
                if pct_1d > 0: score += 1
                score = max(0, min(10, score))

                stock_analysis.append({
                    "Ticker": s,
                    "Precio": round(float(last_p), 2),
                    "Variacion": round(float(pct_1d), 2),
                    "Outperform": is_outperformer,
                    "Score": score
                })

    df_stocks = pd.DataFrame(stock_analysis).sort_values(by="Variacion", ascending=False)
    pct_sma50 = int((above_sma50 / valid_stocks) * 100) if valid_stocks > 0 else 0
    pct_sma200 = int((above_sma200 / valid_stocks) * 100) if valid_stocks > 0 else 0

    sec_ratio = (positive_sec_today / len(sectors)) * 100
    spy_score = max(0, min(100, (spy_1d + 3) * 16.6))
    vix_score = max(0, min(100, (35 - vix_last) * 4))
    health_score = int((sec_ratio * 0.4) + (spy_score * 0.3) + (vix_score * 0.3))

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

    # ===== PANEL IZQUIERDO =====
    with col_izq:
        st.subheader("⚡ Régimen & Amplitud de Mercado")

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

        a1, a2 = st.columns(2)
        a1.metric("Acciones > SMA 50", f"{pct_sma50}%", help="Corto/Mediano plazo: % de acciones arriba de su promedio de 50 ruedas.")
        a2.metric("Acciones > SMA 200", f"{pct_sma200}%", help="Largo plazo: % de acciones arriba de su promedio de 200 ruedas.")

        st.markdown("""
        <div class="info-card">
        <b>📖 Guía Rápida de Amplitud:</b><br>
        • <b>SMA 50:</b> Abajo del 50% indica corrección a corto plazo.<br>
        • <b>SMA 200:</b> Arriba del 70% mantiene la tendencia alcista general.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 Rotación Sectorial (Semáforo de Fuerza)")

        sec_list_chart = []
        for etf, data_sec in sec_results.items():
            sec_list_chart.append({
                "ETF": f"{etf} ({data_sec['nombre']})",
                "Fuerza": data_sec["fuerza"],
                "Condicion": "Fuerte (Le gana al SPY)" if data_sec["fuerza"] >= 0 else "Débil (Cae más que SPY)"
            })
        df_sec_chart = pd.DataFrame(sec_list_chart).sort_values(by="Fuerza", ascending=True)

        fig_bar = px.bar(
            df_sec_chart,
            x="Fuerza",
            y="ETF",
            color="Condicion",
            orientation='h',
            color_discrete_map={
                "Fuerte (Le gana al SPY)": "#00cc96",
                "Débil (Cae más que SPY)": "#ef553b"
            },
            title="Fuerza Relativa por Sector vs SPY"
        )
        fig_bar.update_layout(
            height=380, 
            template="plotly_dark", 
            margin=dict(l=10, r=10, t=30, b=10), 
            paper_bgcolor="rgba(0,0,0,0)",
            legend_title_text=""
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ===== PANEL DERECHO =====
    with col_der:
        st.subheader("🔥 Cartelera del Día & Scoring")

        g_col, l_col = st.columns(2)

        with g_col:
            st.markdown("##### 🚀 Top Ganadoras")
            gainers = df_stocks.head(5)
            for r in gainers.itertuples():
                badge = '<span class="badge-outperform">⚡ Outperformer</span>' if r.Outperform else ''
                st.markdown(f"""
                <div class="card">
                    <b>{r.Ticker}</b> | ${r.Precio} {badge}<br>
                    <span class="badge-green">+{r.Variacion:.2f}%</span> | Score: <b>{r.Score}/10</b>
                </div>
                """, unsafe_allow_html=True)

        with l_col:
            st.markdown("##### 🔻 Top Perdedoras")
            losers = df_stocks.tail(5).iloc[::-1]
            for r in losers.itertuples():
                badge = '<span class="badge-outperform">⚡ Outperformer</span>' if r.Outperform else ''
                st.markdown(f"""
                <div class="card">
                    <b>{r.Ticker}</b> | ${r.Precio} {badge}<br>
                    <span class="badge-red">{r.Variacion:.2f}%</span> | Score: <b>{r.Score}/10</b>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🔍 Lupa Interactiva por Sector")

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
                    
