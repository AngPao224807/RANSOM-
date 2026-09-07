[app]
title = RANSOM
package.name = ransom
package.domain = org.ap.ransom
source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,mp3,ogg,kv
version = 1.0
requirements = python3,kivy==2.3.0,pyjnius,android
orientation = portrait
fullscreen = 1
android.permissions = SET_WALLPAPER,RECEIVE_BOOT_COMPLETED,SYSTEM_ALERT_WINDOW,WAKE_LOCK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.debug = 1
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1