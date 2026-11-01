[app]
title = Lotto Matcher
package.name = lottomatcher
package.domain = org.lottomatch
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy==2.3.0,android,androidstorage4kivy
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.api = 34
android.minapi = 24
android.accept_sdk_license = True
android.permissions =
android.enable_androidx = True
android.gradle_dependencies = androidx.core:core:1.5.0

[buildozer]
log_level = 2
warn_on_root = 1
