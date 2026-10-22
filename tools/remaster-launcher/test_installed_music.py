"""Authored PCM tests for installed music inputs, cache repair and source preservation."""
import hashlib
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from local_music import configuration, prepare_music


class InstalledMusicTests(unittest.TestCase):
    def test_external_sources_writable_cache_relocation_and_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'original music'
            source.mkdir()
            tracks = []
            hashes = {}
            for track in (2, 3):
                path = source / f'{track}.wav'
                with wave.open(str(path), 'wb') as audio:
                    audio.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                    audio.writeframes(struct.pack('<hh', track, -track) * 120)
                tracks.append(dict(cd_track=track, source=str(path)))
                hashes[path] = hashlib.sha256(path.read_bytes()).hexdigest()
            config = dict(schema_version=2, enabled=True, tracks=tracks)
            cache = root / 'user state' / 'music'
            bindings = prepare_music(root / 'absent-app-directory', supplied=config, output=cache)
            manifest = Path(bindings['MW34_MUSIC_PACK']).read_bytes()
            self.assertEqual(manifest[:16], b'MW3CD1\0\0' + struct.pack('<II', 1, 2))
            self.assertIn(str((cache / 'track02.wav').resolve()).encode(), manifest)
            self.assertFalse((root / 'absent-app-directory').exists())
            (cache / 'track02.wav').write_bytes(b'damaged cache')
            prepare_music(root, supplied=config, output=cache)
            self.assertEqual((cache / 'track02.wav').read_bytes(), Path(tracks[0]['source']).read_bytes())
            for path, digest in hashes.items():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_missing_decoder_missing_source_and_wrong_track_order_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(RuntimeError):
                configuration(root, dict(schema_version=2, enabled=True, tracks=[]))
            with self.assertRaises(RuntimeError):
                configuration(root, dict(schema_version=2, enabled=True, tracks=[
                    dict(cd_track=2, source='missing.flac'), dict(cd_track=3, source='other.flac')]))
            for name in ('2.flac', '3.flac'):
                (root / name).write_bytes(b'authored placeholder; decoder must be rejected before reading')
            with self.assertRaisesRegex(RuntimeError, 'preparation tool is missing'):
                configuration(root, dict(schema_version=2, enabled=True, tracks=[
                    dict(cd_track=2, source='2.flac'), dict(cd_track=3, source='3.flac')]))


if __name__ == '__main__':
    unittest.main()
