[app]
title = J Youtube Downloader
package.name = jonayodownloader
package.domain = org.jonayo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.8.9
version.release = 1

# Requisitos. ffmpeg se compila desde la recipe local (6.1.2) de python-for-android
# python3/hostpython3 pineados a 3.12.14 OBLIGATORIO: ffpyplayer 4.5.1 trae
# pic.c generado con Cython viejo que NO compila contra headers de Python 3.13+
# (_PyLong_AsByteArray 6 args, _PyGen_SetStopIterationValue eliminado); el build
# "3.14.2 OK" del 08-15 NO compilaba ffpyplayer como recipe (solo arm64 y sin
# ffpyplayer en requirements). En 3.12 hay que parchear grp (gh-114875) -> recipe
# local recipes/python3, y el ensurepip bundlea pip 25.0.1 roto -> recipe local
# recipes/hostpython3 sustituye la wheel bundleada por 26.2.1 (venv multi-arch
# idempotente). ffpyplayer 4.5.1 es incompatible con ffmpeg 7/8.
requirements = python3==3.12.14,hostpython3==3.12.14,kivy==2.3.1,yt-dlp,ffmpeg,requests,certifi,openssl,ffpyplayer

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,REQUEST_INSTALL_PACKAGES
android.api = 33
# minapi 24 (Android 7.0) OBLIGATORIO: el target NDK de las libs nativas es = minapi,
# y bionic solo declara getgrent/setgrent/endgrent desde API 24. Con 21, el modulo grp
# de python3 3.12 (CPython bug gh-114875, arreglado solo en 3.13) falla al compilar.
android.minapi = 24
android.allow_backup = True
android.build_tools_version = 33.0.0

# APK universal: las 4 arquitecturas para funcionar en cualquier Android
# (ARM 64-bit, ARM 32-bit, x86 64-bit y x86 32-bit). OJO: multiplica el tiempo de build.
# IMPORTANTE: separadas por COMA (buildozer 1.5 getlist divide solo por comas; con
# espacios pasa un solo valor con espacios y p4a falla por storage-dir con espacios).
android.archs = arm64-v8a,armeabi-v7a,x86_64,x86

# NDK 28c: soporta tamaños de página de 16 KB de Android 15+ (r25b crasheaba al arrancar)
android.ndk = 28c
android.sdk = 33

presplash.filename = presplash.png
icon.filename = icon.png

android.enable_androidx = True

# Firma release: buildozer hace override de cada token si existe la env var
# APP_ANDROID_KEYSTORE / APP_ANDROID_KEYALIAS / APP_ANDROID_STOREPASS / APP_ANDROID_KEYPASS,
# que el workflow setea con los secretos. Estos valores son solo defaults locales.
android.signing = True
android.keystore = release.keystore
android.keyalias = jonayodownloader
android.storepass = changeit
android.keypass = changeit
android.release_artifact = apk
p4a.release_artifact = jonayodownloader-release.apk

# Recipes locales: ffmpeg 6.1.2 (openssl fix en configure), ffpyplayer
# (setup.py.patch), python3 (patch grp) y hostpython3 (swap wheel pip bundleada).
# ffmpeg 7/8 rompen la API que usa ffpyplayer 4.5.1, por eso se pinnea 6.1.2.
p4a.local_recipes = ./recipes

[buildozer]
log_level = 2
warn_on_root = 1
