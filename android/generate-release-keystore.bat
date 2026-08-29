@echo off
REM ============================================================================
REM Script to generate a secure production release keystore for Census Assistant
REM Uses standard Java keytool with RSA 4096-bit key and 25-year validity.
REM ============================================================================

set KEYSTORE_FILE=release.keystore
set KEY_ALIAS=census_release
set VALIDITY_DAYS=10000

echo Generating release keystore: %KEYSTORE_FILE% ...
keytool -genkeypair -v ^
  -keystore %KEYSTORE_FILE% ^
  -alias %KEY_ALIAS% ^
  -keyalg RSA ^
  -keysize 4096 ^
  -validity %VALIDITY_DAYS% ^
  -storepass census2027 ^
  -keypass census2027 ^
  -dname "CN=Census Assistant, OU=Census Operations, O=Census Assistant, L=Lakhipur, ST=Assam, C=IN"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Keystore generated successfully: %KEYSTORE_FILE%
    echo Keystore password: census2027
    echo Key alias: %KEY_ALIAS%
    echo Key password: census2027
    echo.
    echo NOTE: Keep this file private and NEVER commit it to GitHub.
    echo .gitignore is already configured to ignore *.keystore files.
) else (
    echo Error generating keystore. Ensure keytool (JDK) is on your PATH.
)
