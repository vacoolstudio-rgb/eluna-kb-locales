#!/usr/bin/env python3
"""
Rebuild manifest.json for a language-pack release.

The app downloads `manifest.json` first and then each `lang_<code>.json`, checking the SHA-256
it was promised. A manifest whose hashes do not match the files is worse than no release: the
app rejects every pack and quietly stays on English, with nothing on screen to say why. So the
hashes are computed here, from the files as they are about to be uploaded, and never by hand.

Usage: tool/build-manifest.py <version tag>
"""
import hashlib
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(version: str) -> int:
    locales = OrderedDict()
    for path in sorted(ROOT.glob('lang_*.json')):
        code = re.fullmatch(r'lang_([\w-]+)\.json', path.name).group(1)
        blob = path.read_bytes()
        # Parsing here is the cheap guard that a broken edit never reaches a release.
        json.loads(blob)
        locales[code] = OrderedDict([
            ('file', path.name),
            ('sha256', hashlib.sha256(blob).hexdigest()),
            ('totalSize', len(blob)),
        ])

    manifest = OrderedDict([
        ('version', version),
        ('generatedAt', datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')),
        ('defaultLocale', 'en'),
        ('locales', locales),
    ])
    (ROOT / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(f'manifest.json: {len(locales)} locales, version {version}')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: build-manifest.py <version tag>', file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
