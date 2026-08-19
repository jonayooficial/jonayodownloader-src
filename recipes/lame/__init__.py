from pythonforandroid.toolchain import Recipe, current_directory, shprint
from os.path import exists, join, realpath
import sh
from multiprocessing import cpu_count


class LameRecipe(Recipe):
    """LAME (libmp3lame) estatico para que ffmpeg pueda codificar MP3.
    Sin libmp3lame, el modo MP3 de la app falla ('Unknown encoder mp3'):
    ffmpeg no trae encoder MP3 nativo, necesita libmp3lame."""
    version = '3.100'
    url = 'https://downloads.sourceforge.net/project/lame/lame/3.100/lame-3.100.tar.gz'
    depends = []
    built_libraries = {'libmp3lame.a': '.'}

    def should_build(self, arch):
        return not exists(join(self.get_build_dir(arch.arch), 'libmp3lame.a'))

    def build_arch(self, arch):
        with current_directory(self.get_build_dir(arch.arch)):
            env = arch.get_env()
            configure = sh.Command('./configure')
            shprint(configure,
                    '--host={}'.format(arch.target),
                    '--disable-shared',
                    '--enable-static',
                    '--disable-frontend',
                    '--disable-decoder',
                    '--disable-rpath',
                    '--prefix={}'.format(realpath('.')),
                    _env=env)
            shprint(sh.make, '-j', str(cpu_count()), _env=env)
            shprint(sh.make, 'install', _env=env)


recipe = LameRecipe()