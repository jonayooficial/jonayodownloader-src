# J Youtube Downloader (Android)

Versión para teléfonos Android del descargador de YouTube. Construida con KivyMD + yt-dlp.

## Características
- Descarga de videos (hasta 4K según el video) en MP4/MKV/WEBM/AVI.
- Extracción de música en MP3/M4A/OPUS/FLAC/WAV con bitrate configurable.
- Soporte de playlists.
- Botón "MI WEB" y Contacto.
- Chequeo automático de actualizaciones.

## Cómo se genera el APK
El APK se compila automáticamente con **GitHub Actions** en la nube (no hace falta Linux ni Android Studio en tu PC):

1. Subir el código al repo.
2. Pushear una etiqueta para release: `git tag v1.3.0 && git push origin v1.3.0`
3. El workflow `Build APK` compila el `.apk`, lo sube como artefacto y (si hay tag) lo publica como Release.

Descargar el `.apk` de la sección Releases e instalarlo (permiso "instalar apps de origen desconocido").

## Compilar localmente (opcional, requiere Linux/WSL)
```bash
pip install buildozer cython
buildozer -v android debug
```
El APK queda en `bin/`.
