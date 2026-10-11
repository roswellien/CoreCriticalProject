"""Retain current BEFORE external pages with physical owning-section rights."""
from pathlib import Path
import hashlib
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).with_name('prepare_inputs.py')
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == 'c83a28afc1ee0883d4af46a2e9a893922927da03522aa291d09a779e0065c21c'
source = BASE.read_text(encoding='utf-8')
old = '2ef1668832203026a9796fda9415a5955b9d917e6d42ea0b9a76e33cd9c28f41'
assert source.count(old) == 1
source = source.replace(old, '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
anchor = "        direct = module(ROOT/'tools/m4-crt-allocation-root/run_v2.py','hypot_input_capture')"
assert source.count(anchor) == 1
source = source.replace(anchor, '''        providers = [CRT,
            PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL',
                '5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes()),
            PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',
                '91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())]
        def external_permission(page):
            owners = [image for image in providers if image.image_base <= page and
                      page+4096 <= image.image_base+image.size_of_image]
            assert len(owners) == 1, hex(page)
            image = owners[0]
            sections = [s for s in image.sections if s['virtual_address'] <= page-image.image_base <
                        s['virtual_address']+max(s['raw_size'],s['virtual_size'])]
            assert len(sections) == 1, hex(page)
            section = sections[0]
            return 2 if section['writable'] else 1 if section['executable'] else 0
''' + anchor)
old = '''                assert page in pages
                pages[page] = (pages[page][0],data[2276+i*4096:2276+(i+1)*4096])'''
new = '''                permission = pages[page][0] if page in pages else external_permission(page)
                pages[page] = (permission,data[2276+i*4096:2276+(i+1)*4096])'''
assert source.count(old) == 1
source = source.replace(old, new)
exec(compile(source, str(BASE), 'exec'), {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'})
