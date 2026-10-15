import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Rotación de Sectores S&P 500", layout="wide")

st.title("📊 Resumen de Rotación de Sectores S&P 500")
st.markdown("Clasificación clara del flujo de dinero en los sectores comparados contra el **SPY**.")

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
            r = sec_price / spy
            sma_r = r.rolling(window=14).mean()
            x = ((r / sma_r) - 1) * 100
            y = x.pct_change(periods=10) * 100
            
            last_x = x.iloc[-1]
            last_y = y.iloc[-1]
            
            if last_x >= 0 and last_y >= 0:
                quadrant = "🟢 Líderes (Fuertes y Subiendo)"
            elif last_x >= 0 and last_y < 0:
                quadrant = "🟠 Debilitándose (Fuerte pero perdiendo fuerza)"
            elif last_x < 0 and last_y < 0:
                quadrant = "🔴 Rezagados (Débiles y Cayendo)"
            else:
                quadrant = "🟣 Mejorando (Débiles pero repuntando)"
                
            results.append({
                "Ticker": ticker,
                "Descripción": name,
                "Fuerza Relativa": round(float(last_x), 2),
                "Momentum": round(float(last_y), 2),
                "Estado": quadrant
            })

    df_res = pd.DataFrame(results)

    # Mostrar por pestañas o bloques limpios agrupados por estado
    estados = df_res["Estado"].unique()

    for estado in sorted(estados):
        st.subheader(estado)
        subset = df_res[df_res["Estado"] == estado]
        
        # Mostramos en columnas o tarjetas simples
        cols = st.columns(len(subset) if len(subset) > 0 else 1)
        for i, row in enumerate(subset.itertuples()):
            with cols[i % len(cols)]:
                st.info(f"**{row.Ticker}**\n\n{row.Descripción}")

    st.markdown("---")
    st.subheader("📋 Tabla Completa de Datos")
    st.dataframe(df_res, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar los datos de Yahoo Finance: {e}")
    
