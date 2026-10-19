"""Install format-aware full-resolution BGRA capture without changing rendering."""
from pathlib import Path
import argparse
import shutil

OVERRIDES = Path(__file__).parent / 'native-overrides'


def apply(source: Path):
    path = source / 'vk_scene.hpp'
    text = path.read_text()
    reference = (OVERRIDES / 'vk_scene.hpp').read_text()
    end = '    // Enhanced settings are explicit;'
    method = '    void capture_fullres_bgra('
    replacement = reference[reference.index(method):reference.index(end)]
    old = next((m for m in (method, '    void capture_fullres_raw_rgba(') if m in text), None)
    if text.count(end) != 1 or '    void capture_fullres_rgb(' not in text:
        raise RuntimeError('Expected the composed photo capture renderer')
    if old:
        text = text[:text.index(old)] + replacement + text[text.index(end):]
    else:
        text = text.replace(end, replacement + end, 1)
    include = '#include "capture_pixels.hpp"'
    if include not in text:
        if text.count('#pragma once') != 1:
            raise RuntimeError('Expected one renderer include guard')
        text = text.replace('#pragma once', '#pragma once\n' + include, 1)
    path.write_text(text)
    path = source / 'photo_replay_stage.inc'
    text = path.read_text()
    if 'capture_fullres_raw_rgba(' not in text and 'capture_fullres_bgra(' not in text:
        raise RuntimeError('Expected one photo/video capture call')
    path.write_text(text.replace('capture_fullres_raw_rgba(', 'capture_fullres_bgra('))
    shutil.copyfile(OVERRIDES / 'capture_pixels.hpp', source / 'capture_pixels.hpp')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source.resolve(strict=True))
