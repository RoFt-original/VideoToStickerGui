from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
import threading
import re
from jnius import autoclass, PythonJavaClass, java_method


# ffmpeg-kit Java bindings
FFmpegKit = autoclass('com.arthenica.ffmpegkit.FFmpegKit')
ReturnCode = autoclass('com.arthenica.ffmpegkit.ReturnCode')


class _ExecCb(PythonJavaClass):
    __javainterfaces__ = ['com/arthenica/ffmpegkit/ExecuteCallback']
    __javacontext__ = 'app'

    def __init__(self, on_complete):
        super().__init__()
        self.on_complete = on_complete

    @java_method('(Lcom/arthenica/ffmpegkit/Session;)V')
    def apply(self, session):
        self.on_complete(session)


class _LogCb(PythonJavaClass):
    __javainterfaces__ = ['com/arthenica/ffmpegkit/LogCallback']
    __javacontext__ = 'app'

    def __init__(self, on_log):
        super().__init__()
        self.on_log = on_log

    @java_method('(Lcom/arthenica/ffmpegkit/Log;)V')
    def apply(self, log):
        try:
            msg = log.getMessage()
        except Exception:
            msg = ''
        self.on_log(msg)


class _StatsCb(PythonJavaClass):
    __javainterfaces__ = ['com/arthenica/ffmpegkit/StatisticsCallback']
    __javacontext__ = 'app'

    def __init__(self, on_stats):
        super().__init__()
        self.on_stats = on_stats

    @java_method('(Lcom/arthenica/ffmpegkit/Statistics;)V')
    def apply(self, stats):
        # time in ms
        try:
            tms = stats.getTime()
        except Exception:
            tms = 0
        self.on_stats(tms)


class LogView(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.label = Label(text='', size_hint_y=None, halign='left', valign='top')
        self.label.bind(texture_size=self._update_height)
        self.add_widget(self.label)

    def _update_height(self, *_):
        self.label.height = self.label.texture_size[1]
        self.label.text_size = (self.width - 20, None)

    def append(self, text: str):
        def _do(*_):
            self.label.text += text
        Clock.schedule_once(_do)


class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.input_path = TextInput(hint_text='Входной файл (.webm для spoof, видео для convert)')
        self.output_path = TextInput(hint_text='Выходной файл (.webm)')
        self.extra_args = TextInput(hint_text='Доп. аргументы')

        self.add_widget(self.input_path)
        self.add_widget(self.output_path)
        self.add_widget(self.extra_args)

        btns = BoxLayout(size_hint=(1, None), height=48)
        self.btn_convert = Button(text='Convert')
        self.btn_spoof = Button(text='Spoof')
        self.btn_convert.bind(on_press=lambda *_: self.run_convert())
        self.btn_spoof.bind(on_press=lambda *_: self._spoof_unavailable())
        btns.add_widget(self.btn_convert)
        btns.add_widget(self.btn_spoof)
        self.add_widget(btns)

        # Progress
        pwrap = BoxLayout(orientation='vertical')
        self.pbar = ProgressBar(max=100, value=0)
        self.status = Label(text='Готов')
        pwrap.add_widget(self.pbar)
        pwrap.add_widget(self.status)
        self.add_widget(pwrap)

        self._thread = None
        self._total = None

    def run_convert(self):
        if self._thread and self._thread.is_alive():
            return
        i = self.input_path.text.strip()
        o = self.output_path.text.strip() or (i + '.webm')
        extra = self.extra_args.text.strip()

        # Базовая команда для видеостикеров Telegram: VP9, 512x512, yuv420p, ~30fps
        vf = "scale=512:-2:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color=black"
        base = f"-y -i '{i}' -vf {vf} -r 30 -an -c:v libvpx-vp9 -b:v 0 -crf 32 -pix_fmt yuv420p -deadline good -speed 4 '{o}'"
        if extra:
            # Примитивно добавим в конец (пользовательская ответственность)
            base = base[:-len("'"+o+"'")] + f" {extra} '{o}'"

        self.status.text = 'Запуск...'
        self.pbar.value = 0
        self._total = None
        # Запуск через ffmpeg-kit async
        def on_complete(session):
            rc = session.getReturnCode()
            ok = ReturnCode.isValueSuccess(rc)
            def _done(*_):
                self.pbar.value = 100 if ok else 0
                self.status.text = 'Готово' if ok else f'Ошибка ({rc})'
            Clock.schedule_once(_done)

        def on_log(message: str):
            # Ищем Duration и time=
            self._handle_log_progress(message)

        def on_stats(tms: int):
            # Можно обновлять прогресс и по статистике, если известна длительность
            if self._total:
                pct = max(0, min(100, int((tms/1000.0) / self._total * 100)))
                Clock.schedule_once(lambda *_: setattr(self.pbar, 'value', pct))

        FFmpegKit.executeAsync(base, _ExecCb(on_complete), _LogCb(on_log), _StatsCb(on_stats))

    def _spoof_unavailable(self):
        Popup(title='Недоступно', content=Label(text='Spoof недоступен на Android в этой версии'), size_hint=(0.8, 0.3)).open()

    def _handle_log_progress(self, text: str):
        if self._total is None:
            m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.?\d*)', text)
            if m:
                h, mnt, s = m.groups()
                try:
                    self._total = int(h) * 3600 + int(mnt) * 60 + float(s)
                    Clock.schedule_once(lambda *_: setattr(self.status, 'text', 'Конвертация...'))
                except Exception:
                    pass
        mt = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', text)
        if mt and self._total:
            h, mnt, s = mt.groups()
            try:
                cur = int(h) * 3600 + int(mnt) * 60 + float(s)
                pct = max(0, min(100, int(cur / self._total * 100)))
                Clock.schedule_once(lambda *_: setattr(self.pbar, 'value', pct))
            except Exception:
                pass


class TGApp(App):
    def build(self):
        return Root()


if __name__ == '__main__':
    TGApp().run()


