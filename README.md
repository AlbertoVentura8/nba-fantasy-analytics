\# NBA Fantasy Analytics 🏀📊



Pipeline ETL y motor analítico con arquitectura Medallion (L1, L2, L3) para la valoración de jugadores en ligas Fantasy NBA por categorías (9-cat).



\## 🏗️ Arquitectura Medallion



\- \*L1\_fantasy/\*: Capa de ingesta bruta. Descarga datasets completos desde nba\_api para las últimas 10 temporadas.

\- \*L2\_fantasy/\*: Capa de transformación. Normalización con Z-Scores ponderados por volumen de tiro (FGA / FTA) y cálculo del valor global Z\_TOTAL.

\- \*L3\_fantasy/: Capa de análisis y consumo. Motores de simulación para estrategias \*Punt y optimización de Draft.



