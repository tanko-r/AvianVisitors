package com.avianvisitors.display;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Native recovery controls; Home HQ remains the Android Home application. */
public class MainActivity extends Activity {
  static final String TAG = "BirdDisplay";
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    LinearLayout layout = new LinearLayout(this);
    layout.setOrientation(LinearLayout.VERTICAL);
    layout.setPadding(48, 32, 48, 32);
    TextView title = new TextView(this);
    title.setText("Bird display\nThe Raspberry Pi runs the page. This frame displays it over Wi-Fi.");
    title.setTextSize(24);
    layout.addView(title);
    button(layout, "Open bird display", v -> {
      getSharedPreferences("display", 0).edit().putBoolean("enabled", true).apply();
      startService(new Intent(this, DisplayService.class).setAction("connect"));
    });
    button(layout, "Android Settings (pause display)", v -> {
      pause(); startActivity(new Intent(Settings.ACTION_SETTINGS));
    });
    button(layout, "Home HQ (pause display)", v -> {
      pause();
      Intent home = getPackageManager().getLaunchIntentForPackage("com.wesbos.homehq");
      if (home != null) startActivity(home);
    });
    setContentView(layout);
    autostart();
  }
  @Override protected void onNewIntent(Intent intent) {
    super.onNewIntent(intent);
    setIntent(intent);
    autostart();
  }
  private void autostart() {
    if (getIntent().getBooleanExtra("autostart", false) &&
        getSharedPreferences("display", 0).getBoolean("enabled", false)) {
      android.util.Log.i(TAG, "Starting saved display after boot request");
      startService(new Intent(this, DisplayService.class));
      finish();
    }
  }
  private void button(LinearLayout parent, String text, View.OnClickListener click) {
    Button button = new Button(this); button.setText(text); button.setOnClickListener(click);
    parent.addView(button, new LinearLayout.LayoutParams(-1, 80));
  }
  private void pause() {
    getSharedPreferences("display", 0).edit().putBoolean("enabled", false).apply();
    stopService(new Intent(this, DisplayService.class));
  }
}
