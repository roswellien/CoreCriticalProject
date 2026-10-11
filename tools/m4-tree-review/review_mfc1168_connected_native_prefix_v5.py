"""Bind the explicitly compiled assembly object at its actual build-root path."""
from pathlib import Path
PARENT=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v4.py')
program=PARENT.read_text()
old="boundary=pin(folder/'connected_hardware_boundary.obj')"
assert program.count(old)==1
program=program.replace(old,"boundary=pin(Path(build['workers']['O0']['path']).parent.parent/'connected_hardware_boundary.obj')")
program=program.replace('  pin(PREVIOUS);pin(BASE);','  pin(PARENT);pin(PREVIOUS);pin(BASE);')
exec(compile(program,str(PARENT),'exec'),globals())
