import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página con tema oscuro
st.set_page_config(
    page_title="Market & Sector Rotation Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Dashboard de Análisis de Mercado & Rotación Sectorial")

# Definición de pestañas principales
tab1, tab2, tab3 = st.tabs([
    "🌀 Rotación Sectorial", 
    "🎯 Régimen & Top Scores", 
    "🇺🇸 Acciones EE. UU. por Sector"
])

# ==========================================
# PESTAÑA 1: ROTACIÓN SECTORIAL
# ==========================================
with tab1:
    st.header("Cuadro de Rotación de Sectores (RRG)")
    st.caption("Visualización de fuerza relativa y momentum por sectores frente al SPY.")
    
    # Datos de ejemplo para generar el gráfico con estelas/trayectorias
    sectors_data = pd.DataFrame({
        'Sector': ['XLK (Tech)', 'XLE (Energía)', 'XLP (Consumo Def.)', 'XLV (Salud)', 'XLI (Industrial)'],
        'Fuerza_Relativa': [-1.5, 1.8, 1.2, 1.5, -0.8],
        'Momentum': [-1.8, 1.1, 1.9, 1.2, -0.5]
    })
    
    # Crear gráfico de dispersión por cuadrantes
    fig_rrg = px.scatter(
        sectors_data, 
        x='Fuerza_Relativa', 
        y='Momentum', 
        text='Sector',
        color='Sector',
        size_max=20
    )
    
    # Dibujar líneas de los cuadrantes (Ejes X=0, Y=0)
    fig_rrg.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_rrg.add_vline(x=0, line_dash="dash", line_color="gray")
    
    fig_rrg.update_layout(
        template="plotly_dark",
        xaxis_title="Fuerza Relativa (vs SPY)",
        yaxis_title="Momentum de la Fuerza",
        height=600
    )
    fig_rrg.update_traces(textposition='top center', marker=dict(size=14))
    
    st.plotly_chart(fig_rrg, use_container_width=True)

# ==========================================
# PESTAÑA 2: RÉGIMEN DE MERCADO & TOP SCORES
# ==========================================
with tab2:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Régimen de Mercado")
        # Gráfico tipo Velocímetro / Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 46,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Puntaje General (0-100)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#00FF7F"},
                'steps': [
                    {'range': [0, 30], 'color': "#8B0000"},
                    {'range': [30, 70], 'color': "#4682B4"},
                    {'range': [70, 100], 'color': "#006400"}
                ]
            }
        ))
        fig_gauge.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with col2:
        st.subheader("🏆 Top 10 Activos del Score")
        # Tabla estilizada de Top Scores
        top_data = pd.DataFrame({
            'Ticker': ['BP', 'ETSY', 'SHEL', 'XOM', 'CVX', 'PM', 'IFF', 'TRV', 'ABBV', 'USO'],
            'Score': [85, 84, 85, 83, 83, 82, 87, 83, 97, 87],
            'Entró': ['5-Oct', '9-Oct', '5-Oct', '5-Oct', '5-Oct', '6-Oct', '6-Oct', '5-Oct', '5-Oct', '12-Oct'],
            'Retorno': ['+12.53%', '+10.99%', '+10.51%', '+9.13%', '+8.97%', '+8.27%', '+8.02%', '+8.00%', '+7.40%', '+7.08%']
        })
        st.dataframe(top_data, use_container_width=True)

# ==========================================
# PESTAÑA 3: ACCIONES EE. UU. POR SECTOR
# ==========================================
with tab3:
    st.header("🇺🇸 Cotizaciones de Acciones de EE. UU. por Sector")
    
    # Diccionario de sectores y sus tickers principales
    sectores = {
        "Tecnología 💻": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"],
        "Energía ⚡": ["XOM", "CVX", "COP", "SLB", "BP"],
        "Salud 🏥": ["JNJ", "PFE", "UNH", "ABBV", "LLY"],
        "Financiero 🏦": ["JPM", "BAC", "WFC", "C", "MS"],
        "Consumo Discrecional 🛒": ["TSLA", "NKE", "MCD", "HD", "SBUX"]
    }
    
    # Generar paneles interactivos expandibles por sector
    for sector_nombre, tickers in sectores.items():
        with st.expander(f"📁 **{sector_nombre}**", expanded=True):
            # Descargar datos en tiempo real con yfinance
            datos_sector = yf.download(tickers, period="2d")['Close']
            
            if not datos_sector.empty and len(datos_sector) >= 2:
                filas = []
                for ticker in tickers:
                    precio_actual = datos_sector[ticker].iloc[-1]
                    precio_anterior = datos_sector[ticker].iloc[-2]
                    variacion = ((precio_actual - precio_anterior) / precio_anterior) * 100
                    
                    filas.append({
                        "Ticker": ticker,
                        "Precio ($)": f"${precio_actual:.2f}",
                        "Variación (%)": f"{variacion:+.2f}%",
                        "Estado": "🟢 Subida" if variacion >= 0 else "🔴 Baja"
                    })
                
                df_mostrar = pd.DataFrame(filas)
                st.dataframe(df_mostrar, use_container_width=True)
            else:
                st.warning(f"Cargando datos para {sector_nombre}...")
