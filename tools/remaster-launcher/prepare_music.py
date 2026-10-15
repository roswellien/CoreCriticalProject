"""Prepare configured local music for native launchers; never launch the game."""
from pathlib import Path
import sys
from local_music import prepare_music

if __name__=='__main__':
    try:
        prepare_music(Path(__file__).resolve().parents[2])
    except (RuntimeError,OSError,ValueError) as error:
        print('ERROR: '+str(error),file=sys.stderr)
        raise SystemExit(2)
