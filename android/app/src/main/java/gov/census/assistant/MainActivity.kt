package gov.census.assistant

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.net.http.SslError
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.provider.Settings
import android.view.View
import android.webkit.*
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import java.io.File
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout

    // Callback supplied by the WebView when the user taps a file/photo input.
    // Must be fulfilled (even with an empty array) or the WebView input hangs.
    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    // Temporary URI for camera captures (ACTION_IMAGE_CAPTURE writes here).
    private var cameraPhotoUri: Uri? = null

    // Backend server URL — a permanent cloud address, not tied to any PC/LAN.
    private val BACKEND_URL = "https://shahinxsha.pythonanywhere.com"
    private val LOCAL_ASSET_URL = "file:///android_asset/index.html"

    // ─────────────────────────────────────────────
    // Activity Result Launchers
    // ─────────────────────────────────────────────



    /**
     * Multi-permission launcher for CAMERA + LOCATION.
     * Called proactively on first launch and re-checked on resume.
     */
    private val fieldPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        val locationGranted = results[Manifest.permission.ACCESS_FINE_LOCATION] == true
                || results[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        val cameraGranted = results[Manifest.permission.CAMERA] == true

        if (!locationGranted) {
            // Check if permanently denied (user ticked "Don't ask again")
            val permanentlyDenied = !shouldShowRequestPermissionRationale(
                Manifest.permission.ACCESS_FINE_LOCATION
            )
            if (permanentlyDenied) {
                showPermanentlyDeniedDialog(
                    "Location Access Required",
                    "Location permission has been permanently denied.\n\n" +
                    "The Attendance feature needs your GPS coordinates to verify field presence.\n\n" +
                    "Please enable it in Settings → Apps → Census Assistant → Permissions → Location."
                )
            }
        }

        if (!cameraGranted) {
            val permanentlyDenied = !shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)
            if (permanentlyDenied) {
                showPermanentlyDeniedDialog(
                    "Camera Access Required",
                    "Camera permission has been permanently denied.\n\n" +
                    "The Attendance feature needs your camera to take the required daily photo.\n\n" +
                    "Please enable it in Settings → Apps → Census Assistant → Permissions → Camera."
                )
            }
        }
    }

    // READ_MEDIA_IMAGES (Android 13+) or READ_EXTERNAL_STORAGE (Android ≤12)
    // for gallery access — only requested when the user taps "Choose from Gallery".
    private val storagePermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            launchGalleryPicker()
        } else {
            val perm = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU)
                Manifest.permission.READ_MEDIA_IMAGES else Manifest.permission.READ_EXTERNAL_STORAGE
            val permanentlyDenied = !shouldShowRequestPermissionRationale(perm)
            if (permanentlyDenied) {
                showPermanentlyDeniedDialog(
                    "Gallery Access Required",
                    "Storage/Gallery permission has been permanently denied.\n\n" +
                    "Please enable it in Settings → Apps → Census Assistant → Permissions."
                )
            } else {
                Toast.makeText(this, "Gallery permission denied. Use camera or file picker instead.", Toast.LENGTH_LONG).show()
            }
            // Cancel the pending WebView file callback so it doesn't hang
            filePathCallback?.onReceiveValue(emptyArray())
            filePathCallback = null
        }
    }

    /**
     * Camera: launches the device's camera app via ACTION_IMAGE_CAPTURE.
     * The photo is written to a temp file under the app's cache and returned
     * as a content:// URI via FileProvider.
     */
    private val cameraLauncher = registerForActivityResult(
        ActivityResultContracts.TakePicture()
    ) { success ->
        val uri = cameraPhotoUri
        if (success && uri != null) {
            filePathCallback?.onReceiveValue(arrayOf(uri))
        } else {
            // User cancelled or capture failed — must still resolve the callback
            filePathCallback?.onReceiveValue(emptyArray())
        }
        filePathCallback = null
        cameraPhotoUri = null
    }

    /**
     * Gallery / Photo Picker: uses PickVisualMedia on Android 13+ which does
     * NOT require any storage permission. Falls back to GetContent on older
     * versions (which needs READ_EXTERNAL_STORAGE, handled by storagePermissionLauncher).
     */
    private val galleryPickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        filePathCallback?.onReceiveValue(if (uri != null) arrayOf(uri) else emptyArray())
        filePathCallback = null
    }

    /**
     * File Picker: Storage Access Framework — works with content:// URIs from
     * any document provider (Google Drive, Downloads, etc.) without needing
     * broad storage permission.
     */
    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        filePathCallback?.onReceiveValue(if (uri != null) arrayOf(uri) else emptyArray())
        filePathCallback = null
    }

    // ─────────────────────────────────────────────
    // Lifecycle
    // ─────────────────────────────────────────────

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(R.layout.activity_main)

        // Full screen immersive mode with proper status bar. This MUST come
        // after setContentView() — window.insetsController needs a decor view
        // to exist, and on some OEM skins (confirmed on ColorOS/Oppo) calling
        // it earlier throws a NullPointerException that crashes the app on
        // every single launch, before the WebView ever gets a chance to load.
        window.statusBarColor = Color.parseColor("#000666")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.insetsController?.let {
                it.show(android.view.WindowInsets.Type.statusBars())
            }
        }

        swipeRefresh = findViewById(R.id.swipe_refresh)
        webView = findViewById(R.id.web_view)

        setupWebView()
        setupSwipeRefresh()

        // Proactively request CAMERA + LOCATION so the Attendance tab works
        // without an extra prompt the first time the user opens it.
        requestFieldPermissions()

        // Probe backend connectivity, then load app
        checkBackendAndLoad()
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
        // Re-evaluate permissions after the user may have returned from Settings.
        // No UI dialog here — just a silent re-request if still missing.
        requestFieldPermissionsIfNeeded()
    }

    override fun onPause() {
        super.onPause()
        webView.onPause()
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }

    // ─────────────────────────────────────────────
    // Permission helpers
    // ─────────────────────────────────────────────

    private fun hasPermission(perm: String): Boolean =
        ContextCompat.checkSelfPermission(this, perm) == PackageManager.PERMISSION_GRANTED

    /**
     * Called on first launch via onCreate(). Shows a rationale dialog if
     * needed before asking the OS for CAMERA + LOCATION together, so the user
     * understands WHY these are required (required by Google Play and good UX).
     */
    private fun requestFieldPermissions() {
        val needsCamera = !hasPermission(Manifest.permission.CAMERA)
        val needsLocation = !hasPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                && !hasPermission(Manifest.permission.ACCESS_COARSE_LOCATION)

        if (!needsCamera && !needsLocation) return   // All already granted

        val needsRationale = (needsCamera && shouldShowRequestPermissionRationale(Manifest.permission.CAMERA))
                || (needsLocation && shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_FINE_LOCATION))

        if (needsRationale) {
            AlertDialog.Builder(this)
                .setTitle("Permissions Required for Attendance")
                .setMessage(
                    "The Attendance feature requires:\n\n" +
                    "• Camera — to take your daily attendance photo\n" +
                    "• Location — to record your GPS coordinates for field verification\n\n" +
                    "These are only used when you mark attendance. No data is collected otherwise."
                )
                .setPositiveButton("Grant Permissions") { _, _ -> launchFieldPermissionRequest() }
                .setNegativeButton("Not Now", null)
                .show()
        } else {
            launchFieldPermissionRequest()
        }
    }

    /** Silent re-request on resume (no rationale dialog — user already saw it). */
    private fun requestFieldPermissionsIfNeeded() {
        val needed = buildList {
            if (!hasPermission(Manifest.permission.CAMERA)) add(Manifest.permission.CAMERA)
            if (!hasPermission(Manifest.permission.ACCESS_FINE_LOCATION)) add(Manifest.permission.ACCESS_FINE_LOCATION)
            if (!hasPermission(Manifest.permission.ACCESS_COARSE_LOCATION)) add(Manifest.permission.ACCESS_COARSE_LOCATION)
        }
        if (needed.isNotEmpty()) {
            // Only re-request if not permanently denied (we don't want to spam
            // the system dialog uselessly — it would be silently dropped by Android).
            val canAsk = needed.any { shouldShowRequestPermissionRationale(it) }
            if (canAsk) fieldPermissionLauncher.launch(needed.toTypedArray())
        }
    }

    private fun launchFieldPermissionRequest() {
        val needed = buildList {
            if (!hasPermission(Manifest.permission.CAMERA)) add(Manifest.permission.CAMERA)
            if (!hasPermission(Manifest.permission.ACCESS_FINE_LOCATION)) add(Manifest.permission.ACCESS_FINE_LOCATION)
            if (!hasPermission(Manifest.permission.ACCESS_COARSE_LOCATION)) add(Manifest.permission.ACCESS_COARSE_LOCATION)
        }
        if (needed.isNotEmpty()) {
            fieldPermissionLauncher.launch(needed.toTypedArray())
        }
    }

    private fun showPermanentlyDeniedDialog(title: String, message: String) {
        AlertDialog.Builder(this)
            .setTitle(title)
            .setMessage(message)
            .setPositiveButton("Open Settings") { _, _ ->
                val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                    data = Uri.fromParts("package", packageName, null)
                }
                startActivity(intent)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    // ─────────────────────────────────────────────
    // Photo / File chooser
    // ─────────────────────────────────────────────

    /**
     * Show a bottom-sheet style dialog offering the user a clear choice:
     *   • Take Photo     — opens the device camera app
     *   • Choose from Gallery — modern photo picker (no storage permission needed on Android 13+)
     *   • Choose from Files  — SAF file picker for any document provider
     *
     * If the user dismisses without choosing, the WebView callback is cancelled
     * so the input element doesn't get stuck in a waiting state.
     */
    private fun showPhotoSourceChooser() {
        val options = arrayOf(
            "📷  Take Photo",
            "🖼️  Choose from Gallery / Photos",
            "📁  Choose from Files"
        )
        AlertDialog.Builder(this)
            .setTitle("Select Photo Source")
            .setItems(options) { _, which ->
                when (which) {
                    0 -> launchCamera()
                    1 -> requestGalleryAndPick()
                    2 -> launchFilePicker()
                }
            }
            .setOnCancelListener {
                // User pressed Back — must cancel the callback or the WebView hangs
                filePathCallback?.onReceiveValue(emptyArray())
                filePathCallback = null
            }
            .show()
    }

    /**
     * Launch the device camera app to capture a new photo.
     * A temporary file is created under the app's cache directory; the
     * FileProvider exposes it as a content:// URI to the camera app.
     */
    private fun launchCamera() {
        if (!hasPermission(Manifest.permission.CAMERA)) {
            Toast.makeText(this,
                "Camera permission is required. Please grant it when prompted.",
                Toast.LENGTH_LONG).show()
            requestFieldPermissions()
            filePathCallback?.onReceiveValue(emptyArray())
            filePathCallback = null
            return
        }

        val photoFile = try {
            createTempImageFile()
        } catch (ex: IOException) {
            Toast.makeText(this, "Could not create photo file. Please try again.", Toast.LENGTH_SHORT).show()
            filePathCallback?.onReceiveValue(emptyArray())
            filePathCallback = null
            return
        }

        val uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", photoFile)
        cameraPhotoUri = uri
        cameraLauncher.launch(uri)
    }

    /** Create a uniquely-named JPEG in the app cache (not on shared storage). */
    @Throws(IOException::class)
    private fun createTempImageFile(): File {
        val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val storageDir = cacheDir    // internal cache — no storage permission needed
        return File.createTempFile("attendance_${timeStamp}_", ".jpg", storageDir)
    }

    /**
     * On Android 13+ (API 33), launch the system Photo Picker directly — it
     * never requires READ_MEDIA_IMAGES. On older Android, check/request
     * READ_EXTERNAL_STORAGE before opening a gallery intent.
     */
    private fun requestGalleryAndPick() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            // Android 13+: Photo Picker — no permission required
            launchGalleryPicker()
        } else {
            // Android ≤12: need READ_EXTERNAL_STORAGE for gallery
            if (hasPermission(Manifest.permission.READ_EXTERNAL_STORAGE)) {
                launchGalleryPicker()
            } else {
                storagePermissionLauncher.launch(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
        }
    }

    private fun launchGalleryPicker() {
        // GetContent("image/*") covers all Android versions and document providers,
        // including Google Photos, Samsung Gallery, and others.
        galleryPickerLauncher.launch("image/*")
    }

    private fun launchFilePicker() {
        // OpenDocument with image MIME types — SAF covers Google Drive, Downloads,
        // local storage, and any other registered document provider.
        filePickerLauncher.launch(arrayOf("image/*"))
    }

    // ─────────────────────────────────────────────
    // WebView setup
    // ─────────────────────────────────────────────

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            loadsImagesAutomatically = true
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            setSupportZoom(false)
            builtInZoomControls = false
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
            javaScriptCanOpenWindowsAutomatically = true
            mediaPlaybackRequiresUserGesture = false
            // Required for navigator.geolocation to work inside the WebView.
            // This is a WebView-level toggle; the Android OS location permission
            // is handled separately via onGeolocationPermissionsShowPrompt().
            setGeolocationEnabled(true)
            // Enable modern web features
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                forceDark = WebSettings.FORCE_DARK_OFF
            }
        }

        // Add native Android bridge
        webView.addJavascriptInterface(WebAppInterface(this), "AndroidBridge")

        // Enable WebView debugging in debug builds
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                // Handle tel: links — open native phone dialer
                if (url.startsWith("tel:")) {
                    handlePhoneCall(url)
                    return true
                }
                // Handle mailto: links
                if (url.startsWith("mailto:")) {
                    val intent = Intent(Intent.ACTION_SENDTO, Uri.parse(url))
                    startActivity(Intent.createChooser(intent, "Send Email"))
                    return true
                }
                // Handle external http links. Links to our own backend or bundled
                // assets stay inside the WebView; only genuinely external links open
                // in the system browser.
                val backendHost = Uri.parse(BACKEND_URL).host
                if (!url.contains(backendHost ?: "\u0000") && !url.startsWith("file://") && url.startsWith("http")) {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    startActivity(intent)
                    return true
                }
                return false
            }

            override fun onReceivedSslError(view: WebView, handler: SslErrorHandler, error: SslError) {
                // BACKEND_URL is a real HTTPS host with a trusted certificate —
                // reject invalid certs instead of blindly bypassing SSL checks.
                handler.cancel()
            }

            override fun onPageFinished(view: WebView, url: String) {
                swipeRefresh.isRefreshing = false
                // Inject Android context info into the web app
                view.evaluateJavascript(
                    "window.ANDROID_MODE = true; " +
                    "window.BACKEND_URL = '$BACKEND_URL'; " +
                    "window.dispatchEvent(new Event('androidready'));",
                    null
                )
            }

            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                if (request.isForMainFrame) {
                    swipeRefresh.isRefreshing = false
                    // view.url can be null on the very first navigation of a fresh WebView
                    // (e.g. when the initial load itself is the one that fails) — a plain
                    // "!!" here throws an NPE and crashes the whole app on launch. Guard
                    // with a safe call instead.
                    val currentUrl = view.url
                    if (currentUrl == null || !currentUrl.startsWith("file://")) {
                        webView.loadUrl(LOCAL_ASSET_URL)
                    }
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {

            /**
             * Handle file/image input from the web page.
             *
             * On Android the WebView calls this when the user taps an
             * `<input type="file">` or `<input type="file" capture>` element.
             * We show our own chooser dialog so the user can pick between
             * Camera, Gallery, or Files — matching the request in the spec.
             */
            override fun onShowFileChooser(
                webView: WebView,
                filePathCallback: ValueCallback<Array<Uri>>,
                fileChooserParams: FileChooserParams
            ): Boolean {
                // Cancel any pending callback first to avoid leaking it
                this@MainActivity.filePathCallback?.onReceiveValue(emptyArray())
                this@MainActivity.filePathCallback = filePathCallback

                showPhotoSourceChooser()
                return true
            }

            /**
             * Required for navigator.geolocation to work inside the WebView.
             *
             * The WebView has its own geolocation sandbox that is separate from
             * the OS location permission: even if ACCESS_FINE_LOCATION is
             * granted to the app, the WebView will call this callback before
             * forwarding any geolocation request to JavaScript. If this method
             * is not overridden, the callback is never invoked and
             * navigator.geolocation always fails silently with "permission denied".
             */
            override fun onGeolocationPermissionsShowPrompt(
                origin: String?,
                callback: GeolocationPermissions.Callback?
            ) {
                val hasFineLoc = hasPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                val hasCoarseLoc = hasPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                val locationGranted = hasFineLoc || hasCoarseLoc

                if (!locationGranted) {
                    // OS permission not yet granted — request it, then invoke
                    // the callback immediately with false (the next time the
                    // user taps "Capture", the OS permission will already be
                    // granted and this path grants it through).
                    AlertDialog.Builder(this@MainActivity)
                        .setTitle("Location Permission Required")
                        .setMessage(
                            "The Attendance feature needs your GPS location to verify " +
                            "that you are in the field.\n\nPlease allow location access " +
                            "when prompted by Android."
                        )
                        .setPositiveButton("Continue") { _, _ ->
                            launchFieldPermissionRequest()
                            // Deny for now — user must tap "Capture" again after granting
                            callback?.invoke(origin, false, false)
                        }
                        .setNegativeButton("Cancel") { _, _ ->
                            callback?.invoke(origin, false, false)
                        }
                        .show()
                } else {
                    // OS permission is granted — tell the WebView to proceed.
                    // retain=true means the WebView remembers this origin so
                    // the user is not re-prompted on every submission.
                    callback?.invoke(origin, true, true)
                }
            }

            /**
             * Grant camera access for WebRTC / getUserMedia requests from the
             * web page (e.g. if the web frontend ever uses a live camera stream).
             */
            override fun onPermissionRequest(request: PermissionRequest?) {
                runOnUiThread {
                    val wantsCamera = request?.resources?.contains(
                        PermissionRequest.RESOURCE_VIDEO_CAPTURE
                    ) == true

                    if (wantsCamera && hasPermission(Manifest.permission.CAMERA)) {
                        request?.grant(request.resources)
                    } else if (wantsCamera) {
                        // Camera not yet granted — request it and deny this
                        // particular WebRTC request; user can retry after granting.
                        requestFieldPermissions()
                        request?.deny()
                    } else {
                        request?.deny()
                    }
                }
            }

            override fun onJsAlert(view: WebView, url: String, message: String, result: JsResult): Boolean {
                AlertDialog.Builder(this@MainActivity)
                    .setMessage(message)
                    .setPositiveButton("OK") { _, _ -> result.confirm() }
                    .setCancelable(false)
                    .show()
                return true
            }
        }
    }

    // ─────────────────────────────────────────────
    // Refresh / connectivity
    // ─────────────────────────────────────────────

    private fun setupSwipeRefresh() {
        swipeRefresh.setColorSchemeColors(
            Color.parseColor("#000666"),
            Color.parseColor("#1a237e"),
            Color.parseColor("#4c56af")
        )
        swipeRefresh.setOnRefreshListener {
            webView.reload()
        }
    }

    private fun checkBackendAndLoad() {
        swipeRefresh.isRefreshing = true
        thread {
            val backendAvailable = try {
                // A public, unauthenticated liveness endpoint — /api/admin/stats
                // used to be probed here, but it now requires admin auth (the
                // portal is locked to Technical Assistants only), so every
                // non-admin launch was failing this check and silently falling
                // back to the stale bundled offline copy instead of the live site.
                val url = URL("$BACKEND_URL/api/health")
                val conn = url.openConnection() as HttpURLConnection
                conn.connectTimeout = 3000
                conn.readTimeout = 3000
                conn.responseCode == 200
            } catch (e: Exception) {
                false
            }

            runOnUiThread {
                if (backendAvailable) {
                    // Connected mode: load from live backend
                    webView.loadUrl(BACKEND_URL)
                } else {
                    // Offline mode: load bundled Stitch UI assets
                    webView.loadUrl(LOCAL_ASSET_URL)
                }
            }
        }
    }

    // ─────────────────────────────────────────────
    // Phone call helper
    // ─────────────────────────────────────────────

    private fun handlePhoneCall(telUrl: String) {
        try {
            val intent = Intent(Intent.ACTION_DIAL, Uri.parse(telUrl))
            startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(this, "Unable to open phone dialer", Toast.LENGTH_SHORT).show()
        }
    }

    // ─────────────────────────────────────────────
    // Back press
    // ─────────────────────────────────────────────

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            // Show exit confirmation
            AlertDialog.Builder(this)
                .setTitle("Exit Census Assistant")
                .setMessage("Are you sure you want to exit?")
                .setPositiveButton("Exit") { _, _ -> @Suppress("DEPRECATION") super.onBackPressed() }
                .setNegativeButton("Stay", null)
                .show()
        }
    }
}
