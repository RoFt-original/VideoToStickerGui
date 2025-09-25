[app]
title = Tgradish GUI
package.name = TgradishGUI
package.domain = org.example
source.dir = .
source.include_exts = py,png,kv,txt
version = 0.1
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0
log_level = 1
icon.filename = icon.png


[buildozer]
log_level = 2
warn_on_root = 0

[android]
android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
# Настройка прав при необходимости
# android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.gradle_dependencies = com.arthenica:ffmpeg-kit-full:6.0-2.LTS
android.gradle_repositories = mavenCentral()


