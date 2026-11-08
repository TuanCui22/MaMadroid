"""Paths and defaults for MaMaDroid, resolved once.

The 1.x code hard-coded three absolute Windows paths inside ``mamadroid_main``:

    C:\\Users\\thanh\\Downloads\\MAMADROID\\MaMadroid\\MaMadroid
    C:\\Users\\thanh\\Downloads\\MAMADROID\\MaMadroid\\MaMadroid\\family
    C:\\Users\\thanh\\Downloads\\MAMADROID\\MaMadroid\\MaMadroid\\Families11.txt

That is why the repo only ever ran on one machine. Everything here resolves
relative to the package directory, so a clone runs anywhere, and every value can
be overridden by an environment variable for the case where the data lives
somewhere else.

Nothing here reads a file or creates a directory at import time: importing a
module should not have side effects.
"""

from __future__ import annotations

import os
from pathlib import Path

#: The package directory: this file lives in it.
PACKAGE_DIR = Path(__file__).resolve().parent

#: Where the reference data lives (class/package/family lists and the per-app
#: abstracted graphs shipped with the repo).
DATA_DIR = Path(os.environ.get("MAMADROID_DATA_DIR", PACKAGE_DIR)).expanduser()

#: Reference lists used to build the Markov state space.
CLASSES_FILE = Path(os.environ.get("MAMADROID_CLASSES", DATA_DIR / "classes.txt"))
PACKAGES_FILE = Path(os.environ.get("MAMADROID_PACKAGES", DATA_DIR / "Packages.txt"))
FAMILIES_FILE = Path(os.environ.get("MAMADROID_FAMILIES", DATA_DIR / "Families11.txt"))

#: Directories of pre-computed abstracted graphs, used when a run needs the
#: reference corpus rather than the APKs under test.
CLASS_GRAPHS_DIR = Path(os.environ.get("MAMADROID_CLASS_DIR", DATA_DIR / "class"))
PACKAGE_GRAPHS_DIR = Path(os.environ.get("MAMADROID_PACKAGE_DIR", DATA_DIR / "package"))
FAMILY_GRAPHS_DIR = Path(os.environ.get("MAMADROID_FAMILY_DIR", DATA_DIR / "family"))

#: Default JVM heap for the androguard/dex2jar path.
DEFAULT_MEMORY = os.environ.get("MAMADROID_MEMORY", "2G")


def require(path: Path, what: str) -> Path:
    """Return the path, or raise with a message that says how to fix it.

    A missing reference file used to surface as a bare FileNotFoundError deep in
    a loop, after the APK conversion had already run for several minutes.
    """
    if not path.exists():
        raise FileNotFoundError(
            "%s not found at %s. Set the matching MAMADROID_* environment "
            "variable, or pass --data-dir." % (what, path))
    return path
