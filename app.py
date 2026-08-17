# -*- coding: utf-8 -*-
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="NBA Fantasy Analytics L3", layout="wide", page_icon="🏀")

CARPETA_L2 = "L2_fantasy"
CATEGORIAS = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT', 'FT_PCT', 'TOV']

# Encabezado principal y Glosario
col_head1, col_head2 = st.columns([0.85, 0.15])
with col_head1:
    st.title("🏀 NBA Fantasy Analytics")
    st.caption("Plataforma analítica con métricas Z-Score ponderadas por volumen y estadísticas tradicionales.")

with col_head2:
    with st.popover("ℹ️ Glosario"):
        st.markdown("""
        **Guía de Métricas:**
        * **Z-Score:** Desviaciones estándar respecto a la media de la liga (`+1.0` = 1 desviación sobre la media).
        * **Z_TOTAL:** Valor base sumando las 9 categorías.
        * **Z_CUSTOM:** Valor recalculado excluyendo las categorías *Punt*.
        * **PUNT:** Ignorar categorías débiles para maximizar el valor relativo del jugador.
        """)

# Carga de datasets
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
    help="Las categorías elegidas se excluyen del cálculo de Z_CUSTOM."
)

top_n = st.sidebar.slider("Jugadores a mostrar", min_value=10, max_value=250, value=50)

# Buscador rápido por nombre o equipo
filtro_busqueda = st.sidebar.text_input("🔍 Buscar por Jugador o Equipo:", "")

# Carga y filtrado de datos
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

# Columnas estándar completas
COLS_FULL = [
    'RANK', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN',
    'Z_CUSTOM', 'Z_TOTAL', 
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 
    'FG_PCT', 'FGA', 'FT_PCT', 'FTA', 'TOV'
]

# Pestañas del Dashboard
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Ranking y Exportación", 
    "👤 Perfil Individual", 
    "⚔️ Comparador Multi-Jugador (2-5)", 
    "🔥 Mapa de Calor"
])

# TAB 1: RANKING COMPLETO + EXPORTACION
with tab1:
    st.subheader(f"Ranking Top {top_n} — Temporada {temporada_sel.replace('_', '-')}")
    
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
    
    # Botón para descargar datos procesados en CSV
    csv_data = df_display.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Descargar Ranking Actual (CSV)",
        data=csv_data,
        file_name=f"ranking_fantasy_{temporada_sel}.csv",
        mime="text/csv"
    )

# TAB 2: PERFIL INDIVIDUAL COMPLETO Y GRAFICOS
with tab2:
    st.subheader("Análisis de Perfil Estadístico")
    col_sel, _ = st.columns([0.4, 0.6])
    with col_sel:
        jugador_sel = st.selectbox("Selecciona un jugador", df_ranking['PLAYER_NAME'].tolist())
    
    p_data = df_ranking[df_ranking['PLAYER_NAME'] == jugador_sel].iloc[0]
    player_id = int(p_data['PLAYER_ID'])
    img_url = f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png"

    col_img, col_metrics = st.columns([0.25, 0.75])
    with col_img:
        st.image(img_url, caption=p_data['PLAYER_NAME'], width=200)
    
    with col_metrics:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Posición Ranking", f"#{p_data['RANK']}")
        m2.metric("Z-Custom", f"{p_data['Z_CUSTOM']:.2f}")
        m3.metric("Z-Total Base", f"{p_data['Z_TOTAL']:.2f}")
        m4.metric("Puntos/Partido", f"{p_data['PTS']:.1f}")

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
            line_color='#006BB6'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[-3, 4])),
            title=f"Radar Z-Score: {jugador_sel}",
            height=400
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with c_bar:
        # Gráfico de barras condicional por Z-Score
        z_df = pd.DataFrame({'Categoría': CATEGORIAS, 'Z-Score': z_values})
        z_df['Color'] = z_df['Z-Score'].apply(lambda x: '#00833E' if x >= 0 else '#C9082A')
        
        fig_bar = px.bar(
            z_df, x='Categoría', y='Z-Score', 
            color='Color', color_discrete_map='identity',
            title=f"Impacto por Categoría (Z-Score): {jugador_sel}"
        )
        fig_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

# TAB 3: COMPARADOR MULTI-JUGADOR (HASTA 5)
with tab3:
    st.subheader("Comparador Multi-Jugador (Hasta 5 perfiles)")
    
    default_players = df_ranking['PLAYER_NAME'].head(3).tolist()
    jugadores_sel = st.multiselect(
        "Selecciona de 2 a 5 jugadores:",
        options=df_ranking['PLAYER_NAME'].tolist(),
        default=default_players,
        max_selections=5
    )

    if len(jugadores_sel) < 2:
        st.warning("⚠️ Selecciona al menos 2 jugadores para la comparación.")
    else:
        colores = ['#17408B', '#C9082A', '#00833E', '#FDB927', '#6F263D']
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
                opacity=0.4
            ))

        fig_comp.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[-3, 4])),
            title=f"Comparativa de Radar ({len(jugadores_sel)} Jugadores)",
            height=500
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("### 📋 Tabla Comparativa Completa")
        cols_comp = COLS_FULL + [f"Z_{cat}" for cat in CATEGORIAS]
        cols_comp = list(dict.fromkeys(cols_comp))
        
        df_comp_table = df_ranking[df_ranking['PLAYER_NAME'].isin(jugadores_sel)][cols_comp].copy()
        cols_float = df_comp_table.select_dtypes(include=['float64']).columns
        df_comp_table[cols_float] = df_comp_table[cols_float].round(2)
        
        st.dataframe(df_comp_table, use_container_width=True, hide_index=True)

# TAB 4: MAPA DE CALOR POR CATEGORIAS
with tab4:
    st.subheader(f"Mapa de Calor de Z-Scores (Top {min(30, top_n)} Jugadores)")
    
    df_heat = df_ranking.head(min(30, top_n)).set_index('PLAYER_NAME')
    cols_z_heat = [f"Z_{cat}" for cat in CATEGORIAS]
    matrix_data = df_heat[cols_z_heat].round(2)
    matrix_data.columns = CATEGORIAS

    fig_heat = px.imshow(
        matrix_data,
        labels=dict(x="Categoría", y="Jugador", color="Z-Score"),
        x=CATEGORIAS,
        y=matrix_data.index,
        color_continuous_scale="RdYlGn",
        aspect="auto"
    )
    fig_heat.update_layout(height=650)
    st.plotly_chart(fig_heat, use_container_width=True)