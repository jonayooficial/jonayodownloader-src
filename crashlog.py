import os
import sys
import shutil
import threading
import traceback


def _external_dir():
    """Carpeta accesible de la app (Android/data/.../files), visible en el
    explorador de archivos del teléfono. Se usa además de la interna para
    poder leer los logs sin USB/root."""
    try:
        if os.environ.get("ANDROID_ARGUMENT"):
            from android import mActivity
            f = mActivity.getExternalFilesDir(None)
            if f is not None:
                return f.getAbsolutePath()
    except Exception:
        pass
    return None


def app_data_dir():
    """Directorio de datos de la app (memoria interna)."""
    try:
        if os.environ.get("ANDROID_ARGUMENT"):
            from android import mActivity
            return mActivity.getFilesDir().getAbsolutePath()
    except Exception:
        pass
    return os.path.dirname(os.path.abspath(__file__))


def _write_file(path, text):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def log_dir():
    d = os.path.join(app_data_dir(), "logs")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        d = app_data_dir()
    return d


def log_file():
    return os.path.join(log_dir(), "app.log")


def crash_file():
    return os.path.join(log_dir(), "crash.txt")


def _all_log_dirs():
    dirs = [log_dir()]
    ext = _external_dir()
    if ext:
        try:
            d = os.path.join(ext, "logs")
            os.makedirs(d, exist_ok=True)
            dirs.append(d)
        except Exception:
            pass
    return dirs


def _read_log_content():
    try:
        p = log_file()
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    return ""


def _write_public_logs(content, filename):
    """Escribe en la carpeta pública Descargas/JONAYO_LOGS del teléfono
    (visible en el explorador de archivos, sin root ni permisos especiales).
    En Android 10+ se usa MediaStore (busca el archivo existente y lo
    sobrescribe, para no crear duplicados); en versiones viejas escribe directo."""
    try:
        if not os.environ.get("ANDROID_ARGUMENT"):
            return False
        from jnius import autoclass
        MediaStore = autoclass("android.provider.MediaStore$Downloads")
        ContentValues = autoclass("android.content.ContentValues")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        resolver = PythonActivity.mActivity.getContentResolver()

        rel = "Download/JONAYO_LOGS"
        selection = "_display_name=? AND relative_path=?"
        sel_args = [filename, rel + "/"]

        item_uri = None
        cursor = resolver.query(MediaStore.EXTERNAL_CONTENT_URI, None,
                                selection, sel_args, None)
        if cursor is not None and cursor.getCount() > 0:
            cursor.moveToFirst()
            id_col = cursor.getColumnIndex("_id")
            if id_col >= 0:
                _id = cursor.getLong(id_col)
                item_uri = Uri.withAppendedPath(MediaStore.EXTERNAL_CONTENT_URI,
                                                str(_id))
        if cursor is not None:
            cursor.close()

        if item_uri is None:
            values = ContentValues()
            values.put("_display_name", filename)
            values.put("mime_type", "text/plain")
            values.put("relative_path", rel)
            item_uri = resolver.insert(MediaStore.EXTERNAL_CONTENT_URI, values)
            if item_uri is None:
                return False
        out = resolver.openOutputStream(item_uri, "w")
        if out is None:
            return False
        out.write(content.encode("utf-8"))
        out.close()
        return True
    except Exception:
        pass

    # Fallback para Android 9 o menos: escritura directa en Descargas
    try:
        from jnius import autoclass
        Environment = autoclass("android.os.Environment")
        dl = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        folder = os.path.join(dl, "JONAYO_LOGS")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def write_log(text):
    # Mantener el log en almacenamiento de la app es barato y seguro.
    # No escribimos a MediaStore en cada linea: eso puede bloquear/ralentizar
    # el arranque y no es necesario para el funcionamiento normal.
    for d in _all_log_dirs():
        try:
            p = os.path.join(d, "app.log")
            with open(p, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass


def write_crash(text):
    for d in _all_log_dirs():
        try:
            p = os.path.join(d, "crash.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
    # El volcado público se hace solo al ocurrir un crash.
    _write_public_logs(text, "crash.txt")


def read_crash():
    for d in _all_log_dirs():
        try:
            p = os.path.join(d, "crash.txt")
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    txt = f.read().strip()
                if txt:
                    return txt
        except Exception:
            continue
    return ""


def clear_crash():
    for d in _all_log_dirs():
        try:
            p = os.path.join(d, "crash.txt")
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def _dump_to_file(etype=None, value=None, tb=None):
    try:
        if etype is None and sys.exc_info()[0] is not None:
            etype, value, tb = sys.exc_info()
        if etype is not None and value is not None:
            lines = traceback.format_exception(etype, value, tb)
            tb = "".join(lines)
        else:
            tb = "NoneType: None"
    except Exception:
        tb = "NoneType: None"
    text = "Versión: J Youtube Downloader v2.0.44\n\n" + tb
    write_crash(text)
    write_log("CRASH:\n" + tb)
    try:
        import sys as _sys
        _sys.stderr.write("CRASH:\n" + tb + "\n")
        _sys.stderr.flush()
    except Exception:
        pass


def _thread_hook(args):
    try:
        tb = "".join(traceback.format_exception(args.exc_type, args.exc_value,
                                                args.exc_traceback))
        write_crash("Versión: J Youtube Downloader v2.0.44\n\n" + tb)
        write_log("CRASH:\n" + tb)
    except Exception:
        try:
            threading.excepthook(args)
        except Exception:
            pass
        _dump_to_file()


def install_crash_handler():
    """Guarda cualquier excepción (principal o thread) en crash.txt."""
    sys.excepthook = _dump_to_file
    threading.excepthook = _thread_hook

    try:
        from kivy.base import ExceptionHandler, ExceptionManager

        class KivyCrashHandler(ExceptionHandler):
            def handle_exception(self, inst):
                try:
                    if inst is None and sys.exc_info()[0] is not None:
                        etype, value, tb = sys.exc_info()
                    else:
                        etype, value, tb = (type(inst), inst, getattr(inst, "__traceback__", None))
                    if etype is None or value is None:
                        _dump_to_file()
                    else:
                        lines = traceback.format_exception(etype, value, tb)
                        tb_text = "".join(lines)
                        text = "Versión: J Youtube Downloader v2.0.44\n\n" + tb_text
                        write_crash(text)
                        write_log("CRASH:\n" + tb_text)
                        try:
                            import sys as _sys
                            _sys.stderr.write("CRASH:\n" + tb_text + "\n")
                            _sys.stderr.flush()
                        except Exception:
                            pass
                except Exception:
                    _dump_to_file()
                return ExceptionManager.RAISE

        ExceptionManager.add_handler(KivyCrashHandler())
    except Exception:
        pass


def export_logs():
    """Copia logs a la carpeta pública de descargas (si se puede)."""
    try:
        src = log_dir()
        if os.environ.get("ANDROID_ARGUMENT"):
            from android import mActivity
            external = mActivity.getExternalFilesDir(None)
            if external is not None:
                external = external.getAbsolutePath()
            else:
                external = app_data_dir()
            dst = os.path.join(external, "logs")
        else:
            dst = os.path.join(os.path.expanduser("~"), "Downloads", "Jonayo_logs")
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return dst
    except Exception:
        return ""