# KTVibes Android TV client

A small WebView-based TV client. KTVibes still runs on a computer on the same network and does all song preparation. This is an initial version: playback, D-pad navigation and synchronization need testing on the TV.

## Build with GitHub Actions

The **Android TV APK** workflow builds on relevant pushes and pull requests, and can also be started from the Actions tab using **Run workflow**. Download `ktvibes-android-tv-debug` from the completed run's artifacts and extract the APK. Artifacts expire after 14 days. No signing secrets or private server addresses are needed. A debug APK is signed with an ephemeral debug key on the build runner, so a later build may require uninstalling an earlier build before installation, which also removes its saved address.

## Build on Windows

Install Android Studio, including the Android SDK, SDK Platform 35 and Android SDK Build-Tools. Android Gradle Plugin 8.7.3 needs JDK 17; Android Studio's bundled JDK works. Open the `android-tv` folder as a project, let Gradle sync and download its dependencies, then choose **Build > Build Bundle(s) / APK(s) > Build APK(s)**. The debug APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

Alternatively, with JDK 17, SDK Platform 35, build tools, and Gradle 8.9 installed, set `ANDROID_HOME` to the SDK directory and run `gradle :app:assembleDebug` in this folder. The project deliberately does not include a Gradle wrapper; Gradle and the Android plugin download dependencies from their configured repositories.

## Install and use

1. Start KTVibes on the computer. Find the computer's LAN IP address; `localhost` on the TV refers to the TV, not the computer. Make sure the Windows firewall allows the server's port (8765 by default) on your private network.
2. With the TV connected and authorized in ADB, install the APK: `adb install -r app/build/outputs/apk/debug/app-debug.apk`. Launch **KTVibes** from the TV apps screen.
3. Enter `http://<computer-ip>:8765` and select **Connect**. Select **Enable sound** on the TV page if prompted. The phone remote works as usual.
4. Press the TV remote's **Back** button to return to the server address and reconnect or change it.

HTTP is enabled because the existing local KTVibes server uses it. Traffic is unencrypted; use a trusted network. The app stores the address locally and blocks top-level navigation away from the configured origin, but the server and its page must still be trusted. No JavaScript-to-Android bridge is exposed.

This is a debug build, not a signed release. Video/audio codec support, WebView playback and remote-control focus vary by device; a production release needs additional testing.
