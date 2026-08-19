import os

from pythonforandroid.recipes.python3 import Python3Recipe

import pythonforandroid.recipes.python3 as _builtin_python3

BUILTIN_PYTHON3_DIR = os.path.dirname(os.path.abspath(_builtin_python3.__file__))


class Python3RecipeNoGrp(Python3Recipe):
    # CPython gh-114875: el modulo grp se compila con solo tener getgrgid, pero
    # grpmodule.c usa la familia getgrent/setgrent/endgrent que bionic NO declara
    # en ningun nivel de API. El fix upstream llego solo a 3.13; con 3.12 (pin
    # impuesto por Cython 3.0.11) hay que excluir grp del configure generado.
    patches = Python3Recipe.patches + ['patches/grp-disable.patch']

    def apply_patch(self, filename, arch, build_dir=None):
        # p4a resuelve cada patch con join(get_recipe_dir(), filename). Al vivir
        # esta recipe en la carpeta local (p4a.local_recipes), los patches base
        # de p4a (pyconfig_detection, reproducible-buildinfo, cpython-311, etc.)
        # no existen ahi. Se resuelven contra el recipe dir del p4a instalado;
        # grp-disable.patch no existe alli y se queda relativo -> carpeta local.
        if not os.path.isabs(filename):
            builtin_path = os.path.join(BUILTIN_PYTHON3_DIR, filename)
            if os.path.isfile(builtin_path):
                filename = builtin_path
        super().apply_patch(filename, arch, build_dir)


recipe = Python3RecipeNoGrp()
