import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

__DIR__ = os.path.dirname(os.path.abspath(__file__))
__PYTHONENV__ = '/../.venv/bin/python'

# Preload src/lib so backend_utils is resolvable when importing lifecycle module
sys.path.insert(0, os.path.join(__DIR__, '..', 'src', 'lib'))

_spec = importlib.util.spec_from_file_location(
    'lifecycle_bin',
    os.path.join(__DIR__, '..', 'src', 'bin', 'lifecycle.py'),
)
_lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lc)


class TestFindScript(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _touch(self, name):
        path = os.path.join(self.tmpdir, name)
        open(path, 'w').close()
        return path

    def test_finds_py_extension(self):
        self._touch('lifecycle.py')
        self.assertEqual(
            _lc.find_script(self.tmpdir, ['lifecycle']),
            os.path.join(self.tmpdir, 'lifecycle.py'),
        )

    def test_finds_sh_extension(self):
        self._touch('O_I.sh')
        self.assertEqual(
            _lc.find_script(self.tmpdir, ['O_I']),
            os.path.join(self.tmpdir, 'O_I.sh'),
        )

    def test_finds_pl_extension(self):
        self._touch('lifecycle.pl')
        self.assertEqual(
            _lc.find_script(self.tmpdir, ['lifecycle']),
            os.path.join(self.tmpdir, 'lifecycle.pl'),
        )

    def test_finds_no_extension(self):
        self._touch('lifecycle')
        self.assertEqual(
            _lc.find_script(self.tmpdir, ['lifecycle']),
            os.path.join(self.tmpdir, 'lifecycle'),
        )

    def test_specific_name_preferred_over_fallback(self):
        self._touch('O_I.py')
        self._touch('lifecycle.py')
        self.assertEqual(
            _lc.find_script(self.tmpdir, ['O_I', 'lifecycle']),
            os.path.join(self.tmpdir, 'O_I.py'),
        )

    def test_falls_back_to_second_name(self):
        self._touch('lifecycle.py')
        self.assertEqual(
            _lc.find_script(self.tmpdir, ['O_I', 'lifecycle']),
            os.path.join(self.tmpdir, 'lifecycle.py'),
        )

    def test_returns_none_when_not_found(self):
        self.assertIsNone(_lc.find_script(self.tmpdir, ['nonexistent']))

    def test_returns_none_on_empty_dir(self):
        self.assertIsNone(_lc.find_script(self.tmpdir, ['lifecycle']))

    def test_returns_none_on_empty_names(self):
        self._touch('lifecycle.py')
        self.assertIsNone(_lc.find_script(self.tmpdir, []))


class TestRunBackend(unittest.TestCase):

    def setUp(self):
        self._scripts = []

    def tearDown(self):
        for s in self._scripts:
            try:
                os.unlink(s)
            except OSError:
                pass

    def _make_script(self, body):
        fd, path = tempfile.mkstemp(suffix='.py', prefix='lc_test_')
        os.write(fd, ('#!/usr/bin/python3\n' + body).encode())
        os.close(fd)
        os.chmod(path, 0o755)
        self._scripts.append(path)
        return path

    def test_returncode_zero(self):
        script = self._make_script('print("ok")\n')
        self.assertEqual(_lc.run_backend(script, '')['returncode'], 0)

    def test_returncode_nonzero(self):
        script = self._make_script('import sys\nsys.exit(3)\n')
        self.assertEqual(_lc.run_backend(script, '')['returncode'], 3)

    def test_content_passed_via_stdin(self):
        script = self._make_script('import sys\nprint(sys.stdin.read().strip())\n')
        ret = _lc.run_backend(script, 'ping')
        self.assertEqual(ret['returncode'], 0)
        self.assertIn('ping', ret['stdout'])

    def test_stdout_captured_as_string(self):
        script = self._make_script('print("hello lifecycle")\n')
        ret = _lc.run_backend(script, '')
        self.assertIsInstance(ret['stdout'], str)
        self.assertIn('hello lifecycle', ret['stdout'])


class TestLifecycleBin(unittest.TestCase):
    """Integration tests: invoke lifecycle.py as a subprocess."""

    def run_backend(self, script, file):
        dir_ = os.getcwd()
        exe = dir_ + __PYTHONENV__
        with open(file, 'r') as fic:
            content = fic.read().replace('\n', '')
        os.chdir('../src/bin')
        ret = subprocess.run([exe, script], input=content.encode(), capture_output=True)
        os.chdir(dir_)
        return {'returncode': ret.returncode, 'stdout': ret.stdout.decode()}

    def test_lifecycle_concerned(self):
        """lifecycle.json: O→I transition, concerned backend → lifecycle script runs."""
        ret = self.run_backend('lifecycle.py', './files_ad_utils/lifecycle.json')
        self.assertEqual(ret['returncode'], 0)
        result = json.loads(ret['stdout'])
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], 'lifecycle.py')

    def test_lifecycle_notconcerned(self):
        """lifecycle-notconcerned.json: backend not concerned → not concerned."""
        ret = self.run_backend('lifecycle.py', './files_ad_utils/lifecycle-notconcerned.json')
        self.assertEqual(ret['returncode'], 0)
        result = json.loads(ret['stdout'])
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], 'not concerned')


if __name__ == '__main__':
    unittest.main()