"""Apply pack-authored muzzle origins after additional chassis visuals."""
from pathlib import Path
import argparse


def apply(source):
    source = Path(source)
    edits = (
        ('mfc_stage.hpp', '#include "additional_chassis_stage.inc"',
         '#include "additional_chassis_stage.inc"\n #include "chassis_sockets_stage.inc"'),
        ('mfc_stage.hpp', 'if(chassis_target(target))return chassis_body(s,target,p,body);',
         'if(chassis_target(target))return chassis_body(s,target,p,body);\n  if(target==0x4b36e0)return chassis_socket_body(s,target,p,body);'),
        ('body_dispatch.hpp', '0x4b4a40U,', '0x4b36e0U,0x4b4a40U,'))
    pending = {}
    for name, old, new in edits:
        text = pending.get(name, (source / name).read_text())
        if new not in text:
            if text.count(old) != 1:
                raise ValueError('Socket adapter does not match source: ' + name)
            text = text.replace(old, new)
        pending[name] = text
    for name, text in pending.items():
        (source / name).write_text(text, encoding='utf-8')
    (source / 'chassis_sockets_stage.inc').write_bytes(
        (Path(__file__).parent / 'native-overrides/chassis_sockets_stage.inc').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)
