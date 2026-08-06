[app]

title = Quant Pro Mobil
package.name = quantpromobil
package.domain = org.quantpro

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,certifi,urllib3,requests

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.api = 33
android.minapi = 21

android.archs = arm64-v8a

android.accept_sdk_licenses = True


[buildozer]

log_level = 2
warn_on_root = 1
