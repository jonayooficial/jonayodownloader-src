import os
from kivy.config import Config
if not os.environ.get("ANDROID_ARGUMENT"):
    Config.set('graphics', 'width', '420'); Config.set('graphics', 'height', '860'); Config.set('graphics', 'resizable', '1')

import crashlog
crashlog.install_crash_handler()
crashlog.write_log("=== Inicio main.py (fusionado) v1.8.9 ===")

import sys
import io
# Kivy/Android: sys.stdout.buffer es str -> rompe yt-dlp write_string
try:
    if hasattr(sys.stdout, 'buffer') and isinstance(getattr(sys.stdout, 'buffer', None), str):
        sys.stdout = io.StringIO()
    if hasattr(sys.stderr, 'buffer') and isinstance(getattr(sys.stderr, 'buffer', None), str):
        sys.stderr = io.StringIO()
except Exception:
    pass
import json
import time
import shutil
import threading
import traceback
import webbrowser

crashlog.write_log("imports stdlib OK")

from kivy import platform
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image, AsyncImage
from kivy.core.image import Image as CoreImage
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from kivy.uix.modalview import ModalView
Video = None

crashlog.write_log("imports kivy OK")

try:
    from updater import check_for_update
except Exception as _e:
    check_for_update = None
    crashlog.write_log("updater import FAILED: " + str(_e)[:200])

crashlog.write_log("imports updater OK")

IS_ANDROID = platform == "android"
if IS_ANDROID:
    crashlog.write_log("imports android OK")

# ─── UI MODERNA ─────────────────────────────────────────────────
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Triangle, Ellipse
from kivy.uix.floatlayout import FloatLayout

BG      = (0.04, 0.04, 0.04, 1)
NAV     = (0.08, 0.08, 0.08, 1)
SUR     = (0.11, 0.11, 0.11, 1)
SUR2    = (0.15, 0.15, 0.15, 1)
SUR3    = (0.20, 0.20, 0.20, 1)
RED     = (1.0, 0.18, 0.33, 1)
REDD    = (0.35, 0.06, 0.12, 1)
WHITE   = (1, 1, 1, 1)
MUTED   = (0.56, 0.56, 0.56, 1)
DIM     = (0.40, 0.44, 0.50, 1)
BORDER  = (0.12, 0.15, 0.19, 1)
GREEN   = (0.20, 0.82, 0.43, 1)
ORANGE  = (1.0, 0.65, 0.08, 1)
ERR     = (1.0, 0.28, 0.32, 1)
DORADO  = (1.0, 0.75, 0.10, 1)
APP_NAME = 'J Youtube Downloader'
APP_VERSION = '2.0.48'
LOGO = 'assets/logo.png'
ICONS = 'assets/icons/'
PICON = 'assets/icons/player/'


def icon(name):
    return os.path.join(ICONS, name + '.png')


def btn_img(btn, name, size=None):
    """Icono PNG centrado dentro de un boton; devuelve el Image para poder
    cambiar el source despues (play/pause, fs/fs_exit...).
    No usa pos_hint (no funciona en Button); centra manualmente."""
    size = size or dp(20)
    img = Image(source=PICON + name + '.png', size_hint=(None, None),
                size=(size, size), allow_stretch=True, keep_ratio=True)
    def _sync(*_):
        try:
            img.center = btn.center
        except Exception:
            pass
    btn.bind(pos=_sync, size=_sync)
    Clock.schedule_once(lambda dt: _sync(), 0)
    btn.add_widget(img)
    return img


def coin_bg(btn, size=None):
    """Fondo circular degradado para el play principal."""
    size = size or dp(38)
    img = Image(source=PICON + 'coin.png', size_hint=(None, None),
                size=(size, size), allow_stretch=True, keep_ratio=True)
    def _sync(*_):
        try:
            img.center = btn.center
        except Exception:
            pass
    btn.bind(pos=_sync, size=_sync)
    Clock.schedule_once(lambda dt: _sync(), 0)
    btn.add_widget(img)
    return img


def set_icon(img_widget, name):
    try:
        img_widget.source = PICON + name + '.png'
    except Exception:
        pass


def rr(w, c=SUR, r=16, border=None):
    with w.canvas.before:
        Color(*c)
        w._rr = RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(r)])
        if border:
            Color(*border)
            w._line = Line(rounded_rectangle=(w.x, w.y, w.width, w.height, dp(r)), width=1)
    def sync(*_):
        w._rr.pos = w.pos; w._rr.size = w.size
        if hasattr(w, '_line'):
            w._line.rounded_rectangle = (w.x, w.y, w.width, w.height, dp(r))
    w.bind(pos=sync, size=sync)
    return w


def draw_icon(w, kind, color=WHITE):
    """Iconos vectoriales para Android. Nunca depende de glifos/emojis de fuente."""
    import math
    specs = {
        'close': 2, 'fs': 8, 'music': 3, 'play': 3, 'pause': 2,
        'next': 4, 'prev': 4, 'queue': 5, 'speed': 2, 'quality': 4,
        'dl': 3, 'stop': 4,
    }
    if hasattr(w, '_icon_sync'):
        try:
            w.unbind(pos=w._icon_sync, size=w._icon_sync)
        except Exception:
            pass
    try:
        w.canvas.after.clear()
    except Exception:
        pass
    if kind == 'play':
        with w.canvas.after:
            Color(*color)
            w._icon_lines = [Triangle(points=[0, 0, 0, 0, 0, 0])]
    elif kind == 'pause':
        with w.canvas.after:
            Color(*color)
            w._icon_lines = [RoundedRectangle(pos=(0, 0), size=(1, 1), radius=[dp(1.5)])
                             for _ in range(2)]
    else:
        with w.canvas.after:
            Color(*color)
            w._icon_lines = [Line(points=[0, 0, 0, 0], width=dp(2.0))
                             for _ in range(specs.get(kind, 2))]

    def sync(*_):
        x, y, s, h = w.x, w.y, w.width, w.height
        L = getattr(w, '_icon_lines', [])
        if not L:
            return
        if kind == 'close':
            m = dp(7); L[0].points = [x+m,y+m,x+s-m,y+h-m]; L[1].points = [x+s-m,y+m,x+m,y+h-m]
        elif kind == 'fs':
            m=dp(5); l=dp(7)
            tl=(x+m,y+h-m); tr=(x+s-m,y+h-m); bl=(x+m,y+m); br=(x+s-m,y+m)
            pts=[(tl[0],tl[1],tl[0]+l,tl[1]),(tl[0],tl[1],tl[0],tl[1]-l),
                 (tr[0]-l,tr[1],tr[0],tr[1]),(tr[0],tr[1],tr[0],tr[1]-l),
                 (bl[0],bl[1],bl[0]+l,bl[1]),(bl[0],bl[1],bl[0],bl[1]+l),
                 (br[0]-l,br[1],br[0],br[1]),(br[0],br[1],br[0],br[1]+l)]
            for ln,p in zip(L,pts): ln.points=list(p)
        elif kind == 'play':
            L[0].points=[x+s*.32,y+h*.20, x+s*.32,y+h*.80, x+s*.78,y+h*.5]
        elif kind == 'pause':
            bw=s*.16; gap=s*.14; by=y+h*.20; bh=h*.60
            cx=x+s*.5
            L[0].pos=(cx-gap/2-bw, by); L[0].size=(bw, bh)
            L[1].pos=(cx+gap/2, by); L[1].size=(bw, bh)
        elif kind in ('next','prev'):
            if kind == 'next':
                L[0].points=[x+s*.28,y+h*.25,x+s*.28,y+h*.75]
                L[1].points=[x+s*.28,y+h*.25,x+s*.62,y+h*.5]
                L[2].points=[x+s*.62,y+h*.5,x+s*.28,y+h*.75]
                L[3].points=[x+s*.75,y+h*.25,x+s*.75,y+h*.75]
            else:
                L[0].points=[x+s*.72,y+h*.25,x+s*.72,y+h*.75]
                L[1].points=[x+s*.72,y+h*.25,x+s*.38,y+h*.5]
                L[2].points=[x+s*.38,y+h*.5,x+s*.72,y+h*.75]
                L[3].points=[x+s*.25,y+h*.25,x+s*.25,y+h*.75]
        elif kind == 'queue':
            for i,yy in enumerate((.30,.50,.70)):
                L[i].points=[x+s*.22,y+h*yy,x+s*.78,y+h*yy]
            L[3].points=[x+s*.22,y+h*.30,x+s*.22,y+h*.70]
            L[4].points=[x+s*.78,y+h*.30,x+s*.78,y+h*.70]
        elif kind == 'speed':
            pts=[]
            r=min(s,h)*.30; cx=x+s*.5; cy=y+h*.5
            for i in range(24):
                a=2*math.pi*i/24
                pts += [cx+r*math.cos(a), cy+r*math.sin(a)]
            L[0].points=pts
            L[1].points=[cx,cy,cx+r*.65,cy+r*.45]
        elif kind == 'quality':
            for i,ln in enumerate(L):
                yy=y+h*(.28+i*.22); x2=x+s*(.45+i*.12)
                ln.points=[x+s*.22,yy,x2,yy]
        elif kind == 'music':
            m=dp(5); cx=x+s*.34; cy=y+h*.68; r=dp(3.5)
            pts=[]
            for i in range(20):
                a=2*math.pi*i/20; pts += [cx+r*math.cos(a),cy+r*math.sin(a)]
            L[0].points=pts; L[1].points=[cx,cy-r,cx,y+h*.28]; L[2].points=[cx,y+h*.28,x+s*.55,y+h*.22]
        elif kind == 'dl':
            cx=x+s*.5
            L[0].points=[cx,y+h*.16,cx,y+h*.72]
            L[1].points=[cx,y+h*.72,x+s*.32,y+h*.40]
            L[2].points=[cx,y+h*.72,x+s*.68,y+h*.40]
        elif kind == 'stop':
            m=dp(7)
            L[0].points=[x+m,y+m,x+s-m,y+m]
            L[1].points=[x+s-m,y+m,x+s-m,y+h-m]
            L[2].points=[x+s-m,y+h-m,x+m,y+h-m]
            L[3].points=[x+m,y+h-m,x+m,y+m]
    w._icon_sync = sync
    w.bind(pos=sync, size=sync)
    sync()
    return w


class B(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down = ''
        if not kw.get('text', ''):
            self.font_size = 0
            self.color = (0, 0, 0, 0)
        self.background_color = (0, 0, 0, 0)
        self.color = kw.get('color', WHITE)
        self.font_size = kw.get('font_size', sp(13))
        self.bold = kw.get('bold', True)
        self.halign = kw.get('halign', 'center')
        self.valign = 'middle'
        self.text_size = (None, None)


class TouchBlockingFloatLayout(FloatLayout):
    """FloatLayout que consume todos los toques dentro de su area.

    El reproductor se agrega como capa encima de Window; sin esto, los toques
    sobre el video (donde no hay ningun boton) atraviesan la capa y abren el
    menu del elemento que esta detras. Al devolver siempre True se bloquea la
    propagacion hacia las tarjetas del fondo; los botones del reproductor
    siguen funcionando porque super() primero les reparte el toque.
    """
    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        return True


class PlayerOverlay:
    """Capa del reproductor a pantalla completa (reemplaza al ModalView).

    El ModalView NO se redimensionaba al girar la pantalla: tras pasar a
    horizontal, las barras/botones del reproductor quedaban en coordenadas
    viejas (o el video fuera de pantalla). Esta capa se agrega directo a
    Window, se fuerza a Window.size en cada relayout y se quita al cerrar.
    Mantiene la interfaz del ModalView (open/dismiss) para no tocar el resto.
    """
    def __init__(self, widget, relayout, on_close=None):
        self.widget = widget
        self.relayout = relayout
        self.on_close = on_close
        self._opened = False

    @property
    def window(self):
        return True if self._opened else None

    def open(self, *args):
        if self._opened:
            return
        from kivy.core.window import Window
        from kivy.clock import Clock
        self._opened = True
        Window.add_widget(self.widget)
        Window.bind(size=self.relayout)
        Clock.schedule_once(self.relayout, 0)
        Clock.schedule_once(self.relayout, 0.25)
        Clock.schedule_once(self.relayout, 0.6)

    def dismiss(self, *args):
        if not self._opened:
            return
        from kivy.core.window import Window
        self._opened = False
        try:
            Window.remove_widget(self.widget)
        except Exception:
            pass
        try:
            Window.unbind(size=self.relayout)
        except Exception:
            pass
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass


def safe_text(value, fallback=''):
    """Normaliza títulos de YouTube para evitar glifos rotos/cuadrados en Android."""
    import unicodedata
    text = str(value or fallback)
    text = unicodedata.normalize('NFKC', text)
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith('C') and ch not in '\n\t':
            continue
        # Eliminar símbolos/emojis que suelen no existir en la fuente Android empaquetada.
        if cat in ('So', 'Sk'):
            continue
        out.append(ch)
    text = ''.join(out).strip()
    return text or fallback


class ClickableBox(ButtonBehavior, BoxLayout):
    """Contenedor táctil real; evita usar Button como padre de layouts complejos."""
    def __init__(self, bg=SUR2, radius=16, border=BORDER, **kw):
        super().__init__(**kw)
        rr(self, bg, radius, border)
        self._pressed = False


class SeekBar(Widget):
    """Barra de progreso estilo profesional: track fino, relleno degradado y
    knob pequeno. Reemplaza al Slider nativo de Kivy (knob gigante azul)."""
    def __init__(self, on_seek=None, height_bar=None, **kw):
        super().__init__(**kw)
        self.vmin = 0.0
        self.vmax = 1.0
        self.value = 0.0
        self.dragging = False
        self.on_seek_cb = on_seek
        try:
            _tex = CoreImage(PICON + 'fill_grad.png').texture
            _tex.wrap = 'clamp_to_edge'
        except Exception:
            _tex = None
        self._grad_tex = _tex
        with self.canvas:
            Color(1, 1, 1, 0.35)
            self._track = RoundedRectangle(radius=[dp(3)])
            if _tex:
                Color(1, 1, 1, 1)
                self._fill = Rectangle(texture=_tex)
            else:
                Color(*RED)
                self._fill = RoundedRectangle(radius=[dp(3)])
            Color(1, 1, 1, 0.95)
            self._knob = Ellipse()
        self.bind(pos=self._redraw, size=self._redraw)

    def _knob_r(self):
        return dp(8) if not self.dragging else dp(10)

    def _x_for(self, v):
        span = max(self.vmax - self.vmin, 1e-6)
        t = (v - self.vmin) / span
        pad = self._knob_r()
        return self.x + pad + t * (self.width - 2 * pad)

    def _v_for(self, x):
        pad = self._knob_r()
        w = max(self.width - 2 * pad, 1)
        t = min(max((x - (self.x + pad)) / w, 0.0), 1.0)
        return self.vmin + t * (self.vmax - self.vmin)

    def _redraw(self, *_):
        h = dp(6)
        cy = self.center_y
        k = self._knob_r()
        self._track.pos = (self.x, cy - h / 2)
        self._track.size = (self.width, h)
        fx = self._x_for(self.value)
        self._fill.pos = (self.x, cy - h / 2)
        self._fill.size = (max(fx - self.x, 0), h)
        self._knob.pos = (fx - k, cy - k)
        self._knob.size = (2 * k, 2 * k)

    def set_value(self, v):
        if not self.dragging:
            v = min(max(v, self.vmin), self.vmax)
            self.value = v
            self._redraw()

    def set_range(self, vmax):
        self.vmax = float(vmax or 1.0)
        self._redraw()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dragging = True
            touch.grab(self)
            self.value = self._v_for(touch.x)
            self._redraw()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.value = self._v_for(touch.x)
            self._redraw()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.dragging = False
            self.value = self._v_for(touch.x)
            self._redraw()
            if self.on_seek_cb:
                try:
                    self.on_seek_cb(self.value)
                except Exception:
                    pass
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)


class IconTextButton(ClickableBox):
    def __init__(self, text, icon_name=None, active=False, font=10.2, icon_size=18, **kw):
        super().__init__(bg=RED if active else SUR2, radius=22, border=None if active else BORDER,
                         orientation='horizontal', spacing=dp(6), padding=(dp(10), 0), **kw)
        if icon_name:
            self.add_widget(Image(source=icon(icon_name), size_hint=(None, None), size=(dp(icon_size), dp(icon_size)),
                                  keep_ratio=True, pos_hint={'center_y': 0.5}))
        label = Label(text=safe_text(text), color=WHITE if active else MUTED, font_size=sp(font), bold=True,
                      halign='center', valign='middle', size_hint_x=1, shorten=True, shorten_from='right')
        def _fit(*_):
            label.text_size = (max(dp(30), label.width), self.height)
        label.bind(width=_fit, height=_fit)
        self.add_widget(label)


class NavItem(ClickableBox):
    def __init__(self, icon_name, text, active=False, on_release_cb=None, **kw):
        super().__init__(bg=(0,0,0,0), border=None, orientation='vertical', spacing=dp(1), padding=(0, dp(3)),
                         **kw)
        self.add_widget(Image(source=icon(icon_name), size_hint=(None, None), size=(dp(26), dp(26)),
                              keep_ratio=True, pos_hint={'center_x': 0.5}))
        self.add_widget(Label(text=safe_text(text), color=RED if active else MUTED, font_size=sp(9.8), bold=True,
                               size_hint_y=None, height=dp(22), halign='center', valign='middle', text_size=(None, None)))
        if on_release_cb:
            self.bind(on_release=lambda *_: on_release_cb())


class IconButton(ClickableBox):
    def __init__(self, icon_name, size=34, bg=(0,0,0,0), radius=14, border=None, **kw):
        super().__init__(bg=bg, radius=radius, border=border, orientation='vertical', **kw)
        self.size_hint_x = kw.get('size_hint_x', None)
        self.width = dp(size)
        self.add_widget(Image(source=icon(icon_name), size_hint=(None, None), size=(dp(size*0.55), dp(size*0.55)),
                              pos_hint={'center_x': .5, 'center_y': .5}, keep_ratio=True))


class Card(BoxLayout):
    def __init__(self, **kw):
        card_color = kw.pop('card_color', SUR)
        kw.setdefault('orientation', 'vertical')
        kw.setdefault('padding', dp(12))
        kw.setdefault('spacing', dp(7))
        super().__init__(**kw)
        rr(self, card_color, 18, BORDER)


class IconLabel(BoxLayout):
    def __init__(self, image_name, text='', color=WHITE, font=12, gap=8, **kw):
        super().__init__(orientation='horizontal', spacing=dp(gap), **kw)
        self.add_widget(Image(source=icon(image_name), size_hint=(None, None), size=(dp(22), dp(22)), keep_ratio=True))
        self.add_widget(Label(text=safe_text(text), color=color, font_size=sp(font), bold=True,
                              halign='left', valign='middle', text_size=(None, None)))


class TextBox(TextInput):
    def __init__(self, hint_text='', draw_card=True, **kw):
        super().__init__(hint_text=hint_text, multiline=False, **kw)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = WHITE
        self.hint_text_color = MUTED
        self.cursor_color = RED
        self.selection_color = (1, .12, .18, .35)
        self.padding = (dp(17), dp(13), dp(17), dp(10))
        self.font_size = sp(12.5)
        if draw_card:
            rr(self, SUR2, 16, BORDER)
        with self.canvas.before:
            Color(*WHITE)

    def _get_line_options(self):
        kw = super()._get_line_options()
        kw['bold'] = True
        return kw


class Thumb(FloatLayout):
    def __init__(self, title='', duration='', i=0, src='', width=124, height=78, **kw):
        super().__init__(size_hint=(None, None), size=(dp(width), dp(height)), **kw)
        rr(self, SUR3, 14)
        if src:
            img = AsyncImage(source=src, size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                             allow_stretch=True, keep_ratio=True)
        else:
            img = Widget(size_hint=(1, 1))
            with img.canvas.before:
                Color(*(RED if i % 2 == 0 else (0.08, .25, .35, 1)))
                img._bg = RoundedRectangle(pos=img.pos, size=img.size, radius=[dp(14)])
            img.bind(pos=lambda *_: setattr(img._bg, 'pos', img.pos),
                     size=lambda *_: setattr(img._bg, 'size', img.size))
        self.add_widget(img)
        if duration:
            tag = Label(text=duration, color=WHITE, font_size=sp(9), bold=True,
                        size_hint=(None, None), size=(dp(40), dp(21)),
                        pos_hint={'right': .98, 'y': .035}, halign='center', valign='middle')
            tag.text_size = tag.size
            rr(tag, (0.01, .015, .02, .88), 7)
            self.add_widget(tag)


class ContextMenu(ModalView):
    def __init__(self, title='Opciones', actions=None, **kw):
        super().__init__(size_hint=(.90, None), height=dp(330), background_color=(0, 0, 0, .48),
                         auto_dismiss=True, **kw)
        box = Card(size_hint=(.92, None), height=dp(304), pos_hint={'center_x': .5, 'center_y': .5},
                   padding=dp(12), spacing=dp(4), card_color=SUR2)
        head = BoxLayout(size_hint_y=None, height=dp(38))
        head.add_widget(Label(text=title, color=WHITE, font_size=sp(15), bold=True, halign='left'))
        close = B(text='', size_hint_x=None, width=dp(35))
        btn_img(close, 'close', dp(14))
        close.bind(on_release=lambda *_: self.dismiss())
        head.add_widget(close)
        box.add_widget(head)
        for label, callback in (actions or []):
            row = B(text=label, color=WHITE, font_size=sp(11.5), halign='left',
                    size_hint_y=None, height=dp(46))
            rr(row, SUR, 12, BORDER)
            row.bind(on_release=lambda *_ , cb=callback: self._run_action(cb))
            box.add_widget(row)
        self.add_widget(box)
    def _run_action(self, callback):
        self.dismiss()
        try:
            callback()
        except Exception as exc:
            crashlog.write_log('Error en menu contextual: ' + str(exc)[:180])
            try:
                InfoDialog('No se pudo ejecutar', str(exc)[:180]).open()
            except Exception:
                pass


class VideoRow(ClickableBox):
    def __init__(self, video, cb=None, compact=False, menu_cb=None, **kw):
        h = 92 if not compact else 84
        super().__init__(bg=SUR, radius=16, border=BORDER, orientation='horizontal', spacing=dp(10), padding=dp(8),
                         size_hint_y=None, height=dp(h), **kw)
        self.video = video; self.cb = cb; self.menu_cb = menu_cb
        thumb = Thumb(safe_text(video.get('title', ''), 'Video'), video.get('duration', ''), video.get('color', 0),
                      video.get('thumb', ''), width=124, height=max(60, h-16))
        thumb.size_hint_x = None
        thumb.width = dp(124 if h >= 90 else 110)
        thumb.size_hint_y = 1
        thumb.height = 0
        self.add_widget(thumb)
        col = BoxLayout(orientation='vertical', spacing=dp(1), size_hint_x=1)
        title = Label(text=safe_text(video.get('title', ''), 'Sin título'), color=WHITE, font_size=sp(10.3), bold=True,
                      halign='left', valign='middle', size_hint_y=None, height=dp(40), shorten=True, shorten_from='right')
        def sync_title(*_):
            title.text_size = (max(dp(50), col.width), dp(40))
        col.bind(width=sync_title); sync_title()
        col.add_widget(title)
        col.add_widget(Label(text=safe_text(video.get('channel', '')), color=MUTED, font_size=sp(8.8),
                             halign='left', size_hint_y=None, height=dp(17), text_size=(None,None), shorten=True, shorten_from='right'))
        meta = ' · '.join([p for p in [safe_text(video.get('views', '')), safe_text(video.get('age', ''))] if p])
        col.add_widget(Label(text=meta, color=DIM, font_size=sp(8.4), halign='left', shorten=True))
        self.add_widget(col)
        if self.menu_cb:
            more = IconButton('more', size=30, size_hint_x=None, width=dp(30), bg=(0,0,0,0))
            more.bind(on_release=lambda *_: self.menu_cb(self.video))
            self.add_widget(more)
    def on_release(self):
        if self.cb:
            try:
                self.cb(self.video)
            except Exception as exc:
                crashlog.write_log('Error abriendo video: ' + str(exc)[:160])



class ChipBar(ScrollView):
    def __init__(self, items, on_select=None, active=0, **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(46))
        super().__init__(do_scroll_y=False, bar_width=0, scroll_type=['content'], **kw)
        box = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint=(None, 1), height=dp(44), padding=(0,0))
        box.bind(minimum_width=box.setter('width'))
        self.box = box; self.buttons = []
        for i, (name, img, query) in enumerate(items):
            w = 132 if name in ('Tendencias', 'En directo') else 108
            b = IconTextButton(name, img, active=(i == active), size_hint=(None, 1), width=dp(w), height=dp(44))
            if on_select:
                b.bind(on_release=lambda _btn, q=query, n=name: on_select(q or n))
            self.buttons.append(b); box.add_widget(b)
        self.add_widget(box)



class Nav(BoxLayout):
    def __init__(self, screen, active='home', **kw):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(78),
                         padding=(dp(8), dp(6)), spacing=dp(6), **kw)
        rr(self, NAV, 0)
        for img, text, name in [('home','Inicio','home'), ('download','Descargas','downloads'), ('music','Música','music'), ('settings','Ajustes','settings')]:
            item = NavItem(img, text, active=(name == active), size_hint=(1, 1),
                           on_release_cb=lambda n=name, s=screen: self._go(s, n))
            self.add_widget(item)
    def _go(self, screen, name):
        try:
            screen.manager.go(name)
        except Exception as exc:
            crashlog.write_log('Error navegando: ' + str(exc)[:160])



class Base(Screen):
    def make(self):
        root = BoxLayout(orientation='vertical', size_hint=(1,1), spacing=0)
        self.content.size_hint_y = 1
        self.content.size_hint_x = 1
        root.add_widget(self.content)
        root.add_widget(Nav(self, self.name))
        return root


class Home(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.content = ScrollView(do_scroll_x=False, bar_width=0)
        body = BoxLayout(orientation='vertical', padding=(dp(16), dp(14)), spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height')); self.body = body; self.content.add_widget(body)
        self.build(); self.add_widget(self.make())

    def build(self):
        c = self.body
        head = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(9))
        head.add_widget(Image(source=icon('yt'), size_hint=(None,None), size=(dp(46),dp(46)), keep_ratio=True))
        t = BoxLayout(orientation='vertical', size_hint_x=1)
        t.add_widget(Label(text=APP_NAME, color=WHITE, font_size=sp(18),
                           halign='left', valign='middle', text_size=(None,None)))
        t.add_widget(Label(text='Descarga tus videos favoritos', color=MUTED, font_size=sp(9.3), halign='left'))
        head.add_widget(t)
        c.add_widget(head)

        c.add_widget(Label(text='Buscar videos', color=WHITE, font_size=sp(23), bold=True,
                           size_hint_y=None, height=dp(38), halign='left'))
        search_wrap = BoxLayout(size_hint_y=None, height=dp(56), padding=(dp(14),0), spacing=dp(8))
        search_wrap.add_widget(Image(source=icon('search'), size_hint=(None,None), size=(dp(22),dp(22)),
                                     keep_ratio=True, pos_hint={'center_y': 0.5}))
        search = TextBox(hint_text='Buscar videos en YouTube...', draw_card=False, size_hint_y=1)
        search.bind(on_text_validate=lambda *_: self.manager.do_search(search.text)); self.search_field=search
        search.bind(text=lambda *_: self.manager._debounced_search(search.text))
        search_wrap.add_widget(search); rr(search_wrap, SUR2, 18, BORDER); c.add_widget(search_wrap)

        chips = [('Tendencias','flame','videos trending now'),('Videos Musicales','music','videos musicales populares'),
                 ('Gaming','game','mejores momentos gaming'),('Noticias','news','noticias de hoy'),('En directo','live','en vivo ahora')]
        c.add_widget(ChipBar(chips, on_select=lambda q: self.manager.do_search(q), size_hint_y=None, height=dp(46)))

        sec = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        sec.add_widget(Image(source=icon('flame'), size_hint=(None,None), size=(dp(23),dp(23))))
        sec.add_widget(Label(text='Tendencias', color=WHITE, font_size=sp(18), bold=True, halign='left'))
        c.add_widget(sec)

        trend_card = Card(size_hint_y=None, padding=dp(8), spacing=dp(8)); trend_card.height=dp(190)
        self.trending_box=trend_card
        for i in range(2):
            skeleton=BoxLayout(orientation='horizontal', spacing=dp(9), size_hint_y=None, height=dp(78))
            sk=Widget(size_hint=(None,None), size=(dp(118),dp(72)))
            rr(sk,SUR3,13); skeleton.add_widget(sk)
            tx=BoxLayout(orientation='vertical', spacing=dp(6));
            a=Widget(size_hint_y=None,height=dp(14)); rr(a,SUR3,7)
            b=Widget(size_hint_y=None,height=dp(11)); rr(b,SUR3,6)
            tx.add_widget(a); tx.add_widget(b); tx.add_widget(Widget()); skeleton.add_widget(tx); trend_card.add_widget(skeleton)
        c.add_widget(trend_card)

        link = Card(size_hint_y=None, height=dp(194), padding=dp(14), spacing=dp(8))
        link.add_widget(IconLabel('link', '¿Tienes un enlace?', color=WHITE, font=17, size_hint_y=None, height=dp(28)))
        link.add_widget(Label(text='Pega aquí el enlace del video de YouTube', color=MUTED, font_size=sp(10),
                              size_hint_y=None, height=dp(21), halign='left'))
        inp = TextBox(hint_text='https://www.youtube.com/watch?v=...', draw_card=False, size_hint_y=None, height=dp(48)); rr(inp, SUR2, 16, BORDER); self.url_field=inp
        inp.bind(on_text_validate=lambda *_: self.manager.analyze_url(inp.text)); link.add_widget(inp)
        pb=B(text='Pegar enlace',size_hint_y=None,height=dp(48),font_size=sp(13)); rr(pb,RED,14)
        pb.bind(on_release=lambda *_: self.manager.paste_link(inp)); link.add_widget(pb); c.add_widget(link)

        promo=Card(size_hint_y=None,height=dp(94),orientation='horizontal',spacing=dp(12),padding=dp(13),card_color=(.10,.055,.065,1))
        promo.add_widget(Image(source=icon('download'),size_hint=(None,None),size=(dp(42),dp(42))))
        ptxt=BoxLayout(orientation='vertical')
        ptxt.add_widget(Label(text='Descarga videos',color=WHITE,font_size=sp(13),bold=True,halign='left'))
        ptxt.add_widget(Label(text='Guarda tus videos favoritos\nde YouTube en tu dispositivo',color=MUTED,font_size=sp(9.3),halign='left'))
        promo.add_widget(ptxt); c.add_widget(promo)

        music=ClickableBox(size_hint_y=None,height=dp(72),orientation='horizontal',spacing=dp(12),padding=dp(13),bg=SUR,radius=16,border=BORDER)
        music.add_widget(Image(source=icon('music'),size_hint=(None,None),size=(dp(38),dp(38))))
        mtx=BoxLayout(orientation='vertical')
        mtx.add_widget(Label(text='Descargar música',color=WHITE,font_size=sp(13.5),bold=True,halign='left'))
        mtx.add_widget(Label(text='Busca canciones y descarga solo el audio',color=MUTED,font_size=sp(9.3),halign='left'))
        music.add_widget(mtx)
        music.add_widget(Label(text='›',color=MUTED,font_size=sp(24),size_hint_x=None,width=dp(28)))
        music.bind(on_release=lambda *_: self.manager.go('music'))
        c.add_widget(music)

    def show_trending(self, items):
        self.trending_box.clear_widgets()
        if not items:
            self.trending_box.height=dp(90); self.trending_box.add_widget(Label(text='No hay tendencias disponibles',color=DIM,font_size=sp(11),size_hint_y=None,height=dp(70))); return
        self.trending_box.height=max(dp(92), dp(8+len(items[:4])*92))
        for v in items[:4]: self.trending_box.add_widget(VideoRow(v,self.manager.open_video_menu,menu_cb=self.manager.show_video_menu))
    def show_trending_error(self,msg):
        self.trending_box.clear_widgets(); self.trending_box.height=dp(90)
        self.trending_box.add_widget(Label(text='No se pudieron cargar las tendencias',color=DIM,font_size=sp(11),halign='center'))


class Search(Base):
    def __init__(self, **kw):
        super().__init__(**kw); self.content=ScrollView(do_scroll_x=False,bar_width=0)
        body=BoxLayout(orientation='vertical',padding=(dp(14),dp(10)),spacing=dp(9),size_hint_y=None); body.bind(minimum_height=body.setter('height')); self.body=body; self.content.add_widget(body); self.build(); self.add_widget(self.make())
    def build(self):
        c=self.body; h=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(6)); b=B(text='‹',font_size=sp(30),size_hint_x=None,width=dp(38)); b.bind(on_release=lambda *_: self.manager.go('home')); h.add_widget(b); h.add_widget(Label(text='Resultados de búsqueda',color=WHITE,font_size=sp(16),bold=True,halign='left')); c.add_widget(h)
        q=TextBox(hint_text='Buscar videos...',size_hint_y=None,height=dp(48)); q.bind(on_text_validate=lambda *_: self.manager.do_search(q.text)); self.query_field=q; c.add_widget(q)
        c.add_widget(ChipBar([('Todos','flame',''),('Videos','download',''),('Canales','yt',''),('Playlists','news','')],size_hint_y=None,height=dp(40)))
        box=BoxLayout(orientation='vertical',spacing=dp(8),size_hint_y=None); box.bind(minimum_height=box.setter('height')); self.results_box=box; c.add_widget(box)
    def set_query(self,q):
        self.query_field.text=q
        self.results_box.clear_widgets()
        wrap=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(120),spacing=dp(8))
        spinner=CircularProgress(size_hint=(None,None),size=(dp(40),dp(40)),pos_hint={'center_x':.5})
        spinner.value=50
        wrap.add_widget(spinner)
        wrap.add_widget(Label(text='Buscando...',color=DIM,size_hint_y=None,height=dp(30)))
        self.results_box.add_widget(wrap)
    def show_results(self,items): self.results_box.clear_widgets(); [self.results_box.add_widget(VideoRow(v,self.manager.open_video_menu,menu_cb=self.manager.show_video_menu)) for v in items] if items else self.results_box.add_widget(Label(text='Sin resultados',color=DIM,size_hint_y=None,height=dp(50)))
    def show_error(self,msg): self.results_box.clear_widgets(); self.results_box.add_widget(Label(text='Error de búsqueda: '+str(msg)[:60],color=ERR,size_hint_y=None,height=dp(50)))


class RadioRow(ButtonBehavior, BoxLayout):
    def __init__(self, title, subtitle='', selected=False, **kw):
        super().__init__(orientation='horizontal',padding=(dp(10),dp(4)),spacing=dp(10),size_hint_y=None,height=dp(52),**kw); self.selected=selected; rr(self,SUR,12,BORDER)
        dot=Widget(size_hint=(None,None),size=(dp(20),dp(20))); self.dot=dot
        with dot.canvas:
            dot.outer_color = Color(*MUTED); dot.outer=Line(circle=(0,0,dp(8)),width=dp(1.5))
            dot.inner_color = Color(*RED); dot.inner=Line(circle=(0,0,dp(4)),width=dp(4))
        dot.bind(pos=self._sync); self._sync(); self.add_widget(dot)
        tx=BoxLayout(orientation='vertical'); tx.add_widget(Label(text=title,color=WHITE,font_size=sp(11),bold=True,halign='left')); tx.add_widget(Label(text=subtitle,color=MUTED,font_size=sp(8.5),halign='left')); self.add_widget(tx)
        self.set_selected(selected)
    def _sync(self,*_):
        self.dot.outer.circle=(self.dot.center_x,self.dot.center_y,dp(8)); self.dot.inner.circle=(self.dot.center_x,self.dot.center_y,dp(4))
    def set_selected(self,val):
        self.selected=val
        self.dot.inner.width=dp(4)
        self.dot.inner_color.rgba = (*RED[:3], 1.0 if val else 0.0)
        color = RED if val else MUTED
        self.dot.outer_color.rgba = color


class Options(Base):
    def __init__(self, **kw):
        super().__init__(**kw); self.video=None; self.mode='video'; self.quality='1080p'; self.content=ScrollView(do_scroll_x=False,bar_width=0); body=BoxLayout(orientation='vertical',padding=(dp(14),dp(10)),spacing=dp(10),size_hint_y=None); body.bind(minimum_height=body.setter('height')); self.body=body; self.content.add_widget(body); self.build(); self.add_widget(self.make())
    def build(self):
        c=self.body; h=BoxLayout(size_hint_y=None,height=dp(48)); b=B(text='‹',font_size=sp(30),size_hint_x=None,width=dp(38)); b.bind(on_release=lambda *_: self.manager.go('home')); h.add_widget(b); h.add_widget(Label(text='Opciones de descarga',color=WHITE,font_size=sp(16),bold=True,halign='left')); c.add_widget(h)
        self.info_card=Card(size_hint_y=None,height=dp(106),orientation='horizontal',spacing=dp(10)); c.add_widget(self.info_card)
        c.add_widget(Label(text='Formato',color=WHITE,font_size=sp(15),bold=True,size_hint_y=None,height=dp(27),halign='left'))
        f=Card(size_hint_y=None,height=dp(112),padding=dp(7)); self.btn_video=RadioRow('Video','Descarga el video con audio',True); self.btn_audio=RadioRow('Solo audio (MP3)','Siempre con la mejor calidad',False); self.btn_video.bind(on_release=lambda *_:self.set_mode('video')); self.btn_audio.bind(on_release=lambda *_:self.set_mode('audio')); f.add_widget(self.btn_video); f.add_widget(self.btn_audio); c.add_widget(f)
        self.q_label=Label(text='Calidad de video',color=WHITE,font_size=sp(15),bold=True,size_hint_y=None,height=dp(27),halign='left')
        c.add_widget(self.q_label)
        q=Card(size_hint_y=None,height=dp(270),padding=dp(7)); self.quality_box=q; self.quality_btns={}
        self._build_quality_rows([('4320p','8K Ultra HD'),('2160p','4K Ultra HD'),('1440p','2K QHD'),('1080p','Full HD'),('720p','HD'),('480p','SD'),('360p','SD')])
        c.add_widget(q); d=B(text='Descargar',size_hint_y=None,height=dp(52),font_size=sp(14)); rr(d,RED,15); d.bind(on_release=lambda *_:self.manager.start_download()); c.add_widget(d)
    def _build_quality_rows(self, pairs):
        """(re)construye las filas de calidad. pairs=[('1080p','Full HD'),...]"""
        q = self.quality_box
        q.clear_widgets()
        self.quality_btns = {}
        sel = getattr(self, 'quality', '1080p')
        if not any(x == sel for x, _ in pairs):
            sel = '1080p' if any(x == '1080p' for x, _ in pairs) else pairs[0][0]
        self.quality = sel
        q.height = dp(14) + dp(52) * len(pairs)
        for x, desc in pairs:
            row = RadioRow(x, desc, x == sel)
            row.bind(on_release=lambda _, q2=x: self.set_quality(q2))
            q.add_widget(row); self.quality_btns[x] = row
    def set_heights(self, heights):
        """Recibe alturas reales del video ([2160,1440,...]) y muestra solo esas."""
        try:
            hs = sorted({int(h) for h in (heights or [])}, reverse=True)[:7]
        except Exception:
            hs = []
        if not hs:
            return
        names = {4320: '8K Ultra HD', 2160: '4K Ultra HD', 1440: '2K QHD', 1080: 'Full HD', 720: 'HD',
                 480: 'SD', 360: 'SD', 240: 'Baja'}
        pairs = [(f'{h}p', names.get(h, '')) for h in hs]
        self._build_quality_rows(pairs)
    def set_video(self,video):
        self.video=video; self.info_card.clear_widgets(); self._info_thumb=Thumb(video.get('title',''),video.get('duration',''),video.get('color',0),video.get('thumb',''),width=126,height=78); self.info_card.add_widget(self._info_thumb); col=BoxLayout(orientation='vertical'); col.add_widget(Label(text=safe_text(video.get('title','Sin título'), 'Sin título'),color=WHITE,font_size=sp(11.5),bold=True,halign='left',valign='middle')); col.add_widget(Label(text=video.get('channel',''),color=MUTED,font_size=sp(9.5),halign='left')); col.add_widget(Label(text=video.get('duration',''),color=DIM,font_size=sp(9),halign='left')); self.info_card.add_widget(col)
    def set_mode(self,mode):
        """video: muestra calidades y miniatura. audio (MP3): siempre la mejor
        calidad posible -> se oculta la lista; solo nombre y canal."""
        self.mode=mode; self.btn_video.set_selected(mode=='video'); self.btn_audio.set_selected(mode=='audio')
        vis = (mode == 'video')
        try:
            self.q_label.height = dp(27) if vis else 0
            self.q_label.opacity = 1 if vis else 0
            self.quality_box.height = (dp(14) + dp(52) * max(len(self.quality_btns), 1)) if vis else 0
            self.quality_box.opacity = 1 if vis else 0
            if getattr(self, '_info_thumb', None) is not None:
                self._info_thumb.width = dp(126) if vis else 0
                self._info_thumb.height = dp(78) if vis else 0
                self._info_thumb.opacity = 1 if vis else 0
        except Exception:
            pass
    def set_quality(self,q):
        self.quality=q
        for x,b in self.quality_btns.items(): b.set_selected(x==q)


class Analyze(Screen):
    def __init__(self,**kw):
        super().__init__(**kw); c=BoxLayout(orientation='vertical',padding=dp(18),spacing=dp(10)); self.add_widget(c); h=BoxLayout(size_hint_y=None,height=dp(48)); b=B(text='‹',font_size=sp(30),size_hint_x=None,width=dp(38)); b.bind(on_release=lambda *_: self.manager.go('home')); h.add_widget(b); h.add_widget(Label(text='Analizando enlace',color=WHITE,font_size=sp(16),bold=True,halign='left')); c.add_widget(h)
        c.add_widget(Widget(size_hint_y=.04)); holder=FloatLayout(size_hint_y=None,height=dp(190)); holder.add_widget(Image(source=icon('yt'),size_hint=(None,None),size=(dp(118),dp(118)),pos_hint={'center_x':.5,'center_y':.5})); c.add_widget(holder)
        c.add_widget(Label(text='Analizando enlace de YouTube...',color=WHITE,font_size=sp(15),bold=True,size_hint_y=None,height=dp(30)))
        c.add_widget(Label(text='Obteniendo información del video',color=MUTED,font_size=sp(10),size_hint_y=None,height=dp(24)))
        self.steps=Card(size_hint_y=None,height=dp(190),padding=dp(10)); self.step_labels=[]
        for x in ['Conectando...','Obteniendo información','Analizando formatos','Listo para descargar']:
            l=Label(text='○  '+x,color=DIM,font_size=sp(10.8),size_hint_y=None,height=dp(38),halign='left'); self.steps.add_widget(l); self.step_labels.append(l)
        c.add_widget(self.steps); c.add_widget(Widget()); b=B(text='Cancelar',color=RED,size_hint_y=None,height=dp(48)); rr(b,SUR,13,BORDER); b.bind(on_release=lambda *_:self.manager.go('home')); c.add_widget(b)
    def set_url(self,url): self.url=url or ''
    def on_enter(self): self.set_step(0); Clock.schedule_once(lambda dt:self.manager.analyze_current_url(),.05)
    def set_step(self,n):
        for i,l in enumerate(self.step_labels): l.text=('✓  ' if i<=n else '○  ')+l.text[3:]; l.color=GREEN if i<=n else DIM


class CircularProgress(Widget):
    def __init__(self,**kw): super().__init__(**kw); self.value=0; self.bind(pos=self._sync,size=self._sync); self._draw()
    def _draw(self):
        with self.canvas: Color(*SUR3); self.bg=Line(circle=(0,0,0),width=dp(9)); Color(*RED); self.arc=Line(circle=(0,0,0,0,0),width=dp(9))
        self._sync()
    def _sync(self,*_):
        cx=self.center_x; cy=self.center_y; r=min(self.width,self.height)/2-dp(9); self.bg.circle=(cx,cy,r); self.arc.circle=(cx,cy,r,0,360*self.value/100)


class Downloading(Screen):
    def __init__(self,**kw):
        super().__init__(**kw); c=BoxLayout(orientation='vertical',padding=dp(15),spacing=dp(9)); self.add_widget(c); h=BoxLayout(size_hint_y=None,height=dp(48)); h.add_widget(B(text='‹',font_size=sp(30),size_hint_x=None,width=dp(38))); h.add_widget(Label(text='Descargando',color=WHITE,font_size=sp(16),bold=True,halign='left')); c.add_widget(h)
        self.info=Card(size_hint_y=None,height=dp(100),orientation='horizontal',spacing=dp(10)); c.add_widget(self.info)
        holder=FloatLayout(size_hint_y=None,height=dp(205)); self.circle=CircularProgress(size_hint=(None,None),size=(dp(180),dp(180)),pos_hint={'center_x':.5,'center_y':.5}); holder.add_widget(self.circle); self.num=Label(text='0%',color=WHITE,font_size=sp(34),bold=True,size_hint=(None,None),size=(dp(120),dp(60)),pos_hint={'center':(.5,.52)},halign='center'); holder.add_widget(self.num); c.add_widget(holder)
        self.st=Label(text='Descargando...',color=WHITE,font_size=sp(14),bold=True,size_hint_y=None,height=dp(26)); c.add_widget(self.st); self.det=Label(text='0 MB de 0 MB\n0.0 MB/s',color=MUTED,font_size=sp(10),size_hint_y=None,height=dp(40)); c.add_widget(self.det)
        row=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(8)); self.pause_btn=B(text='Pausar'); rr(self.pause_btn,SUR,12,BORDER); self.pause_btn.bind(on_release=lambda *_:self.manager.toggle_pause()); cancel=B(text='Cancelar',color=RED); rr(cancel,SUR,12,BORDER); cancel.bind(on_release=lambda *_:self.manager.cancel_download()); row.add_widget(self.pause_btn); row.add_widget(cancel); c.add_widget(row)
        note=Card(size_hint_y=None,height=dp(58),orientation='horizontal',padding=dp(9)); note.add_widget(Label(text='La descarga continúa en segundo plano.',color=MUTED,font_size=sp(9),halign='left')); c.add_widget(note)
    def set_info(self,v): self.info.clear_widgets(); self.info.add_widget(Thumb(safe_text(v.get('title','')),v.get('duration',''),v.get('color',0),v.get('thumb',''))); x=BoxLayout(orientation='vertical'); x.add_widget(Label(text=safe_text(v.get('title','')),color=WHITE,font_size=sp(11),bold=True,halign='left')); x.add_widget(Label(text=self.manager.current_mode_label(),color=MUTED,font_size=sp(9),halign='left')); self.info.add_widget(x); self.circle.value=0; self.num.text='0%'
    def update_progress(self,p,down,total,speed): self.circle.value=p; self.num.text=f'{int(p)}%'; self.st.text='Descarga completada' if p>=100 else 'Descargando...'; self.det.text=f'{down} MB de {total} MB\n{speed}'


class Downloads(Base):
    def __init__(self,**kw):
        super().__init__(**kw); self.filter='Todos'; self.content=ScrollView(do_scroll_x=False,bar_width=0); body=BoxLayout(orientation='vertical',padding=(dp(14),dp(10)),spacing=dp(9),size_hint_y=None); body.bind(minimum_height=body.setter('height')); self.body=body; self.content.add_widget(body); self.build(); self.add_widget(self.make())
    def build(self):
        c=self.body; h=BoxLayout(size_hint_y=None,height=dp(48)); h.add_widget(Label(text='Descargas',color=WHITE,font_size=sp(22),bold=True,halign='left')); sr=B(text='',size_hint_x=None,width=dp(38)); sr.add_widget(Image(source=icon('search'),size_hint=(None,None),size=(dp(22),dp(22)),pos_hint={'center_x':.5,'center_y':.5})); h.add_widget(sr); c.add_widget(h)
        self.counts_lbl=Label(text='',color=MUTED,font_size=sp(9.2),halign='left',size_hint_y=None,height=dp(22))
        c.add_widget(self.counts_lbl)
        c.add_widget(ChipBar([('Todos','flame','Todos'),('Videos','download','Videos'),('Musica','music','Videos_Musica'),('Completadas','yt','Completadas')],on_select=lambda f:self.set_filter(f),size_hint_y=None,height=dp(40)))
        box=BoxLayout(orientation='vertical',spacing=dp(8),size_hint_y=None); box.bind(minimum_height=box.setter('height')); self.list_box=box; c.add_widget(box)
    def set_filter(self,f): self.filter='Audios' if f=='Videos_Musica' else f; self.manager._refresh_downloads()
    def refresh(self,items):
        self.all_items=items
        try:
            nv=sum(1 for d in items if d.get('format')=='MP4')
            nm=sum(1 for d in items if d.get('format')=='MP3')
            self.counts_lbl.text=f'{nv} videos · {nm} canciones'
        except Exception:
            pass
        items=[d for d in items if self._match(d)]
        self.list_box.clear_widgets()
        if not items:
            empty=Card(size_hint_y=None,height=dp(150)); empty.add_widget(Image(source=icon('download'),size_hint=(None,None),size=(dp(38),dp(38)))); empty.add_widget(Label(text='Aún no hay descargas',color=WHITE,font_size=sp(14),bold=True)); empty.add_widget(Label(text='Tus archivos completados aparecerán aquí.',color=MUTED,font_size=sp(9.5))); self.list_box.add_widget(empty); return
        for d in items:
            status=d.get('status',''); col=GREEN if status=='completado' else RED if status=='descargando' else ORANGE
            done = status=='completado'
            if done and d.get('format')=='MP3':
                # Musica descargada: fila compacta SIN miniatura (estilo lista de musica)
                row=ClickableBox(bg=SUR,radius=14,border=BORDER,orientation='horizontal',
                                 padding=(dp(10),dp(6)),spacing=dp(8),size_hint_y=None,height=dp(60))
                pb=B(text='',size_hint_x=None,width=dp(40)); rr(pb,SUR2,20,BORDER)
                btn_img(pb,'play',dp(18))
                row.add_widget(pb)
                x=BoxLayout(orientation='vertical',spacing=dp(1))
                x.add_widget(Label(text=safe_text(d.get('title','')),color=WHITE,font_size=sp(10.5),bold=True,halign='left',valign='middle',size_hint_y=None,height=dp(24),text_size=(None,None),shorten=True,shorten_from='right'))
                x.add_widget(Label(text='MP3 · '+safe_text(d.get('channel',''),'cancion'),color=MUTED,font_size=sp(8.8),halign='left'))
                row.add_widget(x)
                db=B(text='',size_hint_x=None,width=dp(40)); rr(db,(1,1,1,0.08),20,None)
                btn_img(db,'close',dp(15))
                db.bind(on_release=lambda *_,item=d:self.manager.delete_download(item))
                row.add_widget(db)
                row.bind(on_release=lambda *_,item=d:self.manager.play_download(item))
                self.list_box.add_widget(row)
                continue
            row=BoxLayout(orientation='vertical',spacing=dp(6),padding=dp(8),size_hint_y=None,height=dp(152 if done else 102))
            rr(row,SUR,18,BORDER)
            top=ClickableBox(bg=(0,0,0,0),radius=0,border=None,orientation='horizontal',spacing=dp(9),size_hint_y=None,height=dp(78))
            top.add_widget(Thumb(safe_text(d.get('title','')),'',d.get('color',0),d.get('thumb',''),width=110,height=78)); x=BoxLayout(orientation='vertical',spacing=dp(1)); x.add_widget(Label(text=safe_text(d.get('title','')),color=WHITE,font_size=sp(10.8),bold=True,halign='left',valign='middle',size_hint_y=None,height=dp(38),text_size=(None,None)));                 x.add_widget(Label(text=f"{d.get('quality','')} · {d.get('format','')}" + (f" · {d['file_size']}" if d.get('file_size') else ''),color=MUTED,font_size=sp(8.8),halign='left')); x.add_widget(Label(text=status.capitalize(),color=col,font_size=sp(9.5),bold=True,halign='left')); top.add_widget(x)
            row.add_widget(top)
            if done:
                top.bind(on_release=lambda *_ , item=d:self.manager.play_download(item))
                acts=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(8))
                pb=B(text='▶ Reproducir',font_size=sp(10.5)); rr(pb,SUR2,10,BORDER)
                pb.bind(on_release=lambda *_ , item=d:self.manager.play_download(item))
                fb=B(text='Carpeta',font_size=sp(10.5)); rr(fb,SUR2,10,BORDER)
                fb.bind(on_release=lambda *_ , item=d:self.manager.open_folder())
                db=B(text='Borrar',font_size=sp(10.5),color=WHITE); rr(db,RED,10)
                db.bind(on_release=lambda *_ , item=d:self.manager.delete_download(item))
                acts.add_widget(pb); acts.add_widget(fb); acts.add_widget(db)
                row.add_widget(acts)
            self.list_box.add_widget(row)
    def _match(self,d):
        f=self.filter
        if f=='Videos': return d.get('format')=='MP4'
        if f=='Audios': return d.get('format')=='MP3'
        if f=='Completadas': return d.get('status')=='completado'
        return True


class MusicRow(ClickableBox):
    """Fila de música: lista limpia sin miniatura, con play y descargar.
    Toque largo = menu contextual (reproducir/favoritos/descargar)."""
    def __init__(self, item, **kw):
        self.item = item
        super().__init__(bg=SUR, radius=14, border=BORDER, orientation='horizontal',
                         spacing=dp(8), padding=(dp(12), dp(6)),
                         size_hint_y=None, height=dp(64), **kw)
        import time as _t
        self._press_t = 0.0
        self.bind(state=self._on_state)
        num = BoxLayout(size_hint_x=None, width=dp(28), padding=(0, 0))
        num.add_widget(Label(text=str(item.get('idx', '') or ''), color=MUTED,
                             font_size=sp(10), halign='center', valign='middle'))
        self.add_widget(num)
        col = BoxLayout(orientation='vertical', spacing=dp(1), size_hint_x=1)
        title = Label(text=safe_text(item.get('title', ''), 'Sin titulo'), color=WHITE,
                      font_size=sp(10.3), bold=True, halign='left', valign='middle',
                      size_hint_y=None, height=dp(40), shorten=True, shorten_from='right')
        def _fit(*_):
            title.text_size = (max(dp(40), col.width), dp(40))
        col.bind(width=_fit); _fit()
        col.add_widget(title)
        art = ' · '.join([p for p in [safe_text(item.get('channel', '')), safe_text(item.get('duration', ''))] if p])
        col.add_widget(Label(text=art, color=MUTED, font_size=sp(8.8), halign='left',
                             size_hint_y=None, height=dp(17), text_size=(None, None),
                             shorten=True, shorten_from='right'))
        self.add_widget(col)
        self.play_btn = B(text='', size_hint=(None, None), size=(dp(40), dp(40)))
        rr(self.play_btn, SUR2, 12, BORDER)
        self.play_img = btn_img(self.play_btn, 'play', dp(19))
        self.play_btn.bind(on_release=lambda *_: self.manager.music_queue_add(self.item))
        self.add_widget(self.play_btn)
        dl = B(text='', size_hint=(None, None), size=(dp(40), dp(40)))
        rr(dl, RED, 20)
        btn_img(dl, 'dl', dp(18))
        self.add_widget(dl)
        dl.bind(on_release=lambda *_: self.manager.music_download(self.item))
    def _on_state(self, _, value):
        if value == 'down':
            self._press_t = time.time()
    def on_release(self):
        held = time.time() - self._press_t
        if held >= 0.55:
            self.manager.show_music_menu(self.item)
        else:
            self.manager.music_queue_add(self.item)
    def bind_play(self, cb):
        # Compatibilidad: mantener referencia por si se usa externamente
        self._external_play_cb = cb
    def set_playing(self, playing):
        set_icon(self.play_img, 'stop' if playing else 'play')


class Music(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.content = ScrollView(do_scroll_x=False, bar_width=0)
        body = BoxLayout(orientation='vertical', padding=(dp(14), dp(10)), spacing=dp(9), size_hint_y=None)
        body.bind(minimum_height=body.setter('height')); self.body = body; self.content.add_widget(body)
        self._preview = None
        self._mp_visible = False
        self._view_mode = 'local'
        self._player = None
        self.build(); self.add_widget(self.make())
        self._build_mini_player()

    def build(self):
        c = self.body
        h = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        b = B(text='', size_hint_x=None, width=dp(38))
        rr(b, SUR2, 10, BORDER)
        btn_img(b, 'back', dp(18))
        b.bind(on_release=lambda *_: self.manager.go('home'))
        h.add_widget(b)
        h.add_widget(Label(text='Musica', color=WHITE, font_size=sp(16), bold=True, halign='left'))
        fav_b = B(text='', size_hint_x=None, width=dp(38))
        rr(fav_b, SUR2, 10, BORDER)
        btn_img(fav_b, 'heart', dp(19))
        fav_b.bind(on_release=lambda *_: self.manager.go('favs'))
        h.add_widget(fav_b)
        c.add_widget(h)
        q = TextBox(hint_text='Buscar canciones...', size_hint_y=None, height=dp(48))
        q.bind(on_text_validate=lambda *_: self.manager.music_search(q.text))
        self.query_field = q
        c.add_widget(q)
        hint = Card(size_hint_y=None, height=dp(40))
        hint.add_widget(Label(text='Toca play para escuchar · Manten presionado para opciones', color=DIM, font_size=sp(9), halign='center'))
        c.add_widget(hint)
        box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        box.bind(minimum_height=box.setter('height')); self.results_box = box; c.add_widget(box)

    def _build_mini_player(self):
        self._mp = mp = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(64),
                                  pos_hint={'bottom': 1}, opacity=0)
        rr(mp, (0, 0, 0, 0.92), 0)
        top_row = BoxLayout(size_hint_y=None, height=dp(32), padding=(dp(8), 0), spacing=dp(6))
        self._mp_title_wrap = ClickableBox(bg=(0, 0, 0, 0), border=None, size_hint_x=1)
        self._mp_title = Label(text='', color=WHITE, font_size=sp(10), bold=True,
                               halign='left', valign='middle', shorten=True)
        self._mp_title_wrap.add_widget(self._mp_title)
        self._mp_title_wrap.bind(on_release=lambda *_: self.show_player())
        top_row.add_widget(self._mp_title_wrap)
        close_b = B(text='', size_hint_x=None, width=dp(32))
        rr(close_b, (1, 1, 1, 0.10), 16, None)
        btn_img(close_b, 'close', dp(13))
        close_b.bind(on_release=lambda *_: self.manager.music_stop())
        top_row.add_widget(close_b)
        mp.add_widget(top_row)
        bot_row = BoxLayout(size_hint_y=None, height=dp(32), padding=(dp(8), 0), spacing=dp(8))
        self._mp_prev = B(text='', size_hint_x=None, width=dp(34))
        rr(self._mp_prev, SUR2, 17, BORDER)
        btn_img(self._mp_prev, 'prev', dp(16))
        self._mp_prev.bind(on_release=lambda *_: self.manager.music_prev())
        bot_row.add_widget(self._mp_prev)
        self._mp_play = B(text='', size_hint_x=None, width=dp(38))
        coin_bg(self._mp_play, dp(38))
        self._mp_play_img = btn_img(self._mp_play, 'pause', dp(17))
        self._mp_play.bind(on_release=lambda *_: self.manager.music_toggle())
        bot_row.add_widget(self._mp_play)
        self._mp_next = B(text='', size_hint_x=None, width=dp(34))
        rr(self._mp_next, SUR2, 17, BORDER)
        btn_img(self._mp_next, 'next', dp(16))
        self._mp_next.bind(on_release=lambda *_: self.manager.music_next())
        bot_row.add_widget(self._mp_next)
        self._mp_slider = SeekBar(on_seek=lambda v: self.manager.music_seek(v))
        bot_row.add_widget(self._mp_slider)
        self._mp_time = Label(text='', color=MUTED, font_size=sp(8),
                              size_hint_x=None, width=dp(66), halign='center')
        bot_row.add_widget(self._mp_time)
        mp.add_widget(bot_row)
        self.add_widget(mp)
        # Swipe hacia arriba en el mini player abre el reproductor completo.
        # (El tap en el titulo ya lo abre; el swipe funciona desde cualquier
        # punto del mini player sin romper los botones: solo registra Y.)
        self._mp_swipe_y = None
        self._mp_swipe_x = None
        _orig_down = mp.on_touch_down
        _orig_up = mp.on_touch_up
        def _mp_down(touch):
            try:
                if self._mp_visible and mp.opacity > 0 and mp.collide_point(*touch.pos):
                    self._mp_swipe_y = touch.y
                    self._mp_swipe_x = touch.x
            except Exception:
                pass
            return _orig_down(touch)
        def _mp_up(touch):
            try:
                res = _orig_up(touch)
            except Exception:
                res = False
            try:
                sy = self._mp_swipe_y
                sx = self._mp_swipe_x
                if self._mp_visible and mp.opacity > 0 and sy is not None and mp.collide_point(*touch.pos):
                    dy = touch.y - sy
                    dx = abs(touch.x - (sx if sx is not None else touch.x))
                    if dy > dp(48) and dy > dx:
                        self.show_player()
                        self._mp_swipe_y = None
                        self._mp_swipe_x = None
                        return True
            except Exception:
                pass
            self._mp_swipe_y = None
            self._mp_swipe_x = None
            return res
        mp.on_touch_down = _mp_down
        mp.on_touch_up = _mp_up

    def show_mini_player(self, title, playing=True):
        self._mp_title.text = title
        set_icon(self._mp_play_img, 'pause' if playing else 'play')
        if not self._mp_visible:
            self._mp.opacity = 1
            self._mp_visible = True

    def hide_mini_player(self):
        self._mp.opacity = 0
        self._mp_visible = False

    # ─── PLAYER EXPANDIDO ─────────────────────────────────────
    @staticmethod
    def _vid_of(item):
        vid = item.get('id') or ''
        if not vid:
            url = item.get('url') or ''
            if 'v=' in url:
                vid = url.split('v=')[1].split('&')[0]
        return vid

    def _cur_item(self):
        mgr = self.manager
        q = getattr(mgr, '_music_queue', [])
        cur = getattr(mgr, '_music_idx', -1)
        return dict(q[cur]) if 0 <= cur < len(q) else {}

    def close_player(self):
        if self._player is not None:
            try:
                self._player.dismiss()
            except Exception:
                pass
            self._player = None

    def show_player(self):
        """Reproductor a pantalla completa: portada grande, seek, controles
        prev/play/next/shuffle/repeat, favoritos y cola 'A continuacion'."""
        mgr = self.manager
        if getattr(mgr, '_music_idx', -1) < 0 and not getattr(mgr, '_music_queue', []):
            self.show_queue()
            return
        self.close_player()

        root = TouchBlockingFloatLayout()
        panel = BoxLayout(orientation='vertical', size_hint=(None, None),
                          padding=(dp(16), dp(12)), spacing=dp(6))

        def _relayout(*_):
            from kivy.core.window import Window
            panel.width = Window.width - dp(20)
            panel.height = min(Window.height - dp(24), dp(560))
            panel.pos = (dp(10), (Window.height - panel.height) / 2)
        rr(panel, (0.05, 0.06, 0.09, 0.98), 22)
        self._player = PlayerOverlay(root, _relayout)

        top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        back_b = B(text='', size_hint_x=None, width=dp(38))
        rr(back_b, SUR2, 19, BORDER)
        btn_img(back_b, 'close', dp(15))
        back_b.bind(on_release=lambda *_: self.close_player())
        top.add_widget(back_b)
        top.add_widget(Label(text='Reproduciendo', color=MUTED, font_size=sp(11), halign='left'))
        heart_b = B(text='', size_hint_x=None, width=dp(38))
        rr(heart_b, SUR2, 19, BORDER)
        btn_img(heart_b, 'heart', dp(19))
        heart_b.bind(on_release=lambda *_: self._player_fav())
        top.add_widget(heart_b)
        panel.add_widget(top)

        cover_wrap = BoxLayout(size_hint_y=None, height=dp(280), padding=(dp(12), 0))
        cardc = Card()
        # rounded cover like screenshot (18dp)
        rr(cardc, (0,0,0,0), 18)
        self._pl_cover = AsyncImage(size_hint=(1, 1), allow_stretch=True, keep_ratio=True,
                                    nocache=True)
        cardc.add_widget(self._pl_cover)
        cover_wrap.add_widget(cardc)
        panel.add_widget(cover_wrap)

        self._pl_title = Label(text='', color=WHITE, font_size=sp(16), bold=True,
                               halign='center', valign='middle', text_size=(dp(300), None),
                               size_hint_y=None, height=dp(32), shorten=True,
                               shorten_from='right')
        panel.add_widget(self._pl_title)
        self._pl_channel = Label(text='', color=RED, font_size=sp(11),
                                 halign='center', valign='middle',
                                 size_hint_y=None, height=dp(20), shorten=True)
        panel.add_widget(self._pl_channel)

        seek_row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        self._pl_t1 = Label(text='0:00', color=MUTED, font_size=sp(9),
                            size_hint_x=None, width=dp(38), halign='center')
        seek_row.add_widget(self._pl_t1)
        self._pl_slider = SeekBar(on_seek=lambda v: mgr.music_seek(v))
        seek_row.add_widget(self._pl_slider)
        self._pl_t2 = Label(text='0:00', color=MUTED, font_size=sp(9),
                            size_hint_x=None, width=dp(38), halign='center')
        seek_row.add_widget(self._pl_t2)
        panel.add_widget(seek_row)

        ctr = BoxLayout(size_hint_y=None, height=dp(74), spacing=dp(10), padding=(dp(18), 0))
        self._pl_shuffle = B(text='', size_hint_x=None, width=dp(44))
        btn_img(self._pl_shuffle, 'shuffle', dp(21))

        def _tog_shuffle(*_):
            st = mgr.music_shuffle_toggle()
            self._pl_shuffle.opacity = 1 if st else 0.35
        self._pl_shuffle.bind(on_release=_tog_shuffle)
        ctr.add_widget(self._pl_shuffle)
        prevb = B(text='', size_hint_x=None, width=dp(48))
        rr(prevb, SUR2, 24, BORDER)
        btn_img(prevb, 'prev', dp(22))
        prevb.bind(on_release=lambda *_: mgr.music_prev())
        ctr.add_widget(prevb)
        playb = B(text='', size_hint_x=None, width=dp(70))
        coin_bg(playb, dp(70))
        self._pl_play_img = btn_img(playb, 'pause', dp(30))
        playb.bind(on_release=lambda *_: mgr.music_toggle())
        ctr.add_widget(playb)
        nextb = B(text='', size_hint_x=None, width=dp(48))
        rr(nextb, SUR2, 24, BORDER)
        btn_img(nextb, 'next', dp(22))
        nextb.bind(on_release=lambda *_: mgr.music_next())
        ctr.add_widget(nextb)
        self._pl_repeat = B(text='', size_hint_x=None, width=dp(44))
        btn_img(self._pl_repeat, 'repeat', dp(21))

        def _tog_repeat(*_):
            st = mgr.music_repeat_toggle()
            self._pl_repeat.opacity = 1 if st else 0.35
        self._pl_repeat.bind(on_release=_tog_repeat)
        ctr.add_widget(self._pl_repeat)
        panel.add_widget(ctr)

        qhead = BoxLayout(size_hint_y=None, height=dp(30), padding=(dp(4), 0), spacing=dp(6))
        qhead.add_widget(Label(text='A continuacion (%d)' % len(getattr(mgr, '_music_queue', [])),
                               color=WHITE, font_size=sp(11), bold=True, halign='left'))
        qb = B(text='', size_hint_x=None, width=dp(36))
        rr(qb, SUR2, 18, BORDER)
        btn_img(qb, 'queue', dp(16))
        qb.bind(on_release=lambda *_: self.show_queue())
        qhead.add_widget(qb)
        panel.add_widget(qhead)

        sv = ScrollView(do_scroll_x=False, bar_width=0)
        box = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        sv.add_widget(box)
        panel.add_widget(sv)
        self._pl_box = box

        root.add_widget(panel)

        item = self._cur_item()
        vid = self._vid_of(item)
        if vid:
            self._pl_cover.source = mgr._thumb_path('https://i.ytimg.com/vi/%s/mqdefault.jpg' % vid)
            self._pl_cover.opacity = 1
        else:
            self._pl_cover.source = ''
            self._pl_cover.opacity = 0
        self._pl_title.text = safe_text(item.get('title', ''), 'Sin titulo')
        self._pl_channel.text = safe_text(item.get('channel', ''), '')
        set_icon(self._pl_play_img, 'pause' if getattr(mgr, '_music_playing', False) else 'play')
        self._pl_shuffle.opacity = 1 if getattr(mgr, '_shuffle', False) else 0.35
        self._pl_repeat.opacity = 1 if getattr(mgr, '_repeat', False) else 0.35
        self._fill_pl_queue()
        try:
            snd = mgr._music_sound
            pos = snd.get_pos() if snd else 0
            dur = (snd.length if hasattr(snd, 'length') and snd.length else 0) if snd else 0
            fm = lambda x: "{}:{:02d}".format(int(x // 60), int(x % 60))
            self._pl_t1.text = fm(pos)
            self._pl_t2.text = fm(dur) if dur else '0:00'
            self._pl_slider.set_range(dur or 1)
            self._pl_slider.set_value(pos)
        except Exception:
            pass
        self._player.open()

    def _fill_pl_queue(self):
        box = self._pl_box
        box.clear_widgets()
        mgr = self.manager
        q = getattr(mgr, '_music_queue', [])
        cur = getattr(mgr, '_music_idx', -1)
        if not q:
            box.add_widget(Label(text='No hay nada mas en la cola', color=WHITE, font_size=sp(13), bold=True,
                                 halign='center', size_hint_y=None, height=dp(28)))
            box.add_widget(Label(text="La lista de 'A continuacion' esta vacia. Anada canciones a la cola o reproduzca una playlist para ver sugerencias.",
                                 color=MUTED, font_size=sp(9), halign='center', text_size=(dp(300), None),
                                 size_hint_y=None, height=dp(40)))
            return
        # header like screenshot: A continuacion - 11 en total
        box.add_widget(Label(text='A continuacion', color=WHITE, font_size=sp(13), bold=True, halign='left', size_hint_y=None, height=dp(24)))
        box.add_widget(Label(text=f'{len(q)} en total - {max(0,len(q)-cur-1)} siguientes', color=MUTED, font_size=sp(9), halign='left', size_hint_y=None, height=dp(16)))
        for i, it in enumerate(q):
            active = (i == cur)
            es_sig = (i == cur + 1)
            rowb = ClickableBox(bg=RED if es_sig else (SUR if not active else RED), radius=12,
                                border=None if (active or es_sig) else BORDER,
                                orientation='horizontal', padding=(dp(10), dp(6)),
                                spacing=dp(8), size_hint_y=None, height=dp(56))
            num = Label(text=str(i+1), color=MUTED, font_size=sp(10), size_hint_x=None, width=dp(24), halign='center')
            if active: num.color = (1,1,1,1)
            if es_sig: num.color = RED
            rowb.add_widget(num)
            col = BoxLayout(orientation='vertical', spacing=dp(2))
            col.add_widget(Label(text=safe_text(it.get('title', ''), 'Sin titulo'),
                                  color=WHITE if not es_sig else WHITE,
                                  font_size=sp(11), bold=True, halign='left', shorten=True))
            col.add_widget(Label(text=safe_text(it.get('channel',''), 'Desconocido'),
                                  color=RED if es_sig else MUTED, font_size=sp(9), halign='left', shorten=True))
            rowb.add_widget(col)
            if es_sig:
                badge = Label(text='SIGUIENTE', color=(1,1,1,1), font_size=sp(7), bold=True, size_hint_x=None, width=dp(68))
                # badge bg
                bbg = BoxLayout(size_hint_x=None, width=dp(72))
                rr(bbg, RED, 6)
                bbg.add_widget(badge)
                rowb.add_widget(bbg)
            rowb.bind(on_release=lambda *_, idx=i: self._jump_and_refresh(idx))
            box.add_widget(rowb)

    def _jump_and_refresh(self, idx):
        self.manager.music_jump(idx)
        Clock.schedule_once(lambda dt: self.sync_player_track(), 0.2)

    def sync_player_track(self):
        """Refresca portada/titulo/cola del player expandido si esta abierto."""
        ov = self._player
        if ov is None or not getattr(ov, '_opened', False):
            return
        mgr = self.manager
        item = self._cur_item()
        vid = self._vid_of(item)
        if vid:
            self._pl_cover.source = mgr._thumb_path('https://i.ytimg.com/vi/%s/mqdefault.jpg' % vid)
            self._pl_cover.opacity = 1
        else:
            self._pl_cover.source = ''
            self._pl_cover.opacity = 0
        self._pl_title.text = safe_text(item.get('title', ''), 'Sin titulo')
        self._pl_channel.text = safe_text(item.get('channel', ''), '')
        set_icon(self._pl_play_img, 'pause' if mgr._music_playing else 'play')
        self._fill_pl_queue()

    def update_player_tick(self, pos, dur):
        """Sincroniza mini y expanded con el tick del manager."""
        ov = self._player
        if ov is not None and getattr(ov, '_opened', False):
            fm = lambda x: "{}:{:02d}".format(int(x // 60), int(x % 60))
            self._pl_slider.set_range(dur or 1)
            self._pl_slider.set_value(pos)
            self._pl_t1.text = fm(pos)
            self._pl_t2.text = fm(dur) if dur else '0:00'
            set_icon(self._pl_play_img, 'pause' if self.manager._music_playing else 'play')

    def _player_fav(self):
        item = self._cur_item()
        if item:
            self.manager.music_fav_toggle(item)


    def set_query(self, q):
        self.query_field.text = q
        self.stop_preview()
        self._view_mode = 'local'
        self.results_box.clear_widgets()
        self.results_box.add_widget(Label(text='Buscando...', color=DIM, size_hint_y=None, height=dp(50)))

    def toggle_favorites(self):
        self.manager.go('favs')

    def show_favorites(self):
        """Compatibilidad: ahora los favoritos viven en la pantalla 'favs'."""
        self.manager.go('favs')

    def show_queue(self):
        """Modal con la cola de reproduccion; tocar un item salta a ese track."""
        q = getattr(self.manager, '_music_queue', [])
        cur = getattr(self.manager, '_music_idx', -1)
        d = ModalView(size_hint=(0.9, None), height=dp(380), background_color=(0, 0, 0, 0.55))
        card = Card(size_hint=(1, 1), orientation='vertical', padding=dp(10), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(34))
        head.add_widget(Label(text='Cola de reproduccion', color=WHITE, font_size=sp(14),
                              bold=True, halign='left'))
        close = B(text='', size_hint_x=None, width=dp(32))
        rr(close, (1, 1, 1, 0.10), 16, None)
        btn_img(close, 'close', dp(13))
        close.bind(on_release=lambda *_: d.dismiss())
        head.add_widget(close)
        card.add_widget(head)
        sv = ScrollView(do_scroll_x=False, bar_width=0)
        box = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        if not q:
            box.add_widget(Label(text='La cola esta vacia.', color=DIM,
                                 size_hint_y=None, height=dp(40)))
        for i, it in enumerate(q):
            active = (i == cur)
            rowb = ClickableBox(bg=RED if active else SUR, radius=10,
                                border=None if active else BORDER,
                                orientation='horizontal', padding=(dp(8), 0),
                                spacing=dp(4), size_hint_y=None, height=dp(42))
            rowb.add_widget(Label(text=str(i + 1), color=WHITE if active else MUTED,
                                  font_size=sp(9), size_hint_x=None, width=dp(22)))
            rowb.add_widget(Label(text=safe_text(it.get('title', ''), 'Sin titulo'),
                                  color=WHITE if active else MUTED, font_size=sp(9.5),
                                  shorten=True, shorten_from='right'))

            def _jump(idx=i):
                self.manager.music_jump(idx)
                d.dismiss()
            rowb.bind(on_release=lambda *_, f=_jump: f())
            box.add_widget(rowb)
        sv.add_widget(box)
        card.add_widget(sv)
        d.add_widget(card)
        d.open()

    def show_results(self, items):
        self.stop_preview()
        self._view_mode = 'local'
        self.results_box.clear_widgets()
        if not items:
            self.results_box.add_widget(Label(text='Sin resultados', color=DIM, size_hint_y=None, height=dp(50)))
            return
        for idx, it in enumerate(items):
            it['idx'] = idx + 1
            row = MusicRow(it)
            row.manager = self.manager
            row.bind_play(self.manager.music_queue_add)
            self.results_box.add_widget(row)

    def show_error(self, msg):
        self.stop_preview()
        self.results_box.clear_widgets()
        self.results_box.add_widget(Label(text='Error: ' + str(msg)[:70], color=ERR, size_hint_y=None, height=dp(50)))

    def stop_preview(self):
        if self._preview is not None:
            try:
                self._preview.state = 'stop'
                self._preview.source = ''
            except Exception:
                pass
            self._preview = None
        for row in (self.results_box.children or []):
            if isinstance(row, MusicRow):
                row.set_playing(False)

    def set_preview(self, src, row):
        self.stop_preview()
        if not src:
            return
        try:
            from kivy.uix.video import Video as _Vid
        except Exception:
            _Vid = None
        try:
            v = _Vid(source=src, state='play', sound=True, volume=1,
                      size_hint=(None, None), size=(dp(10), dp(10)), opacity=0)
            self.add_widget(v)
            self._preview = v
            if row is not None:
                row.set_playing(True)
        except Exception as e:
            crashlog.write_log('Error preview musica: ' + str(e)[:120])

    def on_pre_enter(self):
        if not self.query_field.text.strip():
            self.show_local_audios()

    def show_local_audios(self):
        self.results_box.clear_widgets()
        mgr = self.manager
        audios = [d for d in getattr(mgr, 'downloads', []) if d.get('format') == 'MP3']
        if not audios:
            self.results_box.add_widget(Label(text='No hay descargas de audio.\nBusca y descarga canciones arriba.', color=DIM, size_hint_y=None, height=dp(70)))
            return
        self.results_box.add_widget(Label(text='Tus canciones descargadas', color=MUTED, font_size=sp(10), size_hint_y=None, height=dp(24), halign='left'))
        for idx, item in enumerate(audios):
            title = safe_text(item.get('title', 'Sin titulo'), 'Sin titulo')
            dur = item.get('duration') or ''
            dur_s = ''
            if dur:
                try:
                    dur_s = f'{int(dur)//60}:{int(dur)%60:02d}'
                except Exception:
                    dur_s = str(dur)
            row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8), padding=(dp(6), dp(4)))
            rr(row, SUR, 12, BORDER)
            play_b = B(text='', size_hint_x=None, width=dp(38))
            rr(play_b, SUR2, 19, BORDER)
            btn_img(play_b, 'play', dp(16))
            play_b.bind(on_release=lambda *_i, it=item: mgr.music_queue_add(it))
            info = BoxLayout(orientation='vertical', spacing=dp(1))
            info.add_widget(Label(text=f'{idx+1}. {title}', color=WHITE, font_size=sp(10.5), bold=True, halign='left', valign='middle', text_size=(None, None)))
            info.add_widget(Label(text=dur_s, color=MUTED, font_size=sp(8.5), halign='left', valign='middle', text_size=(None, None)))
            row.add_widget(play_b)
            row.add_widget(info)
            self.results_box.add_widget(row)


class MusicFavs(Base):
    """Pantalla dedicada de Favoritos: pestanas Canciones/Artistas/Albumes/
    Playlists con contadores, buscador y tarjetas por artista."""
    TABS = [('canciones', 'Canciones'), ('artistas', 'Artistas'),
            ('albumes', 'Albumes'), ('playlists', 'Playlists')]

    def __init__(self, **kw):
        super().__init__(**kw)
        self.content = ScrollView(do_scroll_x=False, bar_width=0)
        body = BoxLayout(orientation='vertical', padding=(dp(14), dp(10)), spacing=dp(9), size_hint_y=None)
        body.bind(minimum_height=body.setter('height')); self.body = body; self.content.add_widget(body)
        self._tab = 'canciones'
        self._artist_filter = None
        self._search_q = ''
        self._tab_btns = {}
        self.build(); self.add_widget(self.make())

    def build(self):
        c = self.body
        h = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        b = B(text='', size_hint_x=None, width=dp(38))
        rr(b, SUR2, 10, BORDER)
        btn_img(b, 'back', dp(18))
        b.bind(on_release=lambda *_: self.manager.go_back())
        h.add_widget(b)
        h.add_widget(Label(text='Favoritos', color=WHITE, font_size=sp(16), bold=True, halign='left'))
        c.add_widget(h)

        tabs = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        for key, label in self.TABS:
            bt = B(text=label, size_hint_x=1, font_size=sp(9.3))
            rr(bt, SUR2, 12, BORDER)
            bt.bind(on_release=lambda *_, k=key: self.set_tab(k))
            tabs.add_widget(bt)
            self._tab_btns[key] = bt
        c.add_widget(tabs)

        q = TextBox(hint_text='Busca artistas, album...', size_hint_y=None, height=dp(44))
        q.bind(on_text_validate=lambda *_: self.set_search(q.text))
        self.search_field = q
        c.add_widget(q)

        box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        self.list_box = box
        c.add_widget(box)

    def set_tab(self, key):
        self._tab = key
        self._artist_filter = None
        self.refresh()

    def set_search(self, text):
        self._search_q = (text or '').strip().lower()
        self.refresh()

    def on_pre_enter(self):
        self.refresh()

    def _favs(self):
        return getattr(self.manager, '_music_favs', [])

    def _matches(self, it):
        if not self._search_q:
            return True
        t = (str(it.get('title', '')) + ' ' + str(it.get('channel', ''))).lower()
        return self._search_q in t

    def refresh(self):
        favs = self._favs()
        counts = {
            'canciones': len(favs),
            'artistas': len({f.get('channel', '') for f in favs if f.get('channel')}),
            'albumes': 0,
            'playlists': 0,
        }
        labels = dict(self.TABS)
        for key, bt in self._tab_btns.items():
            bt.canvas.before.clear()
            if key == self._tab:
                rr(bt, RED, 12, None)
                bt.color = (1, 1, 1, 1)
            else:
                rr(bt, SUR2, 12, BORDER)
                bt.color = MUTED
            bt.text = '%s (%d)' % (labels[key], counts[key])
        self.list_box.clear_widgets()
        if self._tab == 'canciones':
            self._view_songs(favs)
        elif self._tab == 'artistas':
            self._view_artists(favs)
        elif self._tab == 'albumes':
            self._empty('Aun no hay albumes guardados.')
        else:
            self._empty('Aun no tienes playlists.\nMuy pronto podras crearlas.')

    def _empty(self, msg):
        self.list_box.add_widget(Label(text=msg, color=DIM, size_hint_y=None,
                                       height=dp(80), halign='center'))

    def _view_songs(self, favs):
        if not favs:
            self._empty('Sin favoritos.\nManten presionada una cancion\ny elegi "Agregar a favoritos".')
            return
        if not any(self._matches(it) for it in favs):
            self._empty('Sin resultados para tu busqueda.')
            return
        for idx, it in enumerate(favs):
            it['idx'] = idx + 1
            row = MusicRow(dict(it))
            row.manager = self.manager
            self.list_box.add_widget(row)

    def _view_artists(self, favs):
        groups = {}
        order = []
        for it in favs:
            ch = safe_text(it.get('channel', ''), 'Desconocido')
            if ch not in groups:
                groups[ch] = []
                order.append(ch)
            groups[ch].append(it)
        if self._artist_filter:
            ch = self._artist_filter
            head = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            vb = B(text='< Artistas', size_hint_x=None, width=dp(96), font_size=sp(9.5))
            rr(vb, SUR2, 10, BORDER)
            vb.bind(on_release=lambda *_: self._open_artist(None))
            head.add_widget(vb)
            head.add_widget(Label(text=ch, color=WHITE, font_size=sp(12), bold=True, halign='left'))
            self.list_box.add_widget(head)
            songs = [it for it in groups.get(ch, []) if self._matches(it)]
            if not songs:
                self._empty('Sin canciones de este artista.')
            for idx, it in enumerate(songs):
                it['idx'] = idx + 1
                row = MusicRow(dict(it))
                row.manager = self.manager
                self.list_box.add_widget(row)
            return
        if not order:
            self._empty('Sin favoritos todavia.\nLos artistas aparecen aca\nsegun tus canciones guardadas.')
            return
        visibles = 0
        for ch in order:
            songs = groups[ch]
            if not any(self._matches(it) for it in songs):
                continue
            visibles += 1
            card = ClickableBox(bg=SUR, radius=14, border=BORDER,
                                orientation='horizontal', padding=(dp(12), dp(8)),
                                spacing=dp(8), size_hint_y=None, height=dp(58))
            av = Label(text=(ch[:1] or '?').upper(), color=(1, 1, 1, 1), font_size=sp(16),
                       bold=True, size_hint_x=None, width=dp(40))
            with av.canvas:
                from kivy.graphics import Ellipse as _El
                Color(*RED)
                av._circ = _El(pos=av.pos, size=(dp(36), dp(36)))
                Color(1, 1, 1, 1)

                def _sync_av(inst, *_):
                    inst._circ.pos = (inst.center_x - dp(18), inst.center_y - dp(18))
                av.bind(pos=_sync_av, size=_sync_av)
            card.add_widget(av)
            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(text=ch, color=WHITE, font_size=sp(11), bold=True,
                                  halign='left', valign='middle',
                                  size_hint_y=None, height=dp(24), shorten=True,
                                  shorten_from='right'))
            info.add_widget(Label(text='%d canciones' % len(songs), color=MUTED,
                                  font_size=sp(8.5), halign='left'))
            card.add_widget(info)
            card.bind(on_release=lambda *_, name=ch: self._open_artist(name))
            self.list_box.add_widget(card)
        if not visibles:
            self._empty('Sin resultados para tu busqueda.')

    def _open_artist(self, name):
        self._artist_filter = name
        self.refresh()


class Toggle(ButtonBehavior, Widget):
    def __init__(self, value=False, **kw): super().__init__(**kw); self.value=value; self.size_hint=(None,None); self.size=(dp(46),dp(27)); self.bind(pos=self._sync,size=self._sync); self._draw()
    def _draw(self):
        with self.canvas: Color(*SUR3); self.bg=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(14)]); Color(*RED); self.knob=RoundedRectangle(pos=(0,0),size=(dp(21),dp(21)),radius=[dp(11)])
        self._sync()
    def _sync(self,*_):
        self.bg.pos=self.pos; self.bg.size=self.size; self.knob.pos=(self.x+dp(22) if self.value else self.x+dp(3), self.y+dp(3))
    def on_release(self): self.value=not self.value; self._sync()


class Settings(Base):
    def __init__(self,**kw):
        super().__init__(**kw); self.content=ScrollView(do_scroll_x=False,bar_width=0); body=BoxLayout(orientation='vertical',padding=(dp(14),dp(10)),spacing=dp(9),size_hint_y=None); body.bind(minimum_height=body.setter('height')); self.body=body; self.content.add_widget(body); self.build(); self.add_widget(self.make())
    def build(self):
        c=self.body; c.clear_widgets()
        mgr = self.manager
        _s = {}
        if mgr and hasattr(mgr, '_app_settings') and mgr._app_settings:
            _s = mgr._app_settings
        head=BoxLayout(size_hint_y=None,height=dp(48)); head.add_widget(Label(text='Ajustes',color=WHITE,font_size=sp(23),bold=True,halign='left')); head.add_widget(Image(source=icon('settings'),size_hint=(None,None),size=(dp(28),dp(28)))); c.add_widget(head)
        self._section(c,'General')
        self._row(c,'Carpeta de descargas','Toca para elegir','pick_download_folder')
        self._row(c,'Abrir carpeta','Descargas/Jonayo_Downloads','open_folder')
        self._row(c,'Descargar con datos móviles','Puede generar cargos adicionales',toggle=True,default=_s.get('mobile_data',False),on_toggle=lambda v: self._save_setting('mobile_data',bool(v)))
        self._row(c,'Descargas simultáneas','3 descargas')
        self._row(c,'Tema','Oscuro')
        self._row(c,'Seguir escuchando en segundo plano','La musica continua al salir de la app',toggle=True,default=getattr(mgr,'bg_music',True) if mgr else True,on_toggle=self._set_bg_music)
        self._section(c,'Notificaciones')
        self._row(c,'Notificaciones de descargas','Mostrar notificaciones de progreso',toggle=True,default=_s.get('notifications',True),on_toggle=lambda v: self._save_setting('notifications',bool(v)))
        self._row(c,'Sonido al completar','Reproducir sonido al terminar',toggle=True,default=_s.get('sound_done',True),on_toggle=lambda v: self._save_setting('sound_done',bool(v)))
        self._section(c,'Otros')
        self._row(c,'Buscar actualizaciones','v' + APP_VERSION,'check_update_now',arrow=True)
        self._row(c,'Sitio web','jonayo.vercel.app','open_web')
        self._row(c,'Telegram','t.me/Jonayogoth','open_telegram')
        self._row(c,'Compartir la app','',arrow=True)
        info=Card(size_hint_y=None,height=dp(88)); info.add_widget(Label(text=f'J Youtube Downloader\nVersión {APP_VERSION}\nCreada por Jonathan Fariña - Jonayo',color=MUTED,font_size=sp(9.5),halign='center',valign='middle')); c.add_widget(info)
    def _save_setting(self, key, val):
        mgr = self.manager
        if mgr and hasattr(mgr, '_save_app_setting'):
            mgr._save_app_setting(key, val)
    def _section(self,c,text): c.add_widget(Label(text=text,color=WHITE,font_size=sp(14),bold=True,size_hint_y=None,height=dp(27),halign='left'))
    def _row(self,c,title,sub,action=None,toggle=False,default=False,arrow=False,on_toggle=None):
        r=Card(size_hint_y=None,height=dp(67),orientation='horizontal',spacing=dp(10),padding=(dp(12),dp(8)))
        x=BoxLayout(orientation='vertical'); x.add_widget(Label(text=title,color=WHITE,font_size=sp(10.5),bold=True,halign='left')); x.add_widget(Label(text=sub,color=MUTED,font_size=sp(8.5),halign='left')); r.add_widget(x)
        if toggle:
            sw=Toggle(default); r.add_widget(sw)
            if on_toggle: sw.bind(on_release=lambda *_: on_toggle(sw.value))
        elif arrow or action:
            ar=B(text='›',color=MUTED,font_size=sp(22),size_hint_x=None,width=dp(30)); rr(ar, SUR2, 10, BORDER); r.add_widget(ar)
            if action: ar.bind(on_release=lambda *_: self._manager_action(action))
        c.add_widget(r)
    def _set_bg_music(self,v):
        try:
            self.manager.bg_music=bool(v)
            self.manager._save_app_setting('bg_music',bool(v))
        except Exception:
            pass
    def _manager_action(self,a):
        mgr = self.manager
        if mgr:
            try:getattr(mgr,a)()
            except Exception:pass


class InfoDialog(ModalView):
    def __init__(self,title,text,on_ok=None,ok_text='Cerrar',**kw):
        super().__init__(size_hint=(.88,.40),background_color=(0,0,0,.55),**kw); box=Card(size_hint=(.92,None),height=dp(220),pos_hint={'center_x':.5,'center_y':.5},padding=dp(15)); box.add_widget(Label(text=title,color=WHITE,font_size=sp(16),bold=True,size_hint_y=None,height=dp(35))); box.add_widget(Label(text=text,color=MUTED,font_size=sp(10.5),halign='center',valign='middle',text_size=(dp(270),dp(100)),size_hint_y=None,height=dp(100))); ok=B(text=ok_text,size_hint_y=None,height=dp(44)); rr(ok,RED,12); 
        def _close_and_action(*_):
            self.dismiss()
            if on_ok: on_ok()
        ok.bind(on_release=_close_and_action); box.add_widget(ok); self.add_widget(box)

# ─── GESTOR DE PANTALLAS ────────────────────────────────────────
class _YDL_Logger:
    """Logger para yt-dlp. Evita escribir a sys.stdout/stderr (rotos en
    Kivy/Android: su .buffer es un str -> 'str' object has no attribute
    'write') y guarda warnings/errores en el log de la app."""

    def debug(self, msg):
        pass

    def warning(self, msg):
        crashlog.write_log('[yt-dlp] ' + str(msg))

    def error(self, msg):
        crashlog.write_log('[yt-dlp ERROR] ' + str(msg))


def _patch_ytdlp_write_string():
    """Neutraliza escrituras a sys.stdout/stderr cuyo .buffer es un str
    (Android/Kivy): si write_string reventa con AttributeError, no deja
    caer la descarga."""
    try:
        import yt_dlp.utils as _u
        if getattr(_u, '_jonayo_patched', False):
            return
        _orig = _u.write_string

        def _safe(s, out=None, *a, **kw):
            try:
                return _orig(s, out, *a, **kw)
            except AttributeError:
                return

        _u.write_string = _safe
        _u._jonayo_patched = True
    except Exception:
        pass


class M(ScreenManager):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.download_path = self._default_download_path()
        try:
            os.makedirs(self.download_path, exist_ok=True)
        except Exception:
            pass
        self.history_file = os.path.join(self._data_dir(), 'downloads.json')
        self.settings_file = os.path.join(self._data_dir(), 'settings.json')
        self.downloads = self._load_history()
        self.download_tree = self._load_settings().get('download_tree') or ''
        self.downloading = False
        self.paused = False
        self.cancel_event = threading.Event()
        self.current_ydl = None
        self.selected = None
        self.current_mode = 'video'
        self.current_quality = '1080p'
        self._last_dialog = None
        self._back_stack = []
        self._play_temp = None
        self.play_queue = []
        self._stream_cache = {}
        self._search_cache = {}
        self._CACHE_MAX = 50
        self._search_debounce_event = None
        self._search_debounce_delay = 0.5
        self._queue_dialog = None
        self._player_dialog = None
        self._music_queue = []
        self._music_idx = -1
        self._music_sound = None
        self._music_playing = False
        self._music_tick = None
        self._music_suppress_stop = False
        self._shuffle = False
        self._repeat = False
        self._favs_path = os.path.join(self._data_dir(), '.music_favs.json')
        self._music_favs = self._load_favs()
        self._settings_path = os.path.join(self._data_dir(), '.app_settings.json')
        self._app_settings = self._load_app_settings()
        self.bg_music = bool(self._app_settings.get('bg_music', True))

        self.add_widget(Home(name='home'))

        self._setup_done = False
        Clock.schedule_once(lambda dt: self._finish_setup(), 0.05)
        crashlog.write_log("M() construido OK (inicio diferido)")

    def _finish_setup(self):
        if self._setup_done:
            return
        self._setup_done = True
        for _cls, _name in [(Search, 'search'), (Options, 'options'), (Analyze, 'analyze'),
                            (Downloading, 'downloading'), (Downloads, 'downloads'),
                            (Music, 'music'), (MusicFavs, 'favs'), (Settings, 'settings')]:
            try:
                crashlog.write_log(f"Creando pantalla {_name}...")
                self.add_widget(_cls(name=_name))
                crashlog.write_log(f"Pantalla {_name} creada OK")
            except Exception:
                import traceback
                crashlog.write_crash(traceback.format_exc())
        self._ensure_ffmpeg()
        self._cleanup_play_tmp()
        self._load_trending()
        self._check_clipboard()

    def _cleanup_play_tmp(self):
        """Borra archivos temporales de reproducción que quedaron de sesiones
        anteriores (por crash o cierre forzado)."""
        try:
            tmp = os.path.join(self._default_download_path(), '.reproducir')
            if os.path.isdir(tmp):
                for name in os.listdir(tmp):
                    try:
                        os.remove(os.path.join(tmp, name))
                    except Exception:
                        pass
        except Exception:
            pass

    def _status_bar_dp(self):
        """Altura de la barra de estado en dp para no superponer los controles."""
        try:
            if IS_ANDROID:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                res = PythonActivity.mActivity.getResources()
                ident = res.getIdentifier('status_bar_height', 'dimen', 'android')
                px = res.getDimensionPixelSize(ident)
                dpi = Window.dpi or 160
                return int(px * 160 / max(dpi, 1)) + 4
        except Exception:
            pass
        return 0

    def _data_dir(self):
        try:
            if IS_ANDROID:
                from android import mActivity
                return mActivity.getFilesDir().getAbsolutePath()
        except Exception:
            pass
        return os.path.dirname(os.path.abspath(__file__))

    def _load_settings(self):
        try:
            import json
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_settings(self):
        try:
            import json
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump({'download_tree': self.download_tree}, f)
        except Exception:
            pass

    def _default_download_path(self):
        try:
            if IS_ANDROID:
                from android import mActivity
                ex = mActivity.getExternalFilesDir(None)
                if ex:
                    return os.path.join(ex.getAbsolutePath(), 'Jonayo_Downloads')
                return os.path.join(self._data_dir(), 'Jonayo_Downloads')
        except Exception:
            pass
        return os.path.join(os.path.expanduser('~'), 'Downloads', 'Jonayo')

    def _trim_cache(self, cache):
        """Limita un dict cache a _CACHE_MAX entradas eliminando las más antiguas."""
        while len(cache) > self._CACHE_MAX:
            cache.pop(next(iter(cache)))

    def _load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        crashlog.write_log(f'Historial cargado: {len(data)} descargas')
                        return data
                    else:
                        crashlog.write_log(f'Historial corrupto: tipo {type(data)} no es lista, ignorando')
                        try:
                            os.rename(self.history_file, self.history_file + '.bad')
                        except Exception:
                            pass
                        return []
            else:
                crashlog.write_log('Historial no existe aun (primera ejecucion)')
        except Exception as e:
            crashlog.write_log(f'Error cargando historial: {e}')
            try:
                if os.path.exists(self.history_file):
                    os.rename(self.history_file, self.history_file + '.bad')
                    crashlog.write_log('Historial corrupto renombrado a .bad para inspeccion')
            except Exception:
                pass
        return []

    def _save_history(self):
        try:
            tmp = self.history_file + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.downloads, f, ensure_ascii=False, indent=2)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            try:
                os.replace(tmp, self.history_file)
            except Exception:
                # fallback para filesystems sin os.replace atomico
                try:
                    os.rename(tmp, self.history_file)
                except Exception:
                    # ultimo intento: escribir directo
                    with open(self.history_file, 'w', encoding='utf-8') as f2:
                        json.dump(self.downloads, f2, ensure_ascii=False, indent=2)
            crashlog.write_log(f'Historial guardado: {len(self.downloads)} descargas')
        except Exception as e:
            crashlog.write_log(f'Error guardando historial: {e}')

    def go(self, n):
        self.transition = SlideTransition(direction='left', duration=.16)
        if self.current and self.current != n:
            self._back_stack.append(self.current)
        self.current = n
        if n == 'downloads':
            self.get_screen('downloads').refresh(self.downloads)

    def go_back(self):
        if self._back_stack:
            n = self._back_stack.pop()
            self.transition = SlideTransition(direction='right', duration=.16)
            self.current = n
            if n == 'downloads':
                self.get_screen('downloads').refresh(self.downloads)
        else:
            self.confirm_exit()

    # ─── BUSQUEDA REAL ─────────────────────────────────────────
    def _debounced_search(self, query):
        if self._search_debounce_event:
            self._search_debounce_event.cancel()
        self._search_debounce_event = Clock.schedule_once(
            lambda dt: self.do_search(query), self._search_debounce_delay)

    def do_search(self, query):
        query = (query or '').strip()
        if not query:
            return
        crashlog.write_log(f"Busqueda: {query[:60]}")
        self.go('search')
        self.get_screen('search').set_query(query)
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        import yt_dlp
        key = ' '.join((query or '').strip().lower().split())
        try:
            cached = self._search_cache.get(key)
            if cached and (time.time() - cached.get('time', 0) < 300):
                items = cached['items']
                Clock.schedule_once(lambda dt, it=items: self.get_screen('search').show_results(it))
                return
            # extract_flat evita resolver formatos por cada resultado.
            ydl_opts = {
                'quiet': True, 'no_warnings': True, 'noplaylist': True,
                'extract_flat': True, 'playlistend': 8,
                'check_formats': False, 'nocheckcertificate': True,
                'socket_timeout': 10,
                # v2.0.47: android primero (05-09-2026 YouTube bloqueo al resto).
                'extractor_args': {'youtube': {'player_client': ['android', 'android_vr', 'visionos', 'tv', 'web_embedded']}},
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info('ytsearch8:' + query, download=False)
            items = []
            for idx, e in enumerate((results.get('entries') or [])):
                if not e or not e.get('id'):
                    continue
                items.append(self._to_video(e, idx))
            self._search_cache[key] = {'time': time.time(), 'items': items}
            self._trim_cache(self._search_cache)
            Clock.schedule_once(lambda dt, it=items: self.get_screen('search').show_results(it))
        except Exception as e:
            err = str(e)[:150]
            crashlog.write_log("Error busqueda: " + err)
            # v2.0.47: Piped ante CUALQUIER error (antes solo 403; ahora hay
            # 'reload page' y otros bloqueos que tambien lo necesitan).
            if True:
                # fallback Piped search para no dejar la lista en blanco
                try:
                    import requests, certifi
                    from urllib.parse import quote as _q
                    items = []
                    # v2.0.47: el unico Piped vivo (verificado 05-09-2026) primero.
                    for _h in ['https://api.piped.private.coffee', 'https://pipedapi.kavin.rocks', 'https://pipedapi-libre.kavin.rocks', 'https://piped-api.lunar.icu', 'https://pipedapi.adminforge.de']:
                        try:
                            _r = requests.get(f'{_h}/search?q={_q(query)}&filter=videos', timeout=12, verify=certifi.where(), headers={'User-Agent': 'Mozilla/5.0'})
                            _r.raise_for_status()
                            _j = _r.json()
                            _entries = _j.get('items') or _j.get('content') or []
                            for _idx, _en in enumerate(_entries[:8]):
                                _vid = _en.get('url', '').split('v=')[-1].split('&')[0] if 'v=' in str(_en.get('url','')) else str(_en.get('url','')).rstrip('/').split('/')[-1]
                                if not _vid or len(_vid) != 11:
                                    continue
                                items.append({'title': _en.get('title', 'Sin titulo'), 'url': f'https://www.youtube.com/watch?v={_vid}', 'id': _vid, 'duration': '', 'channel': _en.get('uploaderName', ''), 'thumb': _en.get('thumbnail') or '', 'color': _idx % 5})
                            if items:
                                break
                        except Exception:
                            continue
                    if items:
                        self._search_cache[key] = {'time': time.time(), 'items': items}
                        self._trim_cache(self._search_cache)
                        Clock.schedule_once(lambda dt, it=items: self.get_screen('search').show_results(it))
                        return
                except Exception:
                    pass
            Clock.schedule_once(lambda dt, m=err: self.get_screen('search').show_error(m))

    # ─── TENDENCIAS REAL ───────────────────────────────────────
    def _load_trending(self):
        threading.Thread(target=self._trending_thread, daemon=True).start()

    def _check_clipboard(self):
        """Detecta si hay un enlace de video en el portapapeles y pregunta si descargar."""
        try:
            from kivy.core.clipboard import Clipboard
            text = Clipboard.paste()
            if not text:
                return
            text = text.strip()
            if not text.startswith('http://') and not text.startswith('https://'):
                return
            if not any(s in text for s in ['youtube.com', 'youtu.be', 'tiktok.com',
                     'instagram.com', 'facebook.com', 'twitter.com', 'x.com',
                     'vimeo.com', 'dailymotion.com', 'twitch.tv', 'soundcloud.com']):
                return
            def _open_clipboard(dt):
                self._clipboard_url = text
                self._info('Enlace detectado',
                    f'Se encontro este enlace en el portapapeles:\n\n{text[:80]}...\n\n'
                    'Queres analizarlo?',
                    on_ok=lambda: self.analyze_url(self._clipboard_url),
                    ok_text='Analizar')
            Clock.schedule_once(_open_clipboard, 1.5)
        except Exception:
            pass

    def _trending_thread(self):
        import yt_dlp
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True, 'noplaylist': True,
                        'check_formats': False, 'nocheckcertificate': True,
                        'socket_timeout': 15,
                        # v2.0.47: cliente default (web) bloqueado; android primero.
                        'extractor_args': {'youtube': {'player_client': ['android', 'android_vr', 'visionos', 'tv', 'web_embedded']}}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info('ytsearch10:trending videos now',
                                           download=False)
            items = []
            for idx, e in enumerate((results.get('entries') or [])):
                if not e or not e.get('id'):
                    continue
                items.append(self._to_video(e, idx))
            Clock.schedule_once(lambda dt, it=items: self.get_screen('home').show_trending(it))
        except Exception as e:
            err = str(e)[:150]
            crashlog.write_log("Error trending: " + err)
            Clock.schedule_once(lambda dt, m=err: self.get_screen('home').show_trending_error(m))

    def _fast_thumb(self, url):
        """Usa miniaturas pequeñas (mqdefault) en vez de las originales para
        que carguen mucho más rápido en la lista."""
        try:
            if url and 'i.ytimg.com/vi/' in url:
                vid = url.split('/vi/')[1].split('/')[0]
                return 'https://i.ytimg.com/vi/' + vid + '/mqdefault.jpg'
        except Exception:
            pass
        return url

    def _thumb_url_from_id(self, vid):
        """Construye URL de thumbnail directamente desde el ID del video.
        YouTube siempre soporta este patrón sin importar extract_flat."""
        if not vid:
            return ''
        return f'https://i.ytimg.com/vi/{vid}/mqdefault.jpg'

    def _thumb_cache_path(self):
        return os.path.join(self._data_dir(), '.thumbs')

    def _thumb_path(self, url):
        """Cache local persistente de miniaturas: si la imagen ya esta en disco
        devuelve la ruta local (carga instantanea); si no, la baja en un hilo
        secundario y devuelve la URL original para que se vea al instante."""
        try:
            if not url or 'i.ytimg.com/vi/' not in url:
                return url
            vid = url.split('/vi/')[1].split('/')[0]
            cache_dir = self._thumb_cache_path()
            os.makedirs(cache_dir, exist_ok=True)
            local = os.path.join(cache_dir, vid + '.jpg')
            if os.path.exists(local) and os.path.getsize(local) > 500:
                return local
            threading.Thread(target=self._thumb_download, args=(url, local), daemon=True).start()
        except Exception:
            pass
        return url

    def _thumb_download(self, url, local):
        for intento in range(2):
            try:
                try:
                    import certifi
                    import ssl
                    ctx = ssl.create_default_context(cafile=certifi.where())
                    import urllib.request
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
                        data = r.read()
                except Exception:
                    import requests as _req
                    r = _req.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8, verify=True)
                    data = r.content
                if data and len(data) > 500:
                    with open(local, 'wb') as f:
                        f.write(data)
                    return
            except Exception:
                pass
            time.sleep(2)

    def _to_video(self, e, idx):
        dur = e.get('duration') or 0
        dur_txt = f"{int(dur // 60)}:{int(dur % 60):02d}" if dur else ''
        vid = e.get('id') or ''
        page_url = e.get('webpage_url') or e.get('original_url') or e.get('url') or ''
        if vid and (not page_url or not str(page_url).startswith(('http://', 'https://'))):
            page_url = 'https://www.youtube.com/watch?v=' + str(vid)
        return {
            'id': vid,
            'title': e.get('title', 'Sin titulo'),
            'url': page_url,
            'thumb': self._thumb_path(self._fast_thumb(e.get('thumbnail') or '') or self._thumb_url_from_id(vid)),
            'duration': dur_txt,
            'channel': e.get('uploader', ''),
            'views': self._fmt_views(e.get('view_count')),
            'age': '',
            'color': idx % 5,
        }

    def _fmt_views(self, count):
        if not count:
            return ''
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f} M de vistas"
        if count >= 1_000:
            return f"{count / 1_000:.0f} K vistas"
        return f"{count} vistas"

    # ─── OPCIONES ──────────────────────────────────────────────
    def open_options(self, video):
        try:
            self.selected = video or {}
            options = self.get_screen('options')
            options.set_video(self.selected)
            options.set_mode('video')
            url = (video or {}).get('url') or ''
            if url:
                options.set_quality('Detectando calidades...')
                def detect():
                    try:
                        hs = self._available_heights(url)
                        Clock.schedule_once(lambda dt: self._apply_heights(hs))
                    except Exception:
                        Clock.schedule_once(lambda dt: options.set_quality('1080p'))
                threading.Thread(target=detect, daemon=True).start()
            else:
                options.set_quality('1080p')
            self.go('options')
        except Exception as exc:
            crashlog.write_crash('Error abriendo opciones:\n' + traceback.format_exc())
            self._info('No se pudo abrir', str(exc)[:180])

    def _apply_heights(self, hs):
        try:
            options = self.get_screen('options')
            if hs:
                options.set_heights(hs)
                best = f'{hs[0]}p'
                options.set_quality(best)
        except Exception:
            pass

    # ─── COLA ──────────────────────────────────────────────────
    def add_to_queue(self, video, notify=True):
        video = dict(video or {})
        url = video.get('url') or ''
        if not url:
            self._info('Cola', 'Este video no tiene enlace.')
            return
        if any((x.get('url') == url) for x in self.play_queue):
            if notify:
                self._info('Cola', 'El video ya esta en la cola.')
            return
        self.play_queue.append(video)
        crashlog.write_log('Cola: añadido ' + safe_text(video.get('title'), '')[:100])
        if notify:
            self._info('Añadido a la cola', f"{len(self.play_queue)} video(s) en espera.")

    def _remove_from_queue(self, video):
        url = (video or {}).get('url')
        if not url:
            return
        self.play_queue = [x for x in self.play_queue if x.get('url') != url]

    def _queue_next(self):
        if not self.play_queue:
            return None
        return self.play_queue.pop(0)

    def open_queue(self):
        if self._queue_dialog is not None:
            try:
                self._queue_dialog.dismiss()
            except Exception:
                pass
        d = ModalView(size_hint=(0.94, 0.84), background_color=(0,0,0,0.72), auto_dismiss=True)
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        rr(root, NAV, 18, BORDER)
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        head.add_widget(Label(text=f'Cola de reproduccion  ·  {len(self.play_queue)}',
                              color=WHITE, font_size=sp(15), bold=True, halign='left'))
        close = B(text='Cerrar', size_hint_x=None, width=dp(72), font_size=sp(10))
        rr(close, SUR2, 10, BORDER); close.bind(on_release=lambda *_: d.dismiss())
        head.add_widget(close); root.add_widget(head)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(2))
        body = BoxLayout(orientation='vertical', spacing=dp(7), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))
        if not self.play_queue:
            body.add_widget(Label(text='La cola esta vacia.\nUsa “Añadir a cola” desde un video.',
                                  color=MUTED, halign='center', valign='middle', text_size=(dp(280),dp(80)),
                                  size_hint_y=None, height=dp(90)))
        else:
            for idx, item in enumerate(self.play_queue):
                row = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(6))
                rr(row, SUR, 12, BORDER)
                title = Label(text=f'{idx+1}. {safe_text(item.get("title"), "Video")}',
                              color=WHITE, font_size=sp(9.5), halign='left', valign='middle',
                              shorten=True, shorten_from='right', text_size=(None,None))
                row.add_widget(title)
                play = B(text='', size_hint_x=None, width=dp(42))
                rr(play, RED, 9)
                btn_img(play, 'play', dp(14))
                rem = B(text='', size_hint_x=None, width=dp(42))
                rr(rem, SUR2, 9, BORDER)
                btn_img(rem, 'close', dp(12))
                rr(rem, SUR2, 9, BORDER)
                play.bind(on_release=lambda *_ , item=item: (self.play_queue.remove(item), d.dismiss(),
                                                               self.play_stream(item, '720p')))
                rem.bind(on_release=lambda *_ , item=item: (self.play_queue.remove(item), d.dismiss(), self.open_queue()))
                row.add_widget(play); row.add_widget(rem); body.add_widget(row)
        scroll.add_widget(body); root.add_widget(scroll)
        d.add_widget(root); self._queue_dialog=d; d.open()

    # ─── REPRODUCIR EN STREAMING ───────────────────────────────
    def open_video_menu(self, video):
        """Menu del resultado: reproducir, descargar o añadir a cola."""
        def play():
            d.dismiss(); self.open_play_quality(video)
        def download():
            d.dismiss(); self.open_options(video)
        def queue():
            d.dismiss(); self.add_to_queue(video)
        d = ModalView(size_hint=(0.88, None), height=dp(274), background_color=(0,0,0,0.55))
        box = Card(size_hint=(0.94,None), height=dp(262), pos_hint={'center_x':.5,'center_y':.5},
                   orientation='vertical', spacing=dp(8), padding=dp(14))
        box.add_widget(Label(text=safe_text(video.get('title',''),'Video'), color=WHITE, font_size=sp(12.5),
                             bold=True, halign='center', valign='middle', size_hint_y=None, height=dp(42),
                             shorten=True, shorten_from='right', text_size=(dp(230),dp(42))))
        pb=B(text='REPRODUCIR',font_size=sp(13.5),bold=True,color=(0,0,0,1),size_hint_y=None,height=dp(48))
        rr(pb,RED,12); pb.bind(on_release=lambda *_: play())
        qb=B(text='AÑADIR A COLA',font_size=sp(12),color=WHITE,size_hint_y=None,height=dp(44))
        rr(qb,SUR2,12,BORDER); qb.bind(on_release=lambda *_: queue())
        db=B(text='DESCARGAR',font_size=sp(12),color=WHITE,size_hint_y=None,height=dp(44))
        rr(db,SUR2,12,BORDER); db.bind(on_release=lambda *_: download())
        box.add_widget(pb); box.add_widget(qb); box.add_widget(db); d.add_widget(box)
        self._last_dialog=d; d.open()

    QNAMES = {2160: '4K Ultra HD', 1440: '2K QHD', 1080: 'Full HD', 720: 'HD',
              480: 'SD', 360: 'Baja', 240: 'Muy baja', 144: 'Minima'}

    def open_play_quality(self, video, player_callback=None):
        """Selecciona calidad mostrando SOLO las resoluciones que el video
        tiene realmente (hasta 4K/8K si existen). No descarga."""
        def start(q):
            try:
                d.dismiss()
            except Exception:
                pass
            if player_callback:
                player_callback(q)
            else:
                self.play_stream(video, q)
        d = ModalView(size_hint=(0.86, None), height=dp(360), background_color=(0, 0, 0, 0.55))
        box = Card(size_hint=(0.94, None), height=dp(348), pos_hint={'center_x': .5, 'center_y': .5},
                   orientation='vertical', spacing=dp(8), padding=dp(14))
        box.add_widget(Label(text='Calidad de reproduccion', color=WHITE, font_size=sp(14), bold=True,
                             halign='center', size_hint_y=None, height=dp(36)))
        rows = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        rows.bind(minimum_height=rows.setter('height'))
        status = Label(text='Detectando calidades disponibles...', color=MUTED,
                       font_size=sp(10.5), size_hint_y=None, height=dp(40))
        box.add_widget(status)
        box.add_widget(rows)

        def fill(heights):
            try:
                if d.parent is None:
                    return
            except Exception:
                return
            box.remove_widget(status)
            # Si solo detecta 360p (android muxed), mostrar igual opciones HD/FHD
            # porque ios/tv si las tienen para streaming; fill no debe limitar a 360p
            if heights and max(heights) > 360:
                top = [h for h in heights][:6]
                for h in reversed(top):
                    name = self.QNAMES.get(h, '')
                    txt = f'{h}p  ·  {name}' if name else f'{h}p'
                    b = B(text=txt, font_size=sp(12), color=WHITE, size_hint_y=None, height=dp(46))
                    rr(b, SUR, 12, BORDER)
                    b.bind(on_release=lambda *_, qq=f'{h}p': start(qq))
                    rows.add_widget(b)
                if len(rows.children) > 6:
                    pass
            else:
                # Fallback honesto: si no detecta calidades altas, ofrecerlas igual
                # (_resolve_stream intentara el resto de clientes para conseguirlas)
                for q, desc in [('1080p', 'Full HD'), ('720p', 'HD'), ('480p', 'SD'), ('360p', 'Baja')]:
                    b = B(text=f'{q}  ·  {desc}', font_size=sp(12), color=WHITE,
                          size_hint_y=None, height=dp(50))
                    rr(b, SUR, 12, BORDER)
                    b.bind(on_release=lambda *_, qq=q: start(qq))
                    rows.add_widget(b)

        url = (video or {}).get('url') or ''
        if url:
            def work():
                try:
                    hs = self._available_heights(url)
                except Exception as e:
                    crashlog.write_log('Error detectando calidades: ' + str(e)[:120])
                    hs = []
                Clock.schedule_once(lambda dt: fill(hs))
            threading.Thread(target=work, daemon=True).start()
        else:
            Clock.schedule_once(lambda dt: fill([]))
        d.add_widget(box)
        self._last_dialog = d
        d.open()

    def _resolve_stream(self, url, quality):
        """Obtiene el mejor stream <= res pedido y devuelve su URL directa.
        1) progresivo mp4 (android), 2) HLS m3u8 (ios, llega a 1080+).
        ffpyplayer reproduce HLS nativo porque usa ffmpeg por detras."""
        import yt_dlp
        res = int(str(quality or '720p').replace('p','') or 720)
        cache_key = (url, res)
        cached = self._stream_cache.get(cache_key)
        if cached and cached.get('url'):
            return cached
        attempts = [
            # v2.0.47 (05-09-2026): YouTube bloqueo visionos/tv/embedded/safari.
            # Los unicos que devuelven streams hoy son los android (360p).
            # Se prueban primero para no dejar el reproductor en negro.
            (f'best[height<={res}][vcodec!=none][acodec!=none]/best[height<={res}]/best', 'android'),
            (f'best[height<={res}][vcodec!=none][acodec!=none]/best[height<={res}]/best', 'android_vr'),
            (f'best[height<={res}][vcodec!=none][acodec!=none]/best[height<={res}]/best', 'visionos'),
            (f'best[height<={res}][vcodec!=none][acodec!=none]/best[height<={res}]/best', 'tv'),
            (f'best[height<={res}]/best[height<={res}]', 'web_embedded'),
            ('best[protocol^=m3u8]/best', 'web_safari'),
        ]
        last_err = None
        for fmt, client in attempts:
            try:
                opts = {
                    'quiet': True, 'no_warnings': True, 'noplaylist': True,
                    'nocheckcertificate': True, 'socket_timeout': 15,
                    'extractor_args': {'youtube': {'player_client': [client]}},
                    'format': fmt,
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                stream_url = info.get('url') or ''
                if not stream_url:
                    # Si es DASH, info puede tener requested_formats
                    req = info.get('requested_formats') or []
                    for f in req:
                        if f.get('url'):
                            stream_url = f['url']
                            break
                if not stream_url:
                    continue
                real_h = int(info.get('height') or 0)
                # Etiqueta: la calidad elegida cuando el stream real la alcanza;
                # si YouTube solo ofrece menos, se muestra la real (honesto).
                if real_h and real_h < int(res * 0.75):
                    label = f'{real_h}p'
                else:
                    label = f'{res}p'
                result = {
                    'url': stream_url,
                    'quality': label,
                    'duration': info.get('duration') or 0,
                    'title': info.get('title') or '',
                }
                self._stream_cache[cache_key] = result
                self._trim_cache(self._stream_cache)
                return result
            except Exception as e:
                last_err = e
                continue
        # Fallback Piped si todos los clientes dieron 403
        try:
            piped = self._piped_url(url, res)
            if piped:
                result = {'url': piped['url'], 'quality': f"{piped['height']}p" if piped.get('height') else f'{res}p', 'duration': piped.get('duration') or 0, 'title': piped.get('title') or ''}
                self._stream_cache[cache_key] = result
                return result
        except Exception:
            pass
        if last_err:
            raise last_err
        raise Exception('YouTube no devolvio un stream reproducible.')

    def _available_heights(self, url):
        """Resoluciones de VIDEO realmente disponibles (cacheado). Hilo.
        Ignora formatos de solo-audio: los HLS de audio reportan alturas
        falsas (27p/45p/90p) que confundian al menu de calidades."""
        key = ('heights', url)
        c = self._stream_cache.get(key)
        if c is not None:
            return c
        import yt_dlp
        opts = {
            'quiet': True, 'no_warnings': True, 'noplaylist': True,
            'skip_download': True, 'nocheckcertificate': True,
            'socket_timeout': 15, 'check_formats': False,
            # v2.0.47: android primero (resto bloqueado por YouTube).
            'extractor_args': {'youtube': {'player_client': ['android', 'android_vr', 'visionos', 'tv', 'web_embedded']}},
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        hs = set()
        for f in (info.get('formats') or []):
            h = f.get('height')
            vc = str(f.get('vcodec') or 'none')
            if h and vc != 'none':
                try:
                    h = int(h)
                    if h >= 144:
                        hs.add(h)
                except Exception:
                    pass
        out = sorted(hs, reverse=True)
        self._stream_cache[key] = out
        self._trim_cache(self._stream_cache)
        return out

    def _piped_url(self, url, res=720):
        """Fallback Piped: devuelve {'url':..., 'height':..., 'title':...} o None. Directo sin po_token."""
        try:
            import requests, certifi, re
            vid = ''
            if 'v=' in url:
                vid = url.split('v=')[1].split('&')[0].split('?')[0]
            else:
                m = re.search(r'youtu\.be/([^?&/]+)', url)
                if m: vid = m.group(1)
            if not vid: return None
            # v2.0.47: el unico Piped vivo (verificado 05-09-2026) primero.
            for host in ['https://api.piped.private.coffee', 'https://pipedapi.kavin.rocks', 'https://pipedapi-libre.kavin.rocks', 'https://piped-api.lunar.icu', 'https://pipedapi.adminforge.de', 'https://pipedapi.reallyaweso.me', 'https://pipedapi.drgns.space', 'https://pipedapi.owo.si', 'https://api.piped.yt']:
                try:
                    r = requests.get(f'{host}/streams/{vid}', timeout=12, verify=certifi.where(), headers={'User-Agent': 'Mozilla/5.0'})
                    r.raise_for_status()
                    j = r.json()
                    if not j.get('title') and not j.get('videoStreams'):
                        continue
                    vids = j.get('videoStreams') or []
                    # preferir muxed (videoOnly==False, mp4) para que tenga audio
                    muxed = [v for v in vids if v.get('url') and not v.get('videoOnly', True)]
                    pool = muxed or [v for v in vids if v.get('url')]
                    best = None
                    for v in pool:
                        h = v.get('height') or 0
                        try: h = int(h)
                        except: continue
                        if h <= res:
                            if best is None or h > (best.get('height') or 0):
                                best = v
                    if best:
                        return {'url': best['url'], 'height': best.get('height') or res, 'duration': j.get('duration') or 0, 'title': j.get('title') or ''}
                    # si no hay <=res, tomar el menor >res
                    for v in sorted(pool, key=lambda x: x.get('height') or 9999):
                        if v.get('url'):
                            return {'url': v['url'], 'height': v.get('height') or res, 'duration': j.get('duration') or 0, 'title': j.get('title') or ''}
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _piped_fallback(self, url, mode, quality):
        """Descarga via Piped cuando yt-dlp da 403. True si pudo descargar."""
        import re, requests, certifi, subprocess, tempfile
        m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})', url)
        if not m: return False
        vid = m.group(1)
        j = None
        for host in ['https://api.piped.private.coffee', 'https://pipedapi.kavin.rocks', 'https://pipedapi-libre.kavin.rocks', 'https://piped-api.lunar.icu', 'https://pipedapi.adminforge.de', 'https://pipedapi.reallyaweso.me', 'https://pipedapi.drgns.space', 'https://pipedapi.owo.si', 'https://api.piped.yt']:
            try:
                r = requests.get(f'{host}/streams/{vid}', timeout=15, verify=certifi.where(), headers={'User-Agent': 'Mozilla/5.0'})
                r.raise_for_status()
                j = r.json()
                if j.get('title') or j.get('videoStreams') or j.get('audioStreams'):
                    break
                j = None
            except Exception as he:
                crashlog.write_log(f'Piped host fallo {host}: ' + str(he)[:80])
                j = None
                continue
        try:
            if not j:
                return False
            title = re.sub(r'[\\/*?:"<>|]', '', j.get('title','video'))[:80] or vid
            def dl_stream(surl, out_path):
                with requests.get(surl, stream=True, timeout=30, headers={'User-Agent': 'Mozilla/5.0'}, verify=certifi.where()) as s:
                    s.raise_for_status()
                    with open(out_path, 'wb') as f:
                        for chunk in s.iter_content(8192):
                            if self.cancel_event.is_set(): raise InterruptedError('cancelled')
                            if chunk: f.write(chunk)
            if mode == 'audio':
                streams = sorted(j.get('audioStreams') or [], key=lambda x: int(x.get('bitrate') or 0), reverse=True)
                if not streams: return False
                out = os.path.join(self.download_path, f'{title}.mp3')
                tmp = out if streams[0]['url'].endswith('.mp3') else out.replace('.mp3', '.m4a')
                dl_stream(streams[0]['url'], tmp)
                if tmp != out:
                    ff = self._ensure_ffmpeg()
                    subprocess.run([ff or 'ffmpeg', '-y', '-i', tmp, out, '-q:a', '0'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    try: os.remove(tmp)
                    except: pass
                return True
            else:
                res = int(str(quality or '720p').replace('p','') or 720)
                v_streams = [s for s in j.get('videoStreams') or [] if s.get('height') and s.get('url')]
                v_streams = [s for s in v_streams if int(s['height']) <= res]
                v_streams.sort(key=lambda x: int(x['height']), reverse=True)
                a_streams = sorted(j.get('audioStreams') or [], key=lambda x: int(x.get('bitrate') or 0), reverse=True)
                if not v_streams or not a_streams: return False
                v_url, a_url = v_streams[0]['url'], a_streams[0]['url']
                out = os.path.join(self.download_path, f'{title}.mp4')
                tmp_v = os.path.join(tempfile.gettempdir(), f'{vid}_v.mp4')
                tmp_a = os.path.join(tempfile.gettempdir(), f'{vid}_a.m4a')
                dl_stream(v_url, tmp_v); dl_stream(a_url, tmp_a)
                ff = self._ensure_ffmpeg()
                subprocess.run([ff or 'ffmpeg', '-y', '-i', tmp_v, '-i', tmp_a, '-c', 'copy', out], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try: os.remove(tmp_v); os.remove(tmp_a)
                except: pass
                return True
        except Exception as e:
            crashlog.write_log('Piped fallback fallo: ' + str(e)[:150])
            return False

    def play_stream(self, video, quality='720p'):
        """Streaming real: resuelve la URL temporal y la entrega a ffpyplayer."""
        self._remove_from_queue(video)
        url=(video or {}).get('url') or ''
        if not url:
            self._info('Reproducir','Este video no tiene enlace disponible.'); return
        dlg=ModalView(size_hint=(0.9,None),height=dp(150),background_color=(0,0,0,0.65),auto_dismiss=False)
        box=Card(size_hint=(0.94,None),height=dp(138),pos_hint={'center_x':.5,'center_y':.5},
                 orientation='vertical',spacing=dp(8),padding=dp(14))
        lb=Label(text='Conectando con el stream...',color=WHITE,font_size=sp(12),halign='center',
                 valign='middle',text_size=(None,None))
        box.add_widget(lb); dlg.add_widget(box); self._last_dialog=dlg; dlg.open()
        def worker():
            try:
                stream=self._resolve_stream(url,quality)
                item=dict(video); item['stream_url']=stream['url']; item['stream_quality']=stream['quality']
                Clock.schedule_once(lambda dt: (self._dismiss_dialog(dlg),self._play_internal(stream['url'],item)))
            except Exception as e:
                err=str(e)[:180]; crashlog.write_log('Error streaming: '+err)
                Clock.schedule_once(lambda dt: (self._dismiss_dialog(dlg),
                    self._fallback_play_download(url, video, quality)))
        threading.Thread(target=worker,daemon=True).start()

    def _fallback_play_download(self, url, video, quality):
        """Fallback de emergencia: solo se usa si el stream directo no puede abrirse."""
        import yt_dlp
        dlg=ModalView(size_hint=(0.9,None),height=dp(150),background_color=(0,0,0,0.65),auto_dismiss=False)
        box=Card(size_hint=(0.94,None),height=dp(138),pos_hint={'center_x':.5,'center_y':.5},
                 orientation='vertical',spacing=dp(8),padding=dp(14))
        lb=Label(text='Streaming no disponible. Preparando fallback local...',color=WHITE,font_size=sp(11),
                 halign='center',valign='middle',text_size=(None,None))
        bar=ProgressBar(max=100,value=0,size_hint_y=None,height=dp(10))
        box.add_widget(lb); box.add_widget(bar); dlg.add_widget(box); dlg.open()
        out_dir=os.path.join(self._default_download_path(),'.reproducir')
        os.makedirs(out_dir,exist_ok=True)
        def hook(d):
            try:
                if d.get('status')=='downloading':
                    total=d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    done=d.get('downloaded_bytes') or 0
                    p=int(done*100/total) if total else 0
                    Clock.schedule_once(lambda dt,p=p:setattr(bar,'value',p))
            except Exception: pass
        def worker():
            try:
                opts={'outtmpl':os.path.join(out_dir,'%(title).80s.%(ext)s'),
                      'progress_hooks':[hook],'quiet':True,'no_warnings':True,
                      'nocheckcertificate':True,'socket_timeout':20,
                      # v2.0.47: android primero (resto bloqueado por YouTube).
                'extractor_args':{'youtube':{'player_client':['android','android_vr','visionos','tv','web_embedded']}},
                      'format':f'bestvideo[height<={int(str(quality).replace("p","") or 720)}]+bestaudio/best[height<={int(str(quality).replace("p","") or 720)}]/best',
                      'merge_output_format':'mp4'}
                ff=self._ensure_ffmpeg()
                if ff: opts['ffmpeg_location']=ff
                with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
                found=None
                for name in os.listdir(out_dir):
                    if name.lower().endswith(('.mp4','.mkv','.webm')):
                        pth=os.path.join(out_dir,name)
                        if os.path.isfile(pth) and os.path.getsize(pth)>20000:
                            found=pth; break
                if not found: raise Exception('No se genero el archivo temporal.')
                item=dict(video); item['title']=item.get('title') or os.path.basename(found)
                Clock.schedule_once(lambda dt:(self._dismiss_dialog(dlg),setattr(self,'_play_temp',found),
                                               self._play_internal(found,item)))
            except Exception as e:
                err=str(e)[:180]; crashlog.write_log('Fallback reproduccion fallo: '+err)
                Clock.schedule_once(lambda dt:(self._dismiss_dialog(dlg),
                                               self._info('Reproduccion','No se pudo reproducir el video.\n'+err)))
        threading.Thread(target=worker,daemon=True).start()

    def _stream_switch(self, v, item, quality, busy_label=None):
        url=(item or {}).get('url') or ''
        if not url: return
        if busy_label: busy_label.text='Cambiando calidad...'
        def worker():
            try:
                stream=self._resolve_stream(url,quality)
                Clock.schedule_once(lambda dt: self._apply_stream(v,item,stream,busy_label))
            except Exception as e:
                err=str(e)[:160]
                Clock.schedule_once(lambda dt: self._info('Calidad', 'No se pudo cambiar la calidad.\n'+err))
        threading.Thread(target=worker,daemon=True).start()

    def _apply_stream(self, v, item, stream, busy_label=None):
        try:
            pos=v.position or 0
            was_playing = v.state == 'play'
            # No limpiar source/texture para evitar flash blanco; solo cambiar url
            v.source=stream['url']
            if was_playing:
                v.state='play'
            # Restaurar posicion cuando el nuevo stream tenga duration
            def _restore(dt):
                try:
                    if pos and v.duration:
                        p = max(0, min(pos, v.duration))
                        if p < 36000:
                            v.seek(p / v.duration) if v.duration else setattr(v, 'position', p)
                except Exception:
                    pass
            Clock.schedule_once(_restore, 0.4)
            Clock.schedule_once(_restore, 0.9)
            item['stream_url']=stream['url']; item['stream_quality']=stream['quality']
            if busy_label: busy_label.text=stream['quality']
        except Exception as e:
            crashlog.write_log('Error aplicando calidad: '+str(e)[:140])

    def _open_speed(self, v):
        d=ModalView(size_hint=(0.72,None),height=dp(270),background_color=(0,0,0,0.65))
        box=Card(size_hint=(0.92,None),height=dp(250),pos_hint={'center_x':.5,'center_y':.5},
                 orientation='vertical',spacing=dp(7),padding=dp(12))
        box.add_widget(Label(text='Velocidad',color=WHITE,font_size=sp(14),bold=True,size_hint_y=None,height=dp(30)))
        for rate in (0.5,0.75,1.0,1.25,1.5,2.0):
            b=B(text=f'{rate:g}x',font_size=sp(12),color=WHITE,size_hint_y=None,height=dp(32))
            rr(b,SUR,9,BORDER)
            b.bind(on_release=lambda *_ ,r=rate:(d.dismiss(),self._set_playback_rate(v,r)))
            box.add_widget(b)
        d.add_widget(box); d.open()

    def _set_playback_rate(self, v, rate):
        ok=False
        for obj in (getattr(v,'_video',None), getattr(v,'_player',None)):
            if obj is None: continue
            for name in ('set_playback_rate','set_rate','set_speed'):
                try:
                    fn=getattr(obj,name,None)
                    if fn: fn(rate); ok=True; break
                except Exception: pass
            if ok: break
        if not ok:
            self._info('Velocidad', 'Esta version de ffpyplayer no expone control de velocidad.')
        else:
            crashlog.write_log(f'Velocidad de reproduccion: {rate}x')

    def _play_next_queue(self):
        nxt=self._queue_next()
        if nxt:
            self.play_stream(nxt,'720p')
            return True
        return False

    def _jni_fs(self, fs):
        """Oculta/muestra las barras del sistema en el hilo de UI de Android."""
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            act = PythonActivity.mActivity

            def _set():
                try:
                    decor = act.getWindow().getDecorView()
                    flags = decor.getSystemUiVisibility()
                    if fs:
                        flags = flags | 0x1 | 0x2 | 0x4 | 0x200 | 0x1000
                    else:
                        flags = flags & ~(0x1 | 0x2 | 0x4 | 0x200 | 0x1000)
                    decor.setSystemUiVisibility(flags)
                except Exception as e:
                    crashlog.write_log('Fullscreen fallo: ' + str(e)[:120])

            act.runOnUiThread(_set)
        except Exception as e:
            crashlog.write_log('Fullscreen fallo: ' + str(e)[:120])

    def _jni_rotation(self, landscape=False):
        """Mantiene la app vertical y solo usa horizontal en fullscreen."""
        try:
            from jnius import autoclass
            ActivityInfo = autoclass('android.content.pm.ActivityInfo')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            act = PythonActivity.mActivity
            orientation = (ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
                           if landscape else ActivityInfo.SCREEN_ORIENTATION_PORTRAIT)

            def _set_orientation():
                try:
                    act.setRequestedOrientation(orientation)
                except Exception as e:
                    crashlog.write_log('Orientacion UI fallo: ' + str(e)[:120])

            act.runOnUiThread(_set_orientation)
        except Exception as e:
            crashlog.write_log('Orientacion fallo: ' + str(e)[:120])

    def _start_tilt_autorotate(self, state, toggle_fs):
        """Detecta el giro FISICO del telefono con el acelerometro (plyer),
        independiente del auto-rotate del sistema. Solo actua si el fullscreen
        actual lo puso el propio giro (no pisa el boton manual)."""
        try:
            from plyer import accelerometer
            accelerometer.enable()
        except Exception as e:
            crashlog.write_log('Acelerometro no disponible: ' + str(e)[:120])
            return

        state['_tilt_auto'] = False

        def _poll(_dt):
            try:
                acc = accelerometer.acceleration
                ax, ay, az = acc[:3]
            except Exception:
                return
            if ax is None or ay is None:
                return
            landscape = abs(ax) > 6.0 and abs(ax) > abs(ay) * 1.3
            portrait = abs(ay) > 6.0 and abs(ay) > abs(ax) * 1.3
            if landscape and not state['fs']:
                state['_tilt_auto'] = True
                toggle_fs()
            elif portrait and state['fs'] and state.get('_tilt_auto'):
                state['_tilt_auto'] = False
                toggle_fs()

        state['_tilt_ev'] = Clock.schedule_interval(_poll, 0.35)

    def _stop_tilt_autorotate(self, state):
        ev = state.get('_tilt_ev')
        if ev:
            try:
                ev.cancel()
            except Exception:
                pass
        try:
            from plyer import accelerometer
            accelerometer.disable()
        except Exception:
            pass

    def _play_internal(self, source, item=None):
        """Reproductor interno tipo YouTube para archivos locales o streams HTTPS."""
        global Video
        self._player_fallback=False
        if Video is None:
            try:
                from kivy.uix.video import Video as _Video
                Video=_Video
            except Exception:
                crashlog.write_log('Reproductor: no se pudo importar Video: '+str(sys.exc_info()[1])[:200])
                self._info('Reproductor','El reproductor de video no esta disponible.')
                return
        try:
            title=safe_text((item or {}).get('title',''),os.path.basename(source))
            state={'mode':'video','fs':False,'drag':False,'failed':False,'hidden':False,
                   'sound':None,'ended':False,'rate':1.0,'manual_fs':False,'land':False}
            root=TouchBlockingFloatLayout()
            with root.canvas.before:
                Color(0,0,0,1)
                root._bg=Rectangle(pos=root.pos,size=root.size)
            def _bg_sync(*_):
                root._bg.pos=root.pos; root._bg.size=root.size
            root.bind(pos=_bg_sync,size=_bg_sync)
            v=Video(source=source,state='play',volume=1,allow_stretch=True,keep_ratio=True,
                    size_hint=(1,1),pos_hint={'x':0,'y':0})
            root.add_widget(v)

            # Capa de toque: no roba los eventos de los controles porque queda debajo.
            touch_layer=B(text='',size_hint=(1,1),pos_hint={'x':0,'y':0})
            touch_layer.background_color=(0,0,0,0)
            root.add_widget(touch_layer)

            top=BoxLayout(size_hint=(1,None),height=dp(44),spacing=dp(10),
                          padding=(dp(12),dp(5)))
            rr(top,(0,0,0,0.50),0)
            tl=Label(text=title,color=WHITE,font_size=sp(11),bold=True,halign='left',valign='middle',
                     shorten=True,shorten_from='right',text_size=(None,None),size_hint_x=1)
            tl.bind(width=lambda *_: setattr(tl, 'text_size', (tl.width, None)))
            top.add_widget(tl)
            qlabel=B(text='HD',font_size=sp(10),bold=True,color=WHITE,size_hint_x=None,width=dp(52)); rr(qlabel,(1,1,1,0.14),19,None)
            speed=B(text='',size_hint_x=None,width=dp(38)); rr(speed,(1,1,1,0.14),19,None); btn_img(speed,'speed',dp(18))
            fsb=B(text='',size_hint_x=None,width=dp(38)); rr(fsb,(1,1,1,0.14),19,None)
            fsb_img=btn_img(fsb,'fs',dp(18))
            cb=B(text='',size_hint_x=None,width=dp(38)); rr(cb,RED,19,None); btn_img(cb,'close',dp(17))
            top.add_widget(qlabel); top.add_widget(speed); top.add_widget(fsb); top.add_widget(cb)
            root.add_widget(top)

            bottom=BoxLayout(size_hint=(1,None),height=dp(50),spacing=dp(10),
                             padding=(dp(12),dp(6)))
            rr(bottom,(0,0,0,0.50),0)
            pb=B(text='',size_hint_x=None,width=dp(40))
            coin_bg(pb, dp(40))
            pb_img=btn_img(pb,'pause',dp(18))
            prev=B(text='',size_hint_x=None,width=dp(38)); rr(prev,(1,1,1,0.14),19,None); btn_img(prev,'prev',dp(17))
            nxt=B(text='',size_hint_x=None,width=dp(38)); rr(nxt,(1,1,1,0.14),19,None); btn_img(nxt,'next',dp(17))
            # Solo mostrar prev/next si es playlist (mas de 1 en cola)
            if len(getattr(self, 'play_queue', [])) <= 1:
                for w in (prev, nxt):
                    w.opacity = 0; w.disabled = True; w.width = dp(0)

            def _seek_video(val):
                # SeekBar da segundos; Video.seek espera 0-1
                try:
                    if v.duration:
                        v.seek(max(0, min(val, v.duration)) / v.duration)
                except Exception:
                    pass
            sl=SeekBar(on_seek=_seek_video)
            tml=Label(text='0:00 / 0:00',color=WHITE,font_size=sp(9),size_hint_x=None,width=dp(76))
            ab=B(text='',size_hint_x=None,width=dp(38)); rr(ab,(1,1,1,0.14),19,None); btn_img(ab,'audio',dp(17))
            qb=B(text='',size_hint_x=None,width=dp(38)); rr(qb,(1,1,1,0.14),19,None); btn_img(qb,'queue',dp(17))
            bottom.add_widget(pb); bottom.add_widget(prev); bottom.add_widget(nxt); bottom.add_widget(sl)
            bottom.add_widget(tml); bottom.add_widget(ab); bottom.add_widget(qb)
            root.add_widget(bottom)

            # Barra fina superior tipo YouTube.
            thin=ProgressBar(max=1,value=0,size_hint=(1,None),height=dp(2))
            root.add_widget(thin)

            def sync_player_layout(*_):
                # Controles pegados al rect del video (16:9 centrado): en vertical
                # quedan sobre el video, no en franjas negras; en horizontal el
                # rect es ventana completa y nada se corta.
                try:
                    root.size=Window.size; root.pos=(0,0)
                    sw,sh=float(Window.size[0]),float(Window.size[1])
                    ar=16.0/9.0
                    if sw/sh > ar:
                        vh=sh; vw=sh*ar; vx=(sw-vw)/2; vy=0
                    else:
                        vw=sw; vh=sw/ar; vx=0; vy=(sh-vh)/2
                    v.pos=(vx,vy); v.size=(vw,vh)
                    touch_layer.pos=(vx,vy); touch_layer.size=(vw,vh)
                    top.pos=(vx, vy+vh-top.height); top.width=vw
                    bottom.pos=(vx, vy); bottom.width=vw
                    thin.pos=(vx, vy+vh-thin.height); thin.width=vw
                    land=sh<sw
                    if land!=state['land']:
                        state['land']=land
                        if state['mode']=='video' and v.state=='play':
                            # Girar con Kivy a veces deja el render del video en
                            # coordenadas viejas; reiniciar la reproduccion lo
                            # fuerza a redibujarse al nuevo tamano.
                            v.state='pause'
                            Clock.schedule_once(lambda dt: setattr(v,'state','play'),0.25)
                except Exception:
                    pass

            def on_close_player(*_):
                try: v.state='stop'; v.source=''
                except Exception: pass
                if state['sound'] is not None:
                    try: state['sound'].stop(); state['sound'].unload()
                    except Exception: pass
                    state['sound']=None
                if getattr(self,'_play_temp',None)==source:
                    try:
                        os.remove(source)
                        crashlog.write_log('Reproductor: temporal borrado '+os.path.basename(source))
                    except Exception: pass
                    self._play_temp=None
                if state['fs']:
                    self._jni_fs(False)
                self._jni_rotation(False)
                for ev in hide_ev:
                    if ev:
                        try: ev.cancel()
                        except Exception: pass
                try: tick_ev.cancel()
                except Exception: pass
                self._stop_tilt_autorotate(state)
                self._player_dialog=None
            d=PlayerOverlay(root,sync_player_layout,on_close_player)
            self._last_dialog=d; self._player_dialog=d
            d.open()
            # Al abrir el reproductor NO se gira el telefono.
            crashlog.write_log('Reproductor interno abierto: '+safe_text((item or {}).get('title'),os.path.basename(source)))
            t0=[time.time()]
            hide_ev=[None]
            last_touch=[time.time()]

            def show_controls(*_):
                state['hidden']=False; top.opacity=1; bottom.opacity=1; thin.opacity=1
                last_touch[0]=time.time()
                if hide_ev[0]: 
                    try: hide_ev[0].cancel()
                    except Exception: pass
                hide_ev[0]=Clock.schedule_once(lambda dt: hide_controls(),3.0)

            def hide_controls(*_):
                if state['mode']=='video' and v.state=='play':
                    state['hidden']=True; top.opacity=0; bottom.opacity=0; thin.opacity=0

            def tap(*_):
                if state['hidden']: show_controls()
                else: show_controls()
            touch_layer.bind(on_release=tap)
            show_controls()

            def _set_mode(mode):
                if mode=='audio':
                    v.state='stop'
                    if state['sound'] is None:
                        try:
                            from kivy.core.audio import SoundLoader
                            state['sound']=SoundLoader.load(source)
                            if state['sound'] is None: raise Exception('No se pudo cargar audio')
                            state['sound'].volume=1; state['sound'].play()
                        except Exception as e:
                            self._info('Audio','No se pudo activar el modo audio.'); crashlog.write_log('Audio fallo: '+str(e)[:120])
                    v.opacity=0; state['mode']='audio'
                else:
                    if state['sound'] is not None:
                        try: state['sound'].stop(); state['sound'].unload()
                        except Exception: pass
                        state['sound']=None
                    v.opacity=1; state['mode']='video'; v.state='play'
                show_controls()
            ab.bind(on_release=lambda *_:_set_mode('audio' if state['mode']!='audio' else 'video'))

            def toggle_play(*_):
                if state['mode']=='audio' and state['sound'] is not None:
                    if getattr(state['sound'],'state','')=='playing':
                        state['sound'].stop(); set_icon(pb_img,'play')
                    else:
                        state['sound'].play(); set_icon(pb_img,'pause')
                else:
                    if v.state=='play': v.state='pause'; set_icon(pb_img,'play')
                    else: v.state='play'; set_icon(pb_img,'pause')
                show_controls()
            pb.bind(on_release=toggle_play)

            def go_next(*_):
                if not self._play_next_queue():
                    self._info('Cola','No hay mas videos en la cola.')
                else:
                    d.dismiss()
            nxt.bind(on_release=go_next)

            prev.bind(on_release=lambda *_: self._info('Reproductor','El retroceso de video se controla con la barra de progreso.'))

            qlabel.bind(on_release=lambda *_: self.open_play_quality(item or {}, lambda q:self._stream_switch(v,item,q,qlabel)))
            speed.bind(on_release=lambda *_: self._open_speed(v))

            def toggle_fs(*_):
                state['fs'] = not state['fs']
                state['manual_fs'] = state['fs']
                set_icon(fsb_img, 'fs_exit' if state['fs'] else 'fs')
                if state['fs']:
                    self._jni_fs(True)
                    self._jni_rotation(True)
                else:
                    self._jni_fs(False)
                    self._jni_rotation(False)
                show_controls()
                # Esperar al nuevo tamano de la ventana evita que X/fullscreen
                # queden en una coordenada vieja durante el giro.
                Clock.schedule_once(sync_player_layout, 0.10)
                Clock.schedule_once(sync_player_layout, 0.40)
            fsb.bind(on_release=toggle_fs)
            cb.bind(on_release=lambda *_: d.dismiss())
            qb.bind(on_release=lambda *_: self.open_queue())
            self._start_tilt_autorotate(state, toggle_fs)

            def _tick(_dt):
                try:
                    # No se usa el sensor: la orientacion solo cambia mediante
                    # el boton de pantalla completa.
                    sync_player_layout()
                    dur=v.duration or 0; pos=v.position or 0
                    if dur:
                        pos = max(0, min(pos, dur))
                        sl.set_range(dur); sl.set_value(pos)
                    if dur:
                        fm=lambda x:f"{int(x//60)}:{int(x%60):02d}"
                        tml.text=f"{fm(pos)} / {fm(dur)}"; thin.value=min(1,max(0,pos/dur))
                    qlabel.text=safe_text(item.get('stream_quality','HD') if item else 'HD','HD')
                    if state['mode']=='video' and v.state=='play' and not state['hidden'] and (time.time()-last_touch[0])>3:
                        hide_controls()
                    if state['mode']=='video' and v.state=='play' and (time.time()-t0[0])>8 and v.texture is None:
                        # v2.0.48: el stream nunca cargo (403/expirado/CDN caido).
                        # No dejar el player negro congelado: ir al fallback.
                        d.dismiss()
                        url=(item or {}).get('url') or ''
                        if url:
                            self._fallback_play_download(url, item, (item or {}).get('stream_quality','720p'))
                        else:
                            self._info('Reproductor','No se pudo cargar el stream de video.')
                        return
                    if dur and pos >= dur-0.7 and not state['ended']:
                        state['ended']=True
                        if self.play_queue:
                            d.dismiss(); Clock.schedule_once(lambda dt:self._play_next_queue(),0.15)
                except Exception: pass
            tick_ev=Clock.schedule_interval(_tick,0.25)
        except Exception as e:
            crashlog.write_log('Reproductor: error: '+str(e)[:180]+'\n'+traceback.format_exc())
            self._info('Reproductor','No se pudo abrir el reproductor interno.')
            if (item or {}).get('public_uri'): self.play_download(item)

    def _play_progress(self, lb, bar, p, st):
        try:
            bar.value = p
            if p < 100:
                lb.text = ('Descargando para reproducir... ' + st) if st else 'Descargando para reproducir...'
            else:
                lb.text = 'Procesando...'
        except Exception:
            pass

    def _dismiss_dialog(self, dlg):
        try:
            dlg.dismiss()
        except Exception:
            pass



    def paste_link(self, field):
        try:
            from kivy.core.clipboard import Clipboard
            txt = Clipboard.paste()
            if txt:
                field.text = txt.strip()
            if field.text.strip():
                self.analyze_url(field.text)
        except Exception as e:
            crashlog.write_log('Error pegando enlace: ' + str(e)[:120])

    # ─── DESCARGA ──────────────────────────────────────────────
    def analyze_url(self, url):
        url = (url or '').strip()
        if not url:
            self._info('Enlace', 'Pega un enlace de video o musica.')
            return
        if not url.startswith('http://') and not url.startswith('https://'):
            self._info('Enlace no valido', 'El enlace debe empezar con http:// o https://')
            return
        self._pending_url = url
        if 'analyze' in self.screen_names:
            self.get_screen('analyze').set_url(url)
            self.go('analyze')

    def analyze_current_url(self):
        url = getattr(self, '_pending_url', '')
        if not url or not self._setup_done:
            return
        threading.Thread(target=self._analyze_thread, args=(url,), daemon=True).start()

    def _analyze_thread(self, url):
        import yt_dlp
        analyze = self.get_screen('analyze')
        try:
            Clock.schedule_once(lambda dt: analyze.set_step(0))
            is_playlist = 'list=' in url or '/playlist' in url
            info = None
            last_err = None
            # v2.0.47: android primero (unicos que responden hoy); resto de respaldo.
            for _cl in [['android'], ['android_vr'], ['visionos'], ['tv'], ['web_embedded'], ['web_safari']]:
                try:
                    opts = {
                        'quiet': True, 'no_warnings': True,
                        'noplaylist': False if is_playlist else True,
                        'skip_download': True, 'nocheckcertificate': True,
                        'socket_timeout': 15, 'extract_flat': False,
                        'check_formats': False,
                        'extractor_args': {'youtube': {'player_client': _cl, 'player_skip': ['webpage']}},
                    }
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        Clock.schedule_once(lambda dt: analyze.set_step(1))
                        info = ydl.extract_info(url, download=False)
                    if info:
                        break
                except Exception as ce:
                    last_err = ce
                    crashlog.write_log(f'Analyze fallo {_cl}: ' + str(ce)[:100])
                    continue
            # v2.0.48: Piped ante CUALQUIER error (no solo 403).
            if not info and last_err:
                # metadata via Piped para poder seguir a descarga/streaming
                try:
                    import re, requests, certifi
                    _vid = ''
                    if 'v=' in url:
                        _vid = url.split('v=')[1].split('&')[0].split('?')[0]
                    else:
                        _m = re.search(r'youtu\.be/([^?&/]+)', url)
                        if _m: _vid = _m.group(1)
                    # v2.0.47: el unico Piped vivo (verificado 05-09-2026) primero.
                    for _h in ['https://api.piped.private.coffee', 'https://pipedapi.kavin.rocks', 'https://pipedapi-libre.kavin.rocks', 'https://piped-api.lunar.icu', 'https://pipedapi.adminforge.de', 'https://pipedapi.reallyaweso.me', 'https://pipedapi.drgns.space', 'https://api.piped.yt']:
                        try:
                            _r = requests.get(f'{_h}/streams/{_vid}', timeout=12, verify=certifi.where(), headers={'User-Agent': 'Mozilla/5.0'})
                            _r.raise_for_status()
                            _j = _r.json()
                            if _j.get('title'):
                                _hs = set()
                                for _vf in (_j.get('videoStreams') or []):
                                    try:
                                        _hh = int(_vf.get('height') or 0)
                                        if _hh >= 144 and _vf.get('url'):
                                            _hs.add(_hh)
                                    except Exception:
                                        pass
                                info = {'id': _vid, 'title': _j.get('title', 'Video'), 'duration': _j.get('duration') or 0, 'uploader': _j.get('uploader') or '', 'webpage_url': url, 'thumbnail': _j.get('thumbnailUrl') or '', '_piped': True, '_piped_heights': sorted(_hs, reverse=True)}
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
            if not info and last_err:
                raise last_err
            if not info:
                raise RuntimeError('No se pudo obtener la informacion.')
            if info.get('_type') == 'playlist' or info.get('entries'):
                entries = list(info.get('entries') or [])
                entries = [e for e in entries if e and e.get('id')]
                if not entries:
                    raise RuntimeError('La playlist esta vacia o no se pudo leer.')
                Clock.schedule_once(lambda dt, ents=entries, u=url: self._playlist_detected(ents, u))
                return
            if not info.get('id'):
                raise RuntimeError('No se pudo obtener la informacion del video.')
            video = self._to_video(info, 0)
            video['url'] = info.get('webpage_url') or url
            try:
                hs = set(info.get('_piped_heights') or [])
                for f in (info.get('formats') or []):
                    h = f.get('height')
                    vc = str(f.get('vcodec') or 'none')
                    if h and vc != 'none':
                        h = int(h)
                        if h >= 144:
                            hs.add(h)
                video['_heights'] = sorted(hs, reverse=True)
            except Exception:
                video['_heights'] = []
            Clock.schedule_once(lambda dt, v=video: self._analysis_done(v))
        except Exception as e:
            err = str(e)[:180]
            crashlog.write_log('Error analizando enlace: ' + err)
            Clock.schedule_once(lambda dt, m=err: self._analysis_error(m))

    def _playlist_detected(self, entries, url):
        self._playlist_entries = entries
        self._playlist_url = url
        count = len(entries)
        titles = '\n'.join([f"  {i+1}. {safe_text(e.get('title',''), 'Video')}" for i, e in enumerate(entries[:10])])
        if count > 10:
            titles += f"\n  ... y {count - 10} mas"
        self._info('Playlist detectada',
                    f'{count} videos encontrados.\n\n{titles}\n\n'
                    'Se descargaran todos en calidad video (mejor disponible) '
                    'o podes cancelar.',
                    on_ok=lambda: self._start_playlist_download(),
                    ok_text='Descargar todo')

    def _start_playlist_download(self):
        entries = getattr(self, '_playlist_entries', [])
        if not entries:
            return
        self._playlist_queue = list(entries)
        self._playlist_downloaded = 0
        self._playlist_total = len(entries)
        self._info('Descargando playlist',
                    f'0/{self._playlist_total} videos descargados. '
                    'La descarga empezara en segundo plano.')
        threading.Thread(target=self._playlist_download_thread, daemon=True).start()

    def _playlist_download_thread(self):
        import yt_dlp
        _patch_ytdlp_write_string()
        ffmpeg_bin = self._ensure_ffmpeg()
        while self._playlist_queue:
            entry = self._playlist_queue.pop(0)
            vid_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id','')}"
            vid_title = safe_text(entry.get('title', ''), 'video')
            try:
                opts = {
                    'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                    'nocheckcertificate': True, 'quiet': True, 'no_warnings': True,
                    'socket_timeout': 20, 'continuedl': True, 'retries': 5,
                    'fragment_retries': 5, 'concurrent_fragment_downloads': 2,
                    'windowsfilenames': True, 'noprogress': True,
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    # v2.0.47: android primero (resto bloqueado por YouTube).
                    'extractor_args': {'youtube': {'player_client': ['android', 'android_vr', 'visionos', 'tv', 'web_embedded']}},
                }
                if ffmpeg_bin:
                    opts['ffmpeg_location'] = ffmpeg_bin
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([vid_url])
                self._playlist_downloaded += 1
                crashlog.write_log(f'Playlist: {self._playlist_downloaded}/{self._playlist_total} - {vid_title[:40]}')
            except Exception as e:
                crashlog.write_log(f'Playlist error ({vid_title[:30]}): {str(e)[:100]}')
            time.sleep(1)
        self._published = self._publish_new_files()
        total = self._playlist_total
        done = self._playlist_downloaded
        Clock.schedule_once(lambda dt: self._info('Playlist completada',
            f'{done}/{total} videos descargados exitosamente.'))
        self.downloading = False

    def _analysis_done(self, video):
        self.selected = video
        analyze = self.get_screen('analyze')
        analyze.set_step(3)
        opts = self.get_screen('options')
        opts.set_video(video)
        opts.set_mode('video')
        heights = video.pop('_heights', None)
        if heights:
            opts.set_heights(heights)
            best = f'{heights[0]}p' if heights else '4320p'
            opts.set_quality(best)
        else:
            opts.set_quality('1080p')
        Clock.schedule_once(lambda dt: self.go('options'), 0.25)

    def _analysis_error(self, msg):
        analyze = self.get_screen('analyze')
        analyze.set_step(1)
        self._info('No se pudo analizar', msg)
        Clock.schedule_once(lambda dt: self.go('home'), 0.1)

    def start_download(self):
        if not self.selected:
            self._info('Opciones de descarga', 'Selecciona un video primero.')
            return
        opts = self.get_screen('options')
        self.current_mode = opts.mode
        self.current_quality = opts.quality
        self.cancel_event.clear()
        self.paused = False
        self.downloading = True
        self.get_screen('downloading').set_info(self.selected)
        self.go('downloading')
        self._launch_download_thread()

    # ─── MUSICA ────────────────────────────────────────────────
    def music_search(self, query):
        query = (query or '').strip()
        if not query:
            return
        self.go('music')
        self.get_screen('music').set_query(query)
        threading.Thread(target=self._music_search_thread, args=(query,), daemon=True).start()

    def _music_search_thread(self, query):
        import yt_dlp
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True, 'noplaylist': True,
                        'check_formats': False, 'nocheckcertificate': True,
                        'socket_timeout': 15, 'extract_flat': True,
                        # v2.0.48: android primero (default web bloqueado).
                        'extractor_args': {'youtube': {'player_client': ['android', 'android_vr', 'visionos', 'tv', 'web_embedded']}}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info('ytsearch10:' + query, download=False)
            items = []
            for idx, e in enumerate((results.get('entries') or [])):
                if not e or not e.get('id'):
                    continue
                vid = e.get('id') or ''
                page_url = 'https://www.youtube.com/watch?v=' + str(vid)
                dur = e.get('duration') or 0
                dur_txt = f"{int(dur // 60)}:{int(dur % 60):02d}" if dur else ''
                items.append({
                    'title': e.get('title', 'Sin titulo'),
                    'url': page_url,
                    'duration': dur_txt,
                    'channel': e.get('uploader', ''),
                    'color': idx % 5,
                })
            Clock.schedule_once(lambda dt, it=items: self.get_screen('music').show_results(it))
        except Exception as e:
            err = str(e)[:150]
            crashlog.write_log("Error musica: " + err)
            # v2.0.48: fallback Piped antes de mostrar error (misma idea que search).
            try:
                import requests, certifi
                from urllib.parse import quote as _q
                items = []
                for _h in ['https://api.piped.private.coffee', 'https://pipedapi.kavin.rocks', 'https://pipedapi-libre.kavin.rocks']:
                    try:
                        _r = requests.get(f'{_h}/search?q={_q(query)}&filter=music_songs', timeout=12, verify=certifi.where(), headers={'User-Agent': 'Mozilla/5.0'})
                        _r.raise_for_status()
                        _j = _r.json()
                        for _idx, _en in enumerate((_j.get('items') or _j.get('content') or [])[:10]):
                            _vid = _en.get('url', '').split('v=')[-1].split('&')[0] if 'v=' in str(_en.get('url','')) else str(_en.get('url','')).rstrip('/').split('/')[-1]
                            if not _vid or len(_vid) != 11:
                                continue
                            _dur = _en.get('duration') or 0
                            try: _dur = int(_dur)
                            except Exception: _dur = 0
                            _dtxt = f"{_dur // 60}:{_dur % 60:02d}" if _dur and _dur > 0 else ''
                            items.append({'title': _en.get('title', 'Sin titulo'), 'url': f'https://www.youtube.com/watch?v={_vid}', 'duration': _dtxt, 'channel': _en.get('uploaderName', ''), 'color': _idx % 5})
                        if items:
                            break
                    except Exception:
                        continue
                if items:
                    Clock.schedule_once(lambda dt, it=items: self.get_screen('music').show_results(it))
                    return
            except Exception:
                pass
            Clock.schedule_once(lambda dt: self.get_screen('music').show_error(err))

    def music_download(self, item):
        """Descarga solo el audio de la canción seleccionada."""
        url = item.get('url') or ''
        if not url:
            self._info('Descargar música', 'No hay enlace para esta canción.')
            return
        if self.downloading:
            self._info('Descarga en curso', 'Espera a que termine la descarga actual.')
            return
        self.selected = dict(item)
        self.current_mode = 'audio'
        self.current_quality = '192'
        self.cancel_event.clear()
        self.paused = False
        self.downloading = True
        self.get_screen('downloading').set_info(self.selected)
        self.go('downloading')
        self._launch_download_thread()

    def current_mode_label(self):
        q = self.current_quality
        if self.current_mode == 'video':
            return f'{q} · MP4'
        return 'MP3 · Audio'

    def begin_download(self):
        # Compatibilidad con versiones anteriores.
        if not self.downloading and self.selected:
            self.start_download()

    def _launch_download_thread(self):
        url = self.selected.get('url') or ''
        threading.Thread(target=self._download_thread, args=(url,), daemon=True).start()

    def _download_thread(self, url):
        import yt_dlp
        _patch_ytdlp_write_string()
        crashlog.write_log(f"Descarga iniciada modo={self.current_mode} res={self.current_quality}")
        try:
            self._dir_before = set(os.listdir(self.download_path))
        except Exception:
            self._dir_before = set()
        ffmpeg_bin = self._ensure_ffmpeg()
        crashlog.write_log('ffmpeg_bin para yt-dlp: ' + repr(ffmpeg_bin))
        ydl_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self._hook],
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 20,
            'continuedl': True,
            'retries': 5,
            'fragment_retries': 5,
            'concurrent_fragment_downloads': 2,
            'windowsfilenames': True,
            'logger': _YDL_Logger(),
            'noprogress': True,
            # v2.0.47: android primero (unicos que responden hoy); resto de respaldo.
            # NO usar bulk ['visionos','tv','web_embedded']: mezcla clientes
            # con token (mweb/web) y dispara SABR/rate-limit.
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }
        if ffmpeg_bin:
            ydl_opts['ffmpeg_location'] = ffmpeg_bin
        if self.current_mode == 'video':
            res = self.current_quality.replace('p', '')
            ydl_opts['format'] = f'bestvideo[height<={res}]+bestaudio/best[height<={res}]/best'
            ydl_opts['merge_output_format'] = 'mp4'
        else:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        try:
            _dl_err = None
            # v2.0.47: android primero (unicos que responden hoy); resto de respaldo.
            for _cl in [['android'], ['android_vr'], ['visionos'], ['tv'], ['web_embedded'], ['web_safari']]:
                try:
                    ydl_opts['extractor_args'] = {'youtube': {'player_client': _cl}}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        self.current_ydl = ydl
                        ydl.download([url])
                    _dl_err = None
                    break
                except Exception as _de:
                    _dl_err = _de
                    crashlog.write_log(f'Descarga fallo {_cl}: ' + str(_de)[:120])
                    # v2.0.47: probar TODOS los clientes siempre (antes abortaba
                    # ante errores no-403 como 'reload page'; hoy son la norma).
                    continue
            if _dl_err:
                raise _dl_err
            self.current_ydl = None
            if self.cancel_event.is_set():
                if self.paused:
                    Clock.schedule_once(lambda dt: self._set_paused_ui())
                else:
                    Clock.schedule_once(lambda dt: self._cancelled())
                return
            self._published = self._publish_new_files()
            Clock.schedule_once(lambda dt: self._finish())
        except Exception as e:
            err = str(e)[:180]
            self.current_ydl = None
            if self.paused:
                crashlog.write_log('Descarga pausada: ' + err)
                Clock.schedule_once(lambda dt: self._set_paused_ui())
                return
            if self.cancel_event.is_set():
                Clock.schedule_once(lambda dt: self._cancelled())
                return
            # v2.0.47: Piped ante CUALQUIER error de descarga (no solo 403).
            if True:
                try:
                    if self._piped_fallback(url, self.current_mode, self.current_quality):
                        self._published = self._publish_new_files()
                        Clock.schedule_once(lambda dt: self._finish())
                        return
                except Exception as pe:
                    err = f'Piped fallo: {str(pe)[:100]} | {err}'
            crashlog.write_log('Error descarga: ' + err + '\n' + traceback.format_exc())
            Clock.schedule_once(lambda dt, m=err: self._download_error(m))

    def _download_error(self, msg):
        self.downloading = False
        self.paused = False
        self._info('Error en descarga', msg)
        self.go('downloads')

    def _set_paused_ui(self):
        if 'downloading' in self.screen_names:
            screen = self.get_screen('downloading')
            screen.st.text = 'Descarga pausada'
            screen.pause_btn.text = '▶  Reanudar'

    def _cancelled(self):
        self.downloading = False
        self.paused = False
        self.cancel_event.clear()
        self._info('Descarga cancelada', 'La descarga fue cancelada.')
        self.go('downloads')

    def _ensure_ffmpeg(self):
        """Devuelve la ruta al binario ffmpeg empaquetado (libffmpegbin.so)
        dentro del dir nativo del APK y ajusta LD_LIBRARY_PATH para que el
        linker encuentre las libav*.so al ejecutarlo.
        IMPORTANTE: hay que ejecutarlo DESDE nativeLibraryDir (etiqueta
        SELinux apk_data_file, ejecutable por la app). Copiarlo a files/bin
        (app_data_file) da EACCES: SELinux deniega execute_no_trans."""
        try:
            if not IS_ANDROID:
                return None
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            app_info = PythonActivity.mActivity.getApplicationInfo()
            native = app_info.nativeLibraryDir
            ffmpeg_bin = os.path.join(native, 'libffmpegbin.so')
            if not os.path.exists(ffmpeg_bin):
                crashlog.write_log('ffmpeg: libffmpegbin.so no existe en ' + native)
                return None
            # El binario ffmpeg enlaza contra las libav*.so compartidas; sin
            # LD_LIBRARY_PATH el linker no las encuentra al ejecutarlo
            # ("CANNOT LINK EXECUTABLE: library libavdevice.so not found").
            os.environ['LD_LIBRARY_PATH'] = native
            os.environ['PATH'] = native + os.pathsep + os.environ.get('PATH', '')
            crashlog.write_log('ffmpeg bin=' + ffmpeg_bin)
            import subprocess
            try:
                p = subprocess.run([ffmpeg_bin, '-version'], capture_output=True, timeout=15)
                crashlog.write_log('ffmpeg test rc=%s out=%r err=%r' % (p.returncode, p.stdout[:60], p.stderr[:160]))
            except Exception as e:
                crashlog.write_log('ffmpeg test fallo: ' + str(e)[:160])
            return ffmpeg_bin
        except Exception as e:
            crashlog.write_log('ffmpeg setup fallo: ' + str(e)[:150])
            return None

    def _find_ffmpeg_dir(self):
        candidates = [os.environ.get('ANDROID_PRIVATE', ''),
                      os.environ.get('ANDROID_APP_PATH', ''),
                      os.path.join(os.environ.get('ANDROID_PRIVATE', ''), 'bin'),
                      os.getcwd()]
        for base in candidates:
            if not base:
                continue
            for rel in ('ffmpeg', os.path.join('bin', 'ffmpeg')):
                if os.path.exists(os.path.join(base, rel)):
                    return base if rel == 'ffmpeg' else os.path.join(base, 'bin')
        return None

    def _hook(self, d):
        if self.cancel_event.is_set():
            raise Exception('Cancelado por el usuario')
        if self.paused:
            raise Exception('Pausado por el usuario')
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            down = d.get('downloaded_bytes', 0)
            percent = (down / total * 100) if total else 0
            speed = (d.get('_speed_str') or '---').strip()
            Clock.schedule_once(lambda dt, p=percent, db=down, tt=total, sp=speed:
                                self._update_progress(p, db, tt, sp))

    def _update_progress(self, percent, down, total, speed):
        if not self.downloading:
            return
        mb = down / 1_048_576
        mb_t = total / 1_048_576
        self.get_screen('downloading').update_progress(percent, f'{mb:.1f}', f'{mb_t:.1f}', speed)

    def _finish(self):
        self.downloading = False
        self.paused = False
        public = getattr(self, '_published', []) or []
        self._published = []
        entry = None
        if self.selected:
            entry = dict(self.selected)
            entry['quality'] = self.current_quality
            entry['format'] = 'MP3' if self.current_mode == 'audio' else 'MP4'
            entry['status'] = 'completado'
            if public:
                entry['public_uri'] = public[0]['uri']
                entry['public_path'] = public[0]['path']
                entry['local_path'] = public[0].get('local_path', '')
                try:
                    fpath = public[0].get('local_path') or public[0].get('path', '')
                    if fpath and os.path.isfile(fpath):
                        fsize = os.path.getsize(fpath)
                        if fsize >= 1_048_576:
                            entry['file_size'] = f'{fsize / 1_048_576:.1f} MB'
                        elif fsize >= 1024:
                            entry['file_size'] = f'{fsize / 1024:.0f} KB'
                        else:
                            entry['file_size'] = f'{fsize} B'
                except Exception:
                    pass
            self.downloads.insert(0, entry)
            self._save_history()
        self.get_screen('downloading').update_progress(100, '0', '0', '0.0 MB/s')
        path = public[0]['path'] if public else self.download_path
        self._show_completed(entry, path)
        Clock.schedule_once(lambda dt: self.go('downloads'), 0.3)

    def _show_completed(self, entry, path):
        """Diálogo de descarga completada: titulo del archivo grande, datos
        cortos (formato · calidad · carpeta) y acciones. Nunca la ruta larga."""
        d = ModalView(size_hint=(0.94, None), height=dp(280), background_color=(0, 0, 0, 0))
        box = Card(size_hint=(0.94, None), height=dp(268), pos_hint={'center_x': .5, 'center_y': .5},
                   orientation='vertical', spacing=dp(10), padding=dp(16))
        box.add_widget(Label(text='Descarga completada', color=GREEN, font_size=sp(17), bold=True,
                             halign='center', size_hint_y=None, height=dp(36)))
        title = safe_text((entry or {}).get('title', ''), 'Archivo descargado')
        box.add_widget(Label(text=title, color=WHITE, font_size=sp(13.5), bold=True,
                             halign='center', valign='middle',
                             text_size=(dp(290), dp(60)), size_hint_y=None, height=dp(60)))
        fmt = (entry or {}).get('format', '')
        qual = (entry or {}).get('quality', '')
        resumen = ' · '.join([p for p in (fmt, qual, (entry or {}).get('file_size', '')) if p])
        try:
            carp = os.path.basename(os.path.dirname(path)) if path else ''
        except Exception:
            carp = ''
        sub = ' · '.join([p for p in (resumen, 'Carpeta: ' + carp if carp else '') if p])
        box.add_widget(Label(text=sub or 'Guardado en tus descargas', color=MUTED,
                             font_size=sp(10.5), halign='center', valign='middle',
                             size_hint_y=None, height=dp(26),
                             text_size=(dp(290), None), shorten=True, shorten_from='right'))
        row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        buttons = []
        if entry is not None:
            play = B(text='▶ Reproducir', font_size=sp(12.5))
            rr(play, RED, 12, BORDER)
            play.bind(on_release=lambda *_: (d.dismiss(), self.play_download(entry)))
            buttons.append(play)
        folder = B(text='Abrir carpeta', font_size=sp(12.5), color=WHITE)
        rr(folder, SUR2, 12, BORDER)
        folder.bind(on_release=lambda *_: (d.dismiss(), self.open_folder()))
        done = B(text='Listo', font_size=sp(12.5), color=WHITE)
        rr(done, SUR2, 12, BORDER)
        done.bind(on_release=lambda *_: d.dismiss())
        buttons.append(folder); buttons.append(done)
        for b in buttons:
            row.add_widget(b)
        box.add_widget(row)
        d.add_widget(box)
        self._last_dialog = d
        d.open()

    def _publish_new_files(self):
        """Mueve los archivos terminados a la carpeta pública Descargas y
        devuelve la lista [{uri, path}] con la ubicación pública."""
        out = []
        try:
            before = getattr(self, '_dir_before', set())
            now = set(os.listdir(self.download_path))
            final_exts = ('.mp4', '.mp3', '.m4a', '.webm', '.mkv')
            for name in now - before:
                low = name.lower()
                if not low.endswith(final_exts) or low.endswith(('.part', '.ytdl', '.temp', '.tmp')):
                    continue
                src = os.path.join(self.download_path, name)
                if not os.path.isfile(src):
                    continue
                res = self._publish_to_downloads(src, name)
                if res:
                    res['local_path'] = src
                    out.append(res)
        except Exception as e:
            crashlog.write_log('Error publicando archivos: ' + str(e)[:150])
        return out

    def _publish_to_downloads(self, src, filename):
        """Copia un archivo a la carpeta pública Descargas del dispositivo.
        Devuelve {'uri': content_uri o ruta, 'path': ruta visible} o None."""
        try:
            low = filename.lower()
            if low.endswith('.apk'):
                mime = 'application/vnd.android.package-archive'
            elif low.endswith('.mp3'):
                mime = 'audio/mpeg'
            else:
                mime = 'video/mp4'
            # Si el usuario eligió una carpeta, escribir en ella (SAF tree URI)
            if self.download_tree and IS_ANDROID:
                res = self._publish_to_tree(src, filename, mime)
                if res:
                    return res
            if not IS_ANDROID:
                folder = os.path.join(os.path.expanduser('~'), 'Downloads', 'Jonayo_Downloads')
                os.makedirs(folder, exist_ok=True)
                dst = os.path.join(folder, filename)
                shutil.copy2(src, dst)
                return {'uri': 'file://' + dst, 'path': dst}
            if self._android_sdk() >= 29:
                from jnius import autoclass
                MediaStore = autoclass('android.provider.MediaStore$Downloads')
                ContentValues = autoclass('android.content.ContentValues')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                resolver = PythonActivity.mActivity.getContentResolver()
                rel = 'Download/Jonayo_Downloads'
                selection = '_display_name=? AND relative_path=?'
                sel_args = [filename, rel + '/']
                item_uri = None
                cursor = resolver.query(MediaStore.EXTERNAL_CONTENT_URI, None,
                                        selection, sel_args, None)
                if cursor is not None and cursor.getCount() > 0:
                    cursor.moveToFirst()
                    id_col = cursor.getColumnIndex('_id')
                    if id_col >= 0:
                        _id = cursor.getLong(id_col)
                        item_uri = Uri.withAppendedPath(MediaStore.EXTERNAL_CONTENT_URI, str(_id))
                if cursor is not None:
                    cursor.close()
                if item_uri is None:
                    values = ContentValues()
                    values.put('_display_name', filename)
                    values.put('mime_type', mime)
                    values.put('relative_path', rel)
                    item_uri = resolver.insert(MediaStore.EXTERNAL_CONTENT_URI, values)
                    if item_uri is None:
                        return None
                out = resolver.openOutputStream(item_uri, 'w')
                if out is None:
                    return None
                with open(src, 'rb') as f:
                    shutil.copyfileobj(f, out)
                out.close()
                return {'uri': item_uri.toString(), 'path': 'Descargas/Jonayo_Downloads/' + filename}
            # Android 9 o menor: escritura directa
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            dl = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            folder = os.path.join(dl, 'Jonayo_Downloads')
            os.makedirs(folder, exist_ok=True)
            dst = os.path.join(folder, filename)
            shutil.copy2(src, dst)
            return {'uri': 'file://' + dst, 'path': dst}
        except Exception as e:
            crashlog.write_log('Error publicando archivo: ' + str(e)[:150])
            return None

    def _publish_to_tree(self, src, filename, mime):
        """Escribe un archivo dentro del tree URI elegido por el usuario (SAF)."""
        try:
            from jnius import autoclass
            DocumentsContract = autoclass('android.provider.DocumentsContract')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            resolver = PythonActivity.mActivity.getContentResolver()
            tree = Uri.parse(self.download_tree)
            doc = DocumentsContract.createDocument(resolver, tree, mime, filename)
            if doc is None:
                return None
            out = resolver.openOutputStream(doc, 'w')
            if out is None:
                return None
            with open(src, 'rb') as f:
                shutil.copyfileobj(f, out)
            out.close()
            return {'uri': doc.toString(), 'path': 'Carpeta elegida/' + filename}
        except Exception as e:
            crashlog.write_log('Error escribiendo a carpeta elegida: ' + str(e)[:150])
            return None

    def _android_sdk(self):
        try:
            if IS_ANDROID:
                from jnius import autoclass
                return autoclass('android.os.Build$VERSION').SDK_INT
        except Exception:
            pass
        return 0

    def _refresh_downloads(self):
        try:
            self.get_screen('downloads').refresh(self.downloads)
        except Exception:
            pass

    def _play_system(self, item):
        """Abre el reproductor del sistema de Android con el archivo (URI publica)."""
        try:
            uri = (item or {}).get('public_uri') or ''
            mime = 'audio/mpeg' if (item or {}).get('format') == 'MP3' else 'video/mp4'
            if IS_ANDROID and uri:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(Uri.parse(uri), mime)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                PythonActivity.mActivity.startActivity(intent)
                return True
        except Exception as e:
            crashlog.write_log('Reproductor sistema fallo: ' + str(e)[:140])
        return False

    def play_download(self, item):
        """Reproduce el archivo descargado. MP3 -> reproductor de musica de la
        app (mini player + cola). MP4 -> reproductor interno de video; si no
        es posible, usa el reproductor del sistema."""
        try:
            if item.get('format') == 'MP3':
                local = item.get('local_path') or ''
                if local and os.path.isfile(local):
                    self.music_queue_add(dict(item))
                    return
            if getattr(self, '_player_fallback', False):
                # Si el interno ya fallo una vez, no volver a intentarlo en bucle.
                self._player_fallback = False
                if self._play_system(item):
                    return
            local = item.get('local_path') or ''
            if local and os.path.isfile(local):
                self._play_internal_download(local, item)
                return
            uri = item.get('public_uri') or ''
            if not uri:
                self._info('Reproducir', 'Este archivo no tiene una ubicación pública.')
                return
            mime = 'audio/mpeg' if item.get('format') == 'MP3' else 'video/mp4'
            if IS_ANDROID:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(Uri.parse(uri), mime)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                PythonActivity.mActivity.startActivity(intent)
            else:
                webbrowser.open(uri)
        except Exception as e:
            crashlog.write_log('Error reproduciendo: ' + str(e)[:150])
            self._info('No se pudo reproducir', str(e)[:180])

    def _play_internal_download(self, path, item=None):
        """Reproduce un archivo local dentro de la app con pantalla completa,
        tiempo, barra de progreso y modo audio en segundo plano.

        RENOMBRADO desde `_play_internal`: habia DOS metodos con el mismo
        nombre `_play_internal` en esta clase (este y el de streams, mas
        arriba). En Python, cuando dos metodos de una clase comparten
        nombre, el segundo pisa al primero: TODO el codigo llamaba a
        `self._play_internal(...)`, pero SIEMPRE se ejecutaba este (el mas
        simple), nunca el reproductor completo de streams (con boton de
        calidad, velocidad, siguiente/anterior y cola). Ese reproductor
        completo quedaba invisible y sin usarse. Con el rename, cada uno
        se llama por su nombre y ya no se pisan.
        """
        global Video
        self._player_fallback = False
        if Video is None:
            try:
                from kivy.uix.video import Video as _Video
                Video = _Video
            except Exception:
                crashlog.write_log('Reproductor: no se pudo importar kivy.uix.video: ' + str(sys.exc_info()[1])[:200])
                self._info('Reproductor', 'El reproductor de video no esta disponible en esta version.')
                return
        try:
            title = safe_text((item or {}).get('title', ''), os.path.basename(path))
            state = {'mode': 'video', 'fs': False, 'drag': False, 'failed': False, 'sound': None,
                     'manual_fs': False, 'land': False}
            # TouchBlockingFloatLayout (no FloatLayout a secas): sin esto los
            # toques sobre el video atraviesan la capa y abren el menu del
            # elemento de la lista que queda detras (el mismo bug ya arreglado
            # en el reproductor de streams).
            root = TouchBlockingFloatLayout()
            with root.canvas.before:
                Color(0, 0, 0, 1)
                root._bg = Rectangle(pos=root.pos, size=root.size)
            def _bg_sync(*_):
                root._bg.pos = root.pos; root._bg.size = root.size
            root.bind(pos=_bg_sync, size=_bg_sync)
            # CLAVE (bug de orden de capas): el Video hay que agregarlo ANTES
            # que las barras. En Kivy, el widget agregado DESPUES se dibuja
            # ENCIMA. Antes el video se agregaba despues de `top`, asi que el
            # video tapaba completamente la barra superior (agrandar/musica/
            # cerrar quedaban invisibles, aunque el codigo los creaba bien).
            v = Video(source=path, state='play', volume=1, allow_stretch=True, keep_ratio=True,
                      size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            root.add_widget(v)
            top = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10), padding=(dp(12), dp(5)))
            rr(top, (0, 0, 0, 0.50), 0)
            tl = Label(text=title, color=WHITE, font_size=sp(11), bold=True,
                       halign='left', valign='middle', size_hint_x=1, text_size=(None, None))
            top.add_widget(tl)
            fsb = B(text='', size_hint_x=None, width=dp(38)); rr(fsb, (1, 1, 1, 0.14), 19, None)
            fsb_img = btn_img(fsb, 'fs', dp(18))
            ab = B(text='', size_hint_x=None, width=dp(38)); rr(ab, (1, 1, 1, 0.14), 19, None); btn_img(ab, 'audio', dp(17))
            cb = B(text='', size_hint_x=None, width=dp(38)); rr(cb, RED, 19, None); btn_img(cb, 'close', dp(17))
            top.add_widget(fsb); top.add_widget(ab); top.add_widget(cb)
            root.add_widget(top)
            ascreen = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(24))
            al = Label(text=title, color=WHITE, font_size=sp(15), bold=True,
                       halign='center', valign='middle', text_size=(None, None))
            ast = Label(text='Puedes bloquear la pantalla o salir y seguira sonando.', color=MUTED, font_size=sp(10),
                        halign='center', valign='middle', text_size=(None, None))
            ascreen.add_widget(Widget(size_hint_y=1))
            ascreen.add_widget(al)
            ascreen.add_widget(ast)
            ascreen.add_widget(Widget(size_hint_y=1))
            ascreen.size_hint = (1, 1)
            ascreen.pos_hint = {'x': 0, 'y': 0}
            ascreen.opacity = 0
            root.add_widget(ascreen)
            ctrl = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10), padding=(dp(12), dp(6)))
            rr(ctrl, (0, 0, 0, 0.50), 0)
            pb = B(text='', size_hint_x=None, width=dp(40))
            coin_bg(pb, dp(40))
            pb_img = btn_img(pb, 'pause', dp(18))

            def _seek_audio_file(val):
                try:
                    if v.duration:
                        v.seek(max(0, min(val, v.duration)) / v.duration)
                except Exception:
                    pass
            sl = SeekBar(on_seek=_seek_audio_file)
            tml = Label(text='0:00 / 0:00', color=WHITE, font_size=sp(9), size_hint_x=None, width=dp(76))
            ctrl.add_widget(pb); ctrl.add_widget(sl); ctrl.add_widget(tml)
            root.add_widget(ctrl)
            self._last_dialog = None
            self._player_dialog = None

            def _relayout(*_):
                # Controles pegados al rect del video (16:9 centrado)
                try:
                    root.size = Window.size; root.pos = (0, 0)
                    sw, sh = float(Window.size[0]), float(Window.size[1])
                    ar = 16.0 / 9.0
                    if sw / sh > ar:
                        vh = sh; vw = sh * ar; vx = (sw - vw) / 2; vy = 0
                    else:
                        vw = sw; vh = sw / ar; vx = 0; vy = (sh - vh) / 2
                    v.pos = (vx, vy); v.size = (vw, vh)
                    top.pos = (vx, vy + vh - top.height); top.width = vw
                    ctrl.pos = (vx, vy); ctrl.width = vw
                    ascreen.size = root.size; ascreen.pos = (0, 0)
                    land = sh < sw
                    if land != state['land']:
                        state['land'] = land
                        if state['mode'] == 'video' and v.state == 'play':
                            # Girar con Kivy a veces deja el render del video en
                            # coordenadas viejas; reiniciar la reproduccion lo
                            # fuerza a redibujarse al nuevo tamano.
                            v.state = 'pause'
                            Clock.schedule_once(lambda dt: setattr(v, 'state', 'play'), 0.25)
                except Exception:
                    pass

            def on_close_player(*_):
                try:
                    v.state = 'stop'; v.source = ''
                except Exception:
                    pass
                if state['sound'] is not None:
                    try:
                        state['sound'].stop(); state['sound'].unload()
                    except Exception:
                        pass
                    state['sound'] = None
                if getattr(self, '_play_temp', None) == path:
                    try:
                        os.remove(path)
                        crashlog.write_log('Reproductor: temporal borrado ' + os.path.basename(path))
                    except Exception:
                        pass
                    self._play_temp = None
                if state['fs']:
                    self._jni_fs(False)
                self._jni_rotation(False)
                try:
                    tick_ev.cancel()
                except Exception:
                    pass
                self._stop_tilt_autorotate(state)
                self._player_dialog = None
            d = PlayerOverlay(root, _relayout, on_close_player)
            self._last_dialog = d
            self._player_dialog = d
            d.open()
            # El reproductor abre en vertical; solo fullscreen gira a horizontal.
            crashlog.write_log('Reproductor interno abierto: ' + os.path.basename(path))
            t0 = [time.time()]

            def _set_mode(mode):
                if mode == 'audio':
                    v.state = 'stop'
                    if state['sound'] is None:
                        try:
                            from kivy.core.audio import SoundLoader
                            s = SoundLoader.load(path)
                            if s is None:
                                raise Exception('No se pudo cargar el audio')
                            state['sound'] = s
                            s.volume = 1.0
                            s.play()
                        except Exception as e:
                            crashlog.write_log('Modo audio fallo: ' + str(e)[:150])
                            self._info('Audio', 'No se pudo activar el modo audio.\n' + str(e)[:120])
                    else:
                        try:
                            if getattr(state['sound'], 'state', '') != 'playing':
                                state['sound'].play()
                        except Exception:
                            pass
                    v.opacity = 0
                    ascreen.opacity = 1
                    state['mode'] = 'audio'
                else:
                    if state['sound'] is not None:
                        try:
                            state['sound'].stop(); state['sound'].unload()
                        except Exception:
                            pass
                        state['sound'] = None
                    v.opacity = 1
                    ascreen.opacity = 0
                    state['mode'] = 'video'
                    if v.state != 'play':
                        v.state = 'play'
            ab.bind(on_release=lambda *_: _set_mode('audio' if state['mode'] != 'audio' else 'video'))

            def _toggle_play(*_):
                if state['mode'] == 'audio':
                    s = state['sound']
                    if s is not None:
                        if getattr(s, 'state', '') == 'playing':
                            s.stop(); set_icon(pb_img, 'play')
                        else:
                            s.play(); set_icon(pb_img, 'pause')
                else:
                    if v.state == 'play':
                        v.state = 'pause'; set_icon(pb_img, 'play')
                    else:
                        v.state = 'play'; set_icon(pb_img, 'pause')
            pb.bind(on_release=_toggle_play)

            def _toggle_fs(*_):
                state['fs'] = not state['fs']
                state['manual_fs'] = state['fs']
                set_icon(fsb_img, 'fs_exit' if state['fs'] else 'fs')
                self._jni_fs(state['fs'])
                self._jni_rotation(state['fs'])
                Clock.schedule_once(_relayout, 0.10)
                Clock.schedule_once(_relayout, 0.40)
            fsb.bind(on_release=_toggle_fs)
            self._start_tilt_autorotate(state, _toggle_fs)

            cb.bind(on_release=lambda *_: d.dismiss())

            def _tick(_dt):
                try:
                    # Sin sensor: el usuario controla el giro exclusivamente
                    # mediante pantalla completa.
                    _relayout()
                    dur = v.duration or 0
                    pos = v.position or 0
                    if dur:
                        pos = max(0, min(pos, dur))
                        sl.set_range(dur)
                        sl.set_value(pos)
                    if dur:
                        fm = lambda x: f"{int(x//60)}:{int(x%60):02d}"
                        tml.text = f"{fm(pos)} / {fm(dur)}"
                    if state['mode'] == 'video' and v.state == 'play' and (time.time() - t0[0]) > 8 and v.texture is None:
                        state['failed'] = True
                        self._player_fallback = True
                        crashlog.write_log('Reproductor: sin textura en 8s -> reproductor del sistema')
                        d.dismiss()
                        # Directo al reproductor del sistema (evita reabrir el interno en bucle).
                        if not self._play_system(item):
                            self._info('Reproductor', 'El reproductor interno no pudo renderizar el video.')
                except Exception:
                    pass
            tick_ev = Clock.schedule_interval(_tick, 0.5)
        except Exception as e:
            crashlog.write_log('Reproductor: error reproductor interno: ' + str(e)[:150] + '\n' + traceback.format_exc())
            self._info('Reproductor', 'No se pudo abrir el reproductor interno.')
            uri = (item or {}).get('public_uri') or ''
            if uri:
                self.play_download(item)

    def _reset_after(self):
        self.downloading = False
        self.paused = False
        self.go('downloads')

    def toggle_pause(self):
        if not self.downloading:
            return
        if not self.paused:
            self.paused = True
            self.cancel_event.set()
            self.get_screen('downloading').pause_btn.text = '\u25b6  Reanudar'
        else:
            self.paused = False
            self.cancel_event.clear()
            self.get_screen('downloading').pause_btn.text = '||  Pausar'
        self._launch_download_thread()

    def show_music_menu(self, item):
        """Menu contextual de una cancion: reproducir, favoritos, descargar."""
        es_fav = self.music_is_fav(item)
        fav_label = 'Quitar de favoritos' if es_fav else 'Agregar a favoritos'
        actions = [
            ('Reproducir', lambda: self.music_queue_add(item)),
            (fav_label, lambda: self._toggle_fav_and_refresh(item)),
            ('Descargar', lambda: self.music_download(item)),
        ]
        ContextMenu(safe_text(item.get('title', ''), 'Cancion'), actions).open()

    def _toggle_fav_and_refresh(self, item):
        quedo = self.music_fav_toggle(item)
        if self.current == 'favs':
            self.get_screen('favs').refresh()
        return quedo

    def music_queue_add(self, item, row=None):
        """Agrega una cancion a la cola y la reproduce."""
        self._music_queue.append(dict(item))
        idx = len(self._music_queue) - 1
        if self._music_sound is None or not self._music_playing:
            self._music_play_idx(idx)
        else:
            screen = self.get_screen('music')
            screen.show_mini_player(item.get('title', ''), playing=True)

    def _music_resolve_url(self, item, on_done):
        """Resuelve la URL de streaming de un item yt-dlp (en background)."""
        url = item.get('url') or ''
        if not url:
            on_done('')
            return
        def _run():
            import yt_dlp
            _patch_ytdlp_write_string()
            last_err = ''
            # v2.0.47: android primero (unicos que responden hoy); resto de respaldo.
            for client in [['android'], ['android_vr'], ['visionos'], ['tv'], ['web_embedded'], ['web_safari']]:
                try:
                    ydl_opts = {'format': 'bestaudio[ext=m4a]/bestaudio/best',
                                'quiet': True, 'no_warnings': True,
                                'nocheckcertificate': True, 'socket_timeout': 15,
                                'extractor_args': {'youtube': {'player_client': client}}}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                    src = ''
                    if info:
                        src = info.get('url') or ''
                        if not src:
                            fmts = info.get('formats') or []
                            for f in reversed(fmts):
                                if f.get('url'):
                                    src = f['url']
                                    break
                    if src:
                        Clock.schedule_once(lambda dt, s=src: on_done(s))
                        return
                except Exception as e:
                    last_err = str(e)[:150]
                    crashlog.write_log(f'Error resolviendo audio {client}: ' + last_err)
                    continue
            # fallback Piped audio directo (sin yt-dlp) antes de rendirse
            try:
                import re, requests, certifi
                _vid = ''
                if 'v=' in url:
                    _vid = url.split('v=')[1].split('&')[0].split('?')[0]
                else:
                    _m = re.search(r'youtu\.be/([^?&/]+)', url)
                    if _m: _vid = _m.group(1)
                if _vid:
                    # v2.0.47: el unico Piped vivo (verificado 05-09-2026) primero.
                    for _h in ['https://api.piped.private.coffee', 'https://pipedapi.kavin.rocks', 'https://pipedapi-libre.kavin.rocks', 'https://piped-api.lunar.icu', 'https://pipedapi.adminforge.de', 'https://pipedapi.reallyaweso.me', 'https://api.piped.yt']:
                        try:
                            _r = requests.get(f'{_h}/streams/{_vid}', timeout=12, verify=certifi.where(), headers={'User-Agent': 'Mozilla/5.0'})
                            _r.raise_for_status()
                            _j = _r.json()
                            _auds = [a for a in (_j.get('audioStreams') or []) if a.get('url')]
                            if not _auds:
                                continue
                            _auds.sort(key=lambda a: int(a.get('bitrate') or 0), reverse=True)
                            _purl = _auds[0]['url']
                            crashlog.write_log('Piped audio resolve ok: ' + _purl[:80])
                            Clock.schedule_once(lambda dt, s=_purl: on_done(s))
                            return
                        except Exception:
                            continue
            except Exception:
                pass
            if last_err:
                crashlog.write_crash('Error resolviendo audio: ' + last_err)
            Clock.schedule_once(lambda dt: on_done(''))
        threading.Thread(target=_run, daemon=True).start()

    def _music_local_src(self, item):
        """Si el item es una cancion ya descargada, devuelve su archivo."""
        for k in ('local_path', 'public_path'):
            p = item.get(k) or ''
            try:
                if p and os.path.isfile(p):
                    return p
            except Exception:
                pass
        uri = item.get('public_uri') or ''
        if uri.startswith('file://'):
            try:
                p = uri[len('file://'):]
                if os.path.isfile(p):
                    return p
            except Exception:
                pass
        return ''

    def _music_load_and_play(self, src):
        """Carga y reproduce src (URL o archivo). True si pudo empezar."""
        try:
            from kivy.core.audio import SoundLoader
            snd = SoundLoader.load(src)
            if snd is None:
                crashlog.write_log('SoundLoader devolvio None: ' + str(src)[:90])
                return False
            self._music_sound = snd
            self._music_playing = True
            snd.bind(on_stop=self._music_on_stop)
            snd.play()
            try:
                title = self._music_queue[self._music_idx].get('title', '')
            except Exception:
                title = ''
            self.get_screen('music').show_mini_player(title, playing=True)
            self._music_start_tick()
            self._music_update_notification(title, playing=True)
            return True
        except Exception as e:
            crashlog.write_log('Error reproduciendo audio: ' + str(e)[:150])
            self._music_sound = None
            self._music_playing = False
            return False

    def _music_status(self, txt):
        """Muestra estado de carga en el titulo del mini player."""
        try:
            self.get_screen('music')._mp_title.text = txt
        except Exception:
            pass

    def _music_update_notification(self, title='', playing=True):
        """Muestra/actualiza una notificacion de media en Android con controles basicos."""
        if not IS_ANDROID:
            return
        try:
            from jnius import autoclass, JavaRunnable
            Context = autoclass('android.content.Context')
            NotificationManager = autoclass('android.app.NotificationManager')
            Build = autoclass('android.os.Build')
            # Android 8.0+ necesita canal; en 7.x no existe
            if int(str(Build.VERSION.SDK_INT)) >= 26:
                NotificationChannel = autoclass('android.app.NotificationChannel')
            else:
                NotificationChannel = None
            try:
                NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
            except Exception:
                NotificationCompat = autoclass('android.support.v4.app.NotificationCompat')
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Icon = autoclass('android.R$drawable')
            act = PythonActivity.mActivity
            ctx = act.getApplicationContext()
            nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE)
            CHANNEL_ID = 'jonayo_music'
            if not getattr(self, '_notification_channel_created', False) and NotificationChannel:
                channel = NotificationChannel(CHANNEL_ID, 'Reproductor', NotificationManager.IMPORTANCE_LOW)
                nm.createNotificationChannel(channel)
                self._notification_channel_created = True
            open_intent = Intent(Intent.ACTION_VIEW)
            open_intent.setClassName(act, act.getPackageName() + '.org.kivy.android.PythonActivity')
            flags = PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
            pending_open = PendingIntent.getActivity(act, 0, open_intent, flags)
            pause_action = NotificationCompat.Action(0, 'Pausar', pending_open)
            builder = NotificationCompat.Builder(ctx, CHANNEL_ID)
            builder.setSmallIcon(Icon.ic_media_play)
            builder.setContentTitle('Jonayo Music')
            builder.setContentText(title[:60] if title else 'Reproduciendo...')
            builder.setContentIntent(pending_open)
            builder.setAutoCancel(False)
            builder.setOngoing(playing)
            nm.notify(9999, builder.build())
        except Exception as e:
            crashlog.write_log('Notificacion error: ' + str(e)[:100])

    def _music_fallback_download(self, item):
        """Plan B: baja el audio a una carpeta temporal y lo reproduce local.
        Plan C (si esto tambien falla): avisa al usuario con un dialogo."""
        import yt_dlp
        url = item.get('url') or ''
        if not url:
            self._music_alert_fail(item)
            return
        title = safe_text(item.get('title', 'cancion'), 'cancion')
        try:
            out_dir = os.path.join(self._default_download_path(), '.reproducir')
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            out_dir = os.path.join(self._data_dir(), '.reproducir')
            os.makedirs(out_dir, exist_ok=True)
        outtmpl = os.path.join(out_dir, '%(id)s.%(ext)s')

        def hook(d):
            if d.get('status') == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                done = d.get('downloaded_bytes') or 0
                pct = int(done * 100 / total) if total else 0
                Clock.schedule_once(lambda dt, p=pct: self._music_status(
                    title[:28] + (' · %d%%' % p if p else '')))

        def work():
            try:
                _patch_ytdlp_write_string()
                opts = {'outtmpl': outtmpl,
                        'format': 'bestaudio[ext=m4a]/bestaudio/best',
                        'progress_hooks': [hook],
                        'quiet': True, 'no_warnings': True,
                        'nocheckcertificate': True, 'socket_timeout': 20,
                        'windowsfilenames': True,
                        # v2.0.47: android primero (resto bloqueado por YouTube).
                        'extractor_args': {'youtube': {'player_client': ['android', 'android_vr', 'visionos', 'tv', 'web_embedded']}}}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                fn = ''
                if info:
                    rp = info.get('requested_downloads') or []
                    if rp:
                        fn = rp[0].get('filepath') or ''
                if not fn and info:
                    try:
                        fn = ydl.prepare_filename(info)
                    except Exception:
                        fn = ''
                if fn and os.path.isfile(fn):
                    item['local_path'] = fn
                    Clock.schedule_once(lambda dt, f=fn: self._music_load_and_play(f))
                else:
                    raise RuntimeError('archivo no encontrado tras descargar')
            except Exception as e:
                err = str(e)[:180]
                crashlog.write_log('Fallback audio fallo: ' + err)
                # Plan C (v2.0.48): Piped ante CUALQUIER error (no solo 403).
                if True:
                    try:
                        import requests, certifi, re
                        vid = ''
                        if 'v=' in url:
                            vid = url.split('v=')[1].split('&')[0].split('?')[0]
                        else:
                            m = re.search(r'youtu\.be/([^?&/]+)', url)
                            if m: vid = m.group(1)
                        if vid:
                            # v2.0.47: el unico Piped vivo (verificado 05-09-2026) primero.
                            for host in ['https://api.piped.private.coffee', 'https://pipedapi.kavin.rocks', 'https://pipedapi-libre.kavin.rocks', 'https://piped-api.lunar.icu', 'https://pipedapi.adminforge.de', 'https://pipedapi.reallyaweso.me', 'https://pipedapi.drgns.space', 'https://pipedapi.owo.si', 'https://api.piped.yt']:
                                try:
                                    r = requests.get(f'{host}/streams/{vid}', timeout=15, verify=certifi.where(), headers={'User-Agent': 'Mozilla/5.0'})
                                    r.raise_for_status()
                                    j = r.json()
                                    audios = j.get('audioStreams') or []
                                    # elegir m4a/opus con mayor bitrate
                                    best = None
                                    for a in audios:
                                        if a.get('url'):
                                            if best is None or (a.get('bitrate') or 0) > (best.get('bitrate') or 0):
                                                best = a
                                    if best and best.get('url'):
                                        purl = best['url']
                                        crashlog.write_log('Piped fallback ok: ' + purl[:80])
                                        Clock.schedule_once(lambda dt, u=purl: self._music_load_and_play(u))
                                        return
                                except Exception as pe:
                                    crashlog.write_log('Piped fallo: ' + str(pe)[:100])
                                    continue
                    except Exception as pe2:
                        crashlog.write_log('Piped error: ' + str(pe2)[:100])
                crashlog.write_crash('Fallback audio fallo: ' + err)
                Clock.schedule_once(lambda dt, m=err: self._music_alert_fail(item, m))
        threading.Thread(target=work, daemon=True).start()

    def _music_alert_fail(self, item, err=''):
        title = safe_text((item or {}).get('title', ''), '')
        self._music_status(title)
        txt = 'No se pudo reproducir esta cancion.\nVerifica tu conexion e intenta de nuevo.'
        if err:
            txt += '\n\nDetalle: ' + err[:120]
        self._info('Reproductor', txt)

    def _music_play_idx(self, idx):
        """Reproduce la cancion en la cola[idx].
        Orden: archivo local -> streaming URL -> descarga temporal."""
        if idx < 0 or idx >= len(self._music_queue):
            return
        self._music_stop_internal()
        self._music_idx = idx
        item = self._music_queue[idx]
        title = item.get('title', 'Sin titulo')
        screen = self.get_screen('music')
        screen.show_mini_player(title, playing=False)
        screen.sync_player_track()

        local = self._music_local_src(item)
        if local and self._music_load_and_play(local):
            return

        def _on_src(src):
            if src and self._music_load_and_play(src):
                return
            self._music_fallback_download(item)

        self._music_resolve_url(item, _on_src)

    def _music_start_tick(self):
        if self._music_tick:
            try:
                self._music_tick.cancel()
            except Exception:
                pass
        def _tick(_dt):
            screen = self.get_screen('music')
            snd = self._music_sound
            if snd is None:
                return
            try:
                pos = snd.get_pos()
                dur = snd.length if hasattr(snd, 'length') and snd.length else 0
                if dur > 0 and screen._mp_slider is not None:
                    screen._mp_slider.set_range(dur)
                    screen._mp_slider.set_value(pos)
                if screen._mp_time is not None:
                    fm = lambda x: "{}:{:02d}".format(int(x // 60), int(x % 60))
                    screen._mp_time.text = fm(pos) + ' / ' + (fm(dur) if dur else '0:00')
                screen.update_player_tick(pos, dur)
            except Exception:
                pass
        self._music_tick = Clock.schedule_interval(_tick, 0.5)

    def music_seek(self, value):
        """Busca la posicion indicada (segundos) en la cancion actual."""
        snd = self._music_sound
        if snd is None:
            return
        try:
            snd.seek(value)
        except Exception as e:
            crashlog.write_log('Error seek musica: ' + str(e)[:120])

    def _music_on_stop(self, *args):
        """Callback cuando la cancion termina: avanza a la siguiente.
        Si la detencion fue manual (pausa/cambio de track), no avanza."""
        if self._music_suppress_stop:
            self._music_suppress_stop = False
            return
        if not self._music_playing:
            return
        self._music_playing = False
        nxt = self._music_next_index()
        if nxt is not None:
            Clock.schedule_once(lambda dt, i=nxt: self._music_play_idx(i), 0.3)
        else:
            screen = self.get_screen('music')
            screen.show_mini_player('Cola finalizada', playing=False)
            if self._music_tick:
                try:
                    self._music_tick.cancel()
                except Exception:
                    pass
                self._music_tick = None

    def music_toggle(self):
        snd = self._music_sound
        if snd is None:
            return
        if self._music_playing:
            self._music_suppress_stop = True
            snd.stop()
            self._music_playing = False
            screen = self.get_screen('music')
            screen.show_mini_player(self._music_queue[self._music_idx].get('title', ''), playing=False)
        else:
            snd.play()
            self._music_playing = True
            screen = self.get_screen('music')
            screen.show_mini_player(self._music_queue[self._music_idx].get('title', ''), playing=True)
            self._music_start_tick()

    def music_next(self):
        if self._music_idx < len(self._music_queue) - 1:
            self._music_play_idx(self._music_idx + 1)
            try:
                t = self._music_queue[self._music_idx].get('title', '')
                self._music_update_notification(t, playing=True)
            except Exception:
                pass

    def music_prev(self):
        if self._music_idx > 0:
            self._music_play_idx(self._music_idx - 1)
            try:
                t = self._music_queue[self._music_idx].get('title', '')
                self._music_update_notification(t, playing=True)
            except Exception:
                pass

    def music_shuffle_toggle(self):
        self._shuffle = not self._shuffle
        return self._shuffle

    def music_repeat_toggle(self):
        self._repeat = not self._repeat
        return self._repeat

    def _music_next_index(self):
        """Siguiente indice segun shuffle/repeat. None = terminar la cola."""
        n = len(self._music_queue)
        if n == 0:
            return None
        if self._shuffle and n > 1:
            import random
            others = [i for i in range(n) if i != self._music_idx]
            return random.choice(others)
        nxt = self._music_idx + 1
        if nxt < n:
            return nxt
        if self._repeat:
            return 0
        return None

    def music_stop(self):
        self._music_stop_internal()
        screen = self.get_screen('music')
        screen.hide_mini_player()
        if IS_ANDROID:
            try:
                from jnius import autoclass
                Context = autoclass('android.content.Context')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                nm = PythonActivity.mActivity.getApplicationContext().getSystemService(Context.NOTIFICATION_SERVICE)
                nm.cancel(9999)
            except Exception:
                pass

    # ─── FAVORITOS MUSICA ────────────────────────────────────
    def _load_favs(self):
        try:
            import json
            with open(self._favs_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _load_app_settings(self):
        try:
            import json
            with open(self._settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_app_setting(self, key, val):
        try:
            self._app_settings[key] = val
            import json
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._app_settings, f)
        except Exception as e:
            crashlog.write_log('Error guardando ajuste: ' + str(e)[:120])

    def _save_favs(self):
        try:
            import json
            with open(self._favs_path, 'w', encoding='utf-8') as f:
                json.dump(self._music_favs, f, ensure_ascii=False)
        except Exception as e:
            crashlog.write_log('Error guardando favoritos: ' + str(e)[:120])

    def music_is_fav(self, item):
        url = item.get('url', '')
        return any(f.get('url') == url for f in self._music_favs)

    def music_fav_toggle(self, item):
        """Agrega o quita de favoritos. Devuelve True si quedo como favorito."""
        url = item.get('url', '')
        for i, f in enumerate(self._music_favs):
            if f.get('url') == url:
                del self._music_favs[i]
                self._save_favs()
                return False
        self._music_favs.insert(0, dict(item))
        self._save_favs()
        return True

    def music_jump(self, idx):
        """Salta a la posicion idx de la cola."""
        if 0 <= idx < len(self._music_queue):
            self._music_play_idx(idx)

    def _music_stop_internal(self):
        if self._music_tick:
            try:
                self._music_tick.cancel()
            except Exception:
                pass
            self._music_tick = None
        if self._music_sound:
            self._music_suppress_stop = True
            try:
                self._music_sound.stop()
                self._music_sound.unload()
            except Exception:
                pass
            self._music_sound = None
        self._music_playing = False

    def cancel_download(self):
        if not self.downloading:
            return
        if self.paused:
            self.paused = False
            self.downloading = False
            Clock.schedule_once(lambda dt: self._cancelled())
            return
        self.downloading = False
        self.cancel_event.set()
        self.get_screen('downloading').st.text = 'Cancelando...'

    # ─── AJUSTES ───────────────────────────────────────────────
    def open_folder(self):
        if IS_ANDROID:
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                # Si el usuario eligió una carpeta, abrirla; si no, la subcarpeta
                # Jonayo_Downloads dentro de Descargas
                target = self.download_tree or 'content://com.android.externalstorage.documents/document/primary%3ADownload%2FJonayo_Downloads'
                for mime in ('vnd.android.document/directory', 'resource/folder'):
                    try:
                        intent = Intent(Intent.ACTION_VIEW)
                        intent.setDataAndType(Uri.parse(target), mime)
                        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                        PythonActivity.mActivity.startActivity(intent)
                        return
                    except Exception:
                        continue
                # Fallback: abrir con chooser para que el usuario elija la app
                try:
                    intent = Intent(Intent.ACTION_VIEW)
                    intent.setDataAndType(Uri.parse(target), 'resource/folder')
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                    chooser = Intent.createChooser(intent, 'Abrir carpeta de descargas')
                    PythonActivity.mActivity.startActivity(chooser)
                    return
                except Exception as e:
                    crashlog.write_log('Error abriendo carpeta: ' + str(e)[:150])
            except Exception as e:
                crashlog.write_log('Error abriendo carpeta: ' + str(e)[:150])
            try:
                import subprocess
                target = self.download_tree or 'content://com.android.externalstorage.documents/document/primary%3ADownload%2FJonayo_Downloads'
                subprocess.Popen(['am', 'start', '-a', 'android.intent.action.VIEW',
                                  '-d', target, '-t', 'resource/folder'])
            except Exception:
                pass
        else:
            try:
                import subprocess
                folder = os.path.join(os.path.expanduser('~'), 'Downloads', 'Jonayo_Downloads')
                os.makedirs(folder, exist_ok=True)
                subprocess.Popen(['explorer', folder])
            except Exception:
                webbrowser.open('file:///' + os.path.join(os.path.expanduser('~'), 'Downloads'))

    def pick_download_folder(self):
        """Abre el selector de carpetas del sistema y guarda la elegida."""
        if not IS_ANDROID:
            self._info('Carpeta de descargas', 'En escritorio se guarda en\n~/Downloads/Jonayo_Downloads')
            return
        try:
            from android import activity
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            # Necesitamos capturar el resultado de la actividad
            activity.bind(on_activity_result=self._on_folder_picked)
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION |
                            Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                            Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION |
                            Intent.FLAG_GRANT_PREFIX_URI_PERMISSION)
            PythonActivity.mActivity.startActivityForResult(intent, 4242)
        except Exception as e:
            crashlog.write_log('Error selector carpeta: ' + str(e)[:150])
            self._info('Carpeta de descargas', 'No se pudo abrir el selector de carpetas.\n' + str(e)[:80])

    def _on_folder_picked(self, request_code, result_code, data):
        if request_code != 4242 or data is None:
            return
        try:
            from jnius import autoclass
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            uri = data.getData()
            if uri is None:
                return
            try:
                flags = 3  # READ | WRITE persistibles
                PythonActivity.mActivity.getContentResolver().takePersistableUriPermission(uri, flags)
            except Exception:
                pass
            self.download_tree = uri.toString()
            self._save_settings()
            self._info('Carpeta guardada', 'Las descargas se guardaran en la carpeta elegida.')
        except Exception as e:
            crashlog.write_log('Error carpeta elegida: ' + str(e)[:150])
            self._info('Carpeta', 'No se pudo guardar la carpeta.\n' + str(e)[:80])

    def open_web(self):
        webbrowser.open('https://jonayo.vercel.app')

    def open_telegram(self):
        webbrowser.open('https://t.me/Jonayogoth')

    def export_logs(self):
        dst = crashlog.export_logs()
        crashlog.write_log(f"Logs exportados a: {dst}")
        self._info('Logs exportados', 'Se copiaron a:\n' + dst)

    def check_update_now(self):
        crashlog.write_log('Chequeo de actualizaciones manual')
        self._info('Chequeando...', 'Buscando nueva version...')

        def _close_checking():
            dlg = getattr(self, '_last_dialog', None)
            if dlg is not None:
                try:
                    dlg.dismiss()
                except Exception:
                    pass
                self._last_dialog = None

        def _run():
            try:
                from updater import get_latest_version, updater_error
                update = get_latest_version()
                if update:
                    Clock.schedule_once(lambda dt: (_close_checking(), self._on_update_check(update)))
                else:
                    msg = updater_error() or 'Revisa tu conexion a internet.'
                    Clock.schedule_once(lambda dt: (_close_checking(), self._info('Sin conexion', msg)))
            except Exception as e:
                err = str(e)[:120]
                Clock.schedule_once(lambda dt: (_close_checking(), self._info('Sin conexion',
                                                                              'No se pudo verificar. ' + err)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_update_check(self, update, auto=False):
        if not update:
            if not auto:
                Clock.schedule_once(lambda dt: self._info('Sin actualizaciones',
                                                          f'Ya tienes la ultima version (v{APP_VERSION}).'))
            return
        from updater import _cmp_versions
        if _cmp_versions(update.get('version', ''), update.get('current', APP_VERSION)) <= 0:
            if not auto:
                Clock.schedule_once(lambda dt: self._info('Sin actualizaciones',
                                                          f'Ya tienes la ultima version (v{APP_VERSION}).'))
            return
        # Anti-loop: en el chequeo automatico del arranque, avisar una sola vez
        # por version cada 12 horas. El chequeo manual siempre avisa.
        if auto:
            try:
                ver = str(update.get('version', ''))
                prompts = self._app_settings.get('update_prompts', {})
                import time as _t
                last = float(prompts.get(ver, 0) or 0)
                if _t.time() - last < 12 * 3600:
                    crashlog.write_log('Update ' + ver + ': ya avisado hace poco, no repito el dialogo')
                    return
                prompts[ver] = _t.time()
                self._save_app_setting('update_prompts', prompts)
            except Exception:
                pass
        Clock.schedule_once(lambda dt: self._update_dialog(update))

    def _update_dialog(self, update):
        notes = update.get('notes', '') or ''
        if notes:
            parts = [p.strip().lstrip('-').strip()
                     for p in notes.replace('\n', ',').split(',') if p.strip()]
            notes = '\n'.join('- ' + p for p in parts)
        box = Card(size_hint_y=None, height=dp(280))
        box.add_widget(Label(text='Nueva version disponible', color=WHITE, font_size=sp(15),
                             bold=True, halign='center', size_hint_y=None, height=dp(30)))
        ver_text = "v{}  ->  v{}".format(update.get('current', ''), update.get('version', ''))
        box.add_widget(Label(text=ver_text, color=GREEN, font_size=sp(12), bold=True,
                             halign='center', size_hint_y=None, height=dp(24)))
        if notes:
            box.add_widget(Label(text=notes, color=MUTED, font_size=sp(10),
                                 halign='left', valign='top',
                                 text_size=(dp(260), None), size_hint_y=None, height=dp(140)))
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok = B(text='Cancelar')
        rr(ok, SUR2, 12)
        ok.bind(on_release=lambda *_: d.dismiss())
        dl = B(text='Actualizar', color=WHITE)
        rr(dl, RED, 12)
        dl.bind(on_release=lambda *_: (d.dismiss(), self._install_update(update)))
        row.add_widget(ok)
        row.add_widget(dl)
        box.add_widget(row)
        d = ModalView(size_hint=(0.85, 0.50), background_color=(0, 0, 0, 0))
        d.add_widget(box)
        d.open()

    def _install_update(self, update):
        """Descarga el APK e instala la actualización desde la propia app.
        Registra el intento (anti-loop) y marca _updating para que on_pause
        deje morir la app limpia y el reinicio sea con la version nueva."""
        apk_url = update.get('apk_url') or ''
        if not apk_url:
            self._info('Actualizar', 'No se encontro el enlace del APK.\nAbre: ' + update.get('url', ''))
            return
        try:
            import time as _t
            self._save_app_setting('update_attempt', {
                'version': str(update.get('version', '')),
                'time': _t.time()})
        except Exception:
            pass
        self._updating = True
        dest = os.path.join(self.download_path, 'jonayodownloader-update.apk')
        dlg = ModalView(size_hint=(0.9, 0.35), background_color=(0, 0, 0, 0))
        box = Card(size_hint=(0.94, None), height=dp(150), pos_hint={'center_x': .5, 'center_y': .5})
        lbl = Label(text='Descargando actualizacion...', color=WHITE, font_size=sp(12),
                    halign='center', valign='middle', text_size=(dp(260), dp(70)))
        pbar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        box.add_widget(lbl); box.add_widget(pbar)
        dlg.add_widget(box); dlg.open()

        def _progress(done, total):
            pct = int(done * 100 / total) if total else 0
            Clock.schedule_once(lambda dt, p=pct: setattr(pbar, 'value', p))

        def _run():
            try:
                from updater import download_apk
                download_apk(apk_url, dest, _progress)
                Clock.schedule_once(lambda dt: self._launch_installer(dest, dlg))
            except Exception as e:
                err = str(e)[:160]
                crashlog.write_log('Error descargando APK: ' + err)
                Clock.schedule_once(lambda dt: self._finish_update_fail(dlg, err))

        threading.Thread(target=_run, daemon=True).start()

    def _finish_update_fail(self, dlg, err):
        try:
            dlg.dismiss()
        except Exception:
            pass
        self._info('No se pudo actualizar', err + '\n\nDescargalo manual:\n' + 'https://github.com/Jonayo/jonayodownloader-apk/releases')
    def _launch_installer(self, apk_path, dlg):
        try:
            dlg.dismiss()
        except Exception:
            pass
        if not IS_ANDROID:
            self._info('Instala el APK', 'Abri el archivo para instalar:\n' + apk_path)
            return
        uri = None
        try:
            res = self._publish_to_downloads(apk_path, 'jonayodownloader-update.apk')
            if res:
                uri = res.get('uri')
        except Exception as e:
            crashlog.write_log('Error publicando APK: ' + str(e)[:200])
        if not uri:
            self._info('Instala el APK',
                       'No se pudo preparar la instalacion automatica.\n'
                        'Descargalo manual desde:\nhttps://github.com/Jonayo/jonayodownloader-apk/releases')
            return
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.parse(uri), 'application/vnd.android.package-archive')
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION |
                            Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(intent)
        except Exception as e:
            crashlog.write_log('Error abriendo instalador: ' + str(e)[:200])
            self._info('Instala el APK', 'Descargalo manual desde:\nhttps://github.com/Jonayo/jonayodownloader-apk/releases')

    def show_video_menu(self, video):
        def copy_link():
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(video.get('url') or '')
                self._info('Enlace copiado', 'El enlace quedó copiado al portapapeles.')
            except Exception as e:
                self._info('No se pudo copiar', str(e)[:120])
        def share():
            try:
                webbrowser.open(video.get('url') or '')
            except Exception:
                pass
        def download():
            self.open_options(video)
        ContextMenu(title='Opciones del video', actions=[
            ('Descargar este video', download),
            ('Copiar enlace', copy_link),
            ('Abrir / compartir enlace', share),
        ]).open()

    def delete_download(self, item):
        try:
            if item in self.downloads:
                self.downloads.remove(item)
                self._save_history()
                self.get_screen('downloads').refresh(self.downloads)
        except Exception:
            pass

    def show_download_menu(self, item):
        def delete_item():
            self.delete_download(item)
        def open_file():
            self.open_folder()
        def play_item():
            self.play_download(item)
        ContextMenu(title='Opciones de descarga', actions=[
            ('Reproducir', play_item),
            ('Abrir carpeta de descargas', open_file),
            ('Eliminar de la lista', delete_item),
        ]).open()

    def _info(self, title, text, on_ok=None, ok_text='Cerrar'):
        dialog = InfoDialog(title, text, on_ok=on_ok, ok_text=ok_text)
        self._last_dialog = dialog
        dialog.open()

    def confirm_exit(self):
        if self._last_dialog:
            try:
                self._last_dialog.dismiss()
            except Exception:
                pass
        d = ModalView(size_hint=(0.88, 0.4), background_color=(0, 0, 0, 0))
        box = Card(size_hint=(0.92, None), height=dp(230), pos_hint={'center_x': .5, 'center_y': .5})
        box.add_widget(Label(text='¿Salir de la app?', color=WHITE, font_size=sp(16), bold=True,
                             size_hint_y=None, height=dp(40)))
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        no = B(text='No')
        rr(no, SUR2, 12)
        no.bind(on_release=lambda *_: d.dismiss())
        yes = B(text='Salir', color=WHITE)
        rr(yes, RED, 12)
        yes.bind(on_release=lambda *_: (d.dismiss(), App.get_running_app().stop()))
        row.add_widget(no)
        row.add_widget(yes)
        box.add_widget(row)
        d.add_widget(box)
        self._last_dialog = d
        d.open()


class AppMain(App):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        crashlog.write_log("=== Aplicacion iniciada (fusionado) ===")
        Window.bind(on_keyboard=self._on_keyboard)
        try:
            m = M()
        except Exception:
            import traceback
            tb = traceback.format_exc()
            crashlog.write_crash(f"Versión: J Youtube Downloader v{APP_VERSION}\n\n" + tb)
            crashlog.write_log("CRASH en M():\n" + tb)
            try:
                import sys as _sys
                _sys.stderr.write("CRASH en M():\n" + tb + "\n")
                _sys.stderr.flush()
            except Exception:
                pass
            raise
        self.manager = m
        # yt-dlp en vivo: si una descarga previa dejo el motor nuevo, usarlo
        # primero (sys.path) antes de que cualquier thread importe yt_dlp.
        self._ensure_live_ytdlp()
        # descargar el master nuevo 1 vez/dia en segundo plano (aplica al reiniciar)
        Clock.schedule_once(lambda dt: self._update_live_ytdlp_bg(), 5)

        previous_crash = crashlog.read_crash()
        if previous_crash:
            crashlog.write_log('Crash previo detectado.')
            Clock.schedule_once(lambda dt: self._show_crash_notice(previous_crash), 0.5)
        if check_for_update is not None:
            Clock.schedule_once(lambda dt: check_for_update(lambda u: m._on_update_check(u, auto=True)), 2)
        return m

    def _ensure_live_ytdlp(self):
        """Si una actualizacion previa dejo yt-dlp nuevo en user_data_dir,
        ponerlo primero en sys.path antes de que se importe yt_dlp."""
        try:
            import sys as _sys
            import os as _os
            base = _os.path.join(self.user_data_dir, 'yt_dlp_live', 'yt-dlp-master')
            if _os.path.isdir(_os.path.join(base, 'yt_dlp')) and base not in _sys.path:
                _sys.path.insert(0, base)
                try:
                    import yt_dlp as _y
                    crashlog.write_log('yt-dlp live: ' + str(getattr(_y, 'version', '?')))
                except Exception:
                    pass
        except Exception:
            pass

    def _update_live_ytdlp_bg(self):
        """Descarga el master de yt-dlp 1 vez/dia en segundo plano.
        Asi YouTube no rompe la app hasta el proximo APK: aplica al reiniciar."""
        try:
            import os as _os
            import time as _t
            import json as _j
            base = _os.path.join(self.user_data_dir, 'yt_dlp_live')
            try:
                with open(_os.path.join(base, 'state.json'), encoding='utf-8') as _f:
                    _last = float((_j.load(_f) or {}).get('time', 0))
                if _t.time() - _last < 24 * 3600:
                    return
            except Exception:
                pass
            import threading as _th
            _th.Thread(target=self._fetch_live_ytdlp, daemon=True).start()
        except Exception:
            pass

    def _fetch_live_ytdlp(self):
        try:
            import os as _os
            import time as _t
            import json as _j
            import zipfile as _z
            import urllib.request as _u
            base = _os.path.join(self.user_data_dir, 'yt_dlp_live')
            _os.makedirs(base, exist_ok=True)
            _zp = _os.path.join(base, 'master.zip')
            _req = _u.Request('https://github.com/yt-dlp/yt-dlp/archive/refs/heads/master.zip',
                              headers={'User-Agent': 'Mozilla/5.0'})
            with _u.urlopen(_req, timeout=90) as _r, open(_zp, 'wb') as _f:
                while True:
                    _ch = _r.read(1 << 18)
                    if not _ch:
                        break
                    _f.write(_ch)
            # extraer solo el paquete (ahorra espacio/tiempo en el telefono)
            with _z.ZipFile(_zp) as _zf:
                for _n in _zf.namelist():
                    if _n.startswith('yt-dlp-master/yt_dlp/'):
                        _zf.extract(_n, base)
            try:
                _os.remove(_zp)
            except Exception:
                pass
            with open(_os.path.join(base, 'state.json'), 'w', encoding='utf-8') as _f:
                _j.dump({'time': _t.time()}, _f)
            crashlog.write_log('yt-dlp live descargado (aplica al reiniciar)')
        except Exception as _e:
            crashlog.write_log('yt-dlp live fallo: ' + str(_e)[:120])

    def _on_keyboard(self, window, key, scancode, codepoint, modifiers):
        if key == 27:
            m = self.manager
            # 1. Si el reproductor de musica expandido esta abierto, cerrarlo
            # (antes caia a confirm_exit y parecia que pedia cerrar la app).
            try:
                ms = m.get_screen('music')
                if getattr(ms, '_player', None) is not None and getattr(ms._player, '_opened', False):
                    ms.close_player()
                    return True
            except Exception:
                pass
            d = getattr(m, '_last_dialog', None)
            if d is not None and getattr(d, 'window', None):
                try:
                    d.dismiss()
                    return True
                except Exception:
                    pass
            if m._back_stack:
                m.go_back()
            else:
                m.confirm_exit()
            return True
        return False

    def _request_permissions(self, *args):
        # Las descargas se guardan en el almacenamiento especifico de la app,
        # por lo que Android 10+ no necesita permisos de almacenamiento.
        return None

    def _show_crash_notice(self, crash_text):
        try:
            box = Card(size_hint_y=None, height=dp(240))
            box.add_widget(Label(text='La app se cerro antes', color=WHITE, font_size=sp(15),
                                 bold=True, halign='center', size_hint_y=None, height=dp(30)))
            box.add_widget(Label(text='El error quedo guardado. Toca REPORTAR y Telegram se '
                                      'abre con el detalle listo para enviar.',
                                 color=MUTED, font_size=sp(12), halign='center',
                                 text_size=(None, None), size_hint_y=None, height=dp(100)))
            row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
            ok = B(text='Ok')
            rr(ok, SUR2, 12)
            ok.bind(on_release=lambda *_: (crashlog.clear_crash(), d.dismiss()))
            report = B(text='Reportar', color=WHITE)
            rr(report, RED, 12)
            report.bind(on_release=lambda *_: (d.dismiss(), self._send_log()))
            row.add_widget(ok)
            row.add_widget(report)
            box.add_widget(row)
            d = ModalView(size_hint=(0.85, 0.45), background_color=(0, 0, 0, 0))
            d.add_widget(box)
            d.open()
        except Exception:
            pass

    def _send_log(self):
        import urllib.parse
        text = crashlog.read_crash() or 'Sin crash registrado.'
        if len(text) > 3800:
            text = text[:3800] + '\n...(truncado)'
        msg = f'J Youtube Downloader v{APP_VERSION} - crash\n\n' + text
        encoded = urllib.parse.quote(msg)
        crashlog.clear_crash()
        try:
            webbrowser.open('https://t.me/Jonayogoth?text=' + encoded)
        except Exception:
            webbrowser.open('https://t.me/Jonayogoth?text=' + encoded)

    def on_pause(self):
        """HOME o cambiar de app. Con 'Seguir escuchando' activado la app queda
        residente y la musica sigue sonando. Si esta desactivado, se detiene
        la musica y la app se cierra (comportamiento clasico).
        Durante una instalacion de actualizacion siempre se libera la app
        para que el reinicio sea limpio con la version nueva (evita loops)."""
        try:
            m = self.manager
            if getattr(m, '_updating', False):
                return False
            if getattr(m, 'bg_music', True):
                return True
            if m._music_sound is not None:
                m.music_stop()
        except Exception:
            pass
        return False

    def on_resume(self):
        pass

    def on_stop(self):
        crashlog.write_log('App detenida.')


if __name__ == '__main__':
    crashlog.write_log('Iniciando run()...')
    AppMain().run()
    crashlog.write_log('run() termino.')