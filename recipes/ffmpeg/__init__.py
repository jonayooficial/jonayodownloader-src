from pythonforandroid.toolchain import Recipe, current_directory, shprint
from os.path import exists, join, realpath
import sh
from multiprocessing import cpu_count


class FFMpegRecipe(Recipe):
    # ffmpeg 6.1.2: ultima 6.x, la version probada con ffpyplayer 4.5.1
    # (ffmpeg 7/8 eliminaron APIs que ffpyplayer usa: channel_layout, key_frame, av_init_packet)
    version = 'n6.1.2'
    url = 'https://github.com/FFmpeg/FFmpeg/archive/{version}.zip'
    depends = ['sdl2', 'lame', 'openssl']  # HTTPS real + MP3
    opts_depends = ['openssl', 'ffpyplayer_codecs']
    patches = ['patches/configure.patch']
    _libs = [
        "libavcodec.so",
        "libavfilter.so",
        "libavutil.so",
        "libswscale.so",
        "libavdevice.so",
        "libavformat.so",
        "libswresample.so",
        "libffmpegbin.so",
    ]
    built_libraries = dict.fromkeys(_libs, "./lib")

    def should_build(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        return not exists(join(build_dir, 'lib', 'libavcodec.so'))

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['NDK'] = self.ctx.ndk_dir
        return env

    def build_arch(self, arch):
        with current_directory(self.get_build_dir(arch.arch)):
            env = arch.get_env()

            flags = ['--disable-everything']
            cflags = []
            ldflags = []

            if 'openssl' in self.ctx.recipe_build_order:
                flags += [
                    '--enable-version3',
                    '--enable-openssl',
                    '--enable-nonfree',
                    '--enable-protocol=https,tls_openssl',
                ]
                build_dir = Recipe.get_recipe(
                    'openssl', self.ctx).get_build_dir(arch.arch)
                cflags += ['-I' + build_dir + '/include/']
                ldflags += ['-L' + build_dir, '-lssl', '-lcrypto']

            # libmp3lame: encoder MP3 para el modo MP3 de la app
            # (ffmpeg no tiene encoder mp3 nativo; sin esto falla con
            # 'Unknown encoder mp3' al extraer audio a MP3).
            lame_dir = Recipe.get_recipe('lame', self.ctx).get_build_dir(arch.arch)
            cflags += ['-I' + join(lame_dir, 'include')]
            ldflags += ['-L' + join(lame_dir, 'lib'), '-lmp3lame']
            flags += [
                '--enable-libmp3lame',
                '--enable-encoder=libmp3lame,aac',
                '--enable-muxer=mp3,mp4',
            ]

            # Enable codecs only for .mp4:
            flags += [
                '--enable-parser=aac,ac3,h261,h264,mpegaudio,mpeg4video,mpegvideo,vc1',
                '--enable-decoder=aac,h264,mpeg4,mpegvideo,mp3,opus,vorbis,vp9',
                '--enable-muxer=h264,mov,mp4,mpeg2video',
                '--enable-demuxer=aac,h264,hls,http,m4v,matroska,mov,mpegvideo,vc1,rtsp',
            ]

            # needed to prevent _ffmpeg.so: version node not found for symbol av_init_packet@LIBAVFORMAT_52
            # /usr/bin/ld: failed to set dynamic section sizes: Bad value
            flags += [
                '--disable-symver',
            ]

            # disable doc
            flags += [
                '--disable-doc',
            ]

            # vulkan_av1.c de ffmpeg 6.1.2 rompe con los headers Vulkan de NDK
            # r26+ (VkVideoSessionParametersKHR pasó de puntero a handle ->
            # -Wint-conversion). Vulkan no se usa: se desactiva.
            flags += [
                '--disable-vulkan',
            ]

            # other flags:
            flags += [
                '--enable-filter=aresample,resample,crop,adelay,volume,scale',
                '--enable-network',
                '--enable-protocol=file,http,https,hls,udp,tcp,tls,tls_openssl',
                '--enable-small',
                '--enable-hwaccels',
                '--enable-pic',
                '--disable-static',
                '--disable-debug',
                '--enable-shared',
            ]

            if 'arm64' in arch.arch:
                arch_flag = 'aarch64'
            elif 'x86' in arch.arch:
                arch_flag = 'x86'
                flags += ['--disable-asm']
            else:
                arch_flag = 'arm'

            # android:
            flags += [
                '--target-os=android',
                '--enable-cross-compile',
                '--cross-prefix={}-'.format(arch.target),
                '--arch={}'.format(arch_flag),
                '--strip={}'.format(self.ctx.ndk.llvm_strip),
                '--sysroot={}'.format(self.ctx.ndk.sysroot),
                '--enable-neon',
                '--prefix={}'.format(realpath('.')),
            ]

            if arch_flag == 'arm':
                cflags += [
                    '-Wno-error=incompatible-pointer-types',
                    '-mfpu=vfpv3-d16',
                    '-mfloat-abi=softfp',
                    '-fPIC',
                ]

            env['CFLAGS'] += ' ' + ' '.join(cflags)
            env['LDFLAGS'] += ' ' + ' '.join(ldflags)

            configure = sh.Command('./configure')
            shprint(configure, *flags, _env=env)
            shprint(sh.make, '-j', f"{cpu_count()}", _env=env)
            shprint(sh.make, 'install', _env=env)
            shprint(sh.cp, "ffmpeg", "./lib/libffmpegbin.so")


recipe = FFMpegRecipe()
