[app]
title = Fon Analiz v12
package.name = fonanaliz
package.domain = org.niyazi
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0
requirements = python3
orientation = portrait
android.permissions = INTERNET

# SDK ve API sürümlerini sabitleyerek lisans takılmasını önlüyoruz
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
