import argparse
import os
import shutil
import subprocess
import sys


def ensure_buildozer():
    if shutil.which("buildozer"):
        return
    print("Устанавливаю buildozer...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "buildozer", "Cython", "kivy"])


def copy_ffmpeg_assets(source_dir: str, target_dir: str):
    if not os.path.isdir(source_dir):
        raise FileNotFoundError(f"Не найдена папка ffmpeg: {source_dir}")
    os.makedirs(target_dir, exist_ok=True)
    for abi in ("arm64-v8a", "armeabi-v7a"):
        src = os.path.join(source_dir, abi)
        if not os.path.isdir(src):
            print(f"Предупреждение: не найдена папка ABI {src}")
            continue
        dst = os.path.join(target_dir, abi)
        os.makedirs(dst, exist_ok=True)
        for name in os.listdir(src):
            sp = os.path.join(src, name)
            dp = os.path.join(dst, name)
            if os.path.isfile(sp):
                shutil.copy2(sp, dp)


def build_apk(app_name: str | None = None, icon_png: str | None = None, ffmpeg_src: str | None = None):
    ensure_buildozer()
    spec_path = os.path.join("android", "buildozer.spec")
    if not os.path.isfile(spec_path):
        raise FileNotFoundError("Не найден android/buildozer.spec")

    # Copy ffmpeg assets if provided
    if ffmpeg_src:
        copy_ffmpeg_assets(ffmpeg_src, os.path.join("android", "ffmpeg"))

    # Optionally adjust spec
    if app_name or icon_png:
        print("Обновляю buildozer.spec...")
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        if app_name:
            content = content.replace("title = Tgradish GUI", f"title = {app_name}")
            content = content.replace("package.name = TgradishGUI", f"package.name = {app_name}")
        if icon_png:
            content = content.replace("icon.filename = icon.png", f"icon.filename = {icon_png}")
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(content)

    cwd = os.path.abspath("android")
    print("Запуск buildozer через текущий интерпретатор Python...")
    # На Windows бинарь buildozer может быть не в PATH; запускаем модуль напрямую
    subprocess.check_call([sys.executable, "-m", "buildozer", "-v", "android", "debug"], cwd=cwd)
    print("Готово. APK в android/bin/.")


def main():
    parser = argparse.ArgumentParser(description="Сборка APK с помощью Buildozer")
    parser.add_argument("--name", help="Имя приложения (title и package.name)")
    parser.add_argument("--icon", help="Путь к PNG-иконке для Android")
    parser.add_argument("--ffmpeg", help="Папка с ffmpeg по ABI (arm64-v8a/, armeabi-v7a/)")
    args = parser.parse_args()
    build_apk(app_name=args.name, icon_png=args.icon, ffmpeg_src=args.ffmpeg)


if __name__ == "__main__":
    main()


