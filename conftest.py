"""Test-session path setup.

The package lives at MAMADROID/MaMadroid/MaMadroid, which is the layout the
original release used. That nested path means `import MaMadroid` fails from the
repo root, so the parent directory is added here rather than moving the tree.
"""

import sys
from pathlib import Path

PACKAGE_PARENT = Path(__file__).resolve().parent / "MAMADROID" / "MaMadroid"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))
