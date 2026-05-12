#!/usr/bin/python3
# Recherche un script nommé 'lifecycle' (.py/.sh/.pl) dans src/lifecycle/.
# Avant d'exécuter lifecycle.py, vérifie s'il existe un script nommé
# {before.lifecycle}_{after.lifecycle}+extension et l'exécute à la place si trouvé.
# Si aucun script lifecycle n'est trouvé, retourne "not concerned".
import json
import os
import subprocess
import sys

sys.path.append('../lib')
import backend_utils as u


EXTENSIONS = ['', '.py', '.sh', '.pl']


def run_backend(script, content):
    ret = subprocess.run(script, input=content.encode(), capture_output=True)
    return {"returncode": ret.returncode, "stdout": ret.stdout.decode()}


def find_script(lifecycle_dir, names):
    for name in names:
        for ext in EXTENSIONS:
            candidate = lifecycle_dir + '/' + name + ext
            if os.path.isfile(candidate):
                return candidate
    return None


def main():
    lifecycle_dir = '../lifecycle'
    raw = sys.stdin.read()
    content = raw.replace("\n", "")

    try:
        data = json.loads(content)
        before = u.find_key(data, 'before.lifecycle')
        after = u.find_key(data, 'after.lifecycle')
        specific_name = before + '_' + after if before and after else None
    except (json.JSONDecodeError, Exception):
        specific_name = None

    script = None
    if specific_name:
        script = find_script(lifecycle_dir, [specific_name])

    if script is None:
        script = find_script(lifecycle_dir, ['lifecycle'])

    if script is None:
        print(u.returncode(0, "not concerned"))
        exit(0)

    ret = run_backend(script, content)
    print(ret['stdout'])
    exit(ret['returncode'])


if __name__ == '__main__':
    main()