import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Rotación de Sectores S&P 500", layout="wide")

st.title("📊 Resumen de Rotación de Sectores S&P 500")
st.markdown("Clasificación del flujo de dinero en los sectores del S&P 500 frente al **SPY**.")

sectors = {
    "XLK": {
        "nombre": "Tecnología",
        "tickers": "AAPL, MSFT, NVDA, AVGO, ADBX, CRM, AMD, QCOM, INTC, IBM"
    },
    "XLY": {
        "nombre": "Consumo Discrecional",
        "tickers": "AMZN, TSLA, HD, MCD, NKE, LOW, SBUX, TJX, BKNG, CMG"
    },
    "XLC": {
        "nombre": "Comunicaciones",
        "tickers": "GOOGL, META, NFLX, DIS, CMCSA, T, VZ, EA, WBD, TTWO"
    },
    "XLF": {
        "nombre": "Financieros",
        "tickers": "BRK.B, JPM, V, MA, BAC, WFC, GS, MS, C, AXP"
    },
    "XLI": {
        "nombre": "Industriales",
        "tickers": "GE, CAT, UNP, RTX, HON, DE, LMT, BA, ETN, GD"
    },
    "XLE": {
        "nombre": "Energía",
        "tickers": "XOM, CVX, COP, EOG, SLB, MPC, PSX, VLO, WMB, KMI"
    },
    "XLB": {
        "nombre": "Materiales Básicos",
        "tickers": "LIN, SHW, FCX, APD, NEM, EMN, DOW, CTVA, PPG, CE"
    },
    "XLV": {
        "nombre": "Salud",
        "tickers": "LLY, UNH, JNJ, ABBV, MRK, TMO, PFE, ABT, AMGN, ISRG"
    },
    "XLP": {
        "nombre": "Consumo Masivo",
        "tickers": "WMT, PG, KO, PEP, COST, PM, MO, CL, MDLZ, TGT"
    },
    "XLU": {
        "nombre": "Servicios Públicos",
        "tickers": "NEE, SO, DUK, CEG, AEP, SRE, PCG, D, EIX, EXC"
    },
    "XLRE": {
        "nombre": "Real Estate",
        "tickers": "PLD, AMT, EQIX, CCI, SPG, O, Well, PSA, DLR, SBAC"
    }
}

@st.cache_data(ttl=3600)
def load_data():
    ticker_list = ["SPY"] + list(sectors.keys())
    data = yf.download(ticker_list, period="6mo", interval="1d", progress=False)['Close']
    if isinstance(data.columns, pd.MultiIndex):
        data = data.droplevel(0, axis=1)
    return data

try:
    data = load_data()
    spy = data["SPY"]

    results = []

    for ticker, info in sectors.items():
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
                "ETF": ticker,
                "Sector": info["nombre"],
                "Componentes": info["tickers"],
                "Fuerza_Relativa": round(float(last_x), 2),
                "Momentum": round(float(last_y), 2),
                "Estado": quadrant
            })

    df_res = pd.DataFrame(results)

    estados = df_res["Estado"].unique()

    for estado in sorted(estados):
        st.subheader(estado)
        subset = df_res[df_res["Estado"] == estado]
        
        for row in subset.itertuples():
            with st.container():
                st.markdown(f"### 📌 **{row.ETF} - {row.Sector}**")
                st.write(f"**Principales componentes:** `{row.Componentes}`")
                st.markdown("---")

    st.subheader("📋 Tabla Completa de Datos")
    st.dataframe(df_res, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar los datos de Yahoo Finance: {e}")
    
