import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Rotación de Sectores S&P 500", layout="wide")

st.title("📊 Dashboard de Rotación de Sectores S&P 500")
st.markdown("Mapa de **Fuerza Relativa vs. Momentum** comparado contra el **SPY** para identificar el flujo de dinero en tiempo real.")

sectors = {
    "XLK": "Tecnología (AAPL/MSFT)",
    "XLY": "Consumo Discrecional (AMZN/TSLA)",
    "XLC": "Comunicaciones (META/GOOG)",
    "XLF": "Financieros",
    "XLI": "Industriales",
    "XLE": "Energía (Petroleras)",
    "XLB": "Materiales Básicos",
    "XLV": "Salud (Pharma)",
    "XLP": "Consumo Masivo",
    "XLU": "Servicios Públicos",
    "XLRE": "Real Estate"
}

@st.cache_data(ttl=3600)
def load_data():
    tickers = ["SPY"] + list(sectors.keys())
    data = yf.download(tickers, period="6mo", interval="1d", progress=False)['Close']
    if isinstance(data.columns, pd.MultiIndex):
        data = data.droplevel(0, axis=1)
    return data

try:
    data = load_data()
    spy = data["SPY"]

    results = []

    for ticker, name in sectors.items():
        if ticker in data.columns:
            sec_price = data[ticker]
            # Fuerza Relativa
            r = sec_price / spy
            sma_r = r.rolling(window=14).mean()
            x = ((r / sma_r) - 1) * 100
            # Momentum (Rate of Change)
            y = x.pct_change(periods=10) * 100
            
            last_x = x.iloc[-1]
            last_y = y.iloc[-1]
            
            # Asignación de Cuadrantes
            if last_x >= 0 and last_y >= 0:
                quadrant = "Líderes"
            elif last_x >= 0 and last_y < 0:
                quadrant = "Debilitándose"
            elif last_x < 0 and last_y < 0:
                quadrant = "Rezagados"
            else:
                quadrant = "Mejorando"
                
            results.append({
                "Ticker": ticker,
                "Descripción": name,
                "Fuerza_Relativa": round(float(last_x), 2),
                "Momentum": round(float(last_y), 2),
                "Cuadrante": quadrant
            })

    df_res = pd.DataFrame(results)

    # Gráfico interactivo con Plotly (Estilo Cuadrantes)
    fig = px.scatter(
        df_res, 
        x="Fuerza_Relativa", 
        y="Momentum", 
        text="Ticker",
        color="Cuadrante",
        color_discrete_map={
            "Líderes": "#00CC96",
            "Debilitándose": "#FFA15A",
            "Rezagados": "#636EFA",
            "Mejorando": "#AB63FA"
        },
        title="Mapa de Cuadrantes de Rotación Sectorial"
    )

    fig.update_traces(textposition='top center', marker=dict(size=14))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(height=650, template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Detalle de los Sectores")
    st.dataframe(df_res, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar los datos de Yahoo Finance: {e}")
