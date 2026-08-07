[app]
# (str) Title of your application
title = Fon Analiz v12

# (str) Package name
package.name = fonanaliz

# (str) Package domain (needed for android packaging)
package.domain = org.niyazi

# (str) Source code where the application resides
source.dir = .

# (list) Source files to include (let it include py files)
source.include_exts = py,png,jpg,kv,atlas,db

# (list) Application requirements
requirements = python3

# (str) Supported orientations
orientation = portrait

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (list) Permissions
android.permissions = INTERNET

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 1
