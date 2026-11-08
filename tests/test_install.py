"""Parcours du script avec Git/Docker simulés, sans accès au démon réel."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('install.sh', 'compose.yaml', 'Dockerfile', '.env.example'):
            shutil.copy(ROOT / name, self.root / name)
        (self.root / '.git').mkdir()
        (self.root / 'volume-data').write_text('données à préserver')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'commands'
        mock = '''#!/usr/bin/env python3
import os, sys
from pathlib import Path
args = sys.argv[1:]
name = Path(sys.argv[0]).name
with open(os.environ['MOCK_LOG'], 'a') as f:
    f.write(name + ' ' + ' '.join(args) + '\\n')
def out(text): print(text)
if name == 'git':
    if args[:2] == ['status', '--porcelain']: out(os.getenv('MOCK_DIRTY', ''))
    elif args[0] == 'symbolic-ref': out('main')
    elif args[0] == 'rev-parse': out('origin/main')
    elif args[0] == 'config': out('origin' if args[-1].endswith('.remote') else 'refs/heads/main')
    elif args[0] == 'merge' and os.getenv('MOCK_DIVERGED'): sys.exit(1)
elif name == 'ss':
    if os.getenv('MOCK_OCCUPIED'): out('LISTEN')
elif name == 'ip': pass
elif name == 'sleep': pass
elif name == 'docker':
    if args[:2] == ['compose', 'version']: out(os.getenv('MOCK_VERSION', '2.26.1'))
    elif args[0] == 'info': sys.exit(1 if os.getenv('MOCK_DENIED') else 0)
    elif args[0] == 'inspect':
        out('true' if '.Running' in args[-2] else 'running ' + os.getenv('MOCK_HEALTH', 'healthy'))
    else:
        # Retirer les arguments globaux Compose.
        args = args[7:]
        if args == ['config', '--environment']:
            for line in Path('.env').read_text().splitlines():
                if line and not line.startswith('#'): out(line)
        elif args[:1] == ['ps']:
            if os.getenv('MOCK_RUNNING') or Path('started').exists(): out('test-container')
        elif args == ['up', '-d']:
            if os.getenv('MOCK_UP_FAIL'): sys.exit(1)
            Path('started').touch()
        elif args == ['build'] and os.getenv('MOCK_BUILD_FAIL'): sys.exit(1)
'''
        for name in ('docker', 'git', 'ss', 'ip', 'sleep'):
            p = self.bin / name
            p.write_text(mock)
            p.chmod(0o755)
        self.env = dict(os.environ, PATH=f'{self.bin}:/usr/bin:/bin', MOCK_LOG=str(self.log))

    def run_install(self, mode='install', answers='\n\n10.20.30.40\n', **env):
        result = subprocess.run(['bash', 'install.sh', mode], cwd=self.root,
                                env=dict(self.env, **env), input=answers,
                                text=True, capture_output=True, timeout=10)
        self.assertEqual((self.root / 'volume-data').read_text(), 'données à préserver')
        commands = self.log.read_text() if self.log.exists() else ''
        self.assertNotIn('down -v', commands)
        return result, commands

    def existing(self):
        content = 'MIJOTE_BIND=127.0.0.1\nMIJOTE_PORT=8123\nMIJOTE_ALLOWED_ORIGINS=https://example.test\nMIJOTE_SECURE_COOKIE=true\n'
        (self.root / '.env').write_text(content)
        return content

    def test_install_and_rerun_preserve_configuration_and_data(self):
        result, commands = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = (self.root / '.env').read_text()
        self.assertIn('MIJOTE_PORT=8095', content)
        self.assertIn('http://10.20.30.40:8095', content)
        self.assertEqual((self.root / '.env').stat().st_mode & 0o777, 0o600)
        result, commands = self.run_install(answers='', MOCK_RUNNING='1', MOCK_OCCUPIED='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / '.env').read_text(), content)

    def test_existing_https_preserved(self):
        content = self.existing()
        result, _ = self.run_install(answers='')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / '.env').read_text(), content)
        self.assertIn('https://example.test', result.stdout)

    def test_invalid_port(self):
        result, commands = self.run_install(answers='70000\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / '.env').exists())
        self.assertNotIn(' build', commands)

    def test_public_address_refused(self):
        result, _ = self.run_install(answers='\n\n8.8.8.8\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / '.env').exists())

    def test_occupied_port(self):
        result, commands = self.run_install(MOCK_OCCUPIED='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('occupé', result.stderr)
        self.assertNotIn(' build', commands)

    def test_docker_permission_and_compose_version(self):
        for env in ({'MOCK_DENIED': '1'}, {'MOCK_VERSION': '1.29.2'}):
            with self.subTest(env=env):
                result, _ = self.run_install(**env)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / '.env').exists())

    def test_update_dirty_refuses_fetch(self):
        self.existing()
        result, commands = self.run_install('update', answers='', MOCK_DIRTY=' M README.md')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('git fetch', commands)

    def test_update_fast_forward(self):
        content = self.existing()
        result, commands = self.run_install('update', answers='OUI\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('git merge --ff-only FETCH_HEAD', commands)
        self.assertEqual((self.root / '.env').read_text(), content)

    def test_update_divergence_stops_before_build(self):
        self.existing()
        result, commands = self.run_install('update', answers='OUI\n', MOCK_DIVERGED='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(' build', commands)

    def test_uninstall_cancel_and_confirm(self):
        content = self.existing()
        result, commands = self.run_install('uninstall', answers='\n')
        self.assertEqual(result.returncode, 0)
        self.assertNotIn(' down', commands)
        result, commands = self.run_install('uninstall', answers='DESINSTALLER\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn(' down\n', commands)
        self.assertEqual((self.root / '.env').read_text(), content)

    def test_build_startup_and_health_failures(self):
        self.existing()
        for env in ({'MOCK_BUILD_FAIL': '1'}, {'MOCK_UP_FAIL': '1'},
                    {'MOCK_HEALTH': 'unhealthy'}, {'MOCK_HEALTH': 'starting'}):
            with self.subTest(env=env):
                result, _ = self.run_install(answers='', **env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Erreur', result.stderr)


if __name__ == '__main__':
    unittest.main()
