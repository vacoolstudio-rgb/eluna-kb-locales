#!/usr/bin/env python3
"""
Merge translated strings into the language packs.

Input is a flat text file, one entry per line, grouped by language:

    LANG ru
    health.title = Apple Health
    widget.late_few = задержка {{count}} дня

Keys are dotted paths under the pack's `ui` object; `LANG <code>` switches file. Writing a key
that already exists overwrites it, which is what a correction looks like.

Why a text format and not JSON: these files are edited in batches of a thousand lines and a
misplaced brace three languages ago is invisible, while a malformed line here names itself.
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def set_path(tree: dict, dotted: str, value: str) -> None:
    parts = dotted.split('.')
    node = tree
    for part in parts[:-1]:
        nxt = node.get(part)
        if not isinstance(nxt, dict):
            nxt = OrderedDict()
            node[part] = nxt
        node = nxt
    node[parts[-1]] = value


def main(patch_file: str) -> int:
    lang = None
    pending: "OrderedDict[str, list]" = OrderedDict()

    for raw in Path(patch_file).read_text(encoding='utf-8').splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith('#'):
            continue
        if line.startswith('LANG '):
            lang = line[5:].strip()
            pending.setdefault(lang, [])
            continue
        if ' = ' not in line:
            print(f'! skipped (no separator): {line[:60]}', file=sys.stderr)
            continue
        if lang is None:
            print('! a key appeared before any LANG line', file=sys.stderr)
            return 2
        key, value = line.split(' = ', 1)
        pending[lang].append((key.strip(), value.strip()))

    written = 0
    for lang, entries in pending.items():
        path = ROOT / f'lang_{lang}.json'
        if not path.exists():
            print(f'! no pack for {lang}', file=sys.stderr)
            return 2
        data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=OrderedDict)
        ui = data.setdefault('ui', OrderedDict())
        for key, value in entries:
            set_path(ui, key, value)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        written += len(entries)
        print(f'{lang}: {len(entries)} keys')

    print(f'total {written} keys across {len(pending)} languages')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: apply-translations.py <patch file>', file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
