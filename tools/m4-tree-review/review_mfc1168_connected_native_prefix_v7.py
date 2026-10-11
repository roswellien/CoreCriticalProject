"""Include the component's own initialized TLS authority, also in O2 bridges."""
from pathlib import Path
PARENT7=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v6.py')
program=PARENT7.read_text()
anchor="exec(compile(program,str(PARENT6),'exec'),globals())"
addition=r'''
program=program.replace("TLS_names={'?observation", "TLS_names={'?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA','?observation")
program=program.replace("injection=", "generator=generator.replace(\"    bridge_targets[symbol]=matches_c[0][0]\",\"    TLS_relations(image,raw_c,matches_c[0][1],relocs_c,sections_c)\\n    bridge_targets[symbol]=matches_c[0][0]\")\ninjection=")
program=program.replace('  pin(PARENT6);pin(PARENT);pin(PREVIOUS);pin(BASE);','  pin(PARENT7);pin(PARENT6);pin(PARENT);pin(PREVIOUS);pin(BASE);')
'''
assert program.count(anchor)==1
program=program.replace(anchor,addition+anchor)
exec(compile(program,str(PARENT7),'exec'),globals())
