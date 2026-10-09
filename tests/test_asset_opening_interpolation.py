"""Full opening timeline checks using authored timestamps only."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/asset-inventory'))
from interpolate_opening_cinematic import check_grid


class OpeningInterpolationTests(unittest.TestCase):
    def test_complete_grid_accepts_mux_rounding_and_b_frame_packet_order(self):
        grid = [round(i / 30, 3) for i in range(5474)]
        grid[10], grid[11] = grid[11], grid[10]
        self.assertLess(check_grid(grid, 5474, 30), 0.001)

    def test_missing_final_hold_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Expected 5474'):
            check_grid([i / 30 for i in range(5473)], 5474, 30)

    def test_timestamp_gap_is_rejected(self):
        grid = [i / 30 for i in range(5474)]
        grid[2000] += 1 / 30
        with self.assertRaisesRegex(ValueError, 'timestamps'):
            check_grid(grid, 5474, 30)

    def test_wrong_rate_and_start_offset_are_rejected(self):
        for grid in ([i / 15 for i in range(5474)],
                     [i / 30 + 0.01 for i in range(5474)]):
            with self.assertRaisesRegex(ValueError, 'timestamps'):
                check_grid(grid, 5474, 30)


if __name__ == '__main__':
    unittest.main()
