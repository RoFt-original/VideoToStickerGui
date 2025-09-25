# Video to Sticker GUI

Приложение для конвертации видео в стикеры с графическим интерфейсом на Kivy.

## Возможности

- 🎥 Загрузка видео файлов
- ✂️ Обрезка видео по времени
- 🎨 Настройка качества и размера
- 📱 Конвертация в стикеры (GIF/WebP)
- 🖥️ Кроссплатформенный интерфейс
- 📦 Сборка в APK для Android

## Установка и запуск

### Требования

- Python 3.11+
- FFmpeg (включен в проект)
- Kivy

### Быстрый старт

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd video-to-sticker-gui
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите приложение:
```bash
python main.py
```

## Сборка APK для Android

### Автоматическая сборка через GitHub Actions

1. Перейдите в раздел "Actions" в вашем GitHub репозитории
2. Выберите workflow "Build Android APK"
3. Нажмите "Run workflow"
4. Дождитесь завершения сборки
5. Скачайте APK из раздела "Artifacts"

### Локальная сборка

#### Windows

1. Установите Android SDK и NDK
2. Настройте переменные окружения:
   - `ANDROID_HOME` - путь к Android SDK
   - `ANDROID_NDK_HOME` - путь к Android NDK
3. Запустите сборку:
```cmd
build_local.bat
```

#### Linux/macOS

1. Установите Android SDK и NDK
2. Настройте переменные окружения:
```bash
export ANDROID_HOME=/path/to/android-sdk
export ANDROID_NDK_HOME=/path/to/android-ndk
```
3. Запустите сборку:
```bash
./build_local.sh
```

#### Ручная сборка

1. Перейдите в папку `android`:
```bash
cd android
```

2. Установите buildozer:
```bash
pip install buildozer Cython kivy
```

3. Запустите сборку:
```bash
buildozer -v android debug
```

4. APK файл будет создан в папке `android/bin/`

## Структура проекта

```
.
├── .github/
│   └── workflows/
│       └── android-apk.yml          # GitHub Actions workflow
├── android/
│   ├── buildozer.spec               # Конфигурация buildozer
│   ├── main.py                      # Главный файл приложения
│   ├── requirements.txt             # Python зависимости
│   └── assets/                      # Ресурсы приложения
├── ffmpeg_win/                      # FFmpeg для Windows
├── ffmpeg_linux/                    # FFmpeg для Linux
├── build_local.py                   # Python скрипт сборки
├── build_local.bat                  # Windows bat файл
├── build_local.sh                   # Linux/macOS shell скрипт
├── BUILD_INSTRUCTIONS.md            # Подробные инструкции
└── README.md                        # Этот файл
```

## Использование

1. **Загрузка видео**: Нажмите "Выбрать файл" и выберите видео
2. **Настройка параметров**:
   - Время начала и окончания обрезки
   - Качество (низкое/среднее/высокое)
   - Размер (маленький/средний/большой)
3. **Конвертация**: Нажмите "Конвертировать в стикер"
4. **Сохранение**: Выберите папку для сохранения результата

## Технические детали

### Зависимости

- **Kivy** - GUI фреймворк
- **FFmpeg** - обработка видео
- **Pillow** - обработка изображений
- **Buildozer** - сборка APK

### Поддерживаемые форматы

- **Входные**: MP4, AVI, MOV, MKV, WebM
- **Выходные**: GIF, WebP

### Системные требования

- **Windows**: Windows 10+
- **Linux**: Ubuntu 18.04+ или аналогичные
- **macOS**: macOS 10.14+
- **Android**: Android 7.0+ (API 24+)

## Устранение проблем

### Ошибки сборки APK

1. **"Aidl not found"** - убедитесь, что установлены build-tools
2. **Ошибка лицензий** - примите лицензии Android SDK
3. **Ошибка NDK** - проверьте версию NDK (должна быть 25.1.8937393)
4. **Ошибка памяти** - увеличьте память для Java процесса

### Ошибки приложения

1. **"FFmpeg не найден"** - убедитесь, что FFmpeg установлен
2. **Ошибка загрузки видео** - проверьте формат файла
3. **Ошибка конвертации** - проверьте параметры обрезки

## Лицензия

MIT License

## Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## Поддержка

Если у вас возникли проблемы, создайте Issue в репозитории или обратитесь к документации в `BUILD_INSTRUCTIONS.md`.