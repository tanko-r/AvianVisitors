#!/usr/bin/env python3
"""Import separate Cornell song and call examples, without relabeling sounds."""
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
        # Mixed song-and-call tracks are not pure examples of either type.
        song = bool(re.search(r'\bsongs?\b', label, re.I))
        call = bool(re.search(r'\bcalls?\b', label, re.I))
        kind = 'song' if song and not call else 'call' if call and not song else 'other'
        rank = (int(number), name)
        pair = (key, kind)
        if pair not in chosen or rank < chosen[pair][0]:
            chosen[pair] = (rank, entry, common, label)
    manifest = {}
    for (key, kind), (_, entry, common, label) in sorted(chosen.items()):
        filename = hashlib.sha256((key + ':' + kind).encode()).hexdigest()[:24] + '.mp3'
        (dest / filename).write_bytes(archive.read(entry))
        manifest.setdefault(key, {})[kind] = dict(file=filename, common=common, description=label,
                             type=kind, source='Cornell Guide to Bird Sounds (v2025)')
    (dest / 'index.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
print(f'Imported {len(manifest)} species: ' + ', '.join(f'{sum(kind in tracks for tracks in manifest.values())} {kind}' for kind in ('song', 'call', 'other')))
