# v1.8.9 — Streaming y reproductor interno

- Streaming directo HTTPS mediante URL de formato progresivo (video + audio), sin descarga previa.
- ffmpeg 6.1.2 compilado con OpenSSL/HTTPS, HTTP/HLS y demuxers necesarios.
- Fallback local únicamente si el stream directo falla.
- Reproductor interno rediseñado como overlay tipo YouTube: video a pantalla completa con letterbox, controles superpuestos, auto-ocultación, progreso, tiempo, calidad, velocidad, cola, audio, fullscreen y cierre.
- Cola en memoria: añadir, quitar, reproducir siguiente y avanzar automáticamente al terminar.
- Búsquedas con `extract_flat`, 8 resultados y caché de 5 minutos.
- Descargas normales siguen usando el flujo existente y los archivos descargados se reproducen dentro de la app.
