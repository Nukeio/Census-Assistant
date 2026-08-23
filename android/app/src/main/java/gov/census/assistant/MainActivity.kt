package gov.census.assistant

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.net.http.SslError
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.webkit.*
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    // Backend server URL — set to localhost when running local Flask server
    // or to deployed domain (e.g., http://192.168.x.x:8080 for LAN access)
    private val BACKEND_URL = "http://10.0.2.2:8080"  // Android emulator localhost alias
    private val LOCAL_ASSET_URL = "file:///android_asset/index.html"

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (!isGranted) {
            Toast.makeText(this, "Phone permission needed to call support", Toast.LENGTH_SHORT).show()
        }
    }

    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        filePathCallback?.onReceiveValue(if (uri != null) arrayOf(uri) else emptyArray())
        filePathCallback = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Full screen immersive mode with proper status bar
        window.statusBarColor = Color.parseColor("#000666")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.insetsController?.let {
                it.show(android.view.WindowInsets.Type.statusBars())
            }
        }

        setContentView(R.layout.activity_main)

        swipeRefresh = findViewById(R.id.swipe_refresh)
        webView = findViewById(R.id.web_view)

        setupWebView()
        setupSwipeRefresh()

        // Probe backend connectivity, then load app
        checkBackendAndLoad()
    }

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
                // Handle external http links (open in external browser)
                if (!url.contains("10.0.2.2") && !url.startsWith("file://") && url.startsWith("http")) {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    startActivity(intent)
                    return true
                }
                return false
            }

            override fun onReceivedSslError(view: WebView, handler: SslErrorHandler, error: SslError) {
                // Allow self-signed certs in development
                handler.proceed()
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
                    // Fall back to bundled asset
                    if (!view.url!!.startsWith("file://")) {
                        webView.loadUrl(LOCAL_ASSET_URL)
                    }
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            // Handle file upload from web page
            override fun onShowFileChooser(
                webView: WebView,
                filePathCallback: ValueCallback<Array<Uri>>,
                fileChooserParams: FileChooserParams
            ): Boolean {
                this@MainActivity.filePathCallback = filePathCallback
                fileChooserLauncher.launch("*/*")
                return true
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
                val url = URL("$BACKEND_URL/api/admin/stats")
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

    private fun handlePhoneCall(telUrl: String) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE)
            == PackageManager.PERMISSION_GRANTED
        ) {
            val intent = Intent(Intent.ACTION_CALL, Uri.parse(telUrl))
            startActivity(intent)
        } else {
            // Request permission, then show dial intent
            requestPermissionLauncher.launch(Manifest.permission.CALL_PHONE)
            // Fallback: show dial pad
            val intent = Intent(Intent.ACTION_DIAL, Uri.parse(telUrl))
            startActivity(intent)
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            // Show exit confirmation
            AlertDialog.Builder(this)
                .setTitle("Exit Census Assistant")
                .setMessage("Are you sure you want to exit?")
                .setPositiveButton("Exit") { _, _ -> super.onBackPressed() }
                .setNegativeButton("Stay", null)
                .show()
        }
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
    }

    override fun onPause() {
        super.onPause()
        webView.onPause()
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}
