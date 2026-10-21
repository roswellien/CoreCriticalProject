"""Launch the separate local alpha GPU playtest profile."""

import play_remaster

play_remaster.CONFIG = play_remaster.ROOT / "local/remaster/launcher-alpha-gpu-tests.json"

if __name__ == "__main__":
    print("Play MW3 - Alpha GPU Tests", flush=True)
    raise SystemExit(play_remaster.main())
