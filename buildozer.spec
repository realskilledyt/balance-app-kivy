[app]
title = Balance App
package.name = balanceapp
package.domain = org.balanceapp

source.dir = .
source.include_exts = py,kv,png,jpg,ttf,json

version = 0.1

requirements = python3, kivy

orientation = portrait

fullscreen = 1
hide_keyboard = 0

android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b

log_level = 2

# Permissions (file storage only)
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Icon (optional, replace later)
icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

