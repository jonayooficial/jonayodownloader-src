import os
import threading

VERSION = "2.0.45"
API_URL = "https://api.github.com/repos/Jonayo/jonayodownloader-apk/releases/latest"
DL_URL = "https://github.com/Jonayo/jonayodownloader-apk/releases/latest"
_last_error = ""


def _cmp_versions(a, b):
    def _parts(v):
        return [int(x) for x in str(v).strip().lstrip('v').split('.')]
    pa, pb = _parts(a), _parts(b)
    return (pa > pb) - (pa < pb)


def _fetch_json(url, timeout=15):
    import requests
    import certifi
    import time as _t
    last_err = None
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=timeout,
                                headers={"User-Agent": "Mozilla/5.0"},
                                verify=certifi.where())
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            if attempt < 2:
                _t.sleep(1)
    raise last_err


def _asset_url(data):
    """Devuelve la URL directa del APK de release (nunca debug)."""
    assets = data.get("assets") or []
    best = ""
    for a in assets:
        name = str(a.get("name", ""))
        if name.endswith(".apk") and "debug" not in name:
            return a.get("browser_download_url") or ""
    for a in assets:
        name = str(a.get("name", ""))
        if name.endswith(".apk"):
            return a.get("browser_download_url") or ""
    return best


def get_latest_version():
    """Devuelve dict con version, notas, url y apk_url; None si falla o no hay tag.
    Guarda el motivo del fallo en _last_error para mostrarlo al usuario."""
    global _last_error
    _last_error = ""
    try:
        data = _fetch_json(API_URL)
        tag = str(data.get("tag_name", "")).strip().lstrip('v')
        notes = data.get("body", "") or ""
        if not tag:
            _last_error = "El servidor no reporto ninguna version."
            return None
        return {
            "version": tag,
            "current": VERSION,
            "notes": notes,
            "url": DL_URL,
            "apk_url": _asset_url(data),
        }
    except Exception as e:
        msg = str(e)
        if '403' in msg or 'rate limit' in msg.lower():
            _last_error = "Limite de consultas alcanzado. Proba de nuevo en unos minutos."
        elif 'name or service not known' in msg.lower() or 'connection' in msg.lower() or 'timed out' in msg.lower():
            _last_error = "Sin conexion a internet."
        else:
            _last_error = "No se pudo verificar: " + msg[:100]
        return None


def updater_error():
    """Ultimo error de get_latest_version ('' si no hubo)."""
    return _last_error


def download_apk(apk_url, dest, on_progress=None):
    """Descarga el APK a dest con reintento y soporte de resume."""
    import requests
    import certifi
    import time as _t
    max_retries = 5
    for attempt in range(max_retries):
        done = 0
        if attempt > 0:
            try:
                done = os.path.getsize(dest) if os.path.exists(dest) else 0
            except Exception:
                done = 0
            _t.sleep(2 * attempt)
        headers = {"User-Agent": "Mozilla/5.0"}
        if done > 0:
            headers["Range"] = f"bytes={done}-"
        try:
            with requests.get(apk_url, timeout=120, stream=True,
                              headers=headers,
                              verify=certifi.where()) as r:
                if done > 0 and r.status_code == 206:
                    pass
                else:
                    if done > 0:
                        done = 0
                    r.raise_for_status()
                total = int(r.headers.get("Content-Length") or 0)
                if done > 0 and r.status_code == 206:
                    total += done
                mode = "ab" if done > 0 and r.status_code == 206 else "wb"
                with open(dest, mode) as f:
                    for chunk in r.iter_content(chunk_size=1 << 18):
                        if not chunk:
                            continue
                        f.write(chunk)
                        done += len(chunk)
                        if on_progress and total:
                            try:
                                on_progress(done, total)
                            except Exception:
                                pass
            return dest
        except Exception:
            if attempt == max_retries - 1:
                raise
    return dest


def check_for_update(on_result):
    def _run():
        try:
            update = get_latest_version()
            if update and _cmp_versions(update["version"], VERSION) > 0:
                try:
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: on_result(update))
                except Exception:
                    pass
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()