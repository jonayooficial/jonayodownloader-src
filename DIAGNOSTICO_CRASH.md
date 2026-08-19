# DIAGNÓSTICO COMPLETO — Crash de J YouTube Downloader v1.8.6 al arrancar

> Documento de traspaso para que otro agente/chat continúe el trabajo sin
> perder el contexto. Contiene: síntoma, evidencia, causa raíz confirmada,
> verificaciones hechas y opciones de solución.

---

## 0. NUEVO BUG RESUELTO (19-08): error de descarga `'str' object has no attribute 'write'`

> **El crash de arranque (secciones 1-10) ya está RESUELTO en el APK nuevo.**
> La app YA abre la UI. El bug actual es al descargar. Este documento se usa
> para que el agente que hace el build NO elimine los fixes de abajo.

### Síntoma
- La app arranca OK, busca un video, y al pulsar descargar muestra:
  `ERROR EN DESCARGA: 'str' object has no attribute 'write'`
- En `files/logs/app.log` (externo, `/sdcard/Android/data/.../files/logs/app.log`):
  `Error descarga: 'str' object has no attribute 'write'`

### Causa raíz (DOBLE bug)
1. **yt-dlp 2026.07.04 + Kivy 2.3.1:** Kivy reemplaza `sys.stderr` con un
   `ProcessingStream` cuyo `.buffer` es un **str**. Cuando yt-dlp necesita
   avisar/errores llama `sys.stderr.buffer.write(...)` → `'str' object has no
   attribute 'write'`. (issue yt-dlp #14912). Esto enmascara el error REAL.
2. **ffmpeg no se ejecuta:** el APK empaqueta ffmpeg como `libffmpegbin.so` en
   las libs nativas (`/data/app/.../lib/arm64/`). Además, ese binario enlaza
   contra las `libav*.so` compartidas (`DT_NEEDED` verificado con parser ELF:
   libavdevice/avfilter/avformat/avcodec/swresample/swscale/avutil/ssl/crypto) y
   **sin `LD_LIBRARY_PATH` el linker falla**: `CANNOT LINK EXECUTABLE: library
   "libavdevice.so" not found`. Verificado en el teléfono vía adb: sin la env
   var falla, con `LD_LIBRARY_PATH=<dir libs>` funciona (`ffmpeg version d1c422c`).
   Resultado real: yt-dlp dice "ffmpeg is not installed" → el merge de
   video+audio falla → si además no hay logger, el error se vuelve el
   AttributeError de arriba.

### FIX APLICADO en `main.py` (NO BORRAR)
- `class _YDL_Logger` (logger para yt-dlp): `debug`→noop, `warning`/`error`→
  `crashlog.write_log`. En `ydl_opts` se pasa `'logger': _YDL_Logger()`.
  Con esto el flujo NUNCA escribe a `sys.stderr` roto y los errores reales
  quedan en `app.log` (líneas `[yt-dlp]` / `[yt-dlp ERROR]`).
- `M._ensure_ffmpeg()` (se llama al inicio de `_download_thread`):
  1. `jnius` → `PythonActivity.mActivity.getApplicationInfo().nativeLibraryDir`.
  2. Copia `libffmpegbin.so` → `files/app/bin/ffmpeg` (`chmod 0o755`), que es lo
     que busca `_find_ffmpeg_dir()`.
  3. `os.environ['LD_LIBRARY_PATH'] = nativeLibraryDir` para que el subprocess
     de ffmpeg encuentre las `libav*.so`.
- El `except` de `_download_thread` ahora loguea `traceback.format_exc()`.

### PENDIENTE / IMPORTANTE
- **Rebuild + reinstalar + probar.** El flujo de descarga con merge (bestvideo+
  bestaudio → mp4, `-c copy`) funciona con este ffmpeg (muxer mp4 + decod
  h264/aac). PROBAR en el teléfono un video popular.
- **MODO MP3 roto con este ffmpeg:** el binario se compiló con
  `--disable-everything` y **no tiene encoders** (ni libmp3lame ni aac). El modo
  MP3 (`FFmpegExtractAudio`, preferredcodec mp3) fallará con "Unknown encoder
  mp3". Hacer el merge de video es lo único que soporta. Para arreglar MP3 hay
  que reconstruir ffmpeg con `--enable-libmp3lame` (requiere rebuild del APK).

---

## 1. SÍNTOMA

- La app **crashea antes de abrir la UI** (se ve el splash y se cierra).
- **No llega a crear** `Descargas/JONAYO_LOGS/` ni `files/logs/app.log`, porque
  el crash ocurre **durante `Py_Initialize`**, ANTES de que se ejecute
  cualquier código Python (main.py nunca llega a correr).
- Un chat anterior afirmó que era "crash nativo antes de que Python arranque"
  y que "ningún fix de Python lo va a resolver". **Eso es INCORRECTO** (ver §4).

## 2. EVIDENCIA (logcat del teléfono, app lanzada vía adb)

Dispositivo: **Blade 10 Power** (Android 14, Doogee), `BLADE10PO0000005288`.
Paquete: `org.jonayo.jonayodownloader` · Activity real: `org.kivy.android.PythonActivity`
(no `MainActivity`).

```
I python  : Initializing Python for Android
I python  : Setting additional env vars from p4a_env_vars.txt
I python  : Changing directory to '/data/user/0/org.jonayo.jonayodownloader/files/app'
I python  : Preparing to initialize python
I python  : _python_bundle dir exists
I python  : set wchar paths...
W SDLThread: avc: granted { execute } ... _python_bundle/modules/zlib.cpython-312.so   (x2)
I python  : Python initialization failed:
I python  : failed to get the Python codec of the filesystem encoding
I python  : Initialized python
I python  : Python for android ended.
F libc    : FORTIFY: pthread_mutex_lock called on a destroyed mutex ... (múltiples hilos)
F libc    : Fatal signal 6 (SIGABRT) / signal 11 (SIGSEGV)  -> crash del proceso
```

El crash nativo (SIGABRT/SIGSEGV en RenderThread/Jit thread pool) es **secundario**:
ocurre porque el proceso ya está siendo destruido tras el fallo de Python.

## 3. CAUSA RAÍZ (confirmada)

La excepción real, oculta en logcat porque el stderr de Python no se captura,
se obtuvo ejecutando el intérprete embebido del propio APK (ver §6):

```
Fatal Python error: init_fs_encoding: failed to get the Python codec of the filesystem encoding
Python runtime state: core initialized
Traceback (most recent call last):
  File "<frozen zipimport>", line 510, in _get_decompress_func
ImportError: dlopen failed: cannot locate symbol "PyExc_MemoryError" referenced by
  "/data/data/org.jonayo.jonayodownloader/files/app/_python_bundle/modules/zlib.cpython-312.so"

During handling of the above exception, another exception occurred:
zipimport.ZipImportError: can't decompress data; zlib not available

During handling of the above exception, another exception occurred:
zipimport.ZipImportError: can't decompress data; zlib not available
```

**Cadena causal completa:**

1. `Py_Initialize` necesita el codec del filesystem → importa `encodings`.
2. `encodings` vive dentro de `_python_bundle/stdlib.zip` → **zipimport** debe
   descomprimir la entrada (deflate) → necesita el módulo `zlib`.
3. `import zlib` intenta `dlopen("zlib.cpython-312.so")` y **FALLA**:
   el `.so` referencia `PyExc_MemoryError` (un símbolo de libpython) y Android
   no lo encuentra.
4. Sin zlib, zipimport no puede leer `stdlib.zip` → `import encodings` falla
   → `init_fs_encoding` aborta → app muere antes de `import main`.

**Por qué Android no resuelve `PyExc_MemoryError`:**

- `zlib.cpython-312.so` tiene en su sección dinámica **solo**:
  `DT_NEEDED = ['libz.so', 'libdl.so', 'libc.so']` — **NO incluye `libpython3.12.so`**.
- Regla del linker de Android (NDK issue #201): una librería cargada con
  `dlopen` solo puede resolver símbolos de sus **propias dependencias
  (`DT_NEEDED`)** + el ejecutable principal + `LD_PRELOAD`. A diferencia de
  Linux de escritorio, NO ve los símbolos de las libs ya cargadas en otro
  namespace (libpython se carga vía `System.loadLibrary` → namespace
  `clns-4`, invisible para el `dlopen` por defecto).
- Por eso las extensiones de CPython para Android **DEBEN** linkearse con
  `-lpython3.12` (añadiendo `libpython3.12.so` a su `DT_NEEDED`).

**Es el bug conocido de CPython:** gh-111225 ("Cross Compile for Android and
issues with PyExc_OSError"): en Python ≤3.12 el build system **no enlaza las
extensiones contra libpython**. El fix (PR #115780) entró **solo en 3.13+**.
Para 3.12, la corrección la aporta el build system de p4a (patch equivalente
al `bldlibrary.patch` de Chaquopy). **En este build NO se aplicó.**

## 4. POR QUÉ EL OTRO CHAT SE EQUIVOCÓ

- Dijo "crash nativo antes de que Python arranque, ningún fix de Python lo
  resuelve". Falso: el log muestra `Initializing Python for Android` y
  `_python_bundle dir exists`, es decir **Python SÍ arranca** y falla dentro
  de `Py_Initialize` (fase nativa de CPython, sí, pero por un problema de
  build del APK, no del código de la app).
- No es un problema del `main.py`/Kivy. Es un **APK mal construido**.

## 5. VERIFICACIONES REALIZADAS (todo comprobado empíricamente)

| Verificación | Resultado |
|---|---|
| `stdlib.zip` presente y completo en el bundle | ✅ 554 entradas, 122 de `encodings` |
| Integridad del zip (CRC de todas las entradas) | ✅ 0 errores |
| Magic de los `.pyc` (cabecera `cb 0d 0d 0a`) | ✅ = Python 3.12 exacto |
| `encodings/__init__.pyc`, `aliases.pyc`, `utf_8.pyc`, `codecs.pyc` | ✅ presentes |
| `libpython3.12.so` exporta `PyExc_MemoryError` / `Py_Initialize` | ✅ SÍ los exporta (dynsym) |
| `DT_NEEDED` de `zlib.cpython-312.so` | ❌ **solo** libz/libdl/libc — falta `libpython3.12.so` |
| `libz.so` en el dispositivo | ✅ existe en /system/lib64 |
| Carga de zlib en logcat (SELinux audit `execute`) | ✅ se intenta cargar justo antes del fallo |
| Repro del error con el intérprete embebido del APK | ✅ error exacto reproducido (§6) |

Conclusión de las verificaciones: **el stdlib/bundle está bien; lo que está
mal es el enlazado de las extensiones nativas contra libpython** en el APK.

## 6. CÓMO SE REPRODUJO (comandos usados)

`_python_bundle` descomprimido en:
`/data/data/org.jonayo.jonayodownloader/files/app/_python_bundle/`

El APK trae un intérprete embebido: `files/app/.bin/python` (symlink a
`libpythonbin.so`). Se ejecutó con el entorno del bundle:

```sh
# Script colocado en el app dir vía: run-as ... cp /data/local/tmp/runpy.sh files/runpy.sh
#!/system/bin/sh
export LD_LIBRARY_PATH=/data/app/~~9wWJgVfv2ar00bTNhzhPdQ==/org.jonayo.jonayodownloader-1ZKdJriEGj9HWzsIYy9cxg==/lib/arm64
export PYTHONHOME=/data/data/org.jonayo.jonayodownloader/files/app
export PYTHONPATH=/data/data/org.jonayo.jonayodownloader/files/app/_python_bundle/stdlib.zip:/data/data/org.jonayo.jonayodownloader/files/app/_python_bundle/modules
exec ./files/app/.bin/python ./files/pytest.py > ./files/pyout.txt 2>&1
```

Y `pytest.py` hacía `import encodings`, `import codecs`, `import zlib`... → el
error de `PyExc_MemoryError` se imprimió tal cual (stderr a archivo).

Nota: `adb shell ... > archivo` en PowerShell corrompe binarios (los escribe
en UTF-16). Usar `cmd /c "adb exec-out ... > archivo"` para binarios.

## 7. CONTEXTO DE BUILD DEL APK ROTO (importante para el fix)

- Repo local: `C:\Users\Jona\Downloads\jonayodownloader-v1.8.6-full`
- `buildozer.spec`:
  - `requirements = python3==3.12.14,hostpython3==3.12.14,kivy==2.3.1,yt-dlp,ffmpeg,requests,certifi,ffpyplayer`
  - `android.api = 33`, `android.minapi = 24`, `android.ndk = 28c`, `android.sdk = 33`
  - `android.archs = arm64-v8a,armeabi-v7a,x86_64,x86` (APK universal de 4 archs)
  - `p4a.local_recipes = ./recipes`
- Recipes locales presentes: `recipes/{ffmpeg,ffpyplayer,hostpython3,python3}`.
  - `recipes/python3/__init__.py` subclasea `pythonforandroid.recipes.python3.Python3Recipe`
    y solo añade el patch `grp-disable.patch` (CPython gh-114875). **No añade
    ningún patch de enlazado de extensiones contra libpython.**
- Workflows CI (`.github/workflows/build-apk.yml` y `build-debug.yml`):
  - Instalan **`buildozer` SIN pin** (`pip install --user buildozer`) y
    `cython==3.0.11` → **la versión de p4a que se usa no está fijada**.
  - Cualquier actualización upstream de p4a entre v1.7.0 (funcionaba) y
    v1.8.6 (rota) puede haber cambiado el enlazado de las extensiones.
- APKs locales del build roto:
  - `bin/jonayodownloader-1.8.6-arm64-v8a_armeabi-v7a_x86_64_x86-release.apk`
  - `bin-debug/jonayodownloader-1.8.6-arm64-v8a_armeabi-v7a_x86_64_x86-debug.apk`
- Nota: el `pythonutil` del APK sondea `libpython3.14.so` → `3.13` → `3.12`,
  señal de una p4a MUY reciente (soporta Python 3.14/3.13).

## 8. OPCIONES DE SOLUCIÓN (para el siguiente agente)

**El crash NO se arregla tocando main.py. Hay que REBUILD con el enlazado
correcto.** Opciones, de más robusta a más rápida:

### Opción A (recomendada): añadir patch de enlazado a la recipe local de python3
- En `recipes/python3/__init__.py`, aplicar a CPython 3.12 un patch equivalente
  al `bldlibrary.patch` de Chaquopy / PR #115780 de CPython: hacer que las
  extensiones se enlacen con `-lpython3.12` (añadir `libpython3.12.so` a
  `DT_NEEDED`). Se puede lograr:
  - vía patch al `configure`/`Makefile` (LDSHARED/BLDSHARED/MODLIBS), o
  - vía `env['LDFLAGS']`/`env['LIBS']` en `get_recipe_env()` de la recipe
    (cuidado: LDFLAGS afecta al binario principal; lo que hay que tocar es el
    enlazado de los `Modules/*.so`).
- Verificar el resultado en el APK: `readelf -d Modules/zlib.cpython-312.so`
  debe mostrar `NEEDED libpython3.12.so`.

### Opción B: subir a Python 3.13+
- 3.13+ ya enlaza extensiones contra libpython por defecto (fix upstream).
- PERO rompe `ffpyplayer 4.5.1` (Cython viejo) y el resto de trampas
  documentadas en `AGENTS.md` (§3). Solo si se acepta cambiar ffpyplayer o
  parchearlo.

### Opción C: fijar la versión de p4a que funcionaba (v1.7.0)
- El workflow pinnea `buildozer` (y con él la p4a) a la versión que generó
  los APKs de v1.7.0 que sí arrancaban. Requiere saber qué versión era.

### Opción D (parche de emergencia, NO recomendada para release)
- Reparar `DT_NEEDED` de cada `*.so` de `_python_bundle/modules/` y
  `site-packages/` con `patchelf --add-needed libpython3.12.so` y reempaquetar
  el APK. Frágil, no sobrevive reinstalación limpia, y Android necesita que
  `libpython3.12.so` resuelva (que ya está cargada, por lo que podría valer).

## 9. COSAS QUE NO REVISAR YA (descartadas)

- **stdlib.zip**: válido, encodings completo, magic correcto.
- **zlib faltante en x86_64**: es el bug p4a #2460 (otra arquitectura); aquí el
  `zlib.so` EXISTE en las 4 archs, el problema es el enlazado.
- **SELinux**: los audits muestran `granted { execute }` para zlib; no es
  bloqueo de ejecución.
- **código Python / Kivy / ffpyplayer**: nunca llegan a ejecutarse.

## 10. DATOS ÚTILES (paths y comandos del entorno)

- adb: `C:\Windows\adb.exe` (o `C:\adb\adb.exe`). `adb devices` puede colgarse;
  si ocurre: `taskkill /F /IM adb.exe` y reintentar.
- Ver log: `adb logcat -d | findstr "python zlib init_fs"` (stderr de Python NO
  va a logcat por defecto; hay que usar el intérprete embebido o wrapper root).
- Leer archivos internos de la app (debug):
  ```
  adb shell run-as org.jonayo.jonayodownloader cat files/logs/app.log
  adb shell run-as org.jonayo.jonayodownloader cat files/logs/crash.txt
  ```
- El intérprete embebido para repro:
  ```
  adb shell run-as org.jonayo.jonayodownloader ./files/app/.bin/python --version
  ```
  (necesita `LD_LIBRARY_PATH` con el dir `lib/arm64` del APK y
  `PYTHONHOME`/`PYTHONPATH` al bundle; ver §6).
- `run-as` con `sh -c` arranca en cwd distinto; usar `run-as <pkg> <cmd>` con
  rutas relativas al app dir para escribir archivos.
- **Recordatorio**: se modificó `files/app/p4a_env_vars.txt` del teléfono
  (se añadieron `PYTHONVERBOSE=1` y `PYTHONUNBUFFERED=1` para diagnóstico).
  **Restaurarlo** a las 4 líneas originales:
  ```
  P4A_IS_WINDOWED=True
  KIVY_ORIENTATION=Portrait
  P4A_NUMERIC_VERSION=None
  P4A_MINSDK=24
  ```
- Se dejaron en el app dir los archivos de diagnóstico:
  `files/runpy.sh`, `files/pytest.py`, `files/pyout.txt` — se pueden borrar.