import os
import sys
import shlex
import queue
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import runpy
import re

# Попытка импортировать tgradish для упаковки внутрь exe (PyInstaller hidden-import)
try:
    import tgradish as _tgradish  # noqa: F401
except Exception:
    _tgradish = None  # type: ignore


class DependencyChecker:
    """Utility to check for required external tools and build command invocations."""

    @staticmethod
    def has_tgradish_cli() -> bool:
        return shutil.which("tgradish") is not None

    @staticmethod
    def has_tgradish_module() -> bool:
        try:
            import importlib.util
            return importlib.util.find_spec("tgradish") is not None
        except Exception:
            return False

    @staticmethod
    def is_tgradish_available() -> bool:
        return DependencyChecker.has_tgradish_cli() or DependencyChecker.has_tgradish_module()

    @staticmethod
    def tgradish_command() -> list:
        """Return a command prefix for invoking tgradish.

        Prefer the CLI script if present; otherwise fallback to `python -m tgradish`.
        """
        if DependencyChecker.has_tgradish_cli():
            return ["tgradish"]
        # В портативной сборке PyInstaller `-m` недоступен.
        # Фактический запуск будет через встроенный режим (runpy).
        return []

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None


class BackgroundProcessRunner:
    """Run external commands in a background thread and stream their output."""

    def __init__(self, on_output_line, on_process_end):
        self._on_output_line = on_output_line
        self._on_process_end = on_process_end
        self._thread: threading.Thread | None = None
        self._proc: subprocess.Popen | None = None
        self._stop_requested = False

    def run(self, command: list[str], cwd: str | None = None):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Уже запущен процесс. Остановите его перед новым запуском.")
        self._stop_requested = False
        self._thread = threading.Thread(target=self._run_worker, args=(command, cwd), daemon=True)
        self._thread.start()

    def terminate(self):
        self._stop_requested = True
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def _run_worker(self, command: list[str], cwd: str | None):
        try:
            self._on_output_line(f"$ {' '.join(shlex.quote(c) for c in command)}\n")
            self._proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError as e:
            self._on_output_line(f"Ошибка запуска: {e}\n")
            self._on_process_end(1)
            return
        except Exception as e:
            self._on_output_line(f"Не удалось запустить процесс: {e}\n")
            self._on_process_end(1)
            return

        assert self._proc is not None
        with self._proc.stdout as stream:  # type: ignore[arg-type]
            for line in stream:  # type: ignore[assignment]
                if self._stop_requested:
                    break
                self._on_output_line(line)

        # Ensure process is terminated if stop requested
        if self._stop_requested and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

        code = self._proc.wait()
        self._on_process_end(code)


class InProcessTgradishRunner:
    """Run `tgradish` module in-process (no external CLI needed)."""

    def __init__(self, on_output_line, on_process_end):
        self._on_output_line = on_output_line
        self._on_process_end = on_process_end
        self._thread: threading.Thread | None = None
        self._stop_requested = False

    def run(self, tgradish_args: list[str]):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Уже запущен процесс. Остановите его перед новым запуском.")
        self._stop_requested = False
        self._thread = threading.Thread(target=self._worker, args=(tgradish_args,), daemon=True)
        self._thread.start()

    def terminate(self):
        # Корректная остановка встроенного CLI не гарантируется
        self._stop_requested = True
        self._on_output_line("Прерывание встроенного режима не поддерживается полностью. Ожидайте завершения...\n")

    def _worker(self, tgradish_args: list[str]):
        self._on_output_line("$ tgradish " + " ".join(shlex.quote(a) for a in tgradish_args) + "\n")
        if not DependencyChecker.has_tgradish_module():
            self._on_output_line("Встроенный модуль tgradish недоступен.\n")
            self._on_process_end(1)
            return

        # Подмена argv и потоков вывода
        old_argv = sys.argv
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        class _Stream:
            def __init__(self, callback):
                self._buf = ""
                self._cb = callback

            def write(self, s):
                self._buf += str(s)
                while "\n" in self._buf:
                    line, self._buf = self._buf.split("\n", 1)
                    self._cb(line + "\n")

            def flush(self):
                if self._buf:
                    self._cb(self._buf)
                    self._buf = ""

        sys.argv = ["tgradish", *tgradish_args]
        sys.stdout = _Stream(self._on_output_line)  # type: ignore
        sys.stderr = _Stream(self._on_output_line)  # type: ignore
        exit_code = 0
        try:
            runpy.run_module("tgradish", run_name="__main__")
        except SystemExit as e:
            try:
                exit_code = int(getattr(e, "code", 1))
            except Exception:
                exit_code = 1
        except Exception as e:
            self._on_output_line(f"Ошибка выполнения: {e}\n")
            exit_code = 1
        finally:
            try:
                sys.stdout.flush()  # type: ignore
                sys.stderr.flush()  # type: ignore
            except Exception:
                pass
            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        self._on_process_end(exit_code)


class TgradishGUI:
    """Tkinter-based GUI wrapper around tgradish CLI (convert and spoof)."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tgradish GUI")
        self.root.geometry("900x600")
        self.root.minsize(800, 520)

        self.process_runner = BackgroundProcessRunner(
            on_output_line=self._on_process_output_line_threadsafe,
            on_process_end=self._on_process_finished_threadsafe,
        )
        self.inproc_runner = InProcessTgradishRunner(
            on_output_line=self._on_process_output_line_threadsafe,
            on_process_end=self._on_process_finished_threadsafe,
        )

        # Состояние прогресса
        self.current_operation: str | None = None  # 'convert' | 'spoof'
        self.total_duration_s: float | None = None
        self.is_indeterminate: bool = False

        self._build_ui()
        self._update_dependency_labels()

    # --------------------------- UI Construction --------------------------- #
    def _build_ui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(fill=tk.X, padx=12, pady=(12, 6))
        title = ttk.Label(header, text="VideoToSticker", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        # Top spacer (ранее показывал режим, сейчас оставлен как отступ)
        top_bar = ttk.Frame(self.main_frame)
        top_bar.pack(fill=tk.X, padx=12, pady=(6, 6))

        # Убраны кнопки проверки/установки зависимостей

        sep = ttk.Separator(self.main_frame, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=12, pady=(4, 4))

        # Notebook with Convert and Spoof tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        self._build_convert_tab()
        self._build_spoof_tab()

        # Progress section
        prog_frame = ttk.LabelFrame(self.main_frame, text="Прогресс")
        prog_frame.pack(fill=tk.X, padx=12, pady=(6, 12))
        inner = ttk.Frame(prog_frame)
        inner.pack(fill=tk.X, padx=8, pady=8)
        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(inner, orient=tk.HORIZONTAL, mode="determinate", maximum=100, variable=self.progress_var)
        self.progress.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.lbl_percent = ttk.Label(inner, text="0%", width=6)
        self.lbl_percent.pack(side=tk.LEFT, padx=(8, 0))
        self.lbl_status = ttk.Label(prog_frame, text="Готов")
        self.lbl_status.pack(anchor="w", padx=8, pady=(0, 8))

    def _build_convert_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Convert")

        # Input file
        section = ttk.LabelFrame(tab, text="Источник и вывод")
        section.pack(fill=tk.X, padx=10, pady=(12, 6))
        row1 = ttk.Frame(section)
        row1.pack(fill=tk.X, padx=8, pady=(8, 6))
        ttk.Label(row1, text="Входной файл видео:").pack(side=tk.LEFT)
        self.var_convert_input = tk.StringVar()
        ent_in = ttk.Entry(row1, textvariable=self.var_convert_input)
        ent_in.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(row1, text="Обзор...", command=self._browse_convert_input).pack(side=tk.LEFT)

        # Output file
        row2 = ttk.Frame(section)
        row2.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row2, text="Выходной файл (.webm, опционально):").pack(side=tk.LEFT)
        self.var_convert_output = tk.StringVar()
        ent_out = ttk.Entry(row2, textvariable=self.var_convert_output)
        ent_out.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(row2, text="Сохранить как...", command=self._browse_convert_output).pack(side=tk.LEFT)

        # Extra args
        adv = ttk.LabelFrame(tab, text="Дополнительные параметры")
        adv.pack(fill=tk.X, padx=10, pady=6)
        row3 = ttk.Frame(adv)
        row3.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row3, text="Доп. аргументы (опционально):").pack(side=tk.LEFT)
        self.var_convert_extra = tk.StringVar()
        ent_args = ttk.Entry(row3, textvariable=self.var_convert_extra)
        ent_args.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        # Actions
        row4 = ttk.Frame(tab)
        row4.pack(fill=tk.X, padx=10, pady=(6, 12))
        self.btn_convert = ttk.Button(row4, text="Конвертировать", command=self._on_convert)
        self.btn_convert.pack(side=tk.LEFT)
        self.btn_convert_stop = ttk.Button(row4, text="Остановить", command=self._on_stop, state=tk.DISABLED)
        self.btn_convert_stop.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_open_convert_dir = ttk.Button(row4, text="Открыть папку результата", command=self._open_convert_dir)
        self.btn_open_convert_dir.pack(side=tk.LEFT, padx=(8, 0))

    def _build_spoof_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Spoof")

        # Input file
        section = ttk.LabelFrame(tab, text="Файлы")
        section.pack(fill=tk.X, padx=10, pady=(12, 6))
        row1 = ttk.Frame(section)
        row1.pack(fill=tk.X, padx=8, pady=(8, 6))
        ttk.Label(row1, text="Входной .webm стикер:").pack(side=tk.LEFT)
        self.var_spoof_input = tk.StringVar()
        ent_in = ttk.Entry(row1, textvariable=self.var_spoof_input)
        ent_in.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(row1, text="Обзор...", command=self._browse_spoof_input).pack(side=tk.LEFT)

        # Output file
        row2 = ttk.Frame(section)
        row2.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row2, text="Выходной .webm:").pack(side=tk.LEFT)
        self.var_spoof_output = tk.StringVar()
        ent_out = ttk.Entry(row2, textvariable=self.var_spoof_output)
        ent_out.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(row2, text="Сохранить как...", command=self._browse_spoof_output).pack(side=tk.LEFT)

        # Extra args
        adv = ttk.LabelFrame(tab, text="Дополнительные параметры")
        adv.pack(fill=tk.X, padx=10, pady=6)
        row3 = ttk.Frame(adv)
        row3.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row3, text="Доп. аргументы (опционально):").pack(side=tk.LEFT)
        self.var_spoof_extra = tk.StringVar()
        ent_args = ttk.Entry(row3, textvariable=self.var_spoof_extra)
        ent_args.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        # Actions
        row4 = ttk.Frame(tab)
        row4.pack(fill=tk.X, padx=10, pady=(6, 12))
        self.btn_spoof = ttk.Button(row4, text="Подменить длительность", command=self._on_spoof)
        self.btn_spoof.pack(side=tk.LEFT)
        self.btn_spoof_stop = ttk.Button(row4, text="Остановить", command=self._on_stop, state=tk.DISABLED)
        self.btn_spoof_stop.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_open_spoof_dir = ttk.Button(row4, text="Открыть папку результата", command=self._open_spoof_dir)
        self.btn_open_spoof_dir.pack(side=tk.LEFT, padx=(8, 0))

    # ----------------------------- UI Handlers ----------------------------- #
    def _browse_convert_input(self):
        path = filedialog.askopenfilename(title="Выберите видеофайл", filetypes=[
            ("Видео", "*.mp4 *.mov *.mkv *.webm *.avi *.m4v"),
            ("Все файлы", "*.*"),
        ])
        if path:
            self.var_convert_input.set(path)

    def _browse_convert_output(self):
        path = filedialog.asksaveasfilename(title="Сохранить как", defaultextension=".webm", filetypes=[
            ("WebM", "*.webm"),
            ("Все файлы", "*.*"),
        ])
        if path:
            self.var_convert_output.set(path)

    def _browse_spoof_input(self):
        path = filedialog.askopenfilename(title="Выберите .webm стикер", filetypes=[
            ("WebM", "*.webm"),
            ("Все файлы", "*.*"),
        ])
        if path:
            self.var_spoof_input.set(path)

    def _browse_spoof_output(self):
        path = filedialog.asksaveasfilename(title="Сохранить как", defaultextension=".webm", filetypes=[
            ("WebM", "*.webm"),
            ("Все файлы", "*.*"),
        ])
        if path:
            self.var_spoof_output.set(path)

    def _open_convert_dir(self):
        out = self.var_convert_output.get().strip()
        folder = os.path.dirname(out) if out else os.path.dirname(self.var_convert_input.get().strip())
        if folder and os.path.isdir(folder):
            self._open_in_explorer(folder)
        else:
            messagebox.showinfo("Открыть папку", "Сначала укажите файл ввода или вывода.")

    def _open_spoof_dir(self):
        out = self.var_spoof_output.get().strip()
        folder = os.path.dirname(out) if out else os.path.dirname(self.var_spoof_input.get().strip())
        if folder and os.path.isdir(folder):
            self._open_in_explorer(folder)
        else:
            messagebox.showinfo("Открыть папку", "Сначала укажите файл ввода или вывода.")

    def _open_in_explorer(self, path: str):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")

    def _on_convert(self):
        if not DependencyChecker.is_tgradish_available():
            messagebox.showwarning("tgradish недоступен", "В этой сборке tgradish отсутствует. Попробуйте другую сборку или установите tgradish в систему.")
            return
        if not DependencyChecker.is_ffmpeg_available():
            if not messagebox.askyesno("ffmpeg не найден", "Для convert требуется ffmpeg. Продолжить попытку без него?"):
                return
        input_path = self.var_convert_input.get().strip()
        if not input_path:
            messagebox.showinfo("Параметры", "Укажите входной видеофайл.")
            return
        if not os.path.isfile(input_path):
            messagebox.showerror("Файл не найден", f"Не найден файл: {input_path}")
            return
        output_path = self.var_convert_output.get().strip()
        extra = self.var_convert_extra.get().strip()

        base_args: list[str] = ["convert", "-i", input_path]
        if output_path:
            base_args += ["-o", output_path]
        if extra:
            try:
                parts = shlex.split(extra, posix=(os.name != "nt"))
            except ValueError as e:
                messagebox.showerror("Аргументы", f"Ошибка разбора доп. аргументов: {e}")
                return
            base_args += parts

        self._run_tgradish_args(base_args, operation="convert")

    def _on_spoof(self):
        if not DependencyChecker.is_tgradish_available():
            messagebox.showwarning("tgradish недоступен", "В этой сборке tgradish отсутствует. Попробуйте другую сборку или установите tgradish в систему.")
            return
        input_path = self.var_spoof_input.get().strip()
        output_path = self.var_spoof_output.get().strip()
        if not input_path or not output_path:
            messagebox.showinfo("Параметры", "Укажите входной и выходной файл .webm.")
            return
        if not os.path.isfile(input_path):
            messagebox.showerror("Файл не найден", f"Не найден файл: {input_path}")
            return
        extra = self.var_spoof_extra.get().strip()

        base_args: list[str] = ["spoof", input_path, output_path]
        if extra:
            try:
                parts = shlex.split(extra, posix=(os.name != "nt"))
            except ValueError as e:
                messagebox.showerror("Аргументы", f"Ошибка разбора доп. аргументов: {e}")
                return
            base_args += parts

        self._run_tgradish_args(base_args, operation="spoof")

    def _on_stop(self):
        self.process_runner.terminate()

    def _install_tgradish(self):
        messagebox.showinfo("Недоступно", "Функция отключена в этой версии.")

    def _run_tgradish_args(self, args: list[str], operation: str):
        self.current_operation = operation
        # Сброс прогресса
        if operation == "convert":
            self._reset_progress(determinate=True)
            self._set_status("Подготовка...")
        else:
            self._reset_progress(determinate=False)
            self._set_status("Выполняется...")
        # Выбор режима: CLI -> внешний процесс; модуль -> встроенный
        if DependencyChecker.has_tgradish_cli():
            cmd = [*DependencyChecker.tgradish_command(), *args]
            self._start_process(cmd, show_notice=True, inprocess=False)
        elif DependencyChecker.has_tgradish_module():
            self._start_process(args, show_notice=True, inprocess=True)
        else:
            messagebox.showerror("tgradish", "tgradish недоступен ни как CLI, ни как модуль.")

    def _start_process(self, cmd: list[str], show_notice: bool = True, inprocess: bool = False):
        try:
            self.btn_convert.configure(state=tk.DISABLED)
            self.btn_convert_stop.configure(state=(tk.DISABLED if inprocess else tk.NORMAL))
            self.btn_spoof.configure(state=tk.DISABLED)
            self.btn_spoof_stop.configure(state=(tk.DISABLED if inprocess else tk.NORMAL))
        except Exception:
            pass

        if show_notice:
            self._set_status("Запуск...")
        try:
            if inprocess:
                self.inproc_runner.run(cmd)
            else:
                self.process_runner.run(cmd, cwd=None)
        except RuntimeError as e:
            messagebox.showinfo("Процесс уже запущен", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))

    # --------------------------- Progress handling ------------------------- #
    def _on_process_output_line_threadsafe(self, text: str):
        self.root.after(0, lambda t=text: self._process_output_line(t))

    def _process_output_line(self, text: str):
        # Определяем общую длительность
        if self.current_operation == "convert":
            if self.total_duration_s is None:
                m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", text)
                if m:
                    h, mnt, s = m.groups()
                    try:
                        total = int(h) * 3600 + int(mnt) * 60 + float(s)
                        if total > 0:
                            self.total_duration_s = total
                            # Переключаемся на определённый прогресс
                            self._reset_progress(determinate=True)
                            self._set_status("Конвертация...")
                    except Exception:
                        pass
            # Обновляем текущий прогресс по time=
            mt = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", text)
            if mt and self.total_duration_s:
                h, mnt, s = mt.groups()
                try:
                    cur = int(h) * 3600 + int(mnt) * 60 + float(s)
                    pct = max(0, min(100, int(cur / self.total_duration_s * 100)))
                    self._set_progress(pct)
                except Exception:
                    pass
        else:
            # Для spoof оставляем индикатор неопределённым
            pass

    def _on_process_finished_threadsafe(self, exit_code: int):
        def _finish():
            try:
                self.btn_convert.configure(state=tk.NORMAL)
                self.btn_convert_stop.configure(state=tk.DISABLED)
                self.btn_spoof.configure(state=tk.NORMAL)
                self.btn_spoof_stop.configure(state=tk.DISABLED)
            except Exception:
                pass
            self._update_dependency_labels()
            self._stop_indeterminate()
            if exit_code == 0:
                self._set_progress(100)
                self._set_status("Готово")
            else:
                self._set_status(f"Ошибка (код {exit_code})")

        self.root.after(0, _finish)

    def _reset_progress(self, determinate: bool):
        self.total_duration_s = None
        self.is_indeterminate = not determinate
        if determinate:
            try:
                self.progress.configure(mode="determinate")
            except Exception:
                pass
            self._set_progress(0)
            self._stop_indeterminate()
        else:
            try:
                self.progress.configure(mode="indeterminate")
            except Exception:
                pass
            self.progress_var.set(0)
            self.lbl_percent.configure(text="...")
            try:
                self.progress.start(10)
            except Exception:
                pass

    def _set_progress(self, value: int):
        value = max(0, min(100, int(value)))
        self.progress_var.set(value)
        self.lbl_percent.configure(text=f"{value}%")

    def _stop_indeterminate(self):
        try:
            if self.progress and str(self.progress.cget("mode")) == "indeterminate":
                self.progress.stop()
        except Exception:
            pass

    def _set_status(self, text: str):
        self.lbl_status.configure(text=text)

    def _update_dependency_labels(self):
        # Сейчас надпись о режиме скрыта, оставляем хук на будущее
        pass


def main():
    # Make embedded ffmpeg (if bundled) discoverable by PATH early
    try:
        _inject_embedded_ffmpeg_into_path()
    except Exception:
        pass
    root = tk.Tk()
    # Use ttk theme if available
    try:
        style = ttk.Style(root)
        # Тёмная тема в стиле Discord
        style.theme_use("clam")
        bg = "#2b2d31"         # фон окна
        panel = "#1e1f22"      # фон панелей
        card = "#313338"       # фон карточек
        text = "#e3e5e8"       # основной текст
        subtle = "#b5bac1"     # вторичный текст
        accent = "#5865f2"     # акцент Discord

        root.configure(bg=bg)
        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=card, bordercolor=card)
        style.configure("TLabelframe.Label", background=card, foreground=text, font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=bg, foreground=text)
        style.configure("TButton", background=panel, foreground=text, padding=(10, 6), borderwidth=0)
        style.map("TButton", background=[("active", "#3a3c41")])
        style.configure("TEntry", fieldbackground=panel, foreground=text, insertcolor=text)
        style.configure("TNotebook", background=bg, tabposition="n")
        style.configure("TNotebook.Tab", background=panel, foreground=text, padding=(12, 8))
        style.map("TNotebook.Tab", background=[("selected", card)])
        style.configure("Horizontal.TProgressbar", background=accent, troughcolor=panel, bordercolor=panel, lightcolor=accent, darkcolor=accent)
    except Exception:
        pass
    TgradishGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

# ---------------------- Embedded ffmpeg PATH bootstrap ---------------------- #
def _inject_embedded_ffmpeg_into_path():
    """If ffmpeg is shipped alongside the app (PyInstaller), add it to PATH.

    Search locations:
    - In a frozen app: inside sys._MEIPASS under 'ffmpeg' or 'ffmpeg_bin'
    - Next to the executable/script: './ffmpeg' or './ffmpeg_bin'
    """
    if shutil.which("ffmpeg"):
        return

    candidates: list[str] = []

    # When frozen by PyInstaller
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and isinstance(meipass, str):
        candidates.extend([
            os.path.join(meipass, "ffmpeg"),
            os.path.join(meipass, "ffmpeg_bin"),
            meipass,
        ])

    # Directory of the executable/script
    base_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    candidates.extend([
        os.path.join(base_dir, "ffmpeg"),
        os.path.join(base_dir, "ffmpeg_bin"),
        base_dir,
    ])

    ffmpeg_names = ["ffmpeg.exe", "ffmpeg"]
    selected_dir = None
    for d in candidates:
        try:
            if not d or not os.path.isdir(d):
                continue
            for name in ffmpeg_names:
                fp = os.path.join(d, name)
                if os.path.isfile(fp):
                    selected_dir = d
                    break
            if selected_dir:
                break
        except Exception:
            continue

    if selected_dir and selected_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = selected_dir + os.pathsep + os.environ.get("PATH", "")



