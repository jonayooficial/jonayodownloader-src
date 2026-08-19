import glob
import os
import re
import shutil
import tempfile

import sh

from pythonforandroid.logger import shprint
from pythonforandroid.recipes.hostpython3 import HostPython3Recipe
from pythonforandroid.util import BuildInterruptingException

import pythonforandroid.recipes.hostpython3 as _builtin_hostpython3

BUILTIN_HOSTPYTHON3_DIR = os.path.dirname(os.path.abspath(_builtin_hostpython3.__file__))

# El ensurepip de CPython 3.12.x bundlea una wheel rota de pip (25.0.1: la
# publicacion de pypa/pip#12953 sin open_rich_spinner en cli/spinners.py).
# build.py de p4a master re-crea el venv por arch SIN --clear y ademas hace
# `pip install -U pip`: ensurepip reinstala la wheel bundleada (25.0.1) SOBRE
# la ya actualizada (26.2.1) -> mezcla rota -> ImportError open_rich_spinner en
# el 2o arch. Sustituimos la wheel bundleada por una pip buena: el venv siempre
# instala pip==GOOD_PIP, `pip install -U pip` es no-op y el re-run queda
# idempotente en los 4 archs.
GOOD_PIP = "26.2.1"


class HostPython3RecipeNoBrokenPip(HostPython3Recipe):
    def apply_patch(self, filename, arch, build_dir=None):
        # fix_ensurepip.patch vive en la recipe del p4a instalado; al estar esta
        # recipe en la carpeta local (p4a.local_recipes), p4a la buscaria en
        # ./recipes/hostpython3 y no existe alli.
        if not os.path.isabs(filename):
            builtin_path = os.path.join(BUILTIN_HOSTPYTHON3_DIR, filename)
            if os.path.isfile(builtin_path):
                filename = builtin_path
        super().apply_patch(filename, arch, build_dir)

    def build_arch(self, arch):
        super().build_arch(arch)
        major, minor = self.version.split(".")[:2]
        lib_dir = os.path.join(
            self.site_root,
            "usr/local/lib/python{python}.{minor}".format(
                python=major, minor=minor
            ),
        )
        bundled_dir = os.path.join(lib_dir, "ensurepip/_bundled")
        if not os.path.isdir(bundled_dir):
            return
        for old in glob.glob(os.path.join(bundled_dir, "pip-*.whl")):
            os.unlink(old)
        tmpdir = tempfile.mkdtemp(prefix="pipbundle")
        try:
            shprint(
                sh.Command(self.python_exe),
                "-m",
                "pip",
                "download",
                "pip==" + GOOD_PIP,
                "--no-deps",
                "-d",
                tmpdir,
                _env={"HOME": "/tmp", "PATH": self.local_bin},
            )
            wheels = glob.glob(os.path.join(tmpdir, "pip-*.whl"))
            if not wheels:
                raise BuildInterruptingException(
                    "pip download for pip==%s produced no wheel" % GOOD_PIP
                )
            shprint(sh.cp, wheels[0], bundled_dir)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
        # ensurepip construye el nombre de wheel como pip-{_PIP_VERSION}-py3-none-any.whl
        # con _PIP_VERSION hardcodeado; sin actualizarlo busca la wheel vieja y falla.
        ensurepip_init = os.path.join(lib_dir, "ensurepip/__init__.py")
        if os.path.isfile(ensurepip_init):
            with open(ensurepip_init, "r", encoding="utf-8") as f:
                content = f.read()
            content = re.sub(
                r'_PIP_VERSION = "[^"]+"',
                '_PIP_VERSION = "%s"' % GOOD_PIP,
                content,
            )
            with open(ensurepip_init, "w", encoding="utf-8") as f:
                f.write(content)


recipe = HostPython3RecipeNoBrokenPip()