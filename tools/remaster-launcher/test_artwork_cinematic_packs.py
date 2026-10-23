import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from build_ui_packs import build as ui
from build_cinematic_pack import build as cinema


class PackAuthoringTests(unittest.TestCase):
    def verify(self, path):
        with zipfile.ZipFile(path) as archive:
            manifest=json.loads(archive.read('pack.json'))
            self.assertEqual(set(archive.namelist()),set(manifest['files'])|{'pack.json'})
            for name,pin in manifest['files'].items():
                content=archive.read(name)
                self.assertEqual(len(content),pin['bytes'])
                self.assertEqual(hashlib.sha256(content).hexdigest(),pin['sha256'])

    def test_artwork_sources_and_exclusive_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sprites=root/'sprites';sprites.mkdir()
            source=sprites/'0123456789abcdef.rgba'
            content=struct.pack('<4sII4f4B',b'MW3H',1,1,0,0,1,1,0,0,0,255)
            source.write_bytes(content)
            bg=root/'background';bg.write_bytes(struct.pack('<8sIIII3B',b'MWHDBG1\0',1,1,1,1,0,0,0))
            output=root/'menu.mw3pack'
            ui('menu',sprites,bg,'',output);self.verify(output)
            with zipfile.ZipFile(output) as archive:
                payload=json.loads(archive.read('pack.json'))['native_payload']
                self.assertEqual(payload['required_capabilities'], {'ui-artwork':1})
            self.assertEqual(content,source.read_bytes())
            with self.assertRaises(FileExistsError):ui('menu',sprites,bg,'a'*64,output)
            with self.assertRaises(ValueError):ui('hud',sprites,bg,'a'*64,root/'bad.mw3pack')
            source.write_bytes(content[:-1])
            with self.assertRaises(ValueError):ui('hud',sprites,None,'a'*64,root/'truncated.mw3pack')

    def test_cinematic_roles_sources_and_exclusive_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'authored.mp4';source.write_bytes(b'\0\0\0\x18ftypisom'+b'\0'*12)
            content=source.read_bytes()
            data=dict(id='test.bonus',name='Authored example',clips=[dict(id='bonus',title='Bonus',source=source.name,replaces=None)])
            description=root/'description.json';description.write_text(json.dumps(data))
            output=cinema(description,root/'bonus.mw3pack');self.verify(output)
            self.assertEqual(content,source.read_bytes())
            with self.assertRaises(FileExistsError):cinema(description,output)
            data['clips'][0]['replaces']='intro';description.write_text(json.dumps(data))
            with self.assertRaises(ValueError):cinema(description,root/'bad.mw3pack')


if __name__=='__main__':unittest.main()
