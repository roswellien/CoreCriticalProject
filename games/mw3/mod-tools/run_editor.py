"""Entry point for the MechWarrior 3 Map & Mission Editor.

Usage:
  python run_editor.py [--operation c1] [--mission c1m1] [--game-root MW3]
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from editor.ui.main_window import MainWindow


def main():
    parser = argparse.ArgumentParser(description="MechWarrior 3 Map & Mission Editor")
    parser.add_argument("--operation", default="c1", help="Operation ID (e.g. c1, c2, c3, c4, c4b, t1)")
    parser.add_argument("--mission", default="c1m1", help="Mission ID (e.g. c1m1, c1m2, c1ia1)")
    parser.add_argument("--game-root", default="MW3", help="Path to base MW3 installation folder")
    args = parser.parse_args()

    app = MainWindow(game_root=Path(args.game_root), initial_op=args.operation, initial_mission=args.mission)
    app.mainloop()


if __name__ == "__main__":
    main()
