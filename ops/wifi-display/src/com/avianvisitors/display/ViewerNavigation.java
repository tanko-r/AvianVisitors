package com.avianvisitors.display;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.SystemClock;
import android.view.*;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityWindowInfo;
import android.widget.Button;

/** Native recovery Menu and an Android 6 keyboard workaround scoped to AVNC. */
public class ViewerNavigation extends AccessibilityService {
  private WindowManager windows;
  private Button menu;
  private boolean attached;
  private final Handler handler = new Handler();
  private long lastDismiss;
  private int viewerWindow = -1;
  private final Runnable check = new Runnable() {
    public void run() { refresh(); handler.postDelayed(this, 1000); }
  };
  @Override protected void onServiceConnected() {
    windows = (WindowManager)getSystemService(WINDOW_SERVICE);
    menu = new Button(this); menu.setText("Menu"); menu.setAlpha(0.75f);
    menu.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)));
    handler.post(check);
  }
  @Override public void onAccessibilityEvent(AccessibilityEvent event) {
    if (event.getPackageName() != null && "com.gaurav.avnc".contentEquals(event.getPackageName()))
      viewerWindow = event.getWindowId();
    refresh();
  }
  private void refresh() {
    if (menu == null) return;
    boolean viewer = false, imeVisible = false;
    for (AccessibilityWindowInfo window : getWindows()) {
      if (window.getType() == AccessibilityWindowInfo.TYPE_INPUT_METHOD) imeVisible = true;
      if (window.getType() == AccessibilityWindowInfo.TYPE_APPLICATION && window.isFocused()) {
        viewer = viewerWindow >= 0 && window.getId() == viewerWindow;
      }
    }
    if (viewer && !attached) {
      WindowManager.LayoutParams p = new WindowManager.LayoutParams(100, 58,
          WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
          WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE, PixelFormat.TRANSLUCENT);
      p.gravity = Gravity.BOTTOM | Gravity.LEFT;
      windows.addView(menu, p); attached = true;
    } else if (!viewer && attached) { windows.removeView(menu); attached = false; }
    // The vendor can return null accessibility roots for the VNC surface.
    // Match the focused application to AVNC's own window-event ID instead.
    // Debouncing also prevents duplicate window events from closing the viewer.
    if (viewer && imeVisible && SystemClock.uptimeMillis() - lastDismiss > 2000 &&
        getSharedPreferences("display", 0).getBoolean("enabled", false)) {
      lastDismiss = SystemClock.uptimeMillis();
      boolean sent = performGlobalAction(GLOBAL_ACTION_BACK);
      android.util.Log.i(MainActivity.TAG, "Dismiss visible viewer keyboard: " + sent);
    }
  }
  @Override public void onInterrupt() {}
  @Override public void onDestroy() {
    handler.removeCallbacksAndMessages(null);
    if (attached) windows.removeView(menu);
    super.onDestroy();
  }
}
