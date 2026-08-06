[app]

# Uygulama adı
title = Quant Pro Mobil

# Paket adı
package.name = quantpromobil

# Paket domain
package.domain = org.quantpro


# Kaynak klasörü
source.dir = .

# Dahil edilecek dosyalar
source.include_exts = py,kv,png,jpg,jpeg,atlas,json,db


# Versiyon
version = 1.0


# Gereksinimler
requirements = python3,kivy==2.3.0,requests,urllib3,certifi


# Ekran
orientation = portrait

fullscreen = 0


# Android izinleri
android.permissions = INTERNET


# Android sürümü
android.api = 33

# Minimum Android
android.minapi = 21


# NDK
android.ndk = 25.2.9519653


# Mimari
android.archs = arm64-v8a


# Android tema
android.entrypoint = org.kivy.android.PythonActivity


# Uygulama ikonu varsa
# icon.filename = %(source.dir)s/icon.png


# Splash ekranı
# presplash.filename = %(source.dir)s/presplash.png



[buildozer]


# Log seviyesi
log_level = 2


# Root uyarısı
warn_on_root = 1


# Cache
build_dir = .buildozer


# Android debug
android.accept_sdk_license = True
