import sys
import os

# Ensure the project root is on the path for all tests.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import configure_logging

configure_logging()
