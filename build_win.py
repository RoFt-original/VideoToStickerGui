import argparse
import os
import shutil
import subprocess
import sys


def _ensure_pyinstaller_installed():
    try:
        import PyInstaller  # noqa: F401
        return
    except Exception:
        pass
    print("PyInstaller не найден в текущем интерпретаторе. Устанавливаю...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "pyinstaller"]) 


def _find_ffmpeg_exe(ffmpeg_dir: str) -> str:
    if os.path.isfile(ffmpeg_dir) and os.path.basename(ffmpeg_dir).lower() == "ffmpeg.exe":
        return ffmpeg_dir
    target_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for root, _dirs, files in os.walk(ffmpeg_dir):
        if target_name in files:
            return os.path.join(root, target_name)
    raise FileNotFoundError("В указанной папке не найден ffmpeg.exe")


def build_exe(app_name: str, icon_path: str | None, script_path: str, ffmpeg_dir: str | None, onefile: bool = True, windowed: bool = True):
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Не найден скрипт: {script_path}")
    _ensure_pyinstaller_installed()

    # Всегда вызываем PyInstaller через текущий интерпретатор (исключает конфликт с Python 3.13)
    cmd = [sys.executable, "-m", "PyInstaller"]
    if onefile:
        cmd.append("--onefile")
    if windowed:
        cmd.append("--windowed")
    cmd += ["--name", app_name]

    if icon_path:
        if not os.path.isfile(icon_path):
            raise FileNotFoundError(f"Не найдена иконка: {icon_path}")
        cmd += ["--icon", icon_path]

    # Add ffmpeg.exe (если указан каталог, ищем внутри него)
    if ffmpeg_dir:
        ffmpeg_exe = _find_ffmpeg_exe(ffmpeg_dir)
        sep = ";" if os.name == "nt" else ":"
        cmd += ["--add-binary", f"{ffmpeg_exe}{sep}ffmpeg"]

    # Ensure we include tgradish CLI if needed (generally not required)
    # PyInstaller will follow runtime imports; CLI is called as external process

    cmd.append(script_path)

    print("Запуск PyInstaller:\n", " ".join(cmd))
    subprocess.check_call(cmd)
    print("Готово. EXE в папке dist/.")


def main():
    parser = argparse.ArgumentParser(description="Сборка Windows EXE через PyInstaller")
    parser.add_argument("--name", required=True, help="Имя программы (exe)")
    parser.add_argument("--icon", help="Путь к .ico иконке")
    parser.add_argument("--script", default="gui_tgradish.py", help="Главный скрипт Python")
    parser.add_argument("--ffmpeg-dir", help="Папка с ffmpeg.exe (будет упакована)")
    parser.add_argument("--no-onefile", action="store_true", help="Не собирать в один файл")
    parser.add_argument("--console", action="store_true", help="Оставить консольное окно")

    args = parser.parse_args()
    build_exe(
        app_name=args.name,
        icon_path=args.icon,
        script_path=args.script,
        ffmpeg_dir=args.ffmpeg_dir,
        onefile=not args.no_onefile,
        windowed=not args.console,
    )


if __name__ == "__main__":
    main()


