#!/usr/bin/env python3
"""Forward only Chromium's playback sink to the serial-verified frame over ADB."""
import ipaddress
import json
import signal
import subprocess
import time

FRAME_SERIAL = 'a0082c68081700000000'
SINK = 'avian_frame'
PORT = 'tcp:18766'
stopping = False


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=8, check=True).stdout.strip()


def stop(*_):
    global stopping
    stopping = True


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
stream = None
device = None
try:
    while not stopping:
        try:
            sinks = json.loads(run('pactl', '-f', 'json', 'list', 'sinks'))
            if not any(s['name'] == SINK for s in sinks):
                run('pactl', 'load-module', 'module-null-sink', 'sink_name=' + SINK,
                    'rate=22050', 'channels=1', 'sink_properties=device.description=Frame_Speaker')
            for item in json.loads(run('pactl', '-f', 'json', 'list', 'sink-inputs')):
                props = item.get('properties', {})
                if 'chrom' in props.get('application.process.binary', '').lower():
                    run('pactl', 'move-sink-input', str(item['index']), SINK)
            if device:
                if run('adb', '-s', device, 'get-state') != 'device':
                    raise RuntimeError('Frame disconnected')
                if stream and stream.poll() is not None:
                    raise RuntimeError('Audio disconnected')
            else:
                # Current inbound SSH sessions supply candidates, never a LAN scan.
                for line in run('ss', '-tnH', 'state', 'established', 'sport', '=', ':22').splitlines():
                    address = line.split()[3].rsplit(':', 1)[0]
                    try:
                        ip = ipaddress.IPv4Address(address)
                        if not ip.is_private or ' dev wlan0 ' not in run('ip', 'route', 'get', address):
                            continue
                        candidate = address + ':5555'
                        run('adb', 'connect', candidate)
                        if run('adb', '-s', candidate, 'shell', 'getprop', 'ro.serialno').strip() != FRAME_SERIAL:
                            continue
                        run('adb', '-s', candidate, 'forward', PORT, 'tcp:8766')
                        device = candidate
                        stream = subprocess.Popen([
                            'ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error',
                            '-f', 'pulse', '-i', SINK + '.monitor', '-ac', '1', '-ar', '22050',
                            '-f', 's16le', '-flush_packets', '1', 'tcp://127.0.0.1:18766'],
                            stdout=subprocess.DEVNULL)
                        print('Frame speaker relay connected', flush=True)
                        break
                    except (ValueError, subprocess.SubprocessError):
                        continue
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError):
            if stream:
                stream.terminate()
                try:
                    stream.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    stream.kill()
                    stream.wait()
                stream = None
            if device:
                try:
                    run('adb', '-s', device, 'forward', '--remove', PORT)
                except subprocess.SubprocessError:
                    pass
            device = None
        for _ in range(5):
            if stopping:
                break
            time.sleep(1)
finally:
    if stream:
        stream.terminate()
        try:
            stream.wait(timeout=3)
        except subprocess.TimeoutExpired:
            stream.kill()
            stream.wait()
    if device:
        try:
            run('adb', '-s', device, 'forward', '--remove', PORT)
        except subprocess.SubprocessError:
            pass
