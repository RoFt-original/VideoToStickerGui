@echo off
echo 🚀 Запуск сборки APK для Windows...
echo ================================================

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.11 или выше.
    pause
    exit /b 1
)

REM Проверяем наличие Java
java -version >nul 2>&1
if errorlevel 1 (
    echo ❌ Java не найдена. Установите Java 17 или выше.
    pause
    exit /b 1
)

REM Проверяем переменные окружения
if "%ANDROID_HOME%"=="" (
    echo ❌ ANDROID_HOME не установлена. Установите Android SDK.
    pause
    exit /b 1
)

if "%ANDROID_NDK_HOME%"=="" (
    echo ❌ ANDROID_NDK_HOME не установлена. Установите Android NDK.
    pause
    exit /b 1
)

echo ✅ Все требования выполнены
echo.

REM Устанавливаем зависимости
echo 📦 Установка зависимостей...
python -m pip install --upgrade pip
python -m pip install buildozer Cython kivy
if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

REM Переходим в папку android
cd android
if not exist "buildozer.spec" (
    echo ❌ Файл buildozer.spec не найден в папке android
    pause
    exit /b 1
)

REM Собираем APK
echo 🔨 Сборка APK...
buildozer -v android debug
if errorlevel 1 (
    echo ❌ Ошибка сборки APK
    pause
    exit /b 1
)

REM Проверяем результат
if exist "bin\*.apk" (
    echo ✅ APK успешно собран!
    echo 📱 APK файл находится в папке android\bin\
    for %%f in (bin\*.apk) do echo    %%f
) else (
    echo ⚠️ APK файл не найден в папке bin\
)

echo.
echo 🎉 Сборка завершена!
pause
