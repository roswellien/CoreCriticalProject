"""Omit Strider's authenticated interior only in detached photo/replay views.

Requires the existing Avatar fix. Original close/distance chassis and the full
attached interior roster must match; unknown trees and first-person views pass.
"""
from pathlib import Path
import argparse
from apply_avatar_detached_interior import HELPER


STRIDER_HELPER = HELPER.replace('avatar', 'strider').replace('Avatar', 'Strider')


def apply(path: Path):
    source = path.read_text()
    if 'bool strider_detached_interior_node' in source:
        raise RuntimeError('Strider interior filter already installed')
    anchor = 'OverrideScope override_begin(unsigned node)'
    gate = '!override_status_preview()&&avatar_detached_interior_node(node)'
    if source.count(anchor) != 1 or source.count(gate) != 1:
        raise RuntimeError('Expected the current Avatar-filter adapter')
    hooks = path.with_name('mfc_stage.hpp').read_text()
    if 'target==0x53f2e0&&(override_enabled()||photo_replay_detached_cam())' not in hooks:
        raise RuntimeError('Detached stock-view traversal hook is unavailable')
    source = source.replace(anchor, STRIDER_HELPER + '\n' + anchor)
    source = source.replace(gate,
        '!override_status_preview()&&(avatar_detached_interior_node(node)||strider_detached_interior_node(node))')
    path.write_text(source)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)
