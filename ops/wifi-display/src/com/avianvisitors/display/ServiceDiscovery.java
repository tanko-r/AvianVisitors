package com.avianvisitors.display;

import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.os.Handler;
import android.util.Log;
import java.net.Inet4Address;
import java.net.Inet6Address;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Opt-in DNS-SD lookup of one named _http._tcp. service, for networks where the dashboard host's
 * address can't be fixed. Android 6's WebView can't resolve .local names, so this uses NsdManager
 * (API 16) and gives the kiosk a plain http://address/ URL.
 *
 * Only the configured service instance name is accepted (never "any web server"), and the URL is
 * always the root path of the resolved host and port; a TXT "path" is ignored. An optional station
 * id, if configured, must also match the TXT "station_id".
 *
 * Everything here runs on the main thread: NsdManager calls back on its own thread, so each
 * callback is posted to the handler and dropped if its generation is stale. Android 6 allows one
 * resolve at a time (FAILURE_ALREADY_ACTIVE otherwise), so resolves are queued and serialised.
 * Failures retry with a bounded exponential backoff; nothing loops without a delay.
 */
final class ServiceDiscovery {
  interface Callback {
    /** A valid endpoint was resolved (also called again when a re-check finds the same one). */
    void onEndpoint(String url);

    /** A search attempt ended without an endpoint; the next one is already scheduled. */
    void onSearchStalled();
  }

  static final String TYPE = "_http._tcp.";
  static final String TAG = MainActivity.TAG;
  static final long BACKOFF_MIN_MS = 2000;
  static final long BACKOFF_MAX_MS = 60000;
  static final long SEARCH_TIMEOUT_MS = 15000;
  static final long RESOLVE_TIMEOUT_MS = 10000;
  static final long RECHECK_MS = 5 * 60 * 1000;
  static final long NETWORK_SETTLE_MS = 2000;
  static final int MAX_RESOLVE_FAILURES = 4;

  private static final Pattern NAME = Pattern.compile("[A-Za-z0-9][A-Za-z0-9._ -]{0,62}");
  private static final Pattern STATION = Pattern.compile("[A-Za-z0-9][A-Za-z0-9._-]{0,63}");

  // ---- Pure helpers (no Android state), covered by test-discovery.py ----

  /** The instance name if it is a plain DNS-SD label we accept, else null. */
  static String normalizeName(String raw) {
    if (raw == null || raw.endsWith(" ") || !NAME.matcher(raw).matches()) return null;
    return raw;
  }

  static String normalizeStation(String raw) {
    return raw != null && STATION.matcher(raw).matches() ? raw : null;
  }

  /** NSD reports "_http._tcp." on some builds and "_http._tcp" or ".._http._tcp." on others. */
  static boolean isHttpType(String type) {
    if (type == null) return false;
    String t = type;
    while (t.startsWith(".")) t = t.substring(1);
    while (t.endsWith(".")) t = t.substring(0, t.length() - 1);
    return t.equalsIgnoreCase("_http._tcp");
  }

  /**
   * DNS names are case-insensitive. Avahi renames a colliding instance to "name #2"; that variant
   * is only accepted when a station id is configured, because the TXT station_id is then checked.
   */
  static boolean nameMatches(String found, String wanted, boolean stationChecked) {
    if (found == null || wanted == null) return false;
    if (found.equalsIgnoreCase(wanted)) return true;
    if (!stationChecked || found.length() <= wanted.length() + 2) return false;
    if (!found.regionMatches(true, 0, wanted, 0, wanted.length())) return false;
    if (!found.startsWith(" #", wanted.length())) return false;
    for (int i = wanted.length() + 2; i < found.length(); i++) {
      if (found.charAt(i) < '0' || found.charAt(i) > '9') return false;
    }
    return true;
  }

  static boolean stationMatches(Map<String, byte[]> attrs, String station) {
    if (station == null) return true;
    if (attrs == null) return false;
    for (Map.Entry<String, byte[]> e : attrs.entrySet()) {
      if ("station_id".equalsIgnoreCase(e.getKey()) && e.getValue() != null) {
        return station.equals(new String(e.getValue(), StandardCharsets.UTF_8));
      }
    }
    return false;
  }

  /**
   * http://host[:port]/ for a resolved address, or null if it isn't usable. Loopback, wildcard,
   * multicast and IPv6 link-local (needs a scope WebView can't use) are rejected. IPv6 literals are
   * bracketed and lose any %scope. Android 6 reports one address, so IPv4 is preferred only in
   * that an IPv6 address is not used when the platform gives an IPv4 one.
   */
  static String endpointUrl(InetAddress host, int port) {
    if (host == null || port < 1 || port > 65535) return null;
    if (host.isAnyLocalAddress() || host.isLoopbackAddress() || host.isMulticastAddress()) return null;
    String h;
    if (host instanceof Inet4Address) {
      h = host.getHostAddress();
    } else if (host instanceof Inet6Address) {
      if (host.isLinkLocalAddress()) return null;
      h = host.getHostAddress();
      int scope = h.indexOf('%');
      if (scope >= 0) h = h.substring(0, scope);
      h = "[" + h + "]";
    } else {
      return null;
    }
    return "http://" + h + (port == 80 ? "" : ":" + port) + "/";
  }

  /** 2 s, 4 s, 8 s ... capped at 60 s, for the nth consecutive failure (n >= 1). */
  static long backoffMs(int failures) {
    if (failures <= 1) return BACKOFF_MIN_MS;
    if (failures >= 6) return BACKOFF_MAX_MS;
    return Math.min(BACKOFF_MAX_MS, BACKOFF_MIN_MS << (failures - 1));
  }

  // ---- Discovery state machine (main thread only) ----

  private final NsdManager nsd;
  private final Handler handler;
  private final String wanted;
  private final String station;
  private Callback callback;
  private boolean running;
  private int generation;
  private NsdManager.DiscoveryListener active;
  private final ArrayDeque<NsdServiceInfo> queue = new ArrayDeque<>();
  private boolean resolving;
  private int resolveToken;
  private NsdServiceInfo resolvingInfo;
  private int resolveFailures;
  private int searchFailures;
  private int pageFailures;

  private final Runnable beginTask = this::begin;
  private final Runnable searchTimeout = new Runnable() {
    @Override
    public void run() {
      if (running) fail("no matching service found");
    }
  };
  private final Runnable resolveTimeout = new Runnable() {
    @Override
    public void run() {
      if (!running || !resolving) return;
      resolveToken++; // a late answer from this resolve is ignored
      resolving = false;
      resolveFailed(resolvingInfo, -1);
    }
  };
  private final Runnable recheck = new Runnable() {
    @Override
    public void run() {
      if (running) begin(); // fresh browse; the current endpoint stays until a new one resolves
    }
  };

  ServiceDiscovery(NsdManager nsd, Handler handler, String wanted, String station, Callback callback) {
    this.nsd = nsd;
    this.handler = handler;
    this.wanted = wanted;
    this.station = station;
    this.callback = callback;
  }

  void start() {
    if (running) return;
    running = true;
    searchFailures = 0;
    begin();
  }

  /** Stops all work and drops pending callbacks. start() may be called again. */
  void stop() {
    running = false;
    cancelWork();
  }

  /** stop(), and forget the callback so nothing can reach the Activity. */
  void close() {
    stop();
    callback = null;
  }

  /** The endpoint didn't work: look again, after a backoff that grows while it keeps failing. */
  void rediscover() {
    if (!running) return;
    pageFailures++;
    cancelWork();
    long delay = backoffMs(pageFailures);
    Log.i(TAG, "Dashboard endpoint failed; searching again in " + delay + " ms");
    handler.postDelayed(beginTask, delay);
  }

  /** The endpoint answered, so the failure streak is over. */
  void noteHealthy() {
    pageFailures = 0;
  }

  /** Wi-Fi came up or changed: search again soon, with a fresh backoff. */
  void onNetworkChanged() {
    if (!running) return;
    searchFailures = 0;
    cancelWork();
    handler.postDelayed(beginTask, NETWORK_SETTLE_MS);
  }

  private void cancelWork() {
    handler.removeCallbacks(beginTask);
    handler.removeCallbacks(searchTimeout);
    handler.removeCallbacks(resolveTimeout);
    handler.removeCallbacks(recheck);
    generation++;
    queue.clear();
    resolving = false;
    resolvingInfo = null;
    stopActive();
  }

  private void stopActive() {
    NsdManager.DiscoveryListener l = active;
    active = null;
    if (l == null || nsd == null) return;
    try {
      nsd.stopServiceDiscovery(l);
    } catch (RuntimeException e) {
      Log.w(TAG, "stopServiceDiscovery: " + e);
    }
  }

  private void begin() {
    if (!running) return;
    cancelWork();
    resolveFailures = 0;
    if (nsd == null) {
      fail("NsdManager is not available");
      return;
    }
    final int gen = generation;
    NsdManager.DiscoveryListener l = new DiscoveryHandler(gen);
    active = l;
    try {
      nsd.discoverServices(TYPE, NsdManager.PROTOCOL_DNS_SD, l);
    } catch (RuntimeException e) {
      active = null;
      fail("discoverServices: " + e);
      return;
    }
    handler.postDelayed(searchTimeout, SEARCH_TIMEOUT_MS);
  }

  /** One search attempt failed: tell the owner, then try again after a growing delay. */
  private void fail(String why) {
    searchFailures++;
    long delay = backoffMs(searchFailures);
    Log.w(TAG, "Dashboard discovery: " + why + "; retrying in " + delay + " ms");
    cancelWork();
    handler.postDelayed(beginTask, delay);
    if (callback != null) callback.onSearchStalled();
  }

  private void enqueue(NsdServiceInfo info) {
    // Already being resolved (or waiting): a repeated "found" must not start a second resolve.
    if (resolving && resolvingInfo != null && resolvingInfo.getServiceName().equalsIgnoreCase(info.getServiceName())) return;
    for (NsdServiceInfo queued : queue) {
      if (queued.getServiceName().equalsIgnoreCase(info.getServiceName())) return;
    }
    queue.add(info);
    resolveNext();
  }

  private void resolveNext() {
    if (!running || resolving || queue.isEmpty()) return;
    NsdServiceInfo info = queue.poll();
    resolving = true;
    resolvingInfo = info;
    int token = ++resolveToken;
    try {
      nsd.resolveService(info, new ResolveHandler(generation, token));
    } catch (RuntimeException e) {
      resolving = false;
      resolveFailed(info, -1);
      return;
    }
    handler.postDelayed(resolveTimeout, RESOLVE_TIMEOUT_MS);
  }

  private void resolveFailed(final NsdServiceInfo info, int code) {
    resolveFailures++;
    if (resolveFailures >= MAX_RESOLVE_FAILURES) {
      fail("resolve failed (" + code + ")");
      return;
    }
    // ALREADY_ACTIVE means another resolve is still running inside NSD: wait it out briefly.
    long delay = code == NsdManager.FAILURE_ALREADY_ACTIVE ? 1000 : 2000L * resolveFailures;
    final int gen = generation;
    handler.postDelayed(new Runnable() {
      @Override
      public void run() {
        if (running && gen == generation) enqueue(info);
      }
    }, delay);
    resolveNext();
  }

  private void onResolved(NsdServiceInfo info) {
    Log.i(TAG, "Resolved service name=" + info.getServiceName()
        + " TXT count=" + info.getAttributes().size());
    if (!nameMatches(info.getServiceName(), wanted, station != null)
        || !stationMatches(info.getAttributes(), station)) {
      Log.w(TAG, "Ignoring a service that does not match the configured dashboard");
      resolveNext();
      return;
    }
    String url = endpointUrl(info.getHost(), info.getPort());
    if (url == null) {
      Log.w(TAG, "Resolved dashboard address is not usable");
      resolveFailed(info, -2);
      return;
    }
    searchFailures = 0;
    resolveFailures = 0;
    handler.removeCallbacks(searchTimeout);
    handler.removeCallbacks(recheck);
    handler.postDelayed(recheck, RECHECK_MS);
    if (callback != null) callback.onEndpoint(url);
    resolveNext();
  }

  private void post(final int gen, final Runnable r) {
    handler.post(new Runnable() {
      @Override
      public void run() {
        if (running && gen == generation) r.run();
      }
    });
  }

  /** NSD thread callbacks: copy what is needed and hand over to the main thread. */
  private final class DiscoveryHandler implements NsdManager.DiscoveryListener {
    private final int gen;

    DiscoveryHandler(int gen) {
      this.gen = gen;
    }

    @Override
    public void onStartDiscoveryFailed(String type, final int code) {
      post(gen, new Runnable() {
        @Override
        public void run() {
          active = null; // never started, so there is nothing to stop
          fail("start failed (" + code + ")");
        }
      });
    }

    @Override
    public void onStopDiscoveryFailed(String type, int code) {
      Log.w(TAG, "Stopping discovery failed (" + code + ")");
    }

    @Override
    public void onDiscoveryStarted(String type) {
      Log.i(TAG, "Dashboard discovery started");
    }

    @Override
    public void onDiscoveryStopped(String type) {
      Log.i(TAG, "Dashboard discovery stopped");
    }

    @Override
    public void onServiceFound(final NsdServiceInfo info) {
      post(gen, new Runnable() {
        @Override
        public void run() {
          if (isHttpType(info.getServiceType()) && nameMatches(info.getServiceName(), wanted, station != null)) {
            enqueue(info);
          }
        }
      });
    }

    @Override
    public void onServiceLost(NsdServiceInfo info) {
      // The page keeps showing; a later found/resolve or a failed load moves the kiosk.
      Log.i(TAG, "Dashboard service withdrawn from the network");
    }
  }

  private final class ResolveHandler implements NsdManager.ResolveListener {
    private final int gen;
    private final int token;

    ResolveHandler(int gen, int token) {
      this.gen = gen;
      this.token = token;
    }

    @Override
    public void onResolveFailed(final NsdServiceInfo info, final int code) {
      post(gen, new Runnable() {
        @Override
        public void run() {
          if (token != resolveToken) return;
          resolving = false;
          handler.removeCallbacks(resolveTimeout);
          resolveFailed(info, code);
        }
      });
    }

    @Override
    public void onServiceResolved(final NsdServiceInfo info) {
      post(gen, new Runnable() {
        @Override
        public void run() {
          if (token != resolveToken) return;
          resolving = false;
          handler.removeCallbacks(resolveTimeout);
          onResolved(info);
        }
      });
    }
  }
}
