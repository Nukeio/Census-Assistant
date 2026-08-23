# Census Assistant Android App — Build Guide

## Project Structure

```
android/
├── build.gradle                  # Root Gradle config (plugin versions)
├── settings.gradle               # Module inclusion
├── gradle.properties             # AndroidX, JVM settings
├── gradle/wrapper/
│   └── gradle-wrapper.properties # Gradle 8.4 distribution
└── app/
    ├── build.gradle              # App-level deps (AGP 8.2.2, Kotlin 1.9.22)
    ├── proguard-rules.pro        # Protects @JavascriptInterface methods
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/gov/census/assistant/
        │   ├── MainActivity.kt       # WebView host + native intents
        │   └── WebAppInterface.kt    # JS → Android bridge
        └── res/
            ├── layout/activity_main.xml
            ├── values/{colors,strings,themes}.xml
            ├── xml/file_paths.xml
            └── drawable/{splash_background,ic_launcher_foreground}.xml
```

The frontend (`frontend/index.html`, `app.js`, `styles.css`) is bundled
as Android assets via `sourceSets.main.assets.srcDirs += ['../../frontend']`.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| JDK | 17+ | https://adoptium.net/ |
| Android Studio | Hedgehog 2023.1+ | https://developer.android.com/studio |
| Android SDK | API 34 (compileSdk) | via SDK Manager in Android Studio |

---

## Build Steps

### Option A — Android Studio (Recommended)

1. Open **Android Studio**
2. **File → Open** → select the `android/` folder
3. Wait for Gradle sync to complete
4. Connect a device or start an emulator
5. **Run → Run 'app'** (Shift+F10)

### Option B — Command Line

```powershell
# From the android/ directory
cd "D:\Agent Works\Projects\CENSUS ASSISTANT ANDROID APP\android"

# Debug APK
.\gradlew.bat assembleDebug

# Output: app/build/outputs/apk/debug/app-debug.apk
```

> **Note:** `gradlew.bat` requires JDK 17+ on PATH.
> Set `JAVA_HOME` if needed: `$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17..."`

---

## Running the Full Stack

The Android app talks to a permanently-hosted backend, not your PC — it is
not tied to any machine's LAN IP. The backend is deployed at:

```
https://shahinxsha.pythonanywhere.com
```

`MainActivity.kt`'s `BACKEND_URL` constant points there. The app probes
`$BACKEND_URL/api/admin/stats` on startup:
- **Backend reachable** → loads the live app (full functionality, works from
  any network, anywhere)
- **Offline / unreachable** → loads bundled `assets/index.html` (UI only, no
  API calls) instead of crashing

To update the backend code, push to the `Census-Assistant` GitHub repo, then
from a PythonAnywhere Bash console run `git pull` inside `~/Census-Assistant`
and hit **Reload** on the Web tab.

For local development only (testing backend changes before deploying), you
can still run `python server.py` locally and temporarily point `BACKEND_URL`
at `http://10.0.2.2:8080` (Android emulator) or your machine's LAN IP for a
physical device on the same WiFi — just remember to change it back to the
PythonAnywhere URL before shipping a build.

---

## Android Bridge (`window.AndroidBridge`)

The following JS functions are available in the WebView:

| JS Call | Android Action |
|---------|---------------|
| `AndroidBridge.callPhone("9876543210")` | Opens native phone dialer |
| `AndroidBridge.openWhatsApp("919876543210", "msg")` | Opens WhatsApp |
| `AndroidBridge.sendSms("9876543210", "msg")` | Opens SMS composer |
| `AndroidBridge.shareText("title", "body")` | Native share sheet |
| `AndroidBridge.showToast("message")` | Android Toast |
| `AndroidBridge.vibrate(100)` | Haptic feedback (ms) |
| `AndroidBridge.setPreference("key", "val")` | SharedPreferences write |
| `AndroidBridge.getPreference("key", "default")` | SharedPreferences read |
| `AndroidBridge.isNetworkAvailable()` | Returns true/false |
| `AndroidBridge.getDeviceInfo()` | JSON device metadata |

The `frontend/app.js` bridge helpers auto-detect Android and fall back to browser APIs:
- `nativeCall(number)` — dialer or `tel:` link
- `nativeWhatsApp(number, msg)` — bridge or `wa.me` URL
- `nativeShare(title, text)` — bridge or Web Share API

---

### Option C — GitHub Actions (no local Android SDK needed)

Push this whole project to a GitHub repository and the workflow at
`.github/workflows/android-build.yml` builds a debug APK on every push to
`main` that touches `android/` or `frontend/`, and on demand via the
Actions tab ("Run workflow"). The runner installs JDK 17 and the Android
SDK itself — you don't need Android Studio installed anywhere. Download
the built APK from the finished run's **Artifacts** section
(`census-assistant-debug-apk`).

## Deployment to Physical Device (APK Sideload)

```powershell
# Build signed release APK
.\gradlew.bat assembleRelease

# Install via ADB
adb install app\build\outputs\apk\release\app-release-unsigned.apk
```

For Play Store distribution, create a signing keystore in Android Studio:
**Build → Generate Signed Bundle/APK → APK → Create new keystore**
