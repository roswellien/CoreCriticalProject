"""Full-movie timeline and PCM rejection checks using authored metadata."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/asset-inventory'))
import upgrade_opening_cinematic as opening


class OpeningCinematicTests(unittest.TestCase):
    def test_complete_display_grid_and_missing_hold(self):
        grid = [f'{i / 15:.3f}' for i in range(opening.FRAMES)]
        self.assertLess(opening.verify_grid(grid, opening.FRAMES), 0.001)
        with self.assertRaisesRegex(ValueError, 'display frames'):
            opening.verify_grid(grid[:-1], opening.FRAMES)
        grid[1000] = str(1001 / 15)
        with self.assertRaisesRegex(ValueError, 'depart'):
            opening.verify_grid(grid, opening.FRAMES)

    def test_complete_audio_tail_and_offset_rejection(self):
        frames = [{'nb_samples': opening.SAMPLES, 'best_effort_timestamp_time': '0'}]
        self.assertEqual(opening.verify_audio_grid(frames, 22050, opening.SAMPLES), 0)
        frames[0]['nb_samples'] -= 7
        with self.assertRaisesRegex(ValueError, 'sample count'):
            opening.verify_audio_grid(frames, 22050, opening.SAMPLES)
        frames[0]['nb_samples'] += 7
        frames[0]['best_effort_timestamp_time'] = '0.01'
        with self.assertRaisesRegex(ValueError, 'timestamps'):
            opening.verify_audio_grid(frames, 22050, opening.SAMPLES)

    def test_pcm_rejects_truncated_audio(self):
        with patch.object(opening.subprocess, 'run', return_value=SimpleNamespace(stdout=b'\0' * 16)):
            with self.assertRaisesRegex(ValueError, 'PCM length'):
                opening.pcm(Path('authored.avi'), 'ffmpeg')

    def test_source_rejects_unknown_identity(self):
        with patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=82169804)), \
             patch.object(opening, 'digest_file', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                opening.check_source(Path('authored.avi'))


if __name__ == '__main__':
    unittest.main()
