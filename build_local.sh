#!/bin/bash

echo "🚀 Запуск сборки APK для Linux/macOS..."
echo "================================================"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.11 или выше."
    exit 1
fi

# Проверяем версию Python
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Требуется Python 3.11 или выше. Текущая версия: $python_version"
    exit 1
fi

# Проверяем наличие Java
if ! command -v java &> /dev/null; then
    echo "❌ Java не найдена. Установите Java 17 или выше."
    exit 1
fi

# Проверяем переменные окружения
if [ -z "$ANDROID_HOME" ]; then
    echo "❌ ANDROID_HOME не установлена. Установите Android SDK."
    exit 1
fi

if [ -z "$ANDROID_NDK_HOME" ]; then
    echo "❌ ANDROID_NDK_HOME не установлена. Установите Android NDK."
    exit 1
fi

# Проверяем существование папок
if [ ! -d "$ANDROID_HOME" ]; then
    echo "❌ ANDROID_HOME указывает на несуществующую папку: $ANDROID_HOME"
    exit 1
fi

if [ ! -d "$ANDROID_NDK_HOME" ]; then
    echo "❌ ANDROID_NDK_HOME указывает на несуществующую папку: $ANDROID_NDK_HOME"
    exit 1
fi

echo "✅ Все требования выполнены"
echo

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
python3 -m pip install --upgrade pip
python3 -m pip install buildozer Cython kivy

if [ $? -ne 0 ]; then
    echo "❌ Ошибка установки зависимостей"
    exit 1
fi

# Переходим в папку android
cd android
if [ ! -f "buildozer.spec" ]; then
    echo "❌ Файл buildozer.spec не найден в папке android"
    exit 1
fi

# Собираем APK
echo "🔨 Сборка APK..."
buildozer -v android debug

if [ $? -ne 0 ]; then
    echo "❌ Ошибка сборки APK"
    exit 1
fi

# Проверяем результат
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "✅ APK успешно собран!"
    echo "📱 APK файл находится в папке android/bin/"
    ls -la bin/*.apk
else
    echo "⚠️ APK файл не найден в папке bin/"
fi

echo
echo "🎉 Сборка завершена!"
