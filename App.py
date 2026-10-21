import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def obtener_calendario_balances(lista_tickers):
    """
    Consulta los próximos balances de una lista de tickers usando yfinance.
    """
    datos = []
    
    for ticker in lista_tickers:
        try:
            t = yf.Ticker(ticker)
            # get_earnings_dates trae las fechas futuras y pasadas de balances
            cal = t.get_earnings_dates(limit=4)
            
            if cal is not None and not cal.empty:
                # Filtrar fechas futuras o muy recientes del día de hoy
                ahora = datetime.now() - timedelta(days=1)
                fechas_futuras = cal[cal.index >= ahora]
                
                if not fechas_futuras.empty:
                    # Tomamos la fecha más próxima
                    proxima_fecha = fechas_futuras.index[0]
                    fila = fechas_futuras.iloc[0]
                    
                    eps_est = fila.get('EPS Estimate', None)
                    eps_est_str = f"${eps_est:.2f}" if pd.notnull(eps_est) else "N/A"
                    
                    # Determinar si reporta antes de apertura (PRE) o después del cierre (POST)
                    hora = proxima_fecha.hour
                    if hora < 12:
                        momento = "PRE"
                    elif hora >= 16:
                        momento = "POST"
                    else:
                        momento = "DURANTE"

                    datos.append({
                        "Ticker": ticker,
                        "Fecha": proxima_fecha.strftime('%Y-%m-%d'),
                        "Hora (UTC)": proxima_fecha.strftime('%H:%M'),
                        "Momento": momento,
                        "EPS Estimado": eps_est_str,
                        "Fecha_dt": proxima_fecha
                    })
        except Exception as e:
            continue
            
    df = pd.DataFrame(datos)
    if not df.empty:
        # Ordenar por fecha más cercana
        df = df.sort_values(by="Fecha_dt").drop(columns=["Fecha_dt"])
    return df

# --- INTERFAZ DE STREAMLIT ---

def render_seccion_balances():
    st.header("📅 Calendario de Próximos Balances (Earnings)")
    st.write("Monitoreo de presentación de resultados y estimaciones de EPS para CEDEARs y acciones clave.")

    # Tickers por defecto (principales empresas de alto volumen)
    tickers_defecto = [
        "META", "TSLA", "LRCX", "AAPL", "NVDA", "AMZN", "MSFT", 
        "GOOGL", "AMD", "NFLX", "MELI", "BABA", "PFE", "KO", "DIS"
    ]

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        lista_input = st.text_input(
            "Tickers a monitorear (separados por coma):",
            value=", ".join(tickers_defecto)
        )
    
    # Procesar entrada del usuario
    tickers_usuario = [t.strip().upper() for t in lista_input.split(",") if t.strip()]

    with st.spinner("Cargando calendario de balances desde Yahoo Finance..."):
        df_balances = obtener_calendario_balances(tickers_usuario)

    if df_balances.empty:
        st.warning("No se encontraron fechas de balances próximas para los tickers seleccionados.")
        return

    # --- TARJETAS DESTACADAS (Día Actual / Próximos 2 días) ---
    st.subheader("📌 Destacados Próximos")
    
    # Tomamos los primeros 4 tickers con balance más cercano
    top_destacados = df_balances.head(4)
    cols = st.columns(len(top_destacados))

    for i, (_, row) in enumerate(top_destacados.iterrows()):
        with cols[i]:
            badge_color = "🔴" if row["Momento"] == "POST" else "🟡"
            st.metric(
                label=f"{row['Ticker']} ({row['Momento']})",
                value=f"EPS Est: {row['EPS Estimado']}",
                delta=f"Fecha: {row['Fecha']}"
            )

    st.markdown("---")

    # --- TABLA COMPLETA ---
    st.subheader("📋 Tabla General de Balances")

    # Estilizar la tabla según el horario (PRE / POST)
    def resaltar_momento(val):
        if val == "POST":
            return 'background-color: rgba(138, 43, 226, 0.2); color: #d1c4e9; font-weight: bold;'
        elif val == "PRE":
            return 'background-color: rgba(255, 165, 0, 0.2); color: #ffe0b2; font-weight: bold;'
        return ''

    # Mostrar la tabla formateada
    st.dataframe(
        df_balances.style.applymap(resaltar_momento, subset=["Momento"]),
        use_container_width=True,
        hide_index=True
    )

# Para probarlo de forma independiente:
if __name__ == "__main__":
    st.set_page_config(page_title="Dashboard de Balances", layout="wide")
    render_seccion_balances()
    
