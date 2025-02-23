import os
import sys
import subprocess
from pathlib import Path
import pytest

@pytest.fixture(scope="session", autouse=True)
def install_package():
    """Automatically install package in development mode before running tests."""
    project_root = Path(__file__).parent.parent
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(project_root)])
    except subprocess.CalledProcessError:
        # Fallback: add src directory to Python path
        src_path = str(project_root / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path) 