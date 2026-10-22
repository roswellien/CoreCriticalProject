"""Authored audio exercises the authoring contract consumed by the C# installer."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import wave
import zipfile

from build_music_pack import build
from local_music import prepare_music


class MusicPackTests(unittest.TestCase):
    def test_build_extract_and_prepare_without_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [root / 'first.wav', root / 'second.wav']
            for source in sources:
                with wave.open(str(source), 'wb') as audio:
                    audio.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                    audio.writeframes(b'\0' * 80)
            before = [source.read_bytes() for source in sources]
            output = build(*sources, root / 'soundtrack.mw3pack')
            with self.assertRaises(FileExistsError):
                build(*sources, output)
            installed = root / 'relocated pack'
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read('pack.json'))
                for name, pin in manifest['files'].items():
                    content = archive.read(name)
                    self.assertEqual(len(content), pin['bytes'])
                    self.assertEqual(hashlib.sha256(content).hexdigest(), pin['sha256'])
                archive.extractall(installed)  # Only this test's authored archive.
            config = json.loads((installed / 'music/music.json').read_text())
            config['enabled'] = True
            result = prepare_music(installed, supplied=config, output=root / 'user cache')
            self.assertTrue(Path(result['MW34_MUSIC_PACK']).is_file())
            self.assertEqual(before, [source.read_bytes() for source in sources])
            with self.assertRaises(ValueError):
                build(sources[0], sources[0], root / 'duplicate.mw3pack')
            self.assertFalse((root / 'duplicate.mw3pack').exists())


if __name__ == '__main__':
    unittest.main()
