## Tgradish GUI (Tkinter)

Простой графический интерфейс для утилиты `tgradish`, позволяющей конвертировать видео в видеостикеры Telegram и менять отображаемую длительность (spoof).

Основано на проекте `tgradish` автора sliva0. Репозиторий: [GitHub — sliva0/tgradish](https://github.com/sliva0/tgradish)

### Установка

1) Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

2) Для команды `convert` необходим установленный `ffmpeg` в PATH:

- Windows: скачайте сборку с сайта и добавьте `ffmpeg.exe` в PATH.
- Linux/macOS: установите через пакетный менеджер (`apt`, `brew` и т.д.).

`spoof` работает без `ffmpeg`.

### Запуск

```bash
python gui_tgradish.py
```

### Возможности

- Вкладка Convert: выбор входного видео, опционального пути вывода `.webm`, запуск `tgradish convert` с дополнительными аргументами.
- Вкладка Spoof: выбор входного `.webm` и выходного `.webm`, запуск `tgradish spoof` с дополнительными аргументами.
- Кнопка проверки зависимостей и кнопка установки/обновления `tgradish` через pip.
- Потоковый вывод логов процесса в окне приложения, остановка процесса.

### Примечания

- Если скрипт `tgradish` недоступен как команда, приложение запустит `python -m tgradish`.
- Дополнительные аргументы передаются как есть и должны соответствовать CLI `tgradish`.

### Лицензия исходного инструмента

`tgradish` распространяется по лицензии MIT. Подробнее см. в исходном репозитории автора: [sliva0/tgradish](https://github.com/sliva0/tgradish).

## Сборка Windows (.exe) с вшитым ffmpeg и иконкой

1) Скачайте статический `ffmpeg.exe` (например, архив из `Gyan.FFmpeg`) и положите в папку, например `ffmpeg_win` (внутри должен лежать `ffmpeg.exe`).
2) Запустите скрипт сборки:

```powershell
py -3.12 build_win.py --name "TgradishGUI" --icon ".\icon.ico" --script ".\gui_tgradish.py" --ffmpeg-dir ".\ffmpeg_win"
```

- `--name` — имя exe.
- `--icon` — путь к `.ico`.
- `--script` — главный скрипт (по умолчанию `gui_tgradish.py`).
- `--ffmpeg-dir` — папка с `ffmpeg.exe` (будет упакована и автоматически найдена приложением).
- Добавьте `--console`, если нужна консоль. Добавьте `--no-onefile`, чтобы собрать не в один файл.

Готовый exe появится в `dist/`.

## Сборка Android (.apk) через Kivy/Buildozer

В `android/main.py` сделан простой интерфейс с прогресс-баром. Для включения ffmpeg-ассетов используйте структуру каталогов по ABI.

Шаги (Linux):

```bash
python -m pip install buildozer Cython kivy
# Подготовьте папку с бинарниками ffmpeg по ABI:
# ./ffmpeg_src/arm64-v8a/ffmpeg   (исполняемый)
# ./ffmpeg_src/armeabi-v7a/ffmpeg
python build_android.py --name "TgradishGUI" --icon ./android/icon.png --ffmpeg ./ffmpeg_src
```

- Скрипт скопирует ассеты в `android/ffmpeg/**`, а `buildozer.spec` включает их в APK. APK будет в `android/bin/`.

Примечание: Встраивание полнофункционального `ffmpeg` в APK обычно делается через `ffpyplayer` или сборку нативных библиотек. Потребуются тесты на реальном устройстве.

## Альтернативы сборки без WSL (Windows)

- GitHub Actions (Linux CI):
  - Запустите workflow вручную на вкладке Actions. Файл: `.github/workflows/android-apk.yml`.
  - Готовый APK будет доступен как artifact.

- Виртуальная машина через Vagrant/VirtualBox:
  - Установите VirtualBox и Vagrant.
  - В корне проекта:
    ```bash
    vagrant up
    ```
  - После завершения сборки APK лежит в `android/bin/` внутри проекта (смонтированная папка `/vagrant`).


