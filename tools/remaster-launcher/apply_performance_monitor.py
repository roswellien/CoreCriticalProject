"""Install the authored presentation monitor in a reviewed native host snapshot."""
import argparse
from pathlib import Path
import shutil


def apply(host: Path):
    renderer = host / 'vk_scene.hpp'
    text = renderer.read_text()
    old_start = '    // Optional host performance overlay ('
    replacement = '    using PerfOverlay = mw34::performance::Overlay;\n    PerfOverlay overlay;'
    if replacement not in text:
        if text.count(old_start) != 1 or text.count('    } overlay;') != 1:
            raise RuntimeError('Expected exactly one reviewed legacy performance overlay')
        start = text.index(old_start)
        end = text.index('    } overlay;', start) + len('    } overlay;')
        if 'FPS %.1f  AVG %.1fMS  MAX %.1fMS' not in text[start:end]:
            raise RuntimeError('Unexpected legacy overlay implementation')
        text = text[:start] + replacement + text[end:]
    include = '#include "performance_monitor.hpp"\n'
    if include not in text:
        if text.count('#pragma once\n') != 1:
            raise RuntimeError('Expected renderer header guard')
        text = text.replace('#pragma once\n', '#pragma once\n' + include, 1)
    hud = host / 'gpu_hud.inc'
    gpu = hud.read_text()
    old = 'buf(size_t(w)*24,0);ov.draw(buf.data(),w,24);'
    new = 'buf(size_t(w)*ov.buffer_height,0);ov.draw(buf.data(),w,ov.buffer_height);'
    if new not in gpu:
        if gpu.count(old) != 1:
            raise RuntimeError('Expected one reviewed GPU overlay buffer')
        gpu = gpu.replace(old, new)
    # Validate both adapters before changing either.
    renderer.write_text(text)
    hud.write_text(gpu)
    source = Path(__file__).parent / 'native-overrides' / 'performance_monitor.hpp'
    if source.resolve() != (host / source.name).resolve():
        shutil.copyfile(source, host / source.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source)
