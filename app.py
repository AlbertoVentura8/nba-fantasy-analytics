# -*- coding: utf-8 -*-
"""
NBA Fantasy Analytics Pro — Dashboard L3 & Intelligence Hub
Plataforma analítica con métricas avanzadas, palmarés oficial, asistente NL y proyección histórica.
"""

import os
import re
from typing import List, Dict, Tuple, Any
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from nba_api.stats.endpoints import playerawards, playergamelog

# ==========================================
# 1. CONFIGURACIÓN CENTRALIZADA Y ESTILOS UI
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
    "OFF_RTG": st.column_config.NumberColumn("Off Rating", help="Estimación de Rating Ofensivo ajustado por Z-Scores de ataque", format="%.1f"),
    "DEF_RTG": st.column_config.NumberColumn("Def Rating", help="Estimación de Rating Defensivo ajustado por rebotes, robos y tapones", format="%.1f"),
    "NET_RTG": st.column_config.NumberColumn("Net Rating", help="Diferencial Neto (Offensive Rating - Defensive Rating)", format="%.1f"),
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
    
    /* Resaltado dinámico para Tarjetas KPI (Hover Animation) */
    div[data-testid="stMetric"] { 
        background: rgba(30, 41, 59, 0.5) !important; 
        border: 1px solid rgba(255, 255, 255, 0.08) !important; 
        backdrop-filter: blur(12px) !important; 
        border-radius: 14px !important; 
        padding: 12px 16px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px) scale(1.02) !important;
        border-color: #38BDF8 !important;
        box-shadow: 0 12px 25px -5px rgba(56, 189, 248, 0.3) !important;
        background: rgba(30, 41, 59, 0.8) !important;
    }
    
    .player-hero-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    
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

    button[data-baseweb="tab"] { font-size: 15px !important; font-weight: 700 !important; color: #64748B !important; }
    button[aria-selected="true"] { color: #38BDF8 !important; background: rgba(56, 189, 248, 0.08) !important; border-bottom: 3px solid #38BDF8 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNCIONES CACHEADAS Y MOTOR ANALÍTICO
# ==========================================

def calcular_metricas_avanzadas(df_input: pd.DataFrame, punts_sel: List[str]) -> pd.DataFrame:
    """Calcula métricas avanzadas y Z_CUSTOM sobre cualquier DataFrame."""
    df = df_input.copy()
    cols_z_activas = [f"Z_{cat}" for cat in CATEGORIAS if cat not in punts_sel]
    
    df['Z_CUSTOM'] = df[cols_z_activas].sum(axis=1) if cols_z_activas else 0.0
    df['TS_PCT'] = (df['PTS'] / (2 * (df['FGA'] + 0.44 * df['FTA']).replace(0, np.nan))).fillna(0)
    df['AST_TOV'] = (df['AST'] / df['TOV'].replace(0, np.nan)).fillna(df['AST'])
    df['STOCKS'] = df['STL'] + df['BLK']
    df['USG_EST'] = ((df['FGA'] + 0.44 * df['FTA'] + df['TOV']) / df['MIN'].replace(0, np.nan) * 100).fillna(0)
    
    # Rating Ofensivo, Defensivo y Neto
    df['OFF_RTG'] = (108 + (df['Z_PTS'] + df['Z_AST'] + df['Z_FG3M'] + df['Z_FG_PCT'] + df['Z_FT_PCT']) * 3.2).round(1)
    df['DEF_RTG'] = (112 - (df['Z_REB'] + df['Z_STL'] + df['Z_BLK'] - df['Z_TOV']) * 2.8).round(1)
    df['NET_RTG'] = (df['OFF_RTG'] - df['DEF_RTG']).round(1)
    return df

@st.cache_data(ttl=86400)
def obtener_premios_oficiales_nba(player_id: int) -> List[str]:
    try:
        awards_df = playerawards.PlayerAwards(player_id=player_id).get_data_frames()[0]
        if awards_df.empty:
            return []
        conteo = awards_df['DESCRIPTION'].value_counts()
        premios_formateados = []
        for premio, cantidad in conteo.items():
            if "Player of the Week" in premio or "Player of the Month" in premio:
                continue
            premios_formateados.append(f"🏆 {premio} ({cantidad}x)" if cantidad > 1 else f"🏆 {premio}")
        return premios_formateados[:8]
    except Exception:
        return []

@st.cache_data(ttl=43200)
def obtener_gamelog_jugador(player_id: int, temporada_nba: str) -> pd.DataFrame:
    try:
        season_fmt = temporada_nba.replace("_", "-")
        df_gl = playergamelog.PlayerGameLog(player_id=player_id, season=season_fmt).get_data_frames()[0]
        return df_gl
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def cargar_dataset_l2(ruta_archivo: str) -> pd.DataFrame:
    return pd.read_csv(ruta_archivo)

@st.cache_data
def obtener_historico_jugador(nombre_jugador: str, carpeta_l2: str, punts_sel: List[str]) -> pd.DataFrame:
    archivos = [f for f in os.listdir(carpeta_l2) if f.startswith("L2_") and f.endswith(".csv")]
    registros = []
    for archivo in archivos:
        temp_nombre = archivo.replace("L2_", "").replace(".csv", "").replace("_", "-")
        df_temp = pd.read_csv(os.path.join(carpeta_l2, archivo))
        j_row = df_temp[df_temp['PLAYER_NAME'] == nombre_jugador]
        if not j_row.empty:
            row_dict = j_row.iloc[0].to_dict()
            row_dict['TEMPORADA'] = temp_nombre
            registros.append(row_dict)
    if not registros:
        return pd.DataFrame()
    
    df_hist = pd.DataFrame(registros).sort_values(by='TEMPORADA', ascending=True).reset_index(drop=True)
    return calcular_metricas_avanzadas(df_hist, punts_sel)

@st.cache_data
def procesar_ranking_fantasy(df_raw: pd.DataFrame, punts_sel: List[str], filtro_busqueda: str) -> pd.DataFrame:
    df_proc = calcular_metricas_avanzadas(df_raw, punts_sel)
    df_ranking = df_proc.sort_values(by='Z_CUSTOM', ascending=False).reset_index(drop=True)
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

def parsear_consulta_natural(texto_consulta: str) -> str:
    """Parsea frases coloquiales en español a expresiones de Pandas (.query)."""
    text = texto_consulta.lower()
    
    relleno = [
        r'\bdime\b', r'\bmu[eé]strame\b', r'\bbusco\b', r'\bquiero\s+ver\b',
        r'\bjugadores\b', r'\bcon\b', r'\bque\s+tengan\b', r'\bque\s+promedien\b',
        r'\bpor\s+partido\b', r'\bde\s+media\b', r'\ben\s+promedio\b', r'\bjugados\b',
        r'\bal\s+menos\b', r'\bcomo\s+m[ií]nimo\b'
    ]
    for r in relleno:
        text = re.sub(r, ' ', text)
        
    metricas_map = [
        (r'\b(partidos|pj|juegos|encuentros)\b', 'GP'),
        (r'\b(minutos|min|mins|tiempo)\b', 'MIN'),
        (r'\b(puntos|pts|anotaci[oó]n)\b', 'PTS'),
        (r'\b(rebotes|reb|capturas)\b', 'REB'),
        (r'\b(asistencias|ast|pases)\b', 'AST'),
        (r'\b(robos|stl|recuperaciones)\b', 'STL'),
        (r'\b(tapones|bloqueos|blk)\b', 'BLK'),
        (r'\b(triples|3pm)\b', 'FG3M'),
        (r'\b(p[eé]rdidas|tov|turnovers)\b', 'TOV'),
        (r'\b(net rating|net_rtg)\b', 'NET_RTG'),
        (r'\b(off rating|off_rtg)\b', 'OFF_RTG'),
        (r'\b(def rating|def_rtg)\b', 'DEF_RTG'),
        (r'\b(z-custom|z_custom)\b', 'Z_CUSTOM')
    ]
    for pat, col in metricas_map:
        text = re.sub(pat, col, text)

    operadores_map = [
        (r'm[áa]s de|mayor(?:es)? a|superior(?:es)? a|> =|>=', '>='),
        (r'm[eé]nos de|menor(?:es)? a|inferior(?:es)? a|< =|<=', '<='),
        (r'igual a|==', '==')
    ]
    for pat, op in operadores_map:
        text = re.sub(pat, op, text)

    text = re.sub(r'\b(y|además|ademas)\b', ',', text)
    partes = [p.strip() for p in text.split(',') if p.strip()]
    
    condiciones = []
    cols_validas = ['GP', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'TOV', 'NET_RTG', 'OFF_RTG', 'DEF_RTG', 'Z_CUSTOM']
    
    for parte in partes:
        col_encontrada = None
        for c in cols_validas:
            if re.search(r'\b' + c + r'\b', parte):
                col_encontrada = c
                break
                
        if col_encontrada:
            op_encontrado = None
            for op in ['>=', '<=', '==', '>', '<']:
                if op in parte:
                    op_encontrado = op
                    break
            
            nums = re.findall(r'\d+(?:\.\d+)?', parte)
            if nums:
                num = nums[0]
                if not op_encontrado:
                    op_encontrado = '>='
                condiciones.append(f"{col_encontrada} {op_encontrado} {num}")

    return " and ".join(condiciones) if condiciones else texto_consulta.strip()

# ==========================================
# 3. INTERFAZ Y NAVEGACIÓN (STREAMLIT)
# ==========================================

col_h1, col_h2 = st.columns([0.82, 0.18])
with col_h1:
    st.markdown('<p class="main-title">NBA Fantasy Analytics Pro</p>', unsafe_allow_html=True)
    st.caption("Plataforma analítica con inteligencia artificial, ratings avanzados y palmarés oficial.")

with col_h2:
    with st.popover("ℹ️ Glosario Táctico"):
        st.markdown("""
        * **Off Rating:** Estimación de eficiencia anotadora y creación por 100 posesiones.
        * **Def Rating:** Estimación de impacto defensivo (menos es mejor).
        * **Net Rating:** Diferencial Neto de impacto en pista.
        """)

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
    'Z_CUSTOM', 'Z_TOTAL', 'OFF_RTG', 'DEF_RTG', 'NET_RTG', 'TS_PCT', 'AST_TOV', 'STOCKS', 'USG_EST',
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FGA', 'FT_PCT', 'FTA', 'TOV'
]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Leaderboard & Exportación", 
    "👤 Ficha de Jugador & Game Log", 
    "⚔️ Comparador Táctico Multi-Jugador", 
    "🎯 Matriz Scatter Plot Táctica",
    "🤖 Asistente & Query Builder"
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

# TAB 2: FICHA DE JUGADOR & HISTÓRICO CON ÁREA SUAVE
with tab2:
    st.subheader("Ficha de Rendimiento, Game Log y Asistente")
    if df_ranking.empty:
        st.warning("No hay jugadores que coincidan con el filtro.")
    else:
        col_sel, _ = st.columns([0.4, 0.6])
        with col_sel:
            jugador_sel = st.selectbox("Selecciona un jugador:", df_ranking['PLAYER_NAME'].tolist())
        
        p_data = df_ranking[df_ranking['PLAYER_NAME'] == jugador_sel].iloc[0]
        player_id = int(p_data['PLAYER_ID'])
        img_url = f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png"

        premios_oficiales = obtener_premios_oficiales_nba(player_id)
        insignias_fan = calcular_insignias_fantasy(p_data)

        html_oficiales = "".join([f'<span class="badge-chip badge-chip-official">{p}</span>' for p in premios_oficiales])
        html_fantasy = "".join([f'<span class="{b["clase"]}">{b["texto"]}</span>' for b in insignias_fan])

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
        m1.metric("Off Rating", f"{p_data['OFF_RTG']:.1f}")
        m2.metric("Def Rating", f"{p_data['DEF_RTG']:.1f}")
        m3.metric("Net Rating", f"{p_data['NET_RTG']:.1f}")
        m4.metric("True Shooting %", f"{p_data['TS_PCT']*100:.1f}%")
        m5.metric("Z-Custom", f"{p_data['Z_CUSTOM']:.2f}")

        st.divider()

        p_tab1, p_tab2, p_tab3 = st.tabs(["📈 Histórico Multitemporada (Área)", "🔍 Asistente de Partidos & Game Log", "🎯 Radar & Z-Scores"])

        with p_tab1:
            st.markdown("### Trayectoria Histórica Suave (Gráfica de Área)")
            df_hist = obtener_historico_jugador(jugador_sel, CARPETA_L2, punts_sel)
            
            if df_hist.empty:
                st.info("No hay datos históricos suficientes.")
            else:
                stats_opciones = ['Z_CUSTOM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'OFF_RTG', 'DEF_RTG', 'NET_RTG', 'TS_PCT']
                stats_sel_hist = st.multiselect("Selecciona métricas para el gráfico de Área:", options=stats_opciones, default=['PTS', 'Z_CUSTOM'])

                fig_area = go.Figure()
                for idx, st_name in enumerate(stats_sel_hist):
                    if st_name in df_hist.columns:
                        fig_area.add_trace(go.Scatter(
                            x=df_hist['TEMPORADA'], 
                            y=df_hist[st_name], 
                            mode='lines+markers', 
                            name=st_name,
                            line_shape='spline',
                            fill='tozeroy',
                            line=dict(color=PALETA_COLORES[idx % len(PALETA_COLORES)], width=3),
                            opacity=0.4
                        ))

                fig_area.update_layout(
                    template="plotly_dark", height=420,
                    title=f"Evolución Suave Monótona: {jugador_sel}",
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0F172A',
                    xaxis=dict(gridcolor='#334155'), yaxis=dict(gridcolor='#334155')
                )
                st.plotly_chart(fig_area, use_container_width=True)

                st.markdown("---")
                st.markdown("### 📋 Filtro Interactivo de Temporada Histórica")
                temp_hist_choice = st.selectbox("Selecciona una temporada para consultar el desglose completo:", df_hist['TEMPORADA'].tolist())
                row_temp = df_hist[df_hist['TEMPORADA'] == temp_hist_choice].copy()
                cols_show_hist = [c for c in COLS_FULL if c in row_temp.columns]
                st.dataframe(row_temp[cols_show_hist], use_container_width=True, hide_index=True, column_config=COLUMN_CONFIG)

        with p_tab2:
            st.markdown("### 🔍 Asistente de Consulta de Partidos (Game Log)")
            st.caption("Filtra las actuaciones individuales según minutos, puntos o rivales enfrentados.")

            df_gl = obtener_gamelog_jugador(player_id, temporada_sel)

            if df_gl.empty:
                st.warning("⚠️ No se pudieron obtener los datos de partidos en vivo desde la API de la NBA.")
            else:
                c1_f, c2_f, c3_f, c4_f = st.columns(4)
                with c1_f:
                    min_filtro = st.number_input("Minutos Mínimos (MIN >):", min_value=0, max_value=48, value=20)
                with c2_f:
                    pts_filtro = st.number_input("Puntos Mínimos (PTS >=):", min_value=0, max_value=70, value=20)
                with c3_f:
                    reb_filtro = st.number_input("Rebotes Mínimos (REB >=):", min_value=0, max_value=30, value=0)
                with c4_f:
                    ast_filtro = st.number_input("Asistencias Mínimas (AST >=):", min_value=0, max_value=25, value=0)

                mask_gl = (
                    (df_gl['MIN'] >= min_filtro) &
                    (df_gl['PTS'] >= pts_filtro) &
                    (df_gl['REB'] >= reb_filtro) &
                    (df_gl['AST'] >= ast_filtro)
                )
                df_gl_filtrado = df_gl[mask_gl].copy()
                pct_cumplimiento = (len(df_gl_filtrado) / len(df_gl) * 100) if len(df_gl) > 0 else 0

                st.success(f"🎯 **{len(df_gl_filtrado)} de {len(df_gl)} partidos** ({pct_cumplimiento:.1f}% del total) cumplen la condición especificada.")

                cols_gl_vista = ['GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FT_PCT', 'TOV']
                st.dataframe(
                    df_gl_filtrado[cols_gl_vista], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "GAME_DATE": "Fecha",
                        "MATCHUP": "Partido / Rival",
                        "WL": "Rer.",
                        "FG_PCT": st.column_config.NumberColumn("FG%", format="%.3f"),
                        "FT_PCT": st.column_config.NumberColumn("FT%", format="%.3f"),
                    }
                )

        with p_tab3:
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

# TAB 3: COMPARADOR MULTI-JUGADOR CON MODOS DE HISTÓRICO
with tab3:
    st.subheader("Comparador Táctico Multi-Jugador")
    default_players = df_ranking['PLAYER_NAME'].head(3).tolist() if len(df_ranking) >= 3 else df_ranking['PLAYER_NAME'].tolist()
    jugadores_sel = st.multiselect("Selecciona entre 2 y 5 jugadores a comparar:", options=df_ranking['PLAYER_NAME'].tolist(), default=default_players, max_selections=5)

    if len(jugadores_sel) < 2:
        st.warning("⚠️ Selecciona al menos 2 jugadores para comparar.")
    else:
        comp_mode = st.radio("Modo de Comparación:", options=["Radar Temporada Actual", "📈 Evolución Multitemporada por Métrica"], horizontal=True)

        if comp_mode == "Radar Temporada Actual":
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

        else:
            metric_comp_choice = st.selectbox("Métrica a comparar a lo largo de las temporadas:", options=['Z_CUSTOM', 'PTS', 'REB', 'AST', 'OFF_RTG', 'DEF_RTG', 'NET_RTG', 'TS_PCT'])
            
            fig_hist_multi = go.Figure()
            for idx, nombre in enumerate(jugadores_sel):
                df_h = obtener_historico_jugador(nombre, CARPETA_L2, punts_sel)
                if not df_h.empty and metric_comp_choice in df_h.columns:
                    fig_hist_multi.add_trace(go.Scatter(
                        x=df_h['TEMPORADA'],
                        y=df_h[metric_comp_choice],
                        mode='lines+markers',
                        name=nombre,
                        line_shape='spline',
                        line=dict(color=PALETA_COLORES[idx % len(PALETA_COLORES)], width=3)
                    ))

            fig_hist_multi.update_layout(
                template="plotly_dark", height=450,
                title=f"Evolución Histórica Comparativa: {metric_comp_choice}",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0F172A',
                xaxis=dict(gridcolor='#334155'), yaxis=dict(gridcolor='#334155')
            )
            st.plotly_chart(fig_hist_multi, use_container_width=True)

        cols_comp = list(dict.fromkeys(COLS_FULL + [f"Z_{cat}" for cat in CATEGORIAS]))
        df_comp_table = df_ranking[df_ranking['PLAYER_NAME'].isin(jugadores_sel)][cols_comp].copy()
        df_comp_table[df_comp_table.select_dtypes(include=['float64']).columns] = df_comp_table.select_dtypes(include=['float64']).round(2)
        st.dataframe(df_comp_table, use_container_width=True, hide_index=True, column_config=COLUMN_CONFIG)

# TAB 4: SCATTER PLOT
with tab4:
    st.subheader("🎯 Matriz de Cuadrantes Tácticos y Oportunidades")
    col_eje_x, col_eje_y, col_top = st.columns(3)
    opciones_metricas = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'STOCKS', 'TS_PCT', 'OFF_RTG', 'DEF_RTG', 'NET_RTG', 'Z_CUSTOM', 'Z_TOTAL']
    
    with col_eje_x:
        eje_x = st.selectbox("Eje X (Horizontal):", opciones_metricas, index=0)
    with col_eje_y:
        eje_y = st.selectbox("Eje Y (Vertical):", opciones_metricas, index=11)
    with col_top:
        num_fotos = st.slider("Jugadores en gráfico:", min_value=10, max_value=60, value=30)

    df_scatter = df_ranking.head(num_fotos).copy()
    fig_scatter = px.scatter(df_scatter, x=eje_x, y=eje_y, hover_name='PLAYER_NAME', hover_data=['TEAM_ABBREVIATION', 'RANK', 'PTS', 'TS_PCT', 'NET_RTG'], title=f"Matriz Táctica: {eje_y} vs {eje_x}")
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

# TAB 5: ASISTENTE NL Y QUERY BUILDER GLOBAL
with tab5:
    st.subheader("🤖 Asistente Analítico & Buscador de Condicionales Global")
    st.caption(f"Consulta toda la base de datos de la temporada {temporada_sel.replace('_', '-')} introduciendo condiciones estadísticas.")

    st.markdown("**💡 Consultas Rápidas (Atajos):**")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    
    preset_query = ""
    if q_col1.button("🔥 >20 PTS, >15 MIN, >10 PJ"):
        preset_query = "GP >= 10 and MIN >= 15 and PTS >= 20"
    if q_col2.button("🎯 Anotadores Eficientes (>20 PTS, >55% FG%)"):
        preset_query = "PTS >= 20 and FG_PCT >= 0.55"
    if q_col3.button("🛡️ Especialistas Defensivos (>1.5 STL, >1.5 BLK)"):
        preset_query = "STL >= 1.5 and BLK >= 1.5"
    if q_col4.button("👑 Playmakers Elite (>8 AST, <2.5 TOV)"):
        preset_query = "AST >= 8.0 and TOV <= 2.5"

    st.markdown("---")

    input_usuario = st.text_input(
        "💬 Escribe tu consulta en lenguaje natural o sintaxis condicional:",
        value=preset_query if preset_query else "partidos > 10 y minutos > 15 y puntos > 20",
        help="Ejemplo: 'dime jugadores con mas de 10 partidos, 15 minutos y 20 puntos'"
    )

    if input_usuario:
        sintaxis_query = parsear_consulta_natural(input_usuario)
        st.code(f"Sintaxis Pandas generada: df.query('{sintaxis_query}')", language="python")

        try:
            df_asistente = calcular_metricas_avanzadas(df_raw, punts_sel)
            df_filtrado_ast = df_asistente.query(sintaxis_query).sort_values(by='Z_CUSTOM', ascending=False).reset_index(drop=True)
            df_filtrado_ast['RANK'] = df_filtrado_ast.index + 1

            n_res = len(df_filtrado_ast)
            pct_res = (n_res / len(df_asistente) * 100) if len(df_asistente) > 0 else 0

            res1, res2, res3 = st.columns(3)
            res1.metric("Jugadores Encontrados", f"{n_res} de {len(df_asistente)}")
            res2.metric("% de la Liga", f"{pct_res:.1f}%")
            res3.metric("Mejor Valor Z-Custom", f"{df_filtrado_ast.iloc[0]['Z_CUSTOM']:.2f}" if n_res > 0 else "0.0")

            if n_res == 0:
                st.warning("No se encontraron jugadores que cumplan todas las condiciones requeridas.")
            else:
                st.dataframe(
                    df_filtrado_ast[COLS_FULL], 
                    use_container_width=True, 
                    hide_index=True, 
                    column_config=COLUMN_CONFIG
                )

                st.markdown("---")
                st.markdown("### 📊 Gráficas e Inspección Express del Resultado")
                col_vis1, col_vis2 = st.columns([0.55, 0.45])
                
                with col_vis1:
                    st.markdown("#### 🎯 Comparativa de Búsqueda")
                    eje_ast_y = st.selectbox(
                        "Métrica a comparar en el gráfico:", 
                        options=['Z_CUSTOM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'TS_PCT', 'NET_RTG'], 
                        key="ast_y_axis"
                    )
                    
                    fig_ast_bar = px.bar(
                        df_filtrado_ast.head(15),
                        x='PLAYER_NAME',
                        y=eje_ast_y,
                        color='Z_CUSTOM',
                        color_continuous_scale='Viridis',
                        title=f"Top Jugadores Filtrados por {eje_ast_y}",
                        hover_data=['TEAM_ABBREVIATION', 'PTS', 'REB', 'AST']
                    )
                    fig_ast_bar.update_layout(
                        template="plotly_dark", height=380,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0F172A',
                        xaxis_title="", xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_ast_bar, use_container_width=True)

                with col_vis2:
                    st.markdown("#### 👤 Ficha Express de Jugador")
                    jugador_ast_sel = st.selectbox(
                        "Selecciona un jugador para ver su perfil al instante:",
                        options=df_filtrado_ast['PLAYER_NAME'].tolist(),
                        key="ast_player_select"
                    )
                    
                    p_ast_data = df_filtrado_ast[df_filtrado_ast['PLAYER_NAME'] == jugador_ast_sel].iloc[0]
                    p_ast_id = int(p_ast_data['PLAYER_ID'])
                    img_ast_url = f"https://cdn.nba.com/headshots/nba/latest/260x190/{p_ast_id}.png"
                    
                    c_img_ast, c_info_ast = st.columns([0.35, 0.65])
                    with c_img_ast:
                        st.image(img_ast_url, caption=p_ast_data['PLAYER_NAME'], width=120)
                    with c_info_ast:
                        st.markdown(f"**Rank:** #{p_ast_data['RANK']} | **Equipo:** {p_ast_data['TEAM_ABBREVIATION']}")
                        st.markdown(f"**PTS:** {p_ast_data['PTS']:.1f} | **REB:** {p_ast_data['REB']:.1f} | **AST:** {p_ast_data['AST']:.1f}")
                        st.markdown(f"**Z-Custom:** `{p_ast_data['Z_CUSTOM']:.2f}` | **TS%:** `{p_ast_data['TS_PCT']*100:.1f}%`")
                    
                    z_ast_vals = [p_ast_data[f"Z_{cat}"] for cat in CATEGORIAS]
                    fig_mini_radar = go.Figure()
                    fig_mini_radar.add_trace(go.Scatterpolar(
                        r=z_ast_vals + [z_ast_vals[0]], theta=CATEGORIAS + [CATEGORIAS[0]],
                        fill='toself', name=jugador_ast_sel,
                        line_color='#38BDF8', fillcolor='rgba(56, 189, 248, 0.25)'
                    ))
                    fig_mini_radar.update_layout(
                        template="plotly_dark",
                        polar=dict(bgcolor='#0F172A', radialaxis=dict(visible=True, range=[-3, 4], gridcolor='#334155')),
                        height=260, margin=dict(l=20, r=20, t=20, b=20),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_mini_radar, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Error al interpretar la consulta condicional. Por favor revisa la sintaxis. Detalle: {e}")