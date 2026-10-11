"""Review the actual stronger Context, with all three initialized TLS cells."""
from pathlib import Path
BASE8=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v4.py')
program=BASE8.read_text()
edits8=[
 ("boundary=pin(folder/'connected_hardware_boundary.obj')", "boundary=pin(Path(build['workers']['O0']['path']).parent.parent/'connected_hardware_boundary.obj')"),
 ("br,brels=C.function(bs,bsec,'mfc_connected_hardware_call')", "labels=[s for s in bs.values()if s['name']=='mfc_connected_hardware_call'];assert len(labels)==1 and labels[0]['section']==1 and labels[0]['value']==0 and bsec[1]['flags']&0x20000000;br,brels=bsec[1]['bytes'],bsec[1]['relocations']"),
 ("TLS_names={'?observation", "TLS_names={'?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA','?observation"),
 ('  pin(PREVIOUS);pin(BASE);','  pin(BASE8);pin(PREVIOUS);pin(BASE);')
]
for a,b in edits8:assert program.count(a)==1,a;program=program.replace(a,b)
anchor="generator=generator.replace(values['old'],values['new'])"
assert program.count(anchor)==1
program=program.replace(anchor,anchor+'\ngenerator=generator.replace("    bridge_targets[symbol]=matches_c[0][0]","    TLS_relations(image,raw_c,matches_c[0][1],relocs_c,sections_c)\\n    bridge_targets[symbol]=matches_c[0][0]")')
exec(compile(program,str(BASE8),'exec'),globals())
