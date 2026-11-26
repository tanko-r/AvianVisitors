package com.avianvisitors.maintenance;

import android.util.Base64;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.security.*;
import java.security.spec.X509EncodedKeySpec;
import java.util.*;

/** Root boot process: challenge the pinned Pi before allowing its current IP.
 * Candidates from SSH/mDNS are untrusted until RSA verification succeeds. */
public final class MaintenanceGuard {
  private static final SecureRandom random = new SecureRandom();
  private static final String TAG = "frame-maintenance";
  private static String allowed = "";
  private static String previous = "";
  private static String read(String path, int limit) throws IOException {
    try (InputStream in = new FileInputStream(path)) { return read(in, limit); }
  }
  private static String read(InputStream in, int limit) throws IOException {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    byte[] buf = new byte[1024]; int n;
    while ((n = in.read(buf)) != -1) {
      if (out.size() + n > limit) throw new IOException("input too large");
      out.write(buf, 0, n);
    }
    return new String(out.toByteArray(), "UTF-8");
  }
  private static void command(String script) throws Exception {
    Process p = new ProcessBuilder("/system/bin/sh", "-c", script).redirectErrorStream(true).start();
    read(p.getInputStream(), 8192);
    if (p.waitFor() != 0) throw new IOException("firewall command failed");
  }
  private static boolean privateIP(String ip) {
    if (!ip.matches("[0-9]{1,3}(\\.[0-9]{1,3}){3}")) return false;
    String[] parts = ip.split("\\."); int[] n = new int[4];
    for (int i = 0; i < 4; i++) { n[i] = Integer.parseInt(parts[i]); if (n[i] > 255) return false; }
    return n[0] == 10 || (n[0] == 192 && n[1] == 168) || (n[0] == 172 && n[1] >= 16 && n[1] <= 31);
  }
  private static void permit(String ip) throws Exception {
    if (ip.equals(allowed)) return;
    // Fail closed while updating; never leave both old/new peers allowed.
    command("iptables -I AVIAN_ADB 1 -p tcp --dport 5555 -j REJECT; " +
      "iptables -F AVIAN_ADB && iptables -A AVIAN_ADB -p tcp --dport 5555 -j REJECT");
    allowed = "";
    if (!ip.isEmpty()) {
      if (!privateIP(ip)) throw new IOException("invalid peer");
      command("iptables -I AVIAN_ADB 1 -s " + ip + " -p tcp --dport 5555 -j ACCEPT");
      allowed = ip;
    }
    android.util.Log.i(TAG, allowed.isEmpty() ? "ADB access blocked" : "Pinned Pi address authorized");
  }
  private static boolean prove(String ip, PublicKey key) {
    if (!privateIP(ip)) return false;
    HttpURLConnection connection = null;
    try {
      byte[] bytes = new byte[16]; random.nextBytes(bytes);
      StringBuilder nonce = new StringBuilder();
      for (byte b : bytes) nonce.append(String.format(Locale.US, "%02x", b & 255));
      connection = (HttpURLConnection)new URL("http://" + ip + "/avian/api/frame-maintenance.php?nonce=" + nonce).openConnection();
      connection.setConnectTimeout(1500); connection.setReadTimeout(1500);
      connection.setInstanceFollowRedirects(false); connection.setUseCaches(false);
      if (connection.getResponseCode() != 200) return false;
      JSONObject data;
      try (InputStream in = connection.getInputStream()) { data = new JSONObject(read(in, 4096)); }
      if (!ip.equals(data.getString("address")) || !nonce.toString().equals(data.getString("nonce"))) return false;
      Signature verifier = Signature.getInstance("SHA256withRSA"); verifier.initVerify(key);
      verifier.update(("avian-frame-maintenance-v1\n" + nonce + "\n" + ip).getBytes("UTF-8"));
      return verifier.verify(Base64.decode(data.getString("signature"), Base64.DEFAULT));
    } catch (Exception error) { return false; }
    finally { if (connection != null) connection.disconnect(); }
  }
  private static Set<String> sshCandidates() {
    Set<String> ips = new LinkedHashSet<>();
    try {
      for (String line : read("/proc/net/tcp", 65536).split("\n")) {
        String[] columns = line.trim().split("\\s+");
        if (columns.length < 4 || !columns[3].equals("01") || !columns[2].endsWith(":0016")) continue;
        String h = columns[2].substring(0, 8);
        String ip = Integer.parseInt(h.substring(6,8),16) + "." + Integer.parseInt(h.substring(4,6),16) + "." + Integer.parseInt(h.substring(2,4),16) + "." + Integer.parseInt(h.substring(0,2),16);
        if (privateIP(ip)) ips.add(ip);
      }
    } catch (Exception ignored) { }
    return ips;
  }
  private static int u16(byte[] b, int p) { return ((b[p]&255)<<8) | (b[p+1]&255); }
  private static int skipName(byte[] b, int p, int length) throws IOException {
    for (int count=0; count<128 && p<length; count++) {
      int n=b[p++]&255; if (n==0) return p;
      if ((n&192)==192) { if (p>=length) break; return p+1; }
      if (n>63 || p+n>length) break; p+=n;
    }
    throw new IOException("bad DNS name");
  }
  private static Set<String> discover() {
    Set<String> ips = new LinkedHashSet<>();
    // Legacy unicast mDNS query from an ephemeral port: no LAN scan, no
    // dependency on the viewer being open. Avahi supplies A additional records.
    try (DatagramSocket socket = new DatagramSocket()) {
      socket.setSoTimeout(1200);
      ByteArrayOutputStream bytes = new ByteArrayOutputStream(); DataOutputStream out = new DataOutputStream(bytes);
      out.writeShort(random.nextInt(65536)); out.writeShort(0); out.writeShort(1);
      out.writeShort(0); out.writeShort(0); out.writeShort(0);
      for (String label : "AvianVisitors-Dad-491._http._tcp.local".split("\\.")) {
        byte[] raw=label.getBytes("UTF-8"); out.writeByte(raw.length); out.write(raw);
      }
      out.writeByte(0); out.writeShort(33); out.writeShort(1);
      byte[] query=bytes.toByteArray();
      socket.send(new DatagramPacket(query, query.length, InetAddress.getByName("224.0.0.251"),5353));
      for (int packet=0; packet<6; packet++) {
        byte[] b=new byte[8192]; DatagramPacket reply=new DatagramPacket(b,b.length); socket.receive(reply);
        int len=reply.getLength(); if (len<12) continue;
        int questions=u16(b,4), records=u16(b,6)+u16(b,8)+u16(b,10), p=12;
        if (questions>20 || records>100) continue;
        for (int i=0;i<questions;i++) { p=skipName(b,p,len)+4; if(p>len) throw new IOException(); }
        for (int i=0;i<records;i++) {
          p=skipName(b,p,len); if (p+10>len) break;
          int type=u16(b,p), size=u16(b,p+8); p+=10; if (p+size>len) break;
          if (type==1 && size==4) {
            String ip=(b[p]&255)+"."+(b[p+1]&255)+"."+(b[p+2]&255)+"."+(b[p+3]&255);
            if (privateIP(ip)) ips.add(ip);
          }
          p+=size;
        }
      }
    } catch (Exception ignored) { }
    return ips;
  }
  public static void main(String[] args) throws Exception {
    String pem=read("/system/etc/frame-maintenance.pub",8192).replaceAll("-----[^-]+-----", "");
    PublicKey key=KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(Base64.decode(pem,Base64.DEFAULT)));
    command("iptables -F AVIAN_ADB && iptables -A AVIAN_ADB -p tcp --dport 5555 -j REJECT");
    int cycle=0;
    while (true) {
      try {
        Set<String> candidates=new LinkedHashSet<>(); if (!previous.isEmpty()) candidates.add(previous);
        candidates.addAll(sshCandidates());
        if (previous.isEmpty() || cycle++%6==0) candidates.addAll(discover());
        String verified="";
        int attempts=0;
        for (String ip : candidates) { if (++attempts>8) break; if (prove(ip,key)) { verified=ip; break; } }
        permit(verified); previous=verified;
      } catch (Exception error) { try { permit(""); } catch(Exception ignored) { } }
      Thread.sleep(5000);
    }
  }
}
