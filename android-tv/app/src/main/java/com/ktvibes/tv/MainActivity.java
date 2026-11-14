package com.ktvibes.tv;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.InputMethodManager;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.net.URI;
import java.util.Locale;

public class MainActivity extends Activity {
    private static final String PREFS = "server";
    private static final String ADDRESS = "address";
    private WebView webView;
    private String server;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        server = getSharedPreferences(PREFS, MODE_PRIVATE).getString(ADDRESS, "");
        if (server.isEmpty()) showSettings(null); else openServer();
    }

    private void showSettings(String message) {
        disposeWebView();
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(80, 30, 80, 30);
        layout.setBackgroundColor(Color.rgb(20, 16, 38));
        TextView title = new TextView(this);
        title.setText("KTVibes on your TV");
        title.setTextColor(Color.WHITE);
        title.setTextSize(28);
        layout.addView(title);
        TextView help = new TextView(this);
        help.setText(message == null ? "Enter your KTVibes server address, for example http://192.168.1.100:8765" : message);
        help.setTextColor(Color.WHITE);
        help.setTextSize(18);
        help.setPadding(0, 20, 0, 12);
        layout.addView(help);
        EditText address = new EditText(this);
        address.setSingleLine(true);
        address.setTextColor(Color.WHITE);
        address.setHintTextColor(Color.LTGRAY);
        address.setHint("http://192.168.1.100:8765");
        address.setText(server);
        address.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        layout.addView(address, new LinearLayout.LayoutParams(-1, -2));
        Button connect = new Button(this);
        connect.setText("Connect");
        layout.addView(connect);
        connect.setOnClickListener(v -> {
            String normalized = normalizeAddress(address.getText().toString());
            if (normalized == null) {
                address.setError("Enter an HTTP(S) server address, optionally with a port");
                address.requestFocus();
                return;
            }
            server = normalized;
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(ADDRESS, server).apply();
            ((InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(address.getWindowToken(), 0);
            openServer();
        });
        setContentView(layout);
        if (server.isEmpty()) address.requestFocus(); else connect.requestFocus();
    }

    private String normalizeAddress(String input) {
        String value = input.trim();
        if (!value.contains("://")) value = "http://" + value;
        try {
            URI uri = new URI(value);
            String scheme = uri.getScheme().toLowerCase(Locale.ROOT);
            if ((!scheme.equals("http") && !scheme.equals("https")) || uri.getHost() == null
                    || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null
                    || (uri.getPath() != null && !uri.getPath().isEmpty() && !uri.getPath().equals("/"))
                    || uri.getPort() > 65535 || uri.getPort() == 0) return null;
            return new URI(scheme, null, uri.getHost(), uri.getPort(), null, null, null).toString();
        } catch (Exception ignored) { return null; }
    }

    private boolean sameOrigin(Uri uri) {
        Uri base = Uri.parse(server);
        int basePort = base.getPort() == -1 ? ("https".equals(base.getScheme()) ? 443 : 80) : base.getPort();
        int port = uri.getPort() == -1 ? ("https".equals(uri.getScheme()) ? 443 : 80) : uri.getPort();
        return base.getScheme().equalsIgnoreCase(uri.getScheme()) && base.getHost() != null
                && base.getHost().equalsIgnoreCase(uri.getHost()) && basePort == port;
    }

    private void openServer() {
        disposeWebView();
        webView = new WebView(this);
        webView.setBackgroundColor(Color.BLACK);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        webView.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !sameOrigin(request.getUrl());
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showSettings("Could not reach the server. Check KTVibes, Wi-Fi and the address, then try again.");
                }
            }
        });
        setContentView(webView);
        webView.requestFocus();
        webView.loadUrl(server + "/");
    }

    private void disposeWebView() {
        if (webView != null) {
            webView.stopLoading();
            if (webView.getParent() instanceof ViewGroup) {
                ((ViewGroup) webView.getParent()).removeView(webView);
            }
            webView.destroy();
            webView = null;
        }
    }

    @Override public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView != null) {
            showSettings("Change the server address or select Connect to reload.");
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override protected void onDestroy() {
        disposeWebView();
        super.onDestroy();
    }
}
