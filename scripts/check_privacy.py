"""Check distributable project text for personal filesystem paths and private IPv4 addresses.

Local configuration, private data, caches and build outputs are intentionally excluded.
This targeted check complements review; it cannot identify every kind of personal data.
"""
from pathlib import Path
import os
import re


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', '.venv', 'node_modules', 'dist', 'data', 'backups', '__pycache__', '.pytest_cache'}
PATTERNS = [re.compile(r'/(?:home|Users)/[^/\s`]+/'),
            re.compile(r'[A-Za-z]:[\\/]Users[\\/][^\\/\s]+'),
            re.compile(r'(?<![\d.])(?:192\.168|10\.(?:\d{1,3})|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}(?![\d.])')]


def main():
    issues = []
    paths = []
    for directory, folders, files in os.walk(ROOT):
        folders[:] = [name for name in folders if name not in EXCLUDED]
        paths.extend(Path(directory) / name for name in files)
    for path in sorted(paths):
        if path.name == '.env' or path.name.startswith('.env.') and path.name != '.env.example':
            continue
        try:
            content = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(content.splitlines(), 1):
            # Network-security fixtures deliberately exercise synthetic private IPs.
            patterns = PATTERNS[:2] if 'tests' in path.relative_to(ROOT).parts else PATTERNS
            if any(pattern.search(line) for pattern in patterns):
                issues.append(f'{path.relative_to(ROOT)}:{number}')
    if issues:
        print('Chemin personnel ou adresse privée à examiner (contenu non affiché) :\n' + '\n'.join(issues))
        raise SystemExit(1)
    print('Confidentialité : aucun chemin personnel ni adresse IPv4 privée détecté dans les fichiers distribuables.')


if __name__ == '__main__':
    main()
