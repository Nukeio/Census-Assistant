# Census Assistant Android App — Build & Release Guide

This guide covers building both development and production release packages for Census Assistant, with full **Google Play Protect compliance** and **Google Play Console distribution** support.

---

## 1. Google Play Protect Compliance Overview

Previous debug builds were blocked by Google Play Protect due to:
1. **Debug Keystore Signing**: Sideloaded APKs signed with the public Android debug certificate are automatically flagged as untrusted developer builds.
2. **`android:debuggable="true"`**: Enabled memory inspection and process debugging.
3. **High-Risk & Unused Permissions**: Permissions like `CALL_PHONE` and `RECEIVE_BOOT_COMPLETED` triggered malware detection heuristics.
4. **Cleartext HTTP Traffic**: `usesCleartextTraffic="true"` allowed unencrypted network communication.

### Fixes Applied:
- **Clean Permissions**: Removed `CALL_PHONE` (using `Intent.ACTION_DIAL`), removed `RECEIVE_BOOT_COMPLETED`, removed legacy `WRITE_EXTERNAL_STORAGE`.
- **HTTPS Enforcement**: Added `network_security_config.xml` and set `usesCleartextTraffic="false"`.
- **Release Signing**: Configured Gradle to sign release builds using **APK Signature Scheme v1, v2, v3, and v4** with RSA 4096-bit keys and `debuggable="false"`.
- **Play Store Ready**: Gradle generates both signed **Release APK** (`.apk`) and **Android App Bundle** (`.aab`).

---

## 2. Generating a Local Production Release Keystore

To build a signed release APK on your computer:

```cmd
cd android
generate-release-keystore.bat
```

Or run `keytool` manually:

```cmd
keytool -genkeypair -v -keystore release.keystore -alias census_release -keyalg RSA -keysize 4096 -validity 10000 -storepass census2027 -keypass census2027 -dname "CN=Census Assistant, OU=Census Operations, O=Census Assistant, L=Lakhipur, ST=Assam, C=IN"
```

> **Security Note:** `release.keystore` is automatically ignored by `.gitignore` and must **never** be committed to GitHub.

---

## 3. Building the Release APK & AAB Locally

```powershell
cd android

# Build Signed Release APK
.\gradlew.bat assembleRelease

# Build Google Play App Bundle (AAB)
.\gradlew.bat bundleRelease
```

### Outputs:
- **Signed Release APK**: `app/build/outputs/apk/release/app-release.apk`
- **Google Play Bundle**: `app/build/outputs/bundle/release/app-release.aab`

---

## 4. Automated Cloud Builds (GitHub Actions)

Every push to `main` that modifies `android/` or `frontend/` triggers the GitHub Actions workflow at `.github/workflows/android-build.yml`.

The workflow automatically:
1. Compiles the Android project with JDK 17 and API 34.
2. Signs the release APK and AAB with modern v1/v2/v3 signature schemes.
3. Verifies signature integrity with `apksigner verify --verbose`.
4. Uploads two release artifacts to the GitHub Actions run page:
   - `census-assistant-release-apk`
   - `census-assistant-release-aab`

---

## 5. Custom Production Signing with GitHub Secrets (Optional)

If you want GitHub Actions to sign with your own private production keystore:
1. Base64 encode your keystore:
   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("release.keystore"))
   ```
2. In GitHub repository **Settings → Secrets and variables → Actions**, add:
   - `SIGNING_KEY_BASE64`: The base64-encoded string
   - `KEYSTORE_PASSWORD`: Your keystore password
   - `KEY_ALIAS`: Your key alias
   - `KEY_PASSWORD`: Your private key password
