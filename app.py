# -*- coding: utf-8 -*-
"""
NBA Fantasy Analytics Pro — Dashboard L3 & Player Hub
Interfaz visual de alta fidelidad con palmarés oficial NBA, histórico multitemporada e insignias fantasy.
"""

import os
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from nba_api.stats.endpoints import playerawards

# ==========================================
# 1. CONFIGURACIÓN CENTRALIZADA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="NBA Fantasy Analytics Pro", 
    layout="wide", 
    page_icon="🏀"
)

CARPETA_L2: str = "L2_fantasy"
CATEGORIAS: List[str] = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FT_PCT', 'TOV']
PALETA_COLORES: List[str] = ['#38BDF8', '#EF4444', '#10B981', '#F59E0B', '#A855F7']

COLUMN_CONFIG = {
    "RANK": st.column_config.NumberColumn("Rank", help="Posición en el ranking según Z_CUSTOM", format="%d"),
    "PLAYER_NAME": st.column_config.TextColumn("Jugador", help="Nombre del jugador NBA"),
    "TEAM_ABBREVIATION": st.column_config.TextColumn("Equipo", help="Abreviatura del equipo NBA"),
    "GP": st.column_config.NumberColumn("PJ", help="Partidos Jugados (Games Played)", format="%d"),
    "MIN": st.column_config.NumberColumn("MIN", help="Minutos promedio por partido", format="%.1f"),
    "Z_CUSTOM": st.column_config.NumberColumn("Z-Custom", help="Valor analítico recalculado aplicando la estrategia Punt", format="%.2f"),
    "Z_TOTAL": st.column_config.NumberColumn("Z-Total", help="Valor base total considerando las 9 categorías", format="%.2f"),
    "NET_IMPACT": st.column_config.NumberColumn("Net Impact", help="Impacto Neto de Eficiencia y Volumen Fantasy", format="%.2f"),
    "TS_PCT": st.column_config.NumberColumn("TS%", help="True Shooting % (Eficiencia de tiro considerando 2P, 3P y TL)", format="%.3f"),
    "AST_TOV": st.column_config.NumberColumn("AST/TO", help="Ratio de Asistencias por Pérdida de balón", format="%.2f"),
    "STOCKS": st.column_config.NumberColumn("STOCKS", help="Robos (STL) + Tapones (BLK)", format="%.1f"),
    "USG_EST": st.column_config.NumberColumn("USG%", help="Estimación de Porcentaje de Uso Ofensivo", format="%.1f%%"),
    "PTS": st.column_config.NumberColumn("PTS", help="Puntos promedio por partido", format="%.1f"),
    "REB": st.column_config.NumberColumn("REB", help="Rebotes totales promedio por partido", format="%.1f"),
    "AST": st.column_config.NumberColumn("AST", help="Asistencias promedio por partido", format="%.1f"),
    "STL": st.column_config.NumberColumn("STL", help="Robos de balón promedio por partido", format="%.1f"),
    "BLK": st.column_config.NumberColumn("BLK", help="Tapones promedio por partido", format="%.1f"),
    "FG3M": st.column_config.NumberColumn("3PM", help="Triples anotados promedio por partido", format="%.1f"),
    "FG_PCT": st.column_config.NumberColumn("FG%", help="Porcentaje de tiro de campo", format="%.3f"),
    "FT_PCT": st.column_config.NumberColumn("FT%", help="Porcentaje de tiros libres", format="%.3f"),
    "TOV": st.column_config.NumberColumn("TOV", help="Pérdidas de balón por partido", format="%.1f"),
}

for cat in CATEGORIAS:
    COLUMN_CONFIG[f"Z_{cat}"] = st.column_config.NumberColumn(
        f"Z_{cat}", help=f"Desviación estándar Z-Score en {cat}", format="%.2f"
    )

# Inyección CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    .stApp { 
        background: radial-gradient(circle at 10% 10%, #0F172A 0%, #070A12 100%); 
        color: #F8FAFC; 
        font-family: 'Inter', sans-serif;
    }
    .main-title { 
        font-size: 2.4rem !important; 
        font-weight: 800 !important; 
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        margin-bottom: 0px !important;
    }
    
    /* Player Hero Card UI */
    .player-hero-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    
    /* Chips y Badges */
    .badge-chip {
        display: inline-block;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38BDF8;
        padding: 5px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-chip-gold {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.5);
        color: #FBBF24;
    }
    .badge-chip-green {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.5);
        color: #34D399;
    }
    .badge-chip-official {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.2) 0%, rgba(180, 83, 9, 0.3) 100%);
        border: 1px solid #F59E0B;
        color: #FCD34D;
        font-weight: 700;
    }

    div[data-testid="stMetric"] { 
        background: rgba(30, 41, 59, 0.5) !important; 
        border: 1px solid rgba(255, 255, 255, 0.08) !important; 
        backdrop-filter: blur(12px) !important; 
        border-radius: 14px !important; 
        padding: 12px 16px !important;
    }
    button[data-baseweb="tab"] { font-size: 15px !important; font-weight: 700 !important; color: #64748B !important; }
    button[aria-selected="true"] { color: #38BDF8 !important; background: rgba(56, 189, 248, 0.08) !important; border-bottom: 3px solid #38BDF8 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNCIONES CACHEADAS Y CONSULTA DE PREMIOS
# ==========================================

@st.cache_data(ttl=86400)
def obtener_premios_oficiales_nba(player_id: int) -> List[str]:
    """Consulta los premios reales del jugador directamente en la API de la NBA."""
    try:
        awards_df = playerawards.PlayerAwards(player_id=player_id).get_data_frames()[0]
        if awards_df.empty:
            return []
        
        # Filtrar y agrupar galardones relevantes
        conteo = awards_df['DESCRIPTION'].value_counts()
        premios_formateados = []
        
        for premio, cantidad in conteo.items():
            # Excluir menciones menores semanales/mensuales si se desea mayor foco
            if "Player of the Week" in premio or "Player of the Month" in premio:
                continue
            
            if cantidad > 1:
                premios_formateados.append(f"🏆 {premio} ({cantidad}x)")
            else:
                premios_formateados.append(f"🏆 {premio}")
                
        return premios_formateados[:8] # Mostrar los 8 más destacados
    except Exception:
        return []

@st.cache_data(ttl=3600)
def cargar_dataset_l2(ruta_archivo: str) -> pd.DataFrame:
    return pd.read_csv(ruta_archivo)

@st.cache_data
def obtener_historico_jugador(nombre_jugador: str, carpeta_l2: str) -> pd.DataFrame:
    archivos = [f for f in os.listdir(carpeta_l2) if f.startswith("L2_") and f.endswith(".csv")]
    registros = []
    
    for archivo in archivos:
        temp_nombre = archivo.replace("L2_", "").replace(".csv", "").replace("_", "-")
        ruta = os.path.join(carpeta_l2, archivo)
        df_temp = pd.read_csv(ruta)
        
        j_row = df_temp[df_temp['PLAYER_NAME'] == nombre_jugador]
        if not j_row.empty:
            row_dict = j_row.iloc[0].to_dict()
            row_dict['TEMPORADA'] = temp_nombre
            registros.append(row_dict)
            
    if not registros:
        return pd.DataFrame()
        
    df_hist = pd.DataFrame(registros)
    return df_hist.sort_values(by='TEMPORADA', ascending=True).reset_index(drop=True)

@st.cache_data
def procesar_ranking_fantasy(df_raw: pd.DataFrame, punts_sel: List[str], filtro_busqueda: str) -> pd.DataFrame:
    df = df_raw.copy()
    cols_z_activas = [f"Z_{cat}" for cat in CATEGORIAS if cat not in punts_sel]
    
    df['Z_CUSTOM'] = df[cols_z_activas].sum(axis=1) if cols_z_activas else 0.0
    df['TS_PCT'] = (df['PTS'] / (2 * (df['FGA'] + 0.44 * df['FTA']).replace(0, np.nan))).fillna(0)
    df['AST_TOV'] = (df['AST'] / df['TOV'].replace(0, np.nan)).fillna(df['AST'])
    df['STOCKS'] = df['STL'] + df['BLK']
    df['USG_EST'] = ((df['FGA'] + 0.44 * df['FTA'] + df['TOV']) / df['MIN'].replace(0, np.nan) * 100).fillna(0)
    df['NET_IMPACT'] = df['Z_CUSTOM'] * (df['TS_PCT'] / 0.55)

    df_ranking = df.sort_values(by='Z_CUSTOM', ascending=False).reset_index(drop=True)
    df_ranking['RANK'] = df_ranking.index + 1

    if filtro_busqueda:
        mask = (
            df_ranking['PLAYER_NAME'].str.contains(filtro_busqueda, case=False, na=False) |
            df_ranking['TEAM_ABBREVIATION'].str.contains(filtro_busqueda, case=False, na=False)
        )
        df_ranking = df_ranking[mask]

    return df_ranking

def calcular_insignias_fantasy(p_data: pd.Series) -> List[Dict[str, str]]:
    badges = []
    if p_data['Z_CUSTOM'] >= 6.0:
        badges.append({"texto": "⚡ MVP Fantasy Candidate", "clase": "badge-chip-gold"})
    elif p_data['Z_CUSTOM'] >= 3.5:
        badges.append({"texto": "⭐ Fantasy All-Star", "clase": "badge-chip"})
        
    if p_data['PTS'] >= 25.0:
        badges.append({"texto": "🔥 25+ PTS/G", "clase": "badge-chip-gold"})
    if p_data['AST'] >= 8.0:
        badges.append({"texto": "🧠 8+ AST/G", "clase": "badge-chip"})
    if p_data['REB'] >= 10.0:
        badges.append({"texto": "🧺 10+ REB/G", "clase": "badge-chip"})
    if p_data['STOCKS'] >= 2.5:
        badges.append({"texto": "🔒 2.5+ STOCKS/G", "clase": "badge-chip-green"})
    if p_data['FG3M'] >= 3.0:
        badges.append({"texto": "🎯 3+ 3PM/G", "clase": "badge-chip"})
    if p_data['TS_PCT'] >= 0.62:
        badges.append({"texto": "⚡ 62%+ TS", "clase": "badge-chip-gold"})
        
    return badges

# ==========================================
# 3. INTERFAZ Y NAVEGACIÓN
# ==========================================

col_h1, col_h2 = st.columns([0.82, 0.18])
with col_h1:
    st.markdown('<p class="main-title">NBA Fantasy Analytics Pro</p>', unsafe_allow_html=True)
    st.caption("Centro de inteligencia con premios oficiales NBA, métricas avanzadas e histórico multitemporada.")

with col_h2:
    with st.popover("ℹ️ Glosario Táctico"):
        st.markdown("""
        * **TS%:** True Shooting Percentage (Eficiencia global de tiro).
        * **STOCKS:** Robos totales + Tapones totales por partido.
        * **NET_IMPACT:** Valor Z-Custom ajustado por eficiencia True Shooting.
        """)

# Verificación de datos
archivos_l2 = [f for f in os.listdir(CARPETA_L2) if f.startswith("L2_") and f.endswith(".csv")] if os.path.exists(CARPETA_L2) else []

if not archivos_l2:
    st.error(f"No se encontraron datasets en '{CARPETA_L2}'. Ejecuta L1 y L2 primero.")
    st.stop()

temporadas = sorted([f.replace("L2_", "").replace(".csv", "") for f in archivos_l2], reverse=True)

# Sidebar
st.sidebar.header("⚙️ Panel de Control")
temporada_sel = st.sidebar.selectbox("Temporada Principal", temporadas, index=0)
punts_sel = st.sidebar.multiselect("Categorías a descartar (PUNT)", options=CATEGORIAS, default=['FT_PCT', 'TOV'])
top_n = st.sidebar.slider("Jugadores a mostrar", min_value=10, max_value=250, value=50)
filtro_busqueda = st.sidebar.text_input("🔍 Buscar Jugador o Equipo:", "")

# Carga de datos
ruta_csv = os.path.join(CARPETA_L2, f"L2_{temporada_sel}.csv")
df_raw = cargar_dataset_l2(ruta_csv)
df_ranking = procesar_ranking_fantasy(df_raw, punts_sel, filtro_busqueda)

COLS_FULL = [
    'RANK', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN',
    'Z_CUSTOM', 'Z_TOTAL', 'NET_IMPACT', 'TS_PCT', 'AST_TOV', 'STOCKS', 'USG_EST',
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FGA', 'FT_PCT', 'FTA', 'TOV'
]

# Pestañas
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Leaderboard & Exportación", 
    "👤 Ficha de Jugador & Palmarés", 
    "⚔️ Comparador Multi-Jugador (2-5)", 
    "🎯 Matriz Scatter Plot Táctica"
])

# TAB 1: LEADERBOARD
with tab1:
    st.subheader(f"Leaderboard General — Temporada {temporada_sel.replace('_', '-')}")
    df_display = df_ranking[COLS_FULL].head(top_n).copy()
    cols_float = df_display.select_dtypes(include=['float64']).columns
    df_display[cols_float] = df_display[cols_float].round(2)

    st.dataframe(df_display, use_container_width=True, hide_index=True, column_config=COLUMN_CONFIG)
    st.download_button(
        label="📥 Descargar Dataset Procesado (CSV)",
        data=df_display.to_csv(index=False, encoding='utf-8-sig'),
        file_name=f"ranking_fantasy_{temporada_sel}.csv",
        mime="text/csv"
    )

# TAB 2: FICHA DE JUGADOR CON PREMIOS OFICIALES Y HISTÓRICO
with tab2:
    st.subheader("Ficha de Rendimiento & Palmarés Oficial")
    if df_ranking.empty:
        st.warning("No hay jugadores que coincidan con el filtro.")
    else:
        col_sel, _ = st.columns([0.4, 0.6])
        with col_sel:
            jugador_sel = st.selectbox("Selecciona un jugador:", df_ranking['PLAYER_NAME'].tolist())
        
        p_data = df_ranking[df_ranking['PLAYER_NAME'] == jugador_sel].iloc[0]
        player_id = int(p_data['PLAYER_ID'])
        img_url = f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png"

        # Consulta de premios reales e insignias fantasy
        premios_oficiales = obtener_premios_oficiales_nba(player_id)
        insignias_fan = calcular_insignias_fantasy(p_data)

        html_oficiales = "".join([f'<span class="badge-chip badge-chip-official">{p}</span>' for p in premios_oficiales])
        html_fantasy = "".join([f'<span class="{b["clase"]}">{b["texto"]}</span>' for b in insignias_fan])

        # HERO CARD
        st.markdown(f"""
        <div class="player-hero-card">
            <div style="display: flex; align-items: center; gap: 24px;">
                <img src="{img_url}" style="width: 130px; border-radius: 12px; background: #0F172A; border: 2px solid #334155;">
                <div style="flex-grow: 1;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="margin:0; font-size: 2rem; color: #F8FAFC;">{p_data['PLAYER_NAME']}</h2>
                        <span style="background: #38BDF8; color: #0F172A; font-weight: 800; padding: 6px 14px; border-radius: 10px; font-size: 16px;">
                            RANK #{p_data['RANK']}
                        </span>
                    </div>
                    <p style="margin: 4px 0 10px 0; color: #94A3B8; font-size: 15px; font-weight: 600;">
                        {p_data['TEAM_ABBREVIATION']} | {p_data['GP']} PJ | {p_data['MIN']:.1f} MIN/G
                    </p>
                    <div style="margin-bottom: 6px;">
                        <span style="font-size: 11px; color: #F59E0B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; display: block; margin-bottom: 4px;">🥇 Palmarés Oficial NBA:</span>
                        {html_oficiales if html_oficiales else '<span class="badge-chip">Sin títulos individuales registrados</span>'}
                    </div>
                    <div style="margin-top: 8px;">
                        <span style="font-size: 11px; color: #38BDF8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; display: block; margin-bottom: 4px;">⚡ Hit Táctico Fantasy:</span>
                        {html_fantasy}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Valor Z-Custom", f"{p_data['Z_CUSTOM']:.2f}")
        m2.metric("True Shooting %", f"{p_data['TS_PCT']*100:.1f}%")
        m3.metric("Puntos/Partido", f"{p_data['PTS']:.1f}")
        m4.metric("Rebotes + Asistencias", f"{p_data['REB'] + p_data['AST']:.1f}")
        m5.metric("STOCKS (STL+BLK)", f"{p_data['STOCKS']:.1f}")

        st.divider()

        p_tab1, p_tab2 = st.tabs(["📈 Histórico Multitemporada", "🎯 Radar & Desglose Z-Scores"])

        with p_tab1:
            st.markdown("### Trayectoria Histórica del Jugador")
            df_hist = obtener_historico_jugador(jugador_sel, CARPETA_L2)
            
            if len(df_hist) < 2:
                st.info("ℹ️ Se requiere más de 1 temporada cargada en la carpeta `L2_fantasy` para renderizar la gráfica evolutiva.")
            else:
                cols_z_activas_hist = [f"Z_{cat}" for cat in CATEGORIAS if cat not in punts_sel]
                df_hist['Z_CUSTOM_HIST'] = df_hist[cols_z_activas_hist].sum(axis=1) if cols_z_activas_hist else df_hist['Z_TOTAL']

                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=df_hist['TEMPORADA'], y=df_hist['PTS'], mode='lines+markers', name='PTS', line=dict(color='#38BDF8', width=3)))
                fig_line.add_trace(go.Scatter(x=df_hist['TEMPORADA'], y=df_hist['REB'], mode='lines+markers', name='REB', line=dict(color='#10B981', width=2)))
                fig_line.add_trace(go.Scatter(x=df_hist['TEMPORADA'], y=df_hist['AST'], mode='lines+markers', name='AST', line=dict(color='#F59E0B', width=2)))
                fig_line.add_trace(go.Scatter(x=df_hist['TEMPORADA'], y=df_hist['Z_CUSTOM_HIST'], mode='lines+markers', name='Z-Custom', line=dict(color='#C084FC', width=4, dash='dash')))

                fig_line.update_layout(
                    template="plotly_dark",
                    height=420,
                    title=f"Evolución de Estadísticas por Temporada: {jugador_sel}",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='#0F172A',
                    xaxis=dict(gridcolor='#334155'),
                    yaxis=dict(gridcolor='#334155')
                )
                st.plotly_chart(fig_line, use_container_width=True)

        with p_tab2:
            c_radar, c_bar = st.columns(2)
            with c_radar:
                z_values = [p_data[f"Z_{cat}"] for cat in CATEGORIAS]
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=z_values + [z_values[0]], theta=CATEGORIAS + [CATEGORIAS[0]],
                    fill='toself', name=jugador_sel, line_color='#38BDF8', fillcolor='rgba(56, 189, 248, 0.25)'
                ))
                fig_radar.update_layout(
                    template="plotly_dark",
                    polar=dict(bgcolor='#0F172A', radialaxis=dict(visible=True, range=[-3, 4], gridcolor='#334155')),
                    title=f"Huella Radar: {jugador_sel}", height=400,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with c_bar:
                z_df = pd.DataFrame({'Categoría': CATEGORIAS, 'Z-Score': z_values})
                z_df['Color'] = z_df['Z-Score'].apply(lambda x: '#10B981' if x >= 0 else '#EF4444')
                fig_bar = px.bar(z_df, x='Categoría', y='Z-Score', color='Color', color_discrete_map='identity', title="Aportación Neta por Categoría (Z-Score)")
                fig_bar.update_layout(template="plotly_dark", height=400, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bar, use_container_width=True)

# TAB 3: COMPARADOR MULTI-JUGADOR
with tab3:
    st.subheader("Comparador Táctico Multi-Jugador")
    default_players = df_ranking['PLAYER_NAME'].head(3).tolist() if len(df_ranking) >= 3 else df_ranking['PLAYER_NAME'].tolist()
    jugadores_sel = st.multiselect("Selecciona entre 2 y 5 jugadores:", options=df_ranking['PLAYER_NAME'].tolist(), default=default_players, max_selections=5)

    if len(jugadores_sel) < 2:
        st.warning("⚠️ Selecciona al menos 2 jugadores para comparar.")
    else:
        fig_comp = go.Figure()
        for idx, nombre in enumerate(jugadores_sel):
            p_info = df_ranking[df_ranking['PLAYER_NAME'] == nombre].iloc[0]
            z_vals = [p_info[f"Z_{cat}"] for cat in CATEGORIAS]

            fig_comp.add_trace(go.Scatterpolar(
                r=z_vals + [z_vals[0]], theta=CATEGORIAS + [CATEGORIAS[0]], fill='toself',
                name=f"#{p_info['RANK']} {nombre}", line_color=PALETA_COLORES[idx % len(PALETA_COLORES)], opacity=0.35
            ))

        fig_comp.update_layout(template="plotly_dark", polar=dict(bgcolor='#0F172A', radialaxis=dict(visible=True, range=[-3, 4], gridcolor='#334155')), title=f"Superposición Radar ({len(jugadores_sel)} Jugadores)", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_comp, use_container_width=True)

        cols_comp = list(dict.fromkeys(COLS_FULL + [f"Z_{cat}" for cat in CATEGORIAS]))
        df_comp_table = df_ranking[df_ranking['PLAYER_NAME'].isin(jugadores_sel)][cols_comp].copy()
        df_comp_table[df_comp_table.select_dtypes(include=['float64']).columns] = df_comp_table.select_dtypes(include=['float64']).round(2)
        st.dataframe(df_comp_table, use_container_width=True, hide_index=True, column_config=COLUMN_CONFIG)

# TAB 4: SCATTER PLOT
with tab4:
    st.subheader("🎯 Matriz de Cuadrantes Tácticos y Oportunidades")
    col_eje_x, col_eje_y, col_top = st.columns(3)
    opciones_metricas = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'STOCKS', 'TS_PCT', 'NET_IMPACT', 'Z_CUSTOM', 'Z_TOTAL']
    
    with col_eje_x:
        eje_x = st.selectbox("Eje X (Horizontal):", opciones_metricas, index=0)
    with col_eje_y:
        eje_y = st.selectbox("Eje Y (Vertical):", opciones_metricas, index=9)
    with col_top:
        num_fotos = st.slider("Jugadores en gráfico:", min_value=10, max_value=60, value=30)

    df_scatter = df_ranking.head(num_fotos).copy()
    fig_scatter = px.scatter(df_scatter, x=eje_x, y=eje_y, hover_name='PLAYER_NAME', hover_data=['TEAM_ABBREVIATION', 'RANK', 'PTS', 'TS_PCT', 'NET_IMPACT'], title=f"Matriz Táctica: {eje_y} vs {eje_x}")
    fig_scatter.update_traces(marker=dict(size=0, opacity=0))

    x_min, x_max = df_scatter[eje_x].min(), df_scatter[eje_x].max()
    y_min, y_max = df_scatter[eje_y].min(), df_scatter[eje_y].max()
    x_range = (x_max - x_min) if (x_max - x_min) != 0 else 1
    y_range = (y_max - y_min) if (y_max - y_min) != 0 else 1

    size_x, size_y = x_range * 0.08, y_range * 0.08

    for _, row in df_scatter.iterrows():
        p_id = int(row['PLAYER_ID'])
        fig_scatter.add_layout_image(dict(
            source=f"https://cdn.nba.com/headshots/nba/latest/260x190/{p_id}.png",
            xref="x", yref="y", x=row[eje_x], y=row[eje_y],
            sizex=size_x, sizey=size_y, xanchor="center", yanchor="middle",
            sizing="contain", opacity=0.92, layer="above"
        ))

    fig_scatter.add_vline(x=df_scatter[eje_x].mean(), line_dash="dash", line_color="#64748B", opacity=0.6)
    fig_scatter.add_hline(y=df_scatter[eje_y].mean(), line_dash="dash", line_color="#64748B", opacity=0.6)

    fig_scatter.add_annotation(x=0.98, y=0.98, xref="paper", yref="paper", text=f"💎 TOP ELITE<br>(+ {eje_y} / + {eje_x})", showarrow=False, align="right", font=dict(size=12, color="#10B981"), bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#10B981", borderwidth=1, borderpad=6)
    fig_scatter.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text=f"🎯 CHOLLOS / EFICIENTES<br>(+ {eje_y} / - {eje_x})", showarrow=False, align="left", font=dict(size=12, color="#38BDF8"), bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#38BDF8", borderwidth=1, borderpad=6)
    fig_scatter.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", text=f"⚠️ VOLUMEN SIN EFICIENCIA<br>(- {eje_y} / + {eje_x})", showarrow=False, align="right", font=dict(size=12, color="#F59E0B"), bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#F59E0B", borderwidth=1, borderpad=6)
    fig_scatter.add_annotation(x=0.02, y=0.02, xref="paper", yref="paper", text=f"📉 ROL SECUNDARIO<br>(- {eje_y} / - {eje_x})", showarrow=False, align="left", font=dict(size=12, color="#EF4444"), bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#EF4444", borderwidth=1, borderpad=6)

    fig_scatter.update_layout(template="plotly_dark", height=700, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0F172A', font=dict(color="#F8FAFC"), coloraxis_showscale=False)
    st.plotly_chart(fig_scatter, use_container_width=True)