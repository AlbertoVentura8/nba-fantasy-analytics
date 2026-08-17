# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. Configuración de página
st.set_page_config(
    page_title="NBA Fantasy Analytics Pro", 
    layout="wide", 
    page_icon="🏀"
)

# 2. Inyección CSS estilo Cyber-NBA Dark
st.markdown("""
<style>
    /* Estructura Base */
    .stApp {
        background: radial-gradient(circle at top left, #0F172A 0%, #090D16 100%);
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Principal */
    .main-title {
        font-size: 2.3rem !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.8px;
    }
    
    /* Tarjetas KPI Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(16px) !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.25s ease-in-out !important;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #38BDF8 !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 24px rgba(56, 189, 248, 0.15) !important;
    }
    
    /* Pestañas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 700 !important;
        color: #64748B !important;
        padding: 12px 22px !important;
        border-radius: 10px 10px 0 0 !important;
        transition: all 0.2s !important;
    }
    button[aria-selected="true"] {
        color: #38BDF8 !important;
        background: rgba(56, 189, 248, 0.08) !important;
        border-bottom: 3px solid #38BDF8 !important;
    }

    /* Tablas de datos */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

CARPETA_L2 = "L2_fantasy"
CATEGORIAS = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FT_PCT', 'TOV']

# Configuración centralizada de columnas y tooltips explicativos
COLUMN_CONFIG = {
    "RANK": st.column_config.NumberColumn("Rank", help="Posición en el ranking según Z_CUSTOM", format="%d"),
    "PLAYER_NAME": st.column_config.TextColumn("Jugador", help="Nombre del jugador NBA"),
    "TEAM_ABBREVIATION": st.column_config.TextColumn("Equipo", help="Abreviatura del equipo NBA"),
    "GP": st.column_config.NumberColumn("PJ", help="Partidos Jugados (Games Played)", format="%d"),
    "MIN": st.column_config.NumberColumn("MIN", help="Minutos promedio disputados por partido", format="%.1f"),
    "Z_CUSTOM": st.column_config.NumberColumn("Z-Custom", help="Valor analítico recalculado aplicando la estrategia Punt", format="%.2f"),
    "Z_TOTAL": st.column_config.NumberColumn("Z-Total", help="Valor base total considerando las 9 categorías", format="%.2f"),
    "NET_IMPACT": st.column_config.NumberColumn("Net Impact", help="Impacto Neto de Eficiencia y Volumen Fantasy", format="%.2f"),
    "TS_PCT": st.column_config.NumberColumn("TS%", help="True Shooting % (Eficiencia de tiro considerando 2P, 3P y TL)", format="%.3f"),
    "AST_TOV": st.column_config.NumberColumn("AST/TO", help="Ratio de Asistencias por Pérdida de balón", format="%.2f"),
    "STOCKS": st.column_config.NumberColumn("STOCKS", help="Métrica defensiva: Robos (STL) + Tapones (BLK)", format="%.1f"),
    "USG_EST": st.column_config.NumberColumn("USG%", help="Estimación de Porcentaje de Uso Ofensivo por partido", format="%.1f%%"),
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

# Header
col_head1, col_head2 = st.columns([0.82, 0.18])
with col_head1:
    st.markdown('<p class="main-title">🏀 NBA Fantasy Analytics Pro</p>', unsafe_allow_html=True)
    st.caption("Plataforma analítica con métricas avanzadas (TS%, Net Impact, Stocks) y matriz gráfica de cuadrantes tácticos.")

with col_head2:
    with st.popover("ℹ️ Glosario de Métricas"):
        st.markdown("""
        **Líneas Estadísticas Avanzadas:**
        * **TS% (True Shooting):** `PTS / (2 * (FGA + 0.44 * FTA))`
        * **AST/TO:** Ratio Asistencias/Pérdidas.
        * **STOCKS:** Robos (STL) + Tapones (BLK).
        * **NET_IMPACT:** Evaluación global ajustada por tiro y minutos.
        """)

# Carga de datasets
archivos_l2 = [f for f in os.listdir(CARPETA_L2) if f.startswith("L2_") and f.endswith(".csv")] if os.path.exists(CARPETA_L2) else []

if not archivos_l2:
    st.error(f"No se encontraron datasets con prefijo 'L2_' en '{CARPETA_L2}'. Ejecuta L1_fantasy.py y L2_fantasy.py.")
    st.stop()

temporadas = sorted([f.replace("L2_", "").replace(".csv", "") for f in archivos_l2], reverse=True)

# Sidebar
st.sidebar.header("⚙️ Panel de Control")
temporada_sel = st.sidebar.selectbox("Temporada", temporadas, index=0)

punts_sel = st.sidebar.multiselect(
    "Categorías a descartar (PUNT)",
    options=CATEGORIAS,
    default=['FT_PCT', 'TOV'],
    help="Las categorías elegidas quedan excluidas del valor Z_CUSTOM."
)

top_n = st.sidebar.slider("Jugadores a mostrar", min_value=10, max_value=250, value=50)
filtro_busqueda = st.sidebar.text_input("🔍 Buscar Jugador o Equipo:", "")

# Carga y cálculo dinámico de Métricas Avanzadas
df = pd.read_csv(os.path.join(CARPETA_L2, f"L2_{temporada_sel}.csv"))

cols_z_activas = [f"Z_{cat}" for cat in CATEGORIAS if cat not in punts_sel]
df['Z_CUSTOM'] = df[cols_z_activas].sum(axis=1)

df['TS_PCT'] = df['PTS'] / (2 * (df['FGA'] + 0.44 * df['FTA']).replace(0, np.nan))
df['TS_PCT'] = df['TS_PCT'].fillna(0)
df['AST_TOV'] = (df['AST'] / df['TOV'].replace(0, np.nan)).fillna(df['AST'])
df['STOCKS'] = df['STL'] + df['BLK']
df['USG_EST'] = ((df['FGA'] + 0.44 * df['FTA'] + df['TOV']) / df['MIN'].replace(0, np.nan) * 100).fillna(0)
df['NET_IMPACT'] = df['Z_CUSTOM'] * (df['TS_PCT'] / 0.55)

df_ranking = df.sort_values(by='Z_CUSTOM', ascending=False).reset_index(drop=True)
df_ranking['RANK'] = df_ranking.index + 1

if filtro_busqueda:
    df_ranking = df_ranking[
        df_ranking['PLAYER_NAME'].str.contains(filtro_busqueda, case=False, na=False) |
        df_ranking['TEAM_ABBREVIATION'].str.contains(filtro_busqueda, case=False, na=False)
    ]

COLS_FULL = [
    'RANK', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN',
    'Z_CUSTOM', 'Z_TOTAL', 'NET_IMPACT', 'TS_PCT', 'AST_TOV', 'STOCKS', 'USG_EST',
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 
    'FG_PCT', 'FGA', 'FT_PCT', 'FTA', 'TOV'
]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Leaderboard & Exportación", 
    "👤 Perfil Individual Pro", 
    "⚔️ Comparador Multi-Jugador (2-5)", 
    "🎯 Matriz Scatter Plot Táctica"
])

# TAB 1: LEADERBOARD
with tab1:
    st.subheader(f"Leaderboard General — Temporada {temporada_sel.replace('_', '-')}")
    
    df_display = df_ranking[COLS_FULL].head(top_n).copy()
    cols_float = df_display.select_dtypes(include=['float64']).columns
    df_display[cols_float] = df_display[cols_float].round(2)

    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config=COLUMN_CONFIG
    )
    
    csv_data = df_display.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Descargar Dataset Procesado (CSV)",
        data=csv_data,
        file_name=f"ranking_fantasy_{temporada_sel}.csv",
        mime="text/csv"
    )

# TAB 2: PERFIL INDIVIDUAL PRO
with tab2:
    st.subheader("Ficha de Rendimiento Avanzado")
    col_sel, _ = st.columns([0.4, 0.6])
    with col_sel:
        jugador_sel = st.selectbox("Selecciona un jugador:", df_ranking['PLAYER_NAME'].tolist())
    
    p_data = df_ranking[df_ranking['PLAYER_NAME'] == jugador_sel].iloc[0]
    player_id = int(p_data['PLAYER_ID'])
    img_url = f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png"

    col_img, col_metrics = st.columns([0.22, 0.78])
    with col_img:
        st.image(img_url, caption=p_data['PLAYER_NAME'], width=190)
    
    with col_metrics:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Posición Ranking", f"#{p_data['RANK']}")
        m2.metric("Z-Custom", f"{p_data['Z_CUSTOM']:.2f}")
        m3.metric("True Shooting %", f"{p_data['TS_PCT']*100:.1f}%")
        m4.metric("Net Impact", f"{p_data['NET_IMPACT']:.2f}")

        st.write("")
        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Puntos/Partido", f"{p_data['PTS']:.1f}")
        m6.metric("Rebotes", f"{p_data['REB']:.1f}")
        m7.metric("Asistencias", f"{p_data['AST']:.1f}")
        m8.metric("STOCKS (Robos+Tapones)", f"{p_data['STOCKS']:.1f}")

    st.divider()

    c_radar, c_bar = st.columns(2)
    
    with c_radar:
        z_values = [p_data[f"Z_{cat}"] for cat in CATEGORIAS]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=z_values + [z_values[0]],
            theta=CATEGORIAS + [CATEGORIAS[0]],
            fill='toself',
            name=jugador_sel,
            line_color='#38BDF8',
            fillcolor='rgba(56, 189, 248, 0.25)'
        ))
        fig_radar.update_layout(
            template="plotly_dark",
            polar=dict(
                bgcolor='#0F172A',
                radialaxis=dict(visible=True, range=[-3, 4], gridcolor='#334155')
            ),
            title=f"Huella Radar: {jugador_sel}",
            height=420,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with c_bar:
        z_df = pd.DataFrame({'Categoría': CATEGORIAS, 'Z-Score': z_values})
        z_df['Color'] = z_df['Z-Score'].apply(lambda x: '#10B981' if x >= 0 else '#EF4444')
        
        fig_bar = px.bar(
            z_df, x='Categoría', y='Z-Score', 
            color='Color', color_discrete_map='identity',
            title=f"Aportación Neta por Categoría (Z-Score)"
        )
        fig_bar.update_layout(
            template="plotly_dark",
            height=420, 
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# TAB 3: COMPARADOR MULTI-JUGADOR
with tab3:
    st.subheader("Comparador Táctico Multi-Jugador")
    
    default_players = df_ranking['PLAYER_NAME'].head(3).tolist()
    jugadores_sel = st.multiselect(
        "Selecciona entre 2 y 5 jugadores a comparar:",
        options=df_ranking['PLAYER_NAME'].tolist(),
        default=default_players,
        max_selections=5
    )

    if len(jugadores_sel) < 2:
        st.warning("⚠️ Selecciona al menos 2 jugadores para comparar.")
    else:
        colores = ['#38BDF8', '#EF4444', '#10B981', '#F59E0B', '#A855F7']
        fig_comp = go.Figure()
        
        for idx, nombre in enumerate(jugadores_sel):
            p_info = df_ranking[df_ranking['PLAYER_NAME'] == nombre].iloc[0]
            z_vals = [p_info[f"Z_{cat}"] for cat in CATEGORIAS]

            fig_comp.add_trace(go.Scatterpolar(
                r=z_vals + [z_vals[0]],
                theta=CATEGORIAS + [CATEGORIAS[0]],
                fill='toself',
                name=f"#{p_info['RANK']} {nombre}",
                line_color=colores[idx % len(colores)],
                opacity=0.35
            ))

        fig_comp.update_layout(
            template="plotly_dark",
            polar=dict(
                bgcolor='#0F172A',
                radialaxis=dict(visible=True, range=[-3, 4], gridcolor='#334155')
            ),
            title=f"Superposición Radar ({len(jugadores_sel)} Jugadores)",
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("### 📋 Tabla Comparativa con Estadísticas Avanzadas")
        cols_comp = COLS_FULL + [f"Z_{cat}" for cat in CATEGORIAS]
        cols_comp = list(dict.fromkeys(cols_comp))
        
        df_comp_table = df_ranking[df_ranking['PLAYER_NAME'].isin(jugadores_sel)][cols_comp].copy()
        cols_float = df_comp_table.select_dtypes(include=['float64']).columns
        df_comp_table[cols_float] = df_comp_table[cols_float].round(2)
        
        st.dataframe(
            df_comp_table, 
            use_container_width=True, 
            hide_index=True,
            column_config=COLUMN_CONFIG
        )

# TAB 4: SCATTER PLOT CON ETIQUETAS DE CUADRANTE TÁCTICO
with tab4:
    st.subheader("🎯 Matriz de Cuadrantes Tácticos y Oportunidades")
    st.caption("Usa las etiquetas explicativas en las esquinas del gráfico para interpretar el perfil de cada jugador.")

    col_eje_x, col_eje_y, col_top = st.columns(3)
    
    opciones_metricas = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'STOCKS', 'TS_PCT', 'NET_IMPACT', 'Z_CUSTOM', 'Z_TOTAL']
    
    with col_eje_x:
        eje_x = st.selectbox("Eje X (Horizontal):", opciones_metricas, index=0)
    with col_eje_y:
        eje_y = st.selectbox("Eje Y (Vertical):", opciones_metricas, index=9)
    with col_top:
        num_fotos = st.slider("Jugadores en gráfico:", min_value=10, max_value=60, value=30)

    df_scatter = df_ranking.head(num_fotos).copy()

    # Base Scatter sin escala de color redundante
    fig_scatter = px.scatter(
        df_scatter,
        x=eje_x,
        y=eje_y,
        hover_name='PLAYER_NAME',
        hover_data=['TEAM_ABBREVIATION', 'RANK', 'PTS', 'TS_PCT', 'NET_IMPACT'],
        title=f"Matriz Táctica: {eje_y} vs {eje_x}"
    )

    # Ocultar marcadores de puntos para dejar solo los headshots limpios
    fig_scatter.update_traces(marker=dict(size=0, opacity=0))

    # Dimensionamiento dinámico de fotos
    x_min, x_max = df_scatter[eje_x].min(), df_scatter[eje_x].max()
    y_min, y_max = df_scatter[eje_y].min(), df_scatter[eje_y].max()
    
    x_range = (x_max - x_min) if (x_max - x_min) != 0 else 1
    y_range = (y_max - y_min) if (y_max - y_min) != 0 else 1

    size_x = x_range * 0.08
    size_y = y_range * 0.08

    # Superponer fotos CDN de cada jugador
    for _, row in df_scatter.iterrows():
        p_id = int(row['PLAYER_ID'])
        fig_scatter.add_layout_image(
            dict(
                source=f"https://cdn.nba.com/headshots/nba/latest/260x190/{p_id}.png",
                xref="x",
                yref="y",
                x=row[eje_x],
                y=row[eje_y],
                sizex=size_x,
                sizey=size_y,
                xanchor="center",
                yanchor="middle",
                sizing="contain",
                opacity=0.92,
                layer="above"
            )
        )

    # Líneas medias divisoras de cuadrantes
    media_x = df_scatter[eje_x].mean()
    media_y = df_scatter[eje_y].mean()

    fig_scatter.add_vline(x=media_x, line_dash="dash", line_color="#64748B", opacity=0.6)
    fig_scatter.add_hline(y=media_y, line_dash="dash", line_color="#64748B", opacity=0.6)

    # ANOTACIONES EN LAS 4 ESQUINAS (EXPLICACIÓN TÁCTICA DE CUADRANTES)
    fig_scatter.add_annotation(
        x=0.98, y=0.98, xref="paper", yref="paper",
        text=f"💎 TOP ELITE<br>(+ {eje_y} / + {eje_x})",
        showarrow=False, align="right",
        font=dict(size=12, color="#10B981"),
        bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#10B981", borderwidth=1, borderpad=6
    )

    fig_scatter.add_annotation(
        x=0.02, y=0.98, xref="paper", yref="paper",
        text=f"🎯 CHOLLOS / EFICIENTES<br>(+ {eje_y} / - {eje_x})",
        showarrow=False, align="left",
        font=dict(size=12, color="#38BDF8"),
        bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#38BDF8", borderwidth=1, borderpad=6
    )

    fig_scatter.add_annotation(
        x=0.98, y=0.02, xref="paper", yref="paper",
        text=f"⚠️ VOLUMEN SIN EFICIENCIA<br>(- {eje_y} / + {eje_x})",
        showarrow=False, align="right",
        font=dict(size=12, color="#F59E0B"),
        bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#F59E0B", borderwidth=1, borderpad=6
    )

    fig_scatter.add_annotation(
        x=0.02, y=0.02, xref="paper", yref="paper",
        text=f"📉 ROL SECUNDARIO<br>(- {eje_y} / - {eje_x})",
        showarrow=False, align="left",
        font=dict(size=12, color="#EF4444"),
        bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#EF4444", borderwidth=1, borderpad=6
    )

    fig_scatter.update_layout(
        template="plotly_dark",
        height=700,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#0F172A',
        font=dict(color="#F8FAFC"),
        coloraxis_showscale=False
    )

    st.plotly_chart(fig_scatter, use_container_width=True)