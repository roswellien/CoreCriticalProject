"""Per-movie stereo/mono admission using authored AVI metadata only."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/asset-inventory'))
from upgrade_cinematic_batch import contract


def fixture(channels, bits):
    align = channels * bits // 8
    fmt = {'format_tag': 1, 'channels': channels, 'sample_rate': 22050,
           'byte_rate': 22050 * align, 'block_align': align, 'bits_per_sample': bits}
    metadata = {'streams': [
        {'type': 'vids', 'handler': 'IV50', 'start': 0, 'rate': 15, 'scale': 1,
         'length': 3, 'video_format': {'width': 640, 'height': 480}},
        {'type': 'auds', 'start': 0, 'audio_format': fmt, 'sample_size': align,
         'rate': 22050 * align, 'scale': align, 'length': 4417,
         'observed_data_bytes': {'01wb': 4417 * align}}]}
    return metadata, {'frames': 3, 'audio': deepcopy(fmt)}


class CinematicBatchTests(unittest.TestCase):
    def test_mono_8_and_stereo_16_keep_original_pcm_contract_and_tail(self):
        for channels, bits, codec in [(1, 8, 'pcm_u8'), (2, 16, 'pcm_s16le')]:
            metadata, expected = fixture(channels, bits)
            result = contract(metadata, expected)
            self.assertEqual(result['codec'], codec)
            self.assertEqual(result['samples'], 4417)
            self.assertEqual(result['duration'], 4417 / 22050)

    def test_audio_offsets_and_inconsistent_pcm_bytes_rejected(self):
        for field, value in [('start', 1), ('observed_data_bytes', {'01wb': 100})]:
            metadata, expected = fixture(1, 8)
            metadata['streams'][1][field] = value
            with self.assertRaisesRegex(ValueError, 'contract'):
                contract(metadata, expected)

    def test_changed_video_identity_contract_rejected(self):
        for field, value in [('rate', 30), ('length', 2), ('handler', 'OTHER')]:
            metadata, expected = fixture(2, 16)
            metadata['streams'][0][field] = value
            with self.assertRaisesRegex(ValueError, 'contract'):
                contract(metadata, expected)


if __name__ == '__main__':
    unittest.main()
