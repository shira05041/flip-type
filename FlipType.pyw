"""Entry point: double-click (or run with pythonw) to start FlipType in the tray."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fliptype.app import main

main()
