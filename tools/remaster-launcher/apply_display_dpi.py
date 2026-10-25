"""Apply the native process DPI contract to a fresh private host source copy."""
from pathlib import Path
import argparse


def apply(host):
    host = Path(host)
    main = host / 'main_v2.inc'
    text = main.read_text(encoding='utf-8')
    include = '#include "observations.hpp"'
    start = 'try{\n mw34::texture_diagnostics::hardware_summary();'
    if text.count(include) != 1 or text.count(start) != 1:
        raise ValueError('Native entry/DPI initialization source contract changed')
    if 'require_native_coordinates' in text:
        raise ValueError('DPI contract already applied; use a fresh host copy')
    root = Path(__file__).resolve().parents[2]
    for name in ('display_dpi.hpp', 'native_host.manifest'):
        dest = host / 'graphics' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((root / 'runtime/graphics' / name).read_bytes())
    text = text.replace(include, include + '\n#include "graphics/display_dpi.hpp"')
    text = text.replace(start, 'try{\n mw34::display::require_native_coordinates();\n'
                        ' if(argc==2&&std::string(argv[1])=="--check-display-dpi")return 0;\n'
                        ' mw34::texture_diagnostics::hardware_summary();')
    main.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
