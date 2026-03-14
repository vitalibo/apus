import fileinput
import json
import subprocess  # noqa: S404
from pathlib import Path

MODULES = {}


def export_requirements(module):
    """Exports the dependencies of a given module in a format suitable for requirements.txt."""

    command = (
        f'uv export --package {module}',
        '--no-dev --no-header --no-editable --no-hashes --no-annotate --no-emit-workspace --format requirements-txt',
        "| sed 's/ ;.*//'",
        '| paste -sd "," -',
    )
    result = subprocess.run(' '.join(command), shell=True, check=True, stdout=subprocess.PIPE, text=True)  # noqa: S602
    return result.stdout.strip()


def refresh_requirements(root):
    """Refreshes the MODULES dictionary with the current dependencies of each module"""

    requirements = {}
    for module in root.iterdir():
        if module.is_dir() and module.name.startswith('apus-'):
            requirements[module.name.replace('-', '_')] = export_requirements(module.name)

    with fileinput.FileInput(__file__, inplace=True) as file:
        for line in file:
            if line == 'MODULES = {}\n':
                print(f'MODULES = {json.dumps(requirements, indent=4)}')  # noqa: T201
            else:
                print(line, end='')  # noqa: T201


def __getattr__(name):
    return MODULES[name]


if __name__ == '__main__':
    refresh_requirements(Path(__file__).parent.parent.parent.parent.parent)
