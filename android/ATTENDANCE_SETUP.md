# Android setup for the Field Attendance tab

The Attendance tab needs two things a plain `WebView` does **not** grant by
default: the device camera (for `<input type="file" accept="image/*" capture>`)
and the device GPS (for `navigator.geolocation`). Without the wiring below the
tab loads fine but the photo picker never opens the camera and the location
capture silently fails with "permission denied".

`AndroidManifest.xml` already declares the permissions (`CAMERA`,
`ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`). The three changes below go
into `app/src/main/java/gov/census/assistant/MainActivity.kt`.

---

## 1. Imports

Add to the import block at the top of `MainActivity.kt`:

```kotlin
import android.Manifest
import android.content.pm.PackageManager
import android.webkit.GeolocationPermissions
import android.webkit.PermissionRequest
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
```

## 2. Ask for the runtime permissions on launch

Add this constant and call inside the activity. Call `requestFieldPermissions()`
from the end of `onCreate()`:

```kotlin
companion object {
    private const val FIELD_PERMISSION_REQUEST = 4201
}

private fun requestFieldPermissions() {
    val needed = arrayOf(
        Manifest.permission.CAMERA,
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.ACCESS_COARSE_LOCATION
    ).filter {
        ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
    }

    if (needed.isNotEmpty()) {
        ActivityCompat.requestPermissions(this, needed.toTypedArray(), FIELD_PERMISSION_REQUEST)
    }
}
```

## 3. Let the WebView use them

Inside the `WebChromeClient` the activity already sets on the WebView, add these
two overrides. **`onGeolocationPermissionsShowPrompt` is the important one** —
without it `navigator.geolocation` never fires its success callback, no matter
what the manifest says:

```kotlin
override fun onGeolocationPermissionsShowPrompt(
    origin: String?,
    callback: GeolocationPermissions.Callback?
) {
    val granted = ContextCompat.checkSelfPermission(
        this@MainActivity, Manifest.permission.ACCESS_FINE_LOCATION
    ) == PackageManager.PERMISSION_GRANTED

    if (!granted) requestFieldPermissions()
    // retain = true so the user is not re-prompted on every submission
    callback?.invoke(origin, granted, true)
}

override fun onPermissionRequest(request: PermissionRequest?) {
    runOnUiThread {
        val wantsCamera = request?.resources?.contains(PermissionRequest.RESOURCE_VIDEO_CAPTURE) == true
        val hasCamera = ContextCompat.checkSelfPermission(
            this@MainActivity, Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED

        if (wantsCamera && hasCamera) request?.grant(request.resources) else request?.deny()
    }
}
```

Also make sure the WebView settings include:

```kotlin
webView.settings.setGeolocationEnabled(true)
webView.settings.javaScriptEnabled = true
webView.settings.domStorageEnabled = true
webView.settings.allowFileAccess = true
```

If the activity does not already override `onShowFileChooser`, the camera/file
picker will not open at all. The standard implementation launches the chooser
intent the WebView hands you and passes the result back through the callback —
if `MainActivity` already handles Excel/PDF uploads in the Admin panel, that
override exists and needs no change.

---

## HTTPS is required for location

Browsers and the Android WebView only expose `navigator.geolocation` on a
**secure context**: `https://`, or `localhost`. If the app points at a plain
`http://` LAN address, location capture will be refused before any permission
prompt appears, and the Attendance tab will say *"Location blocked (insecure
connection)"*.

For field use, deploy the backend behind HTTPS (Render already terminates TLS
for you) and point `BACKEND_URL` at the `https://` origin. The rest of the app
works over `http://`; only attendance location capture requires TLS.

## Verifying on a device

1. Install the APK and open **Attendance** from the home screen.
2. Android should prompt for Camera and Location on first launch — accept both.
3. Tap **Capture** under Current Location; the card should turn green with
   coordinates and an accuracy figure within a few seconds outdoors.
4. Tap the photo box; the camera app should open directly.
5. Submit, then reopen the tab — it should show your entry as *Pending review*
   rather than an empty form.
