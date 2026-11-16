package com.avianvisitors.display;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
public class BootReceiver extends BroadcastReceiver {
  @Override public void onReceive(Context c, Intent intent) {
    if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction()) &&
        c.getSharedPreferences("display", 0).getBoolean("enabled", false))
      c.startService(new Intent(c, DisplayService.class));
  }
}
