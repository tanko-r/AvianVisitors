package com.avianvisitors.display;

import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.util.Log;
import java.io.InputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;

/** Raw kiosk PCM via a loopback-only, Pi ADB-forwarded connection. No LAN listener. */
final class FrameAudio implements Runnable {
  private volatile boolean running = true;
  private ServerSocket server;
  private Socket client;
  void start() { new Thread(this, "frame-audio").start(); }
  synchronized void close() {
    running = false;
    try { if (client != null) client.close(); } catch (Exception ignored) { }
    try { if (server != null) server.close(); } catch (Exception ignored) { }
  }
  public void run() {
    try {
      synchronized (this) {
        if (!running) return;
        server = new ServerSocket(8766, 1, InetAddress.getByName("127.0.0.1"));
      }
      while (running) {
        AudioTrack track = null;
        try {
          Socket accepted = server.accept();
          synchronized (this) { client = accepted; if (!running) { client.close(); break; } }
          client.setSoTimeout(10000);
          int size = Math.max(4096, AudioTrack.getMinBufferSize(22050,
              AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT));
          track = new AudioTrack(AudioManager.STREAM_MUSIC, 22050,
              AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT, size, AudioTrack.MODE_STREAM);
          if (track.getState() != AudioTrack.STATE_INITIALIZED) throw new IllegalStateException("Audio unavailable");
          track.play();
          Log.i("BirdDisplayAudio", "Kiosk speaker connected");
          InputStream input = client.getInputStream();
          byte[] bytes = new byte[2048];
          int count, pending = 0;
          while (running && (count = input.read(bytes, pending, bytes.length - pending)) != -1) {
            count += pending;
            pending = count & 1;
            byte remainder = bytes[count - 1];
            count -= pending;
            int offset = 0;
            while (running && offset < count) {
              int written = track.write(bytes, offset, count - offset);
              if (written <= 0) throw new IllegalStateException("Speaker write failed");
              offset += written;
            }
            if (pending != 0) bytes[0] = remainder;
          }
        } catch (Exception e) {
          if (running) Log.i("BirdDisplayAudio", "Speaker stream ended; waiting for Pi");
        } finally {
          if (track != null) { track.pause(); track.flush(); track.release(); }
          synchronized (this) {
            try { if (client != null) client.close(); } catch (Exception ignored) { }
            client = null;
          }
        }
      }
    } catch (Exception e) { Log.e("BirdDisplayAudio", "Loopback speaker unavailable", e); }
    finally { close(); }
  }
}
