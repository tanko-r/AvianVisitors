package com.avianvisitors.display;

import android.app.*;
import android.content.*;
import android.net.ConnectivityManager;
import android.net.nsd.NsdManager;
import android.net.wifi.WifiManager;
import android.net.Uri;
import android.os.*;
import android.util.Log;

/** Discover exactly this station, then use the provisioned AVNC SSH profile. */
public class DisplayService extends Service {
  private final Handler handler = new Handler(Looper.getMainLooper());
  private ServiceDiscovery discovery;
  private WifiManager.MulticastLock multicast;
  private String lastHost;
  private boolean listening;
  private FrameAudio audio;
  private final BroadcastReceiver network = new BroadcastReceiver() {
    @Override public void onReceive(Context context, Intent intent) {
      if (discovery != null) discovery.onNetworkChanged();
    }
  };
  @Override public int onStartCommand(Intent intent, int flags, int id) {
    if (!getSharedPreferences("display", 0).getBoolean("enabled", false)) {
      stopSelf(); return START_NOT_STICKY;
    }
    if (intent != null && "connect".equals(intent.getAction())) lastHost = null;
    if (discovery == null) {
      Notification.Builder note = new Notification.Builder(this)
          .setContentTitle("Bird display").setContentText("Finding your Raspberry Pi")
          .setSmallIcon(android.R.drawable.ic_menu_view).setOngoing(true)
          .setContentIntent(PendingIntent.getActivity(this, 0,
              new Intent(this, MainActivity.class), PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));
      if (Build.VERSION.SDK_INT >= 26) {
        getSystemService(NotificationManager.class).createNotificationChannel(
            new NotificationChannel("display", "Bird display", NotificationManager.IMPORTANCE_LOW));
        note.setChannelId("display");
      }
      startForeground(11, note.build());
      audio = new FrameAudio();
      audio.start();
      WifiManager wifi = (WifiManager) getApplicationContext().getSystemService(WIFI_SERVICE);
      if (wifi != null) {
        multicast = wifi.createMulticastLock("bird-display-discovery");
        multicast.setReferenceCounted(false); multicast.acquire();
      }
      discovery = new ServiceDiscovery((NsdManager)getSystemService(NSD_SERVICE), handler,
          // Android 6 vendor NSD can omit TXT. Require the exact service name;
          // the independently pinned SSH keys authenticate the actual station.
          "AvianVisitors-Dad-491", null, new ServiceDiscovery.Callback() {
        public void onEndpoint(String endpoint) {
          String host = Uri.parse(endpoint).getHost();
          if (host == null || host.equals(lastHost)) return;
          Uri uri = Uri.parse("vnc://127.0.0.1:5901").buildUpon()
              .appendQueryParameter("ConnectionName", "AvianVisitorsWiFi")
              .appendQueryParameter("ChannelType", "24")
              .appendQueryParameter("SshHost", host)
              .appendQueryParameter("SshPort", "22")
              .appendQueryParameter("SshUsername", "frameview")
              .appendQueryParameter("SaveConnection", "true").build();
          try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri).setPackage("com.gaurav.avnc")
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            lastHost = host;
            Log.i(MainActivity.TAG, "Opening saved SSH display at discovered station");
          } catch (ActivityNotFoundException e) { Log.e(MainActivity.TAG, "Install AVNC first"); }
        }
        public void onSearchStalled() { Log.i(MainActivity.TAG, "Station search will retry"); }
      });
      registerReceiver(network, new IntentFilter(ConnectivityManager.CONNECTIVITY_ACTION));
      listening = true;
      discovery.start();
    } else if (intent != null && "connect".equals(intent.getAction())) discovery.rediscover();
    return START_STICKY;
  }
  @Override public void onDestroy() {
    if (audio != null) audio.close();
    if (listening) unregisterReceiver(network);
    if (discovery != null) discovery.close();
    if (multicast != null && multicast.isHeld()) multicast.release();
    handler.removeCallbacksAndMessages(null);
    super.onDestroy();
  }
  @Override public IBinder onBind(Intent intent) { return null; }
}
