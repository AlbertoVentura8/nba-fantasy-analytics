# -*- coding: utf-8 -*-
import os
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

# 2. Inyección de CSS para Identidad Visual Avanzada
st.markdown("""
<style>
    /* Estilo general del Dashboard */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Encabezados y títulos */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    /* Contenedores y Tarjetas KPI */
    div[data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Personalización de Pestañas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        padding: 10px 20px !important;
    }
    button[aria-selected="true"] {
        color: #38BDF8 !important;
        border-bottom-color: #38BDF8 !important;
    }
    
    /* Ajuste de imágenes e insignias */
    .player-headshot {
        border-radius: 16px;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 2px solid #334155;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

CARPETA_L2 = "L2_fantasy"
CATEGORIAS = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FT_PCT', 'TOV']

# Encabezado principal
col_head1, col_head2 = st.columns([0.82, 0.18])
with col_head1:
    st.title("🏀 NBA Fantasy Analytics Pro")
    st.caption("Plataforma analítica con métricas Z-Score ponderadas por volumen e inteligencia táctica.")

with col_head2:
    with st.popover("ℹ️ Glosario de Métricas"):
        st.markdown("""
        **Guía Rápida:**
        * **Z-Score:** Desviaciones estándar sobre la media (`+1.0` = Top Elite).
        * **Z_TOTAL:** Valor base considerando las 9 categorías.
        * **Z_CUSTOM:** Valor recalculado tras aplicar la estrategia *Punt*.
        * **Scatter Plot:** Cuadrantes para identificar chollos y jugadores de alto impacto.
        """)

# Carga de datos
archivos_l2 = [f for f in os.listdir(CARPETA_L2) if f.startswith("L2_") and f.endswith(".csv")] if os.path.exists(CARPETA_L2) else []

if not archivos_l2:
    st.error(f"No se encontraron datasets con prefijo 'L2_' en '{CARPETA_L2}'. Ejecuta L1_fantasy.py y L2_fantasy.py.")
    st.stop()

temporadas = sorted([f.replace("L2_", "").replace(".csv", "") for f in archivos_l2], reverse=True)

# Sidebar - Panel de control
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

# Procesamiento del dataset
df = pd.read_csv(os.path.join(CARPETA_L2, f"L2_{temporada_sel}.csv"))

cols_z_activas = [f"Z_{cat}" for cat in CATEGORIAS if cat not in punts_sel]
df['Z_CUSTOM'] = df[cols_z_activas].sum(axis=1)
df_ranking = df.sort_values(by='Z_CUSTOM', ascending=False).reset_index(drop=True)
df_ranking['RANK'] = df_ranking.index + 1

if filtro_busqueda:
    df_ranking = df_ranking[
        df_ranking['PLAYER_NAME'].str.contains(filtro_busqueda, case=False, na=False) |
        df_ranking['TEAM_ABBREVIATION'].str.contains(filtro_busqueda, case=False, na=False)
    ]

COLS_FULL = [
    'RANK', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN',
    'Z_CUSTOM', 'Z_TOTAL', 
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 
    'FG_PCT', 'FGA', 'FT_PCT', 'FTA', 'TOV'
]

# Estructura de Pestañas
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Leaderboard & Exportación", 
    "👤 Perfil Individual", 
    "⚔️ Comparador Multi-Jugador (2-5)", 
    "🎯 Matriz Scatter Plot (Cuadrantes)"
])

# TAB 1: RANKING Y EXPORTACIÓN
with tab1:
    st.subheader(f"Leaderboard General — Temporada {temporada_sel.replace('_', '-')}")
    
    df_display = df_ranking[COLS_FULL].head(top_n).copy()
    cols_float = df_display.select_dtypes(include=['float64']).columns
    df_display[cols_float] = df_display[cols_float].round(2)

    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "PLAYER_NAME": "Jugador",
            "TEAM_ABBREVIATION": "Equipo",
            "GP": "PJ",
            "MIN": "MIN",
            "Z_CUSTOM": st.column_config.NumberColumn("Z-Custom", format="%.2f"),
            "Z_TOTAL": st.column_config.NumberColumn("Z-Total", format="%.2f"),
            "FG_PCT": st.column_config.NumberColumn("FG%", format="%.3f"),
            "FT_PCT": st.column_config.NumberColumn("FT%", format="%.3f"),
        }
    )
    
    csv_data = df_display.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Descargar Dataset Filtrado (CSV)",
        data=csv_data,
        file_name=f"ranking_fantasy_{temporada_sel}.csv",
        mime="text/csv"
    )

# TAB 2: PERFIL INDIVIDUAL MEJORADO
with tab2:
    st.subheader("Ficha de Rendimiento Individual")
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
        m2.metric("Z-Custom (Estrategia)", f"{p_data['Z_CUSTOM']:.2f}")
        m3.metric("Z-Total Base", f"{p_data['Z_TOTAL']:.2f}")
        m4.metric("Puntos/Partido", f"{p_data['PTS']:.1f}")

        st.write("")
        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Rebotes", f"{p_data['REB']:.1f}")
        m6.metric("Asistencias", f"{p_data['AST']:.1f}")
        m7.metric("Robos", f"{p_data['STL']:.1f}")
        m8.metric("Tapones", f"{p_data['BLK']:.1f}")

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
                bgcolor='#1E293B',
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

# TAB 3: COMPARADOR MULTI-JUGADOR (2 A 5)
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
        st.warning("⚠️ Selecciona al menos 2 jugadores para generar la comparación.")
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
                bgcolor='#1E293B',
                radialaxis=dict(visible=True, range=[-3, 4], gridcolor='#334155')
            ),
            title=f"Superposición de Huella Radar ({len(jugadores_sel)} Jugadores)",
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("### 📋 Tabla Comparativa Completa")
        cols_comp = COLS_FULL + [f"Z_{cat}" for cat in CATEGORIAS]
        cols_comp = list(dict.fromkeys(cols_comp))
        
        df_comp_table = df_ranking[df_ranking['PLAYER_NAME'].isin(jugadores_sel)][cols_comp].copy()
        cols_float = df_comp_table.select_dtypes(include=['float64']).columns
        df_comp_table[cols_float] = df_comp_table[cols_float].round(2)
        
        st.dataframe(df_comp_table, use_container_width=True, hide_index=True)

# TAB 4: SCATTER PLOT INTERACTIVO (CUADRANTES DE VALOR)
with tab4:
    st.subheader("🎯 Matriz de Correlación y Detección de Oportunidades")
    st.caption("Usa los cuadrantes para descubrir jugadores con alto valor analítico en relación a su volumen de juego o puntuación.")

    col_eje_x, col_eje_y, col_size = st.columns(3)
    
    opciones_metricas = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'Z_CUSTOM', 'Z_TOTAL', 'GP']
    
    with col_eje_x:
        eje_x = st.selectbox("Eje X (Horizontal):", opciones_metricas, index=0) # Por defecto MIN
    with col_eje_y:
        eje_y = st.selectbox("Eje Y (Vertical):", opciones_metricas, index=7) # Por defecto Z_CUSTOM
    with col_size:
        eje_size = st.selectbox("Tamaño de Burbuja:", opciones_metricas, index=1) # Por defecto PTS

    df_scatter = df_ranking.head(top_n).copy()

    fig_scatter = px.scatter(
        df_scatter,
        x=eje_x,
        y=eje_y,
        size=eje_size,
        color='Z_CUSTOM',
        hover_name='PLAYER_NAME',
        hover_data=['TEAM_ABBREVIATION', 'RANK', 'PTS', 'REB', 'AST'],
        color_continuous_scale='Viridis',
        title=f"Análisis de Cuadrantes: {eje_x} vs {eje_y} (Tamaño = {eje_size})"
    )

    # Líneas medias para dividir los 4 cuadrantes
    media_x = df_scatter[eje_x].mean()
    media_y = df_scatter[eje_y].mean()

    fig_scatter.add_vline(x=media_x, line_dash="dash", line_color="#94A3B8", opacity=0.6)
    fig_scatter.add_hline(y=media_y, line_dash="dash", line_color="#94A3B8", opacity=0.6)

    fig_scatter.update_layout(
        template="plotly_dark",
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#1E293B',
        font=dict(color="#F8FAFC")
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

    st.info(f"💡 **Tip Analítico:** Los jugadores situados en el **cuadrante superior izquierdo** (por encima de la media en {eje_y} con menor valor en {eje_x}) son perfiles extremadamente eficientes y objetivos primarios para fichajes/traspasos.")