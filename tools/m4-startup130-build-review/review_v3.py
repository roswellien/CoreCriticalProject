"""Bind the unchanged130 checks to the corrected final native19 build."""
from pathlib import Path
import importlib.util
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).with_name('review_v2.py')
spec = importlib.util.spec_from_file_location('frozen130_build_checks', parent)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
checks.PREP = checks.ROOT / 'reports/m4-joint-startup130/preparation-r2'
checks.PREPSHA = '060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c'
checks.NPREP = checks.ROOT / 'reports/m4-formatting-native/preparation-r19'
checks.NPSHA = '1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3'
checks.BUILD = checks.ROOT / 'reports/m4-joint-startup130/build-r2/build.json'
checks.BUILDSHA = '1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53'
checks.__file__ = str(Path(__file__).resolve())
frozen_common = checks.common


def common(name):
    result = frozen_common(name)
    result[2](parent)
    return result


checks.common = common
ROOT, PREP, NPREP, LLVM = checks.ROOT, checks.PREP, checks.NPREP, checks.LLVM
emit, machine, sha = checks.emit, checks.machine, checks.sha

if __name__ == '__main__':
    if sys.argv[1] == 'abi':
        checks.abi(sys.argv[2])
    elif sys.argv[1] == 'link':
        checks.link(*sys.argv[2:])
    else:
        raise ValueError(sys.argv[1])
