"""Test configuration for pytest."""

import sys
from pathlib import Path

# Add the source directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
