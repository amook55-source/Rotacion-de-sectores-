import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def render_seccion_balances_automatico():
    st.header("📅 Próximos Balances (Organizados por Día)")
    st.write("Calendario automático de reportes de resultados para las principales acciones y CEDEARs.")

    tickers_automaticos = [
        "META", "TSLA", "LRCX", "AAPL", "NVDA", "AMZN", "MSFT", 
        "GOOGL", "AMD", "NFLX", "MELI", "BABA", "JPM", "DIS", 
        "KO", "INTC", "PYPL", "BA", "PEP", "XOM", "CVX", "PFE"
    ]

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
        df = obtener_balances_automaticos(tickers_automaticos)

    if df.empty:
        st.warning("No se pudieron recuperar las fechas en este momento. Probá recargar la página.")
        return

    df = df.sort_values(by="Hora_dt")
    fechas_unicas = df["Fecha"].unique()

    for fecha in fechas_unicas:
        df_dia = df[df["Fecha"] == fecha]
        
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
                
