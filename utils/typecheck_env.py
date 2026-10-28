#!/usr/bin/env python3

# MODULE:    typecheck_env
#
# PURPOSE:   Create a virtual environment for type checkers (ty, pyrefly,
#            pyright) which provides the generated GRASS Python code
#
# SPDX-FileCopyrightText: 2026 GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later

"""Make the generated code of a GRASS build or installation visible to type checkers

The grass.lib package is generated during the build, so it is not in the source
tree. This script creates a virtual environment and adds a .pth file with the
location of the Python code of a built or installed GRASS to it. Type checkers
read the environment, so the project configuration does not need any
machine-specific paths.

Usage:

    python utils/typecheck_env.py
    python utils/typecheck_env.py --grass build/output/bin/grass --venv .venv
"""

import argparse
import shutil
import subprocess
import sys
import venv
from pathlib import Path

PTH_NAME = "grass_generated.pth"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--grass",
        default="grass",
        help="GRASS executable of the build or installation (default: grass on PATH)",
    )
    parser.add_argument(
        "--venv",
        type=Path,
        default=Path(".venv"),
        help="virtual environment to create or update (default: .venv)",
    )
    args = parser.parse_args()

    grass = shutil.which(args.grass)
    if not grass:
        sys.exit(f"GRASS executable '{args.grass}' not found")
    python_path = subprocess.run(
        [grass, "--config", "python_path"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not (Path(python_path) / "grass" / "lib").is_dir():
        sys.exit(f"No grass.lib in {python_path}, is GRASS built with Python support?")

    if not args.venv.exists():
        venv.create(args.venv, with_pip=False, symlinks=True)
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    venv_python = (
        args.venv / bin_dir / ("python.exe" if bin_dir == "Scripts" else "python")
    )
    site_packages = Path(
        subprocess.run(
            [
                str(venv_python),
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    (site_packages / PTH_NAME).write_text(python_path + "\n", encoding="utf-8")
    print(f"Added {python_path} to {args.venv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
