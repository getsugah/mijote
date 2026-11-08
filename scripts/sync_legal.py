"""Copy canonical legal notices into public build assets without modifying the app.

Copyright 2026 Getsugah
SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('LICENSE', 'NOTICE', 'COMMERCIAL.md', 'ASSETS.md',
         'THIRD_PARTY_NOTICES.txt', 'THIRD_PARTY_MANIFEST.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check copies without writing files.')
    args = parser.parse_args()
    destination = ROOT / 'frontend' / 'public' / 'legal'
    mismatches = []
    for name in FILES:
        content = (ROOT / name).read_bytes()
        target = destination / name
        if not target.is_file() or target.read_bytes() != content:
            if args.check:
                mismatches.append(name)
            else:
                destination.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    if mismatches:
        raise SystemExit('Copies des notices à synchroniser : ' + ', '.join(mismatches))
    print('Copies des notices vérifiées.' if args.check else 'Notices synchronisées pour les distributions frontend et Docker.')


if __name__ == '__main__':
    main()
