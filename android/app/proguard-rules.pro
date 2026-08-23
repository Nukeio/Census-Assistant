# Add project specific ProGuard rules here.

# Keep WebAppInterface methods accessible from JavaScript
-keepclassmembers class gov.census.assistant.WebAppInterface {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep Kotlin coroutines
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keepnames class okhttp3.internal.publicsuffix.PublicSuffixDatabase

# Gson
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class com.google.gson.stream.** { *; }

# General
-keepattributes SourceFile,LineNumberTable
