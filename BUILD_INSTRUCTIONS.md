# Инструкции по сборке APK

## Локальная сборка

### Требования
- Python 3.11+
- Java 17+
- Android SDK
- Android NDK 25.1.8937393
- Buildozer

### Установка зависимостей

1. Установите Python зависимости:
```bash
pip install buildozer Cython kivy
```

2. Установите Android SDK и NDK
3. Настройте переменные окружения:
```bash
export ANDROID_HOME=/path/to/android-sdk
export ANDROID_NDK_HOME=/path/to/android-ndk
```

### Сборка APK

1. Перейдите в папку `android`:
```bash
cd android
```

2. Запустите сборку:
```bash
buildozer -v android debug
```

3. APK файл будет создан в папке `android/bin/`

## Сборка через GitHub Actions

### Автоматическая сборка

1. Перейдите в раздел "Actions" в вашем GitHub репозитории
2. Выберите workflow "Build Android APK"
3. Нажмите "Run workflow"
4. Дождитесь завершения сборки
5. Скачайте APK из раздела "Artifacts"

### Что делает workflow

1. **Checkout** - загружает код из репозитория
2. **Setup Java 17** - устанавливает Java 17
3. **Setup Python** - устанавливает Python 3.11
4. **Set up Android SDK** - устанавливает Android SDK с API 33
5. **Accept Android SDK licenses** - принимает лицензии Android SDK
6. **Install additional Android tools** - устанавливает platform-tools и build-tools
7. **Install build tools** - устанавливает Python зависимости (buildozer, Cython, kivy)
8. **Build APK** - собирает APK файл
9. **Upload artifact** - загружает APK как артефакт

### Структура проекта

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
└── README.md
```

### Конфигурация buildozer.spec

Основные настройки в `android/buildozer.spec`:

- `title` - название приложения
- `package.name` - имя пакета
- `package.domain` - домен пакета
- `source.include_exts` - расширения файлов для включения
- `android.permissions` - разрешения Android
- `android.api` - минимальная версия Android API
- `android.minapi` - минимальная версия Android API
- `android.ndk` - версия Android NDK

### Устранение проблем

1. **Ошибка "Aidl not found"** - убедитесь, что установлены build-tools
2. **Ошибка лицензий** - примите лицензии Android SDK
3. **Ошибка NDK** - проверьте версию NDK (должна быть 25.1.8937393)
4. **Ошибка памяти** - увеличьте память для Java процесса

### Дополнительные команды

- Очистка проекта: `buildozer android clean`
- Пересборка: `buildozer android debug --private .`
- Просмотр логов: `buildozer android debug -v`
