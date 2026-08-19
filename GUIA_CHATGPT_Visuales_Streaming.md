# GUÍA PARA CHATGPT — J YouTube Downloader v1.8.8

> Proyecto: **jonayodownloader-android** — App Android (Kivy 2.3.1 + Python 3.12 + Python-for-Android).
> Toda la UI está en `main.py` (sin archivos .kv). Antes de tocar nada LEE `AGENTS.md`
> (memoria del proyecto: fixes críticos, build, CI, trampas).

---

## 1. LO QUE DEBES SOLUCIONAR (prioridad del usuario)

1. **Reproducción en streaming SIN descargar** (como YouTube): tocar REPRODUCIR debe
   empezar a ver el video al instante, con opción de calidad, y poder **añadir a una cola**
   de reproducción los videos que quieras ver después.
2. **Estilo visual del reproductor interno** tipo YouTube (controles limpios, bien ubicados,
   nada de iconos "gigantes" mal colocados ni cuadros [x][x][x]).
3. **Velocidad de búsqueda**: hoy tarda 30-40 s en encontrar videos y las miniaturas cargan
   lentas. Debe ser casi instantáneo como la app de YouTube.
4. **Cola de reproducción** (diseñar + implementar).

---

## 2. CONTEXTO TÉCNICO (IMPORTANTE)

- **UI 100% en `main.py`** con Kivy. No hay `.kv`. Las clases se construyen en Python.
- **El APK se parchea sin recompilar**: se sustituye `main.pyc` dentro del `private.tar`
  del bundle (scripts `tools/patch_apk.py` + `tools/sign_apk.py`). Esto significa que en el
  ciclo local **solo se puede cambiar `main.py`**.
- **Cualquier cambio que requiera compilar código nativo** (recipes, buildozer.spec, servicios,
  módulos .so) exige un **rebuild completo vía GitHub Actions** (workflows en `.github/workflows/`,
  ~18-22 min por build). El CI se dispara con `push` a `main`.
- **ffpyplayer 4.5.1** es el único provider de video en Android. Su FFmpeg compilado **NO
  soporta streaming HTTPS** → el widget `Video` de Kivy solo reproduce **archivos locales**.
- El binario `ffmpeg` CLI del APK (`libffmpegbin.so`, en `nativeLibraryDir`) SÍ tiene red
  (lo usa yt-dlp para descargar/fusionar).
- Se usa `yt-dlp` (2026.7.4) con `extractor_args: player_client=['tv','android']` porque el
  cliente web da `HTTP 403` y sin JS runtime el nsig queda incompleto.
- Android 14, teléfono Blade 10 Power (Doogee). Paquete `org.jonayo.jonayodownloader`.

---

## 3. PROBLEMA 1 — STREAMING SIN DESCARGAR + COLA (el más importante)

### Estado actual
`REPRODUCIR` en un resultado de búsqueda hace esto (`play_stream` → `_play_download_thread`):
1. Muestra diálogo "Preparando reproducción..." con barra de progreso.
2. **Descarga** el video a la carpeta temporal `.reproducir` (calidad elegida: 1080p/720p/480p/360p).
3. Al terminar, abre el **reproductor interno** (`_play_internal`) con el archivo local.
4. El archivo temporal **se borra al cerrar** el reproductor.

El usuario NO quiere descargar para ver: quiere **streaming instantáneo**.

### Causa raíz
El provider de video de Kivy en Android (ffpyplayer 4.5.1) no puede abrir URLs HTTPS
(white screen, sin textura). Verificado en logs: `Reproductor: sin textura en streaming`.

### Opciones técnicas (elige y diseña la mejor)

**Opción A — Rebuild del recipe ffpyplayer con red (recomendado, requiere CI):**
Crear/parchear `recipes/ffpyplayer/__init__.py` (o su patch de config de FFmpeg) para
compilar su FFmpeg con:
`--enable-network --enable-protocol=http,https --enable-demuxer=hls,http,http_persistent
 --enable-decoder=h264,aac --enable-openssl`
Luego subir a `main` y el CI recompila. Con eso el widget `Video` de Kivy podría reproducir
URLs de googlevideo directamente (streaming real). Riesgo: el build de ffpyplayer puede ser
frágil; hay que probar.

**Opción B — MediaPlayer nativo de Android vía pyjnius (sin rebuild):**
Crear un `SurfaceView` + `android.media.MediaPlayer` con pyjnius y añadirlo a la ventana de la
Activity. Reproduce cualquier URL con decodificación nativa. PROBLEMA: la SurfaceView queda
ENCIMA de la ventana de Kivy, así que los controles Kivy no se pueden superponer. Solución
posible: usar `TextureView` y capturar su textura para renderizarla dentro de Kivy, o poner
los controles como botones Android nativos encima. Es complejo y frágil sin rebuild.

**Opción C — Transcodificar con el ffmpeg CLI y alimentar a ffpyplayer por pipe/stdin:**
Usar `libffmpegbin.so` para bajar y transcodificar el stream y pasárselo a ffpyplayer por un
pipe. Muy complejo y con latencia.

**Recomendación:** Opción A (rebuild ffpyplayer con red en CI). Diseña el patch y el flujo de
`extract_info(download=False)` → elegir formato (URL directa) → `Video(source=url)`. Mantener
el flujo actual de descarga-temp como FALLBACK si el streaming falla.

### Cola de reproducción (diseñarla)
- En el menú del video (2 botones grandes: REPRODUCIR / DESCARGAR) añadir "➕ Añadir a cola".
- Una pantalla/listado de cola (botón en el reproductor y/o en el Nav).
- Al terminar un video, reproducir el siguiente de la cola automáticamente.
- Guardar la cola en memoria (o en `downloads.json` / un `queue.json`).

---

## 4. PROBLEMA 2 — ESTILO VISUAL DEL REPRODUCTOR (main.py, `_play_internal`, ~línea 1740)

### Síntomas reportados por el usuario
- Iconos "gigantes" arriba a la derecha; el video se ve pequeño abajo; 60% de la pantalla libre.
- Antes los iconos salían como **cuadros [x][x][x]** porque los glifos `⛶` `🎵` `✕` NO existen
  en la fuente Android.

### Lo que ya se hizo
- Se creó `draw_icon(w, kind)` (a nivel de módulo, ~línea 96): dibuja iconos VECTORIALES con
  canvas (`close` = X, `fs` = esquinas de pantalla completa, `music` = nota musical). Usarlos
  en vez de glifos.
- `_status_bar_dp()`: altura de la barra de estado para no tapar los controles con la hora.
- Bug de layout corregido: la pantalla de audio oculta ocupaba espacio; ahora `ascreen` se
  colapsa (`size_hint_y=None; height=0`) cuando está en modo video.
- Barras superior/inferior con fondo translúcido `(0,0,0,0.55)`.

### Estructura actual del reproductor (`_play_internal`)
```
ModalView(size_hint=(1,1), fondo transparente)
└─ root (BoxLayout vertical, padding superior = status bar)
   ├─ top (52dp): Título | botón fs | botón música | botón cerrar   ← iconos canvas
   ├─ varea (FloatLayout, ocupa el resto): widget Video (llena)
   ├─ ascreen (colapsado salvo en modo audio)
   └─ ctrl (56dp): ⏸ | Slider(progreso) | 0:00 / 0:00
```

### Lo que se pide (rediseño tipo YouTube)
1. **Controles superpuestos al video** (overlay), no barras separadas que roban espacio.
2. **Auto-ocultar** los controles a los ~3 s de reproducir y mostrar al tocar la pantalla.
3. Barra superior discreta (fondo degradado negro semitransparente, título con ellipsis,
   botones pequeños ~40dp).
4. Barra de progreso fina **arriba** (estilo YouTube) y/o en la fila inferior con el tiempo
   `0:00 / 3:45`.
5. Botones: pausa/reproducir, **adelante/atrás** (no imprescindible), **velocidad**, **calidad**,
   **siguiente video de la cola**, **modo audio (música)**, **pantalla completa** (immersive),
   **cerrar**.
6. Que el video llene todo el espacio disponible **centrado** y con letterbox (negro), usando
   `Video` con `allow_stretch` correcto dentro de un `FloatLayout`.
7. Iconos SIEMPRE vectoriales (ampliar `draw_icon` con más tipos: pausa, play, siguiente,
   velocidad, etc.). NUNCA usar glifos que la fuente Android no tenga.

---

## 5. PROBLEMA 3 — VELOCIDAD DE BÚSQUEDA (main.py, `_search_thread` ~línea 900)

- Hoy: `yt_dlp.extract_info('ytsearch10:'+query, download=False)` tarda 30-40 s.
- Miniaturas: se cambió `maxresdefault` → `mqdefault` (`_fast_thumb`) para que carguen rápido.

### Ideas para optimizar (implementar la mejor)
1. **Cachear búsquedas recientes** en memoria/JSON (evitar repetir la misma consulta).
2. Reducir a **5-8 resultados** (menos tiempo de extracción).
3. Usar `extract_flat=True` para la búsqueda (no resolver formatos → mucho más rápido) y
   resolver el video solo cuando se elige REPRODUCIR/DESCARGAR.
4. Con `extract_flat`, el `url`/`id` de cada entrada basta; los formatos se obtienen al abrir.
5. Considerar una **API de búsqueda de YouTube** (requiere clave, no recomendado sin key).
6. Paralelizar la carga de miniaturas (AsyncImage ya es async; con mqdefault es suficiente).

---

## 6. RESTRICCIONES Y TRAMPAS (LEER AGENTS.md OBLIGATORIO)

- **NO romper el fix de pantalla negra**: las pantallas se crean de forma DIFERIDA
  (`Clock.schedule_once(lambda dt: self._finish_setup(), 0.05)` en `M.__init__`). No volver a
  crear todo en `build()`.
- **Versión consistente**: `buildozer.spec` `version` == `updater.py` `VERSION` ==
  `main.py` `APP_VERSION`. Hoy = `1.8.8`.
- **Firma release** en `buildozer.spec` (5 líneas del keystore). No quitarlas.
- **No subir versiones de Python 3.13/3.14** (ffpyplayer rompe).
- **grp** arreglado con patch local de python3 (3.12). No tocar.
- **ffpyplayer 4.5.1** incompatible con ffmpeg 7/8 → pin ffmpeg 6.1.2.
- **SELinux**: no se puede ejecutar binarios desde la carpeta de datos de la app
  (`app_data_file`). Solo desde `nativeLibraryDir`. El `_ensure_ffmpeg` de main.py ya lo maneja.
- **`adb install -r` NO actualiza el código**: hay que desinstalar e instalar de cero para
  probar cambios de `main.py`.
- La clave de firma local (`tools/key.pk8`, `tools/cert.pem`) NO se regenera; no borrarla.

---

## 7. QUÉ ENTREGAR (formato de respuesta)

1. **Explicación corta** de la solución elegida para streaming (y por qué).
2. **Código exacto a insertar/reemplazar en `main.py`** (diferencias claras, con números de línea
   actuales si es posible).
3. **Archivos a crear/modificar para el rebuild** (recipe ffpyplayer, buildozer.spec, servicios)
   con el contenido completo.
4. **Instrucciones de build/test** paso a paso.

### Archivos clave del proyecto
- `main.py` — toda la UI y lógica (lo más importante).
- `crashlog.py`, `updater.py`, `buildozer.spec`.
- `recipes/` — ffmpeg, lame, python3, hostpython3.
- `.github/workflows/` — build-apk.yml y build-debug.yml (CI).
- `AGENTS.md` — memoria del proyecto (leer primero).
- `assets/` — iconos y logo.