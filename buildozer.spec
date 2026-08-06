[app]

title = Quant Pro Mobil
package.name = quantpromobil
package.domain = org.quantpro

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas

version = 1.0

requirements = python3,kivy==2.3.0,requests,urllib3,certifi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.sdk = 33
android.build_tools_version = 33.0.2
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]

log_level = 2
warn_on_root = 1
