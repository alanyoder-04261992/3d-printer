#!/usr/bin/env python3
"""Start a new print project from projects/_template.

Usage:
    python3 tools/new_project.py "Door latch handle"

Creates projects/door-latch-handle/ with a README brief and a model.scad
starting point.
"""
import datetime
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "projects" / "_template"


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or not slugify(argv[0]):
        print(__doc__.strip())
        return 2
    name = argv[0].strip()
    dest = ROOT / "projects" / slugify(name)
    if dest.exists():
        print(f"{dest.relative_to(ROOT)} already exists")
        return 1
    shutil.copytree(TEMPLATE, dest)
    today = datetime.date.today().isoformat()
    for path in dest.iterdir():
        if path.is_file():
            text = path.read_text()
            path.write_text(text.replace("{{NAME}}", name).replace("{{DATE}}", today))
    print(f"Created {dest.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
