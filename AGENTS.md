# GUÍA — CÓMO SE CREAN LOS APK (MEMORIA DEL PROYECTO)

> **IMPORTANTE PARA CUALQUIER SESIÓN FUTURA:** Este documento registra TODO lo que
> descubrimos para lograr que la app compile y funcione en Android. Léelo SIEMPRE
> antes de tocar el proyecto. Nunca olvidar el fix de la pantalla negra ni el flujo
> completo de build/release.

---

## 1. ARQUITECTURA Y REPOS DE GITHUB

| Repo | Qué es |
|---|---|
| `Jonayo/jonayodownloader-android` | Código fuente (este proyecto). Los builds CI viven aquí. |
| `Jonayo/jonayodownloader-apk` | Repo de **Releases/APKs**. Ahí se suben los APK compilados. |

- Flujo normal: **push a `main`** → GitHub Actions compila 2 builds en paralelo
  (debug + release) → descargar artefactos → subir APK al release en `jonayodownloader-apk`.
- El APK compilado es **universal**: `android.archs = arm64-v8a armeabi-v7a x86_64 x86`
  (las 4 arquitecturas). Funciona en cualquier Android (ARM 64/32 y x86 64/32).
  OJO: multiplica el tiempo de build; los workflows tienen `timeout-minutes: 360`.

### Rutas locales del PC del usuario
- Repo local: `E:\ESCRITORIO 19 julio 2026\ESCRITORIO 7\youtube-android`
- Backups en Desktop: `C:\Users\Jonayo\Desktop\` (`BACK UP 2 J Downloader.zip`, etc.)
- Proyectos que manda ChatGPT: `C:\Users\Jonayo\Desktop\Jonayo_YT_Downloader_vX.Y.Z_*\youtube-android`
- APK descargados (temp): `C:\Users\Jonayo\AppData\Local\Temp\opencode\apk_*\`

---

## 2. ⚠️ EL FIX DE LA PANTALLA NEGRA (LO MÁS IMPORTANTE)

**Síntoma:** la app arrancaba sin crash, el log decía `M() construido OK` y todas las
pantallas "creadas OK", PERO en pantalla solo se veía el color de fondo BG `(8,13,18)`
(89% del screenshot) — ningún widget se dibujaba. La ventana SDL era 720x1436
(nativa), o sea el tamaño/config NO era el problema.

**Causa raíz:** construir TODAS las pantallas dentro de `build()`/`__init__` antes
del primer frame dejaba la UI sin pintar.

**El FIX (no romperlo nunca):**
1. En `M.__init__` (o `build()`) SOLO se crea la pantalla `Home`:
   ```python
   self.add_widget(Home(name='home'))
   self._setup_done = False
   Clock.schedule_once(lambda dt: self._finish_setup(), 0.05)
   ```
2. El resto de pantallas se crean 50 ms DESPUÉS del primer frame:
   ```python
   def _finish_setup(self):
       if self._setup_done: return
       self._setup_done = True
       for cls, name in [(Search,'search'), (Options,'options'), (Analyze,'analyze'),
                         (Downloading,'downloading'), (Downloads,'downloads'),
                         (Settings,'settings')]:
           self.add_widget(cls(name=name))
       self._load_trending()
   ```
3. Usar SIEMPRE `add_widget(...)` para añadir pantallas (NO `children=[...]`).
4. El primer frame debe pintarse inmediatamente; el resto se va añadiendo después.

**Cómo se diagnosticó:** con adb (ver sección 6). Esto superó al intento previo de
arreglarlo vía `Config.set('graphics', ...)` — ese fix SÍ estaba activo (ventana
720x1436) y NO resolvía el negro. El diferido de pantallas fue el que lo arregló.

---

## 3. buildozer.spec — CLAVES QUE NO SE PUEDEN QUITAR

```ini
version = 1.7.0            # DEBE coincidir con updater.py VERSION
version.release = 1
requirements = python3==3.12.14,hostpython3==3.12.14,kivy==2.3.1,yt-dlp,ffmpeg,requests,ffpyplayer
orientation = portrait
android.permissions = INTERNET     # SOLO INTERNET (permisos mínimos → menos alertas)
android.api = 33
android.minapi = 24             # margen de seguridad (default NDK = minapi); grp se
                                # arregla con el patch local recipes/python3 (abajo)
android.build_tools_version = 33.0.0
android.archs = arm64-v8a,armeabi-v7a,x86_64,x86
android.ndk = 28c                  # soporta páginas de 16 KB de Android 15+ (r25b crasheaba)
android.sdk = 33
android.enable_androidx = True

# FIRMA RELEASE — ESTAS 5 LÍNEAS SON OBLIGATORIAS
android.signing = True
android.keystore = release.keystore
android.keyalias = jonayodownloader
android.storepass = changeit
android.keypass = changeit
android.release_artifact = apk
p4a.release_artifact = jonayodownloader-release.apk
```

**TRAMPAS YA VISTAS:**
- Un "proyecto arreglado" de ChatGPT quitó las líneas del keystore → el release
  firmado fallaba. Hay que restaurarlas SIEMPRE.
- `source.include_exts = py,png,jpg,kv,atlas,ttf` → incluye los PNG de assets/.
- ffmpeg: el workflow fija `URL_ffmpeg` (tarball de FFmpeg n6.1.2) — es necesario
  para que yt-dlp convierta formatos. ffpyplayer 4.5.1 es incompatible con ffmpeg
  7/8 (usa APIs eliminadas como av_get_channel_layout_* y av_init_packet), por eso
  se pinnea 6.1.2. También se pinnea python3/hostpython3 a **3.12.14** (OBLIGATORIO:
  ffpyplayer 4.5.1 trae `pic.c` generado con Cython viejo que NO compila contra
  headers de Python 3.13+ — `_PyLong_AsByteArray` pasó a 6 args y
  `_PyGen_SetStopIterationValue` se eliminó. El build "3.14.2 OK" del 08-15 era
  arm64-only y SIN ffpyplayer como recipe).
- ffmpeg 6.1.2: la recipe local (`recipes/ffmpeg`) aplica `configure.patch` que
  neutraliza el check de openssl en configure (no hay pkg-config en Android).
  Además pasa `--disable-vulkan`: `libavcodec/vulkan_av1.c` de 6.1.2 no compila
  con los headers Vulkan de NDK r26+ (VkVideoSessionParametersKHR cambió de
  puntero a handle → `-Wint-conversion`). Vulkan no se usa en la app.
- `android.archs` con varias arquitecturas DEBE ir separado por comas
  (`arm64-v8a,armeabi-v7a,x86_64,x86`). Con espacios, buildozer 1.5 getlist
  devuelve un solo valor con espacios y p4a falla con
  "storage dir path cannot contain spaces".
- **grp (CPython gh-114875) — resuelto con patch local (3.12):** con 3.12, el
  módulo `grp` rompía el build en TODAS las arquitecturas (el configure de 3.12 solo
  comprueba `getgrgid`/`getgrgid_r`, pero `grpmodule.c` llama a `setgrent`/`getgrent`/
  `endgrent`, que bionic NO declara → `-Werror=implicit-function-declaration`). El fix
  upstream llegó en 3.13+, así que con 3.12.14 hay que aplicar el patch local
  `recipes/python3/patches/grp-disable.patch` (cambia el check del configure a
  `getgrent` + getgrgid). La recipe local `recipes/python3/__init__.py` además
  ENRUTA los patches base de p4a contra `pythonforandroid.recipes.python3.__file__`
  (porque p4a resuelve los patches relativos al dir de la recipe local, y los
  base no existen ahí). Si se subiera a 3.13+ se podría quitar.
- **TRAMPA pip en builds multi-arch (resuelta con recipe hostpython3):** el build
  apk-universal de 4 archs fallaba en el stage final `Installing pure Python
  modules` con
  `ImportError: cannot import name 'open_rich_spinner' from 'pip._internal.cli.spinners'`.
  Causa: `run_pymodules_install` de p4a master se ejecuta UNA VEZ POR ARQUITECTURA y
  cada vez hace `python -m venv venv` (sin `--clear`) + `pip install -U pip`. Con
  python 3.12.14, el ensurepip bundleaba pip **25.0.1** (release ROTA de pip: le falta
  `open_rich_spinner`); en el 2º arch el venv re-creado reinstalaba la wheel bundleada
  (25.0.1) ENCIMA del 26.2.1 ya instalado → mezcla rota → pip no importa. La recipe
  local `recipes/hostpython3/__init__.py` SUSTITUYE la wheel bundleada del ensurepip
  por pip 26.2.1 (`pip download pip==26.2.1` dentro de `build_arch`, tras el build
  del hostpython) Y actualiza `_PIP_VERSION` en el `Lib/ensurepip/__init__.py`
  instalado (ensurepip construye el nombre de wheel como `pip-{_PIP_VERSION}-py3-
  none-any.whl` con la versión hardcodeada: si solo cambias la wheel, el venv busca
  la pip-25.0.1 vieja y `venv/bin/python -m ensurepip --upgrade` falla con non-zero,
  como en el run 32063881113). Con ambas cosas, el venv siempre nace con pip sano,
  `pip install -U pip` es no-op y el re-run es idempotente en los 4 archs. NO subir
  a 3.13/3.14 para esquivar esto: ffpyplayer rompe (ver arriba).

---

## 4. updater.py — VERSIÓN CONSISTENTE

```python
VERSION = "1.7.0"          # DEBE ser igual que `version` en buildozer.spec
API_URL = "https://api.github.com/repos/Jonayo/jonayodownloader-apk/releases/latest"
```

La app compara `VERSION` contra la última release en `jonayodownloader-apk`.
**Si `VERSION` queda desactualizado** (ej. "1.4.0" mientras el spec es 1.7.0), la
app instalada pensará que está vieja y pedirá actualizarse siempre. Verificar ambos
antes de subir.

---

## 5. WORKFLOWS (GitHub Actions)

Dos workflows, ambos se disparan con `push` a `main`:
- `build-apk.yml` → **Build APK** (release firmado). Añade el paso de firmar
  usando secretos:
  - `secrets.RELEASE_KEYSTORE_B64` (base64 del keystore) → `release.keystore`
  - `secrets.RELEASE_KEY_ALIAS`
  - `secrets.RELEASE_STORE_PASS`
  - Env vars: `APP_ANDROID_*` y `P4A_RELEASE_*`
- `build-debug.yml` → **Build Debug APK** (solo para probar; artefacto `apk-debug`).

**Secretos configurados en GitHub** (repo `jonayodownloader-android` → Settings →
Secrets): `RELEASE_KEYSTORE_B64`, `RELEASE_KEY_ALIAS`, `RELEASE_STORE_PASS`.
No guardar el keystore en el repo de código (`.gitignore` tiene `*.keystore`).

---

## 6. COMANDOS ÚTILES (rutas completas — el PATH del PC es limitado)

```bat
REM git
"C:\Program Files\Git\cmd\git.exe" status / add -A / commit -m "..." / push

REM GitHub CLI
"C:\Users\Jonayo\gh\bin\gh.exe" run list --repo Jonayo/jonayodownloader-android --limit 2
"C:\Users\Jonayo\gh\bin\gh.exe" run download <RUN_ID> --repo Jonayo/jonayodownloader-android --name apk --dir "C:\Users\Jonayo\AppData\Local\Temp\opencode\apk_xxx"
"C:\Users\Jonayo\gh\bin\gh.exe" release create v1.7.0 --repo Jonayo/jonayodownloader-apk --title "v1.7.0" --notes "..."
"C:\Users\Jonayo\gh\bin\gh.exe" release upload v1.7.0 --repo Jonayo/jonayodownloader-apk --clobber "<apk>"

REM Python (py_compile para validar sintaxis)
"C:\Users\Jonayo\AppData\Local\Programs\Python\Python312\python.exe" -m py_compile main.py crashlog.py updater.py

REM adb
"C:\Users\Jonayo\AppData\Local\Android\Sdk\platform-tools\adb.exe" devices
REM Si adb se cuelga: cerrar adb.exe (taskkill) antes de `adb devices`
```

---

## 7. DEBUG EN EL TELÉFONO (adb)

- Dispositivo: Blade 10 Power (`BLADE10PO0000005288`, Android 14, Doogee).
- Paquete: `org.jonayo.jonayodownloader` (domain `org.jonayo`, name `jonayodownloader`).
- Logs de la app (archivos internos):
  ```bat
  adb shell run-as org.jonayo.jonayodownloader cat files/logs/app.log
  adb shell run-as org.jonayo.jonayodownloader cat files/logs/crash.txt
  ```
- Screenshot para analizar pantalla negra:
  ```bat
  adb exec-out screencap -p > screen.png
  ```
- El app.log registra pasos: `=== Inicio main.py ===`, imports, `M() construido OK`,
  `Creando pantalla X...`, `Pantalla X creada OK`.

**Play Protect:** un APK sideloaded siempre dirá "aplicación no certificada".
Con permisos `INTERNET` SOLO se evita la alerta de "roba datos" (no hay
permisos de almacenamiento porque se usa `getExternalFilesDir(None)`, que no
necesita permisos). La única forma de quitar "no certificada" del todo es publicar
en Play Console.

---

## 8. FLUJO COMPLETO PARA SACAR UNA VERSIÓN NUEVA

1. Editar `main.py` / `crashlog.py` / `updater.py` / `buildozer.spec`.
2. **Consistencia de versión:** `buildozer.spec` `version` == `updater.py` `VERSION`.
3. Validar sintaxis: `python -m py_compile main.py crashlog.py updater.py`.
4. `git add -A && git commit -m "vX.Y.Z descripción" && git push`.
5. Ver builds CI (`gh run list`). Los dos se disparan solos; tardan ~18-22 min.
6. Al terminar, descargar artefacto release: `gh run download <RUN_ID> --name apk`.
7. Crear/actualizar release en `jonayodownloader-apk`:
   `gh release create vX.Y.Z --repo Jonayo/jonayodownloader-apk --title "vX.Y.Z" --notes "..."`
   (si ya existe, usar `--notes` con cuidado o editar el release).
8. Subir ambos APK con `--clobber`:
   - `jonayodownloader-<v>-arm64-v8a-release.apk` (firmado, para el usuario)
   - `jonayodownloader-<v>-arm64-v8a-debug.apk` (de prueba)
9. Link de descarga directa:
   `https://github.com/Jonayo/jonayodownloader-apk/releases/download/vX.Y.Z/<archivo>.apk`
10. El usuario desinstala la versión previa, instala la nueva y prueba.

---

## 9. CONSEJOS PARA CUALQUIER "PROYECTO ARREGLADO" QUE MANDE CHATGPT

Antes de copiarlo al repo, comprobar SIEMPRE:
- [ ] `updater.py` `VERSION` coincide con el spec.
- [ ] `buildozer.spec` conserva las 5 líneas de firma del keystore (sección 3).
- [ ] El arranque diferido (`Clock.schedule_once(lambda dt: self._finish_setup(), 0.05)`)
      sigue presente (sección 2) — NO revertirlo a crear todo en `build()`.
- [ ] `crashlog.py` no cambió respecto al que funciona.
- [ ] Assets nuevos (ej. `assets/icons/*.png`) se copiaron enteros al repo.
- [ ] Los workflows de `.github/workflows/` no se rompieron.
- [ ] Compila: `python -m py_compile main.py crashlog.py updater.py`.