@echo off
setlocal
cd /d "%~dp0"
echo [PuddingPods] Building debug APK...
call gradlew.bat :app:assembleDebug
if errorlevel 1 (
  echo.
  echo Build failed. Open this project in Android Studio and let Gradle sync/download dependencies, then retry.
  pause
  exit /b 1
)
echo.
echo APK: app\build\outputs\apk\debug\app-debug.apk
pause
