[app]
title = Quant Pro Mobil
package.name = quantpromobil
package.domain = org.quantpro
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.include_patterns = assets/*,images/*.png
source.exclude_exts = spec
version = 1.0
requirements = python3,kivy,certifi,urllib3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.archs = arm64-v8a
p4s_branch = master

[buildozer]
log_level = 2
warn_on_root = 1
