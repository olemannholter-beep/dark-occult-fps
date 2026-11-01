import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_set0_candle_bearer import export_all_set0_starter

OUTPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "assets", "models", "armor"))

if __name__ == "__main__":
    export_all_set0_starter(OUTPUT_DIR)
