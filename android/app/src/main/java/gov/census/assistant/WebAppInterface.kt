package gov.census.assistant

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.webkit.JavascriptInterface
import android.widget.Toast
import org.json.JSONArray
import org.json.JSONObject

/**
 * WebAppInterface — Native Android bridge exposed to the WebView JavaScript context
 * as `window.AndroidBridge`.
 *
 * All @JavascriptInterface methods are callable from JS via:
 *   AndroidBridge.methodName(args)
 */
class WebAppInterface(private val context: Context) {

    // ─────────────────────────────────────────────
    // Device & App Info
    // ─────────────────────────────────────────────

    @JavascriptInterface
    fun getDeviceInfo(): String {
        return JSONObject().apply {
            put("platform", "android")
            put("sdkVersion", Build.VERSION.SDK_INT)
            put("model", "${Build.MANUFACTURER} ${Build.MODEL}")
            put("osVersion", Build.VERSION.RELEASE)
            put("appVersion", "1.0.0")
        }.toString()
    }

    @JavascriptInterface
    fun getAppVersion(): String = "1.0.0"

    // ─────────────────────────────────────────────
    // Phone / Communication
    // ─────────────────────────────────────────────

    /**
     * Open the native phone dialer with a pre-filled number.
     * Requires CALL_PHONE permission for direct calling.
     */
    @JavascriptInterface
    fun callPhone(phoneNumber: String) {
        try {
            val cleanNumber = phoneNumber.replace(Regex("[^\\d+]"), "")
            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$cleanNumber"))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
        } catch (e: Exception) {
            showToast("Unable to open phone dialer")
        }
    }

    /**
     * Open WhatsApp with a pre-filled message to the given phone number.
     * Falls back to a web WhatsApp link if WhatsApp is not installed.
     */
    @JavascriptInterface
    fun openWhatsApp(phoneNumber: String, message: String = "") {
        try {
            val cleanNumber = phoneNumber.replace(Regex("[^\\d+]"), "")
            val encodedMsg = Uri.encode(message)
            val uri = Uri.parse("https://wa.me/$cleanNumber?text=$encodedMsg")
            val intent = Intent(Intent.ACTION_VIEW, uri).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            showToast("Unable to open WhatsApp")
        }
    }

    /**
     * Compose a new SMS to the given phone number.
     */
    @JavascriptInterface
    fun sendSms(phoneNumber: String, message: String = "") {
        try {
            val uri = Uri.parse("smsto:${phoneNumber.replace(Regex("[^\\d+]"), "")}")
            val intent = Intent(Intent.ACTION_SENDTO, uri).apply {
                putExtra("sms_body", message)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            showToast("Unable to open messaging app")
        }
    }

    // ─────────────────────────────────────────────
    // Share / Export
    // ─────────────────────────────────────────────

    /**
     * Share arbitrary text content via the native Android share sheet.
     */
    @JavascriptInterface
    fun shareText(title: String, text: String) {
        try {
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_SUBJECT, title)
                putExtra(Intent.EXTRA_TEXT, text)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(Intent.createChooser(intent, "Share via").apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            })
        } catch (e: Exception) {
            showToast("Unable to share")
        }
    }

    /**
     * Open a URL in the device's external browser.
     */
    @JavascriptInterface
    fun openExternalUrl(url: String) {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            showToast("Unable to open URL")
        }
    }

    // ─────────────────────────────────────────────
    // UI Feedback
    // ─────────────────────────────────────────────

    /**
     * Show a short native toast message.
     */
    @JavascriptInterface
    fun showToast(message: String) {
        (context as? android.app.Activity)?.runOnUiThread {
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
        }
    }

    /**
     * Trigger a brief haptic vibration (e.g., on button tap confirmation).
     */
    @JavascriptInterface
    fun vibrate(durationMs: Long = 100L) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vm.defaultVibrator.vibrate(
                    VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE)
                )
            } else {
                @Suppress("DEPRECATION")
                val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(durationMs)
                }
            }
        } catch (e: Exception) {
            // Vibration not available on this device — silently ignore
        }
    }

    // ─────────────────────────────────────────────
    // Local Storage / Preferences
    // ─────────────────────────────────────────────

    /**
     * Persist a string value to Android SharedPreferences.
     */
    @JavascriptInterface
    fun setPreference(key: String, value: String) {
        context.getSharedPreferences("census_prefs", Context.MODE_PRIVATE)
            .edit()
            .putString(key, value)
            .apply()
    }

    /**
     * Read a persisted string value from Android SharedPreferences.
     */
    @JavascriptInterface
    fun getPreference(key: String, defaultValue: String = ""): String {
        return context.getSharedPreferences("census_prefs", Context.MODE_PRIVATE)
            .getString(key, defaultValue) ?: defaultValue
    }

    /**
     * Clear all saved preferences (e.g., on logout).
     */
    @JavascriptInterface
    fun clearPreferences() {
        context.getSharedPreferences("census_prefs", Context.MODE_PRIVATE)
            .edit()
            .clear()
            .apply()
    }

    // ─────────────────────────────────────────────
    // Network
    // ─────────────────────────────────────────────

    /**
     * Returns true if the device has active network connectivity.
     */
    @JavascriptInterface
    fun isNetworkAvailable(): Boolean {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val network = cm.activeNetwork ?: return false
            val caps = cm.getNetworkCapabilities(network) ?: return false
            caps.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET)
        } else {
            @Suppress("DEPRECATION")
            cm.activeNetworkInfo?.isConnected == true
        }
    }
}
