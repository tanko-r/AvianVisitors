#!/usr/bin/env python3
"""Exercise the real ServiceDiscovery class (src/.../ServiceDiscovery.java) against host fakes.

Needs Python 3 and a JDK on PATH. No SDK, device or network. The fakes model NsdManager's
documented callback behaviour (callbacks on another thread, one resolve at a time, listener reuse
errors, FAILURE_ALREADY_ACTIVE) and a virtual clock. They do NOT prove that Android 6's mdnsd
browses, resolves or returns TXT records on a real network; that needs a live-network test.
"""
from pathlib import Path
import subprocess
import tempfile

KIOSK = Path(__file__).resolve().parent
PACKAGE = Path("com/avianvisitors/display")
REAL = (KIOSK / "src" / PACKAGE / "ServiceDiscovery.java").read_text(encoding="utf-8")

SOURCES = {
    "android/util/Log.java": """package android.util;
public class Log {
  public static java.util.List<String> lines = new java.util.ArrayList<>();
  public static int i(String t, String m) { lines.add(m); return 0; }
  public static int w(String t, String m) { lines.add(m); return 0; }
}""",
    "android/os/Handler.java": """package android.os;
import java.util.*;
public class Handler {
  public long now;
  private static class Task { long at; long seq; Runnable r; }
  private long seq;
  public final List<Task> tasks = new ArrayList<>();
  public boolean post(Runnable r) { return postDelayed(r, 0); }
  public boolean postDelayed(Runnable r, long d) {
    Task t = new Task(); t.at = now + d; t.seq = seq++; t.r = r; tasks.add(t); return true; }
  public void removeCallbacks(Runnable r) { tasks.removeIf(t -> t.r == r); }
  public int pending() { return tasks.size(); }
  /** Runs everything due up to now+ms, in time order, advancing the virtual clock. */
  public void advance(long ms) {
    long end = now + ms;
    while (true) {
      Task next = null;
      for (Task t : tasks) if (t.at <= end && (next == null || t.at < next.at || (t.at == next.at && t.seq < next.seq))) next = t;
      if (next == null) break;
      tasks.remove(next); now = Math.max(now, next.at); next.r.run();
    }
    now = end;
  }
}""",
    "android/net/nsd/NsdServiceInfo.java": """package android.net.nsd;
import java.net.InetAddress; import java.util.*;
public class NsdServiceInfo {
  public String name, type; public InetAddress host; public int port; public Map<String, byte[]> attrs = new HashMap<>();
  public NsdServiceInfo() {}
  public NsdServiceInfo(String n, String t) { name = n; type = t; }
  public String getServiceName() { return name; } public String getServiceType() { return type; }
  public InetAddress getHost() { return host; } public int getPort() { return port; }
  public Map<String, byte[]> getAttributes() { return attrs; }
}""",
    "android/net/nsd/NsdManager.java": """package android.net.nsd;
import java.util.*;
public class NsdManager {
  public static final int PROTOCOL_DNS_SD = 1;
  public static final int FAILURE_INTERNAL_ERROR = 0, FAILURE_ALREADY_ACTIVE = 3, FAILURE_MAX_LIMIT = 4;
  public interface DiscoveryListener {
    void onStartDiscoveryFailed(String t, int c); void onStopDiscoveryFailed(String t, int c);
    void onDiscoveryStarted(String t); void onDiscoveryStopped(String t);
    void onServiceFound(NsdServiceInfo i); void onServiceLost(NsdServiceInfo i);
  }
  public interface ResolveListener { void onResolveFailed(NsdServiceInfo i, int c); void onServiceResolved(NsdServiceInfo i); }
  // Test hooks
  public final List<DiscoveryListener> started = new ArrayList<>();
  public final List<DiscoveryListener> stopped = new ArrayList<>();
  public final List<ResolveListener> resolves = new ArrayList<>();
  public final List<NsdServiceInfo> resolveInfos = new ArrayList<>();
  public boolean throwOnDiscover, throwOnStop; public int activeResolves, alreadyActiveSeen;
  public void discoverServices(String type, int proto, DiscoveryListener l) {
    if (throwOnDiscover) throw new IllegalArgumentException("boom");
    if (started.contains(l) && !stopped.contains(l)) throw new IllegalArgumentException("listener already in use");
    started.add(l);
  }
  public void stopServiceDiscovery(DiscoveryListener l) {
    if (throwOnStop) throw new IllegalArgumentException("listener not registered");
    stopped.add(l);
  }
  public void resolveService(NsdServiceInfo i, ResolveListener l) {
    if (resolves.contains(l)) throw new IllegalArgumentException("listener already in use");
    resolves.add(l); resolveInfos.add(i);
  }
  public DiscoveryListener lastBrowse() { return started.get(started.size() - 1); }
  public ResolveListener lastResolve() { return resolves.get(resolves.size() - 1); }
}""",
    str(PACKAGE / "MainActivity.java"): "package com.avianvisitors.display; public class MainActivity { static final String TAG = \"test\"; }",
    str(PACKAGE / "ServiceDiscovery.java"): REAL,
    str(PACKAGE / "DiscoveryHarness.java"): r'''package com.avianvisitors.display;
import android.net.nsd.*; import android.os.Handler; import android.util.Log;
import java.net.*; import java.util.*;

public class DiscoveryHarness {
  static int checks;
  static void check(boolean ok, String name) {
    if (!ok) throw new AssertionError(name);
    checks++; System.out.println("PASS " + name);
  }
  static InetAddress ip(String s) { try { return InetAddress.getByName(s); } catch (Exception e) { throw new RuntimeException(e); } }

  static class Rec implements ServiceDiscovery.Callback {
    final List<String> urls = new ArrayList<>(); int stalls;
    public void onEndpoint(String u) { urls.add(u); }
    public void onSearchStalled() { stalls++; }
  }
  static NsdServiceInfo svc(String name, String host, int port) {
    NsdServiceInfo i = new NsdServiceInfo(name, "_http._tcp."); if (host != null) i.host = ip(host); i.port = port; return i;
  }
  static final String NAME = "AvianVisitors-Dad-491";

  public static void main(String[] a) throws Exception {
    helpers();
    flow();
    concurrency();
    failures();
    lifecycle();
    System.out.println(checks + " checks passed");
  }

  static void helpers() {
    check(ServiceDiscovery.normalizeName(NAME).equals(NAME), "normal instance name accepted");
    check(ServiceDiscovery.normalizeName("") == null && ServiceDiscovery.normalizeName(null) == null, "empty/null name rejected");
    check(ServiceDiscovery.normalizeName("a/b") == null && ServiceDiscovery.normalizeName("x\"y") == null
        && ServiceDiscovery.normalizeName("name ") == null && ServiceDiscovery.normalizeName("-x") == null,
        "odd characters and trailing space rejected");
    StringBuilder b = new StringBuilder(); for (int i = 0; i < 64; i++) b.append('a');
    check(ServiceDiscovery.normalizeName(b.toString()) == null, "name over 63 characters rejected");
    check(ServiceDiscovery.isHttpType("_http._tcp.") && ServiceDiscovery.isHttpType("_http._tcp")
        && ServiceDiscovery.isHttpType("._http._tcp.") && !ServiceDiscovery.isHttpType("_ssh._tcp.")
        && !ServiceDiscovery.isHttpType(null), "service type tolerance");
    check(ServiceDiscovery.nameMatches(NAME, NAME, false) && ServiceDiscovery.nameMatches(NAME.toLowerCase(), NAME, false),
        "exact name matches, case-insensitively");
    check(!ServiceDiscovery.nameMatches("AvianVisitors-Dad-4910", NAME, true) && !ServiceDiscovery.nameMatches("Other", NAME, true)
        && !ServiceDiscovery.nameMatches(NAME + "2", NAME, true), "other names never match");
    check(!ServiceDiscovery.nameMatches(NAME + " #2", NAME, false), "collision variant refused without a station id");
    check(ServiceDiscovery.nameMatches(NAME + " #2", NAME, true) && !ServiceDiscovery.nameMatches(NAME + " #x", NAME, true)
        && !ServiceDiscovery.nameMatches(NAME + " #", NAME, true), "collision variant accepted only with station id and digits");
    Map<String, byte[]> txt = new HashMap<>(); txt.put("path", "/evil?x=1".getBytes()); txt.put("station_id", "avian-dad-491".getBytes());
    check(ServiceDiscovery.stationMatches(txt, "avian-dad-491") && !ServiceDiscovery.stationMatches(txt, "avian-other")
        && !ServiceDiscovery.stationMatches(new HashMap<>(), "avian-dad-491") && ServiceDiscovery.stationMatches(null, null),
        "station_id verification");
    check("http://192.168.1.7/".equals(ServiceDiscovery.endpointUrl(ip("192.168.1.7"), 80)), "IPv4 port 80 URL");
    check("http://192.168.1.7:8080/".equals(ServiceDiscovery.endpointUrl(ip("192.168.1.7"), 8080)), "IPv4 non-default port URL");
    check("http://[2001:db8:0:0:0:0:0:1]/".equals(ServiceDiscovery.endpointUrl(ip("2001:db8::1"), 80)), "IPv6 literal bracketed");
    check(ServiceDiscovery.endpointUrl(ip("fe80::1"), 80) == null, "IPv6 link-local rejected");
    check(ServiceDiscovery.endpointUrl(ip("127.0.0.1"), 80) == null && ServiceDiscovery.endpointUrl(ip("0.0.0.0"), 80) == null
        && ServiceDiscovery.endpointUrl(ip("224.0.0.251"), 80) == null && ServiceDiscovery.endpointUrl(ip("::1"), 80) == null,
        "loopback, wildcard, multicast rejected");
    check(ServiceDiscovery.endpointUrl(null, 80) == null && ServiceDiscovery.endpointUrl(ip("10.0.0.2"), 0) == null
        && ServiceDiscovery.endpointUrl(ip("10.0.0.2"), 70000) == null, "missing host or bad port rejected");
    check(ServiceDiscovery.backoffMs(1) == 2000 && ServiceDiscovery.backoffMs(2) == 4000 && ServiceDiscovery.backoffMs(5) == 32000
        && ServiceDiscovery.backoffMs(6) == 60000 && ServiceDiscovery.backoffMs(500) == 60000 && ServiceDiscovery.backoffMs(0) == 2000,
        "backoff doubles then caps at 60 s");
  }

  static Object[] make(String station) {
    NsdManager nsd = new NsdManager(); Handler h = new Handler(); Rec r = new Rec();
    ServiceDiscovery d = new ServiceDiscovery(nsd, h, NAME, station, r);
    return new Object[] {nsd, h, r, d};
  }

  static void flow() {
    Object[] m = make(null); NsdManager nsd = (NsdManager) m[0]; Handler h = (Handler) m[1]; Rec r = (Rec) m[2]; ServiceDiscovery d = (ServiceDiscovery) m[3];
    d.start(); d.start();
    check(nsd.started.size() == 1, "start is idempotent: one browse");
    NsdManager.DiscoveryListener browse = nsd.lastBrowse();
    browse.onServiceFound(svc("SomeOtherWebServer", "10.0.0.9", 80)); h.advance(0);
    check(nsd.resolves.isEmpty(), "other service names are never resolved");
    browse.onServiceFound(new NsdServiceInfo(NAME, "_ssh._tcp.")); h.advance(0);
    check(nsd.resolves.isEmpty(), "right name with wrong type is ignored");
    browse.onServiceFound(svc(NAME, null, 0)); h.advance(0);
    check(nsd.resolves.size() == 1, "matching service is resolved");
    nsd.lastResolve().onServiceResolved(svc(NAME, "192.168.68.99", 80)); h.advance(0);
    check(r.urls.equals(Arrays.asList("http://192.168.68.99/")), "resolved address becomes a plain http URL");
    check(r.stalls == 0, "success is not reported as a stall");
    // Address change without a failed load: periodic re-browse finds the new address.
    h.advance(ServiceDiscovery.RECHECK_MS + 1);
    check(nsd.started.size() == 2 && nsd.stopped.contains(browse), "re-check restarts the browse and releases the old listener");
    nsd.lastBrowse().onServiceFound(svc(NAME, null, 0)); h.advance(0);
    nsd.lastResolve().onServiceResolved(svc(NAME, "192.168.68.120", 80)); h.advance(0);
    check(r.urls.get(r.urls.size() - 1).equals("http://192.168.68.120/"), "moved station is picked up by the re-check");
    // Late callback from the first (replaced) browse is dropped.
    int before = nsd.resolves.size();
    browse.onServiceFound(svc(NAME, null, 0)); h.advance(0);
    check(nsd.resolves.size() == before, "late callback from a replaced browse is ignored");
  }

  static void concurrency() {
    Object[] m = make(null); NsdManager nsd = (NsdManager) m[0]; Handler h = (Handler) m[1]; Rec r = (Rec) m[2]; ServiceDiscovery d = (ServiceDiscovery) m[3];
    d.start(); NsdManager.DiscoveryListener browse = nsd.lastBrowse();
    browse.onServiceFound(svc(NAME, null, 0)); browse.onServiceFound(svc(NAME, null, 0)); h.advance(0);
    check(nsd.resolves.size() == 1, "duplicate found events produce one resolve");
    nsd.lastResolve().onResolveFailed(svc(NAME, null, 0), NsdManager.FAILURE_ALREADY_ACTIVE); h.advance(0);
    check(nsd.resolves.size() == 1, "FAILURE_ALREADY_ACTIVE waits instead of resolving at once");
    h.advance(1000);
    check(nsd.resolves.size() == 2, "resolve retried after 1 s");
    nsd.lastResolve().onServiceResolved(svc(NAME, "10.1.2.3", 80)); h.advance(0);
    check(r.urls.equals(Arrays.asList("http://10.1.2.3/")), "resolve succeeds after ALREADY_ACTIVE");
    // A resolve that never answers is abandoned, and its late answer ignored.
    Object[] m2 = make(null); NsdManager n2 = (NsdManager) m2[0]; Handler h2 = (Handler) m2[1]; Rec r2 = (Rec) m2[2]; ServiceDiscovery d2 = (ServiceDiscovery) m2[3];
    d2.start(); n2.lastBrowse().onServiceFound(svc(NAME, null, 0)); h2.advance(0);
    NsdManager.ResolveListener hung = n2.lastResolve();
    h2.advance(ServiceDiscovery.RESOLVE_TIMEOUT_MS + 1);
    h2.advance(2000);
    check(n2.resolves.size() == 2, "hung resolve times out and is retried");
    hung.onServiceResolved(svc(NAME, "10.9.9.9", 80)); h2.advance(0);
    check(r2.urls.isEmpty(), "answer from an abandoned resolve is ignored");
    n2.lastResolve().onServiceResolved(svc(NAME, "10.1.1.1", 80)); h2.advance(0);
    check(r2.urls.equals(Arrays.asList("http://10.1.1.1/")), "current resolve still works");
  }

  static void failures() {
    Object[] m = make(null); NsdManager nsd = (NsdManager) m[0]; Handler h = (Handler) m[1]; Rec r = (Rec) m[2]; ServiceDiscovery d = (ServiceDiscovery) m[3];
    d.start();
    NsdManager.DiscoveryListener l1 = nsd.lastBrowse();
    l1.onStartDiscoveryFailed("_http._tcp.", 0); h.advance(0);
    check(r.stalls == 1 && nsd.started.size() == 1, "start failure reported, no immediate retry");
    h.advance(1999); check(nsd.started.size() == 1, "no retry before 2 s");
    h.advance(2); check(nsd.started.size() == 2 && nsd.lastBrowse() != l1, "retry with a new listener after 2 s");
    check(!nsd.stopped.contains(l1), "a browse that never started is not stopped");
    // Nothing on the network for ten minutes: bounded number of attempts, none in a tight loop.
    Object[] q = make(null); NsdManager nq = (NsdManager) q[0]; Handler hq = (Handler) q[1]; ServiceDiscovery dq = (ServiceDiscovery) q[3];
    dq.start(); hq.advance(10 * 60 * 1000);
    check(nq.started.size() <= 14 && nq.started.size() >= 8, "empty network: " + nq.started.size() + " attempts in 10 min");
    check(hq.pending() <= 3, "empty network leaves only the next attempt's timers queued");
    // Unavailable NSD must not crash.
    Handler hn = new Handler(); Rec rn = new Rec();
    ServiceDiscovery dn = new ServiceDiscovery(null, hn, NAME, null, rn); dn.start(); hn.advance(0);
    check(rn.stalls == 1, "missing NsdManager reports a stall instead of crashing");
    dn.stop();
    // discoverServices throwing is survived.
    NsdManager nt = new NsdManager(); nt.throwOnDiscover = true; Handler ht = new Handler(); Rec rt = new Rec();
    ServiceDiscovery dt = new ServiceDiscovery(nt, ht, NAME, null, rt); dt.start(); ht.advance(1);
    check(rt.stalls == 1, "discoverServices exception is caught and retried");
    nt.throwOnDiscover = false; ht.advance(2000);
    check(nt.started.size() == 1, "browse starts once the platform recovers");
    // Loopback address from a (hostile) answer is not used.
    Object[] x = make(null); NsdManager nx = (NsdManager) x[0]; Handler hx = (Handler) x[1]; Rec rx = (Rec) x[2]; ServiceDiscovery dx = (ServiceDiscovery) x[3];
    dx.start(); nx.lastBrowse().onServiceFound(svc(NAME, null, 0)); hx.advance(0);
    nx.lastResolve().onServiceResolved(svc(NAME, "127.0.0.1", 80)); hx.advance(0);
    check(rx.urls.isEmpty(), "loopback answer is not reported");
    // Station id configured: wrong or missing TXT is refused, right one accepted.
    Object[] s = make("avian-dad-491"); NsdManager ns = (NsdManager) s[0]; Handler hs = (Handler) s[1]; Rec rs = (Rec) s[2]; ServiceDiscovery ds = (ServiceDiscovery) s[3];
    ds.start(); ns.lastBrowse().onServiceFound(svc(NAME, null, 0)); hs.advance(0);
    NsdServiceInfo bad = svc(NAME, "10.0.0.5", 80); bad.attrs.put("station_id", "someone-else".getBytes());
    ns.lastResolve().onServiceResolved(bad); hs.advance(0);
    check(rs.urls.isEmpty(), "wrong station_id refused");
    ns.lastBrowse().onServiceFound(svc(NAME + " #2", null, 0)); hs.advance(0);
    NsdServiceInfo good = svc(NAME + " #2", "10.0.0.6", 80); good.attrs.put("station_id", "avian-dad-491".getBytes());
    ns.lastResolve().onServiceResolved(good); hs.advance(0);
    check(rs.urls.equals(Arrays.asList("http://10.0.0.6/")), "collision-renamed instance accepted with matching station_id");
  }

  static void lifecycle() {
    Object[] m = make(null); NsdManager nsd = (NsdManager) m[0]; Handler h = (Handler) m[1]; Rec r = (Rec) m[2]; ServiceDiscovery d = (ServiceDiscovery) m[3];
    d.start(); nsd.lastBrowse().onServiceFound(svc(NAME, null, 0)); h.advance(0);
    nsd.lastResolve().onServiceResolved(svc(NAME, "10.0.0.8", 80)); h.advance(0);
    // Endpoint failure: rediscover backs off 2, 4, 8 ... and noteHealthy resets.
    int s0 = nsd.started.size();
    d.rediscover(); h.advance(1999); check(nsd.started.size() == s0, "rediscover waits 2 s the first time");
    h.advance(2); check(nsd.started.size() == s0 + 1, "rediscover then browses again");
    d.rediscover(); h.advance(3999); check(nsd.started.size() == s0 + 1, "second consecutive failure waits 4 s");
    h.advance(2); check(nsd.started.size() == s0 + 2, "then browses");
    d.noteHealthy(); d.rediscover(); h.advance(2001);
    check(nsd.started.size() == s0 + 3, "after a healthy load the wait is back to 2 s");
    // stop(): release the browse, leave no timers, ignore late callbacks.
    NsdManager.DiscoveryListener live = nsd.lastBrowse();
    d.stop();
    check(nsd.stopped.contains(live) && h.pending() == 0, "stop releases the browse and clears every timer");
    int urls = r.urls.size(), resolvesBefore = nsd.resolves.size();
    live.onServiceFound(svc(NAME, null, 0)); h.advance(1000000);
    check(nsd.resolves.size() == resolvesBefore && r.urls.size() == urls && h.pending() == 0, "callbacks after stop do nothing");
    // stop() survives the platform refusing to stop a listener, and start() works again.
    nsd.throwOnStop = true; d.start(); d.stop(); nsd.throwOnStop = false;
    int before = nsd.started.size(); d.start();
    check(nsd.started.size() == before + 1, "restart after stop browses with a fresh listener");
    // close(): no callback reaches the owner afterwards.
    nsd.lastBrowse().onServiceFound(svc(NAME, null, 0)); h.advance(0);
    d.close(); nsd.lastResolve().onServiceResolved(svc(NAME, "10.0.0.50", 80)); h.advance(0);
    check(r.urls.size() == urls, "nothing reaches the owner after close()");
    // Network change: debounced restart with fresh backoff.
    Object[] n = make(null); NsdManager nn = (NsdManager) n[0]; Handler hn = (Handler) n[1]; ServiceDiscovery dn = (ServiceDiscovery) n[3];
    dn.start(); int k = nn.started.size();
    dn.onNetworkChanged(); dn.onNetworkChanged(); hn.advance(1999);
    check(nn.started.size() == k, "network change is debounced");
    hn.advance(2); check(nn.started.size() == k + 1, "network change restarts the browse once");
  }

  static void unusedGuard() { Log.i("t", "x"); }
}
''',
}

with tempfile.TemporaryDirectory(prefix="homehq-discovery-") as directory:
    root = Path(directory)
    for name, source in SOURCES.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    subprocess.run(["javac", "--release", "8", "-d", str(root)] +
                   [str(file) for file in root.rglob("*.java")], check=True, timeout=60)
    subprocess.run(["java", "-cp", str(root), "com.avianvisitors.display.DiscoveryHarness"],
                   check=True, timeout=60)
