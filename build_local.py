#!/usr/bin/env python3
"""
Скрипт для локальной сборки APK файла
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Проверяет наличие необходимых инструментов"""
    print("🔍 Проверка требований...")
    
    # Проверка Python
    if sys.version_info < (3, 11):
        print("❌ Требуется Python 3.11 или выше")
        return False
    
    # Проверка Java
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Java не найдена")
            return False
        print("✅ Java найдена")
    except FileNotFoundError:
        print("❌ Java не найдена")
        return False
    
    # Проверка Android SDK
    android_home = os.environ.get('ANDROID_HOME')
    if not android_home:
        print("❌ ANDROID_HOME не установлена")
        return False
    
    if not os.path.exists(android_home):
        print("❌ ANDROID_HOME указывает на несуществующую папку")
        return False
    
    print("✅ Android SDK найдена")
    
    # Проверка Android NDK
    ndk_home = os.environ.get('ANDROID_NDK_HOME')
    if not ndk_home:
        print("❌ ANDROID_NDK_HOME не установлена")
        return False
    
    if not os.path.exists(ndk_home):
        print("❌ ANDROID_NDK_HOME указывает на несуществующую папку")
        return False
    
    print("✅ Android NDK найдена")
    
    return True

def install_dependencies():
    """Устанавливает Python зависимости"""
    print("📦 Установка зависимостей...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'buildozer', 'Cython', 'kivy'], check=True)
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def build_apk():
    """Собирает APK файл"""
    print("🔨 Сборка APK...")
    
    android_dir = Path('android')
    if not android_dir.exists():
        print("❌ Папка android не найдена")
        return False
    
    try:
        # Переходим в папку android
        os.chdir(android_dir)
        
        # Запускаем buildozer
        result = subprocess.run(['buildozer', '-v', 'android', 'debug'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ APK успешно собран!")
            
            # Ищем APK файл
            bin_dir = Path('bin')
            if bin_dir.exists():
                apk_files = list(bin_dir.glob('*.apk'))
                if apk_files:
                    print(f"📱 APK файл: {apk_files[0].absolute()}")
                    return True
            
            print("⚠️ APK файл не найден в папке bin/")
            return False
        else:
            print(f"❌ Ошибка сборки: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        # Возвращаемся в корневую папку
        os.chdir('..')

def main():
    """Главная функция"""
    print("🚀 Запуск сборки APK...")
    print("=" * 50)
    
    # Проверяем требования
    if not check_requirements():
        print("\n❌ Требования не выполнены. Установите необходимые инструменты.")
        sys.exit(1)
    
    # Устанавливаем зависимости
    if not install_dependencies():
        print("\n❌ Не удалось установить зависимости.")
        sys.exit(1)
    
    # Собираем APK
    if not build_apk():
        print("\n❌ Не удалось собрать APK.")
        sys.exit(1)
    
    print("\n🎉 Сборка завершена успешно!")

if __name__ == '__main__':
    main()
