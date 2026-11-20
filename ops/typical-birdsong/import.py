#!/usr/bin/env python3
"""Import one unmodified Cornell MP3 per species into a private library."""
import argparse
import hashlib
import json
import pathlib
import re
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive')
parser.add_argument('destination')
args = parser.parse_args()
dest = pathlib.Path(args.destination)
dest.mkdir(parents=True, exist_ok=True)
chosen = {}
with zipfile.ZipFile(args.archive) as archive:
    for entry in archive.infolist():
        if entry.filename.startswith('__MACOSX/'):
            continue
        name = pathlib.PurePosixPath(entry.filename).name
        match = re.fullmatch(r'(.+?) (\d+) (.+)\.mp3', name, re.I)
        if not match:
            continue
        common, number, label = match.groups()
        key = re.sub('[^a-z0-9]', '', common.lower())
        rank = ('song' not in label.lower(), int(number), name)
        if key not in chosen or rank < chosen[key][0]:
            chosen[key] = (rank, entry, common, label)
    manifest = {}
    for key, (_, entry, common, label) in sorted(chosen.items()):
        filename = hashlib.sha256(key.encode()).hexdigest()[:24] + '.mp3'
        (dest / filename).write_bytes(archive.read(entry))
        manifest[key] = dict(file=filename, common=common, description=label,
                             source='Cornell Guide to Bird Sounds (v2025)')
    (dest / 'index.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
print(f'Imported {len(manifest)} species; songs preferred, calls used otherwise.')
