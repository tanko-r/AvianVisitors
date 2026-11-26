#!/usr/bin/env python3
"""Forward only Chromium's playback sink to the serial-verified frame over ADB."""
import ipaddress
import json
import os
import select
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
events = None
try:
    while not stopping:
        try:
            sinks = json.loads(run('pactl', '-f', 'json', 'list', 'sinks'))
            if not any(s['name'] == SINK for s in sinks):
                run('pactl', 'load-module', 'module-null-sink', 'sink_name=' + SINK,
                    'rate=22050', 'channels=1', 'sink_properties=device.description=Frame_Speaker')
                sinks = json.loads(run('pactl', '-f', 'json', 'list', 'sinks'))
            sink_index = next(s['index'] for s in sinks if s['name'] == SINK)
            if events is None or events.poll() is not None:
                events = subprocess.Popen(['pactl', 'subscribe'], stdout=subprocess.PIPE,
                                          stderr=subprocess.DEVNULL)
            for item in json.loads(run('pactl', '-f', 'json', 'list', 'sink-inputs')):
                props = item.get('properties', {})
                if ('chrom' in props.get('application.process.binary', '').lower()
                        and item['sink'] != sink_index):
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
        # Wake immediately when Chromium creates a playback stream, rather
        # than losing the first seconds of a short bird call to polling.
        if events and events.poll() is None:
            if select.select([events.stdout], [], [], 1)[0]:
                os.read(events.stdout.fileno(), 8192)
        else:
            time.sleep(1)
finally:
    if events:
        events.terminate()
        events.wait(timeout=3)
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
