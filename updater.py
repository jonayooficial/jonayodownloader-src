import os
import threading

VERSION = "1.9.8"
API_URL = "https://api.github.com/repos/jonayooficial/jonayodownloader-apk/releases/latest"
DL_URL = "https://github.com/jonayooficial/jonayodownloader-apk/releases/latest"


def _cmp_versions(a, b):
    def _parts(v):
        return [int(x) for x in str(v).strip().lstrip('v').split('.')]
    pa, pb = _parts(a), _parts(b)
    return (pa > pb) - (pa < pb)


def _fetch_json(url, timeout=15):
    import requests
    import certifi
    resp = requests.get(url, timeout=timeout,
                        headers={"User-Agent": "Mozilla/5.0"},
                        verify=certifi.where())
    resp.raise_for_status()
    return resp.json()


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
    """Devuelve dict con version, notas, url y apk_url; None si falla o no hay tag."""
    try:
        data = _fetch_json(API_URL)
        tag = str(data.get("tag_name", "")).strip().lstrip('v')
        notes = data.get("body", "") or ""
        if not tag:
            return None
        return {
            "version": tag,
            "current": VERSION,
            "notes": notes,
            "url": DL_URL,
            "apk_url": _asset_url(data),
        }
    except Exception:
        return None


def download_apk(apk_url, dest, on_progress=None):
    """Descarga el APK a dest en streaming. Lanza excepción si falla."""
    import requests
    import certifi
    with requests.get(apk_url, timeout=60, stream=True,
                      headers={"User-Agent": "Mozilla/5.0"},
                      verify=certifi.where()) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 15):
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