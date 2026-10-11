"""116 whole persistent game source model, no candidate AFTER seed."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'tools/m4-container-source/compare_connected.py';assert not p.exists();s=(ROOT/'tools/m4-fs-source/compare_connected.py').read_text()
def one(a,b):
 global s
 assert s.count(a)==1,a[:90];s=s.replace(a,b)
s=s.replace("ROOT/'reports/m4-fs-source'/name","ROOT/'reports/m4-container-source'/name").replace("ROOT/'tools/m4-fs-source/game_model.py'","ROOT/'tools/m4-container-source/game_model.py'").replace('native109','native116').replace('selected109','selected116').replace('persistent109','persistent116').replace('entire35pages','entire37pages')
one('0x731000,0x5f498000)','0x731000,0x5f498000,0x736000,0x5f4cc000)')
one("def equal(a,b,label):need(len(a)==len(b)and a==b,label+' '+str(first_diff(a,b)))","def equal(a,b,label):\n if len(a)!=len(b)or a!=b:raise ValueError(label+' '+str(first_diff(a,b)))")
one("  def initial_page(p):","  mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())\n  def initial_page(p):\n   if p==0x5f4cc000:\n    result=bytearray(4096)\n    for sec in mfc.sections:\n     lo=max(p,mfc.image_base+sec['virtual_address']);hi=min(p+4096,mfc.image_base+sec['virtual_address']+sec['raw_size'])\n     if hi>lo:offset=sec['raw_offset']+lo-mfc.image_base-sec['virtual_address'];result[lo-p:hi-p]=mfc.data[offset:offset+hi-lo]\n    return bytes(result)")
one("ROOT/'reports/m4-fs-source/original-validation-r1/report.json','a419e9a7819ba38077621efdda6da5440c0f00042c6c492d7dc672ebeab632b4'","ROOT/'reports/m4-container-source/original-validation-r1/report.json','4012b8c62c821131469e012f1e10ba31b621c524c6b0a9b042d5150dd2f3067b'")
one("+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots=","+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes());roots=")
one("ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json'","ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json'")
s=s.replace('o[145636:288996]','o[153828:305380]').replace('o[2276:145636]','o[2276:153828]').replace("len(expected_callbacks)==81,'All81","len(expected_callbacks)==88,'All88")
p.write_text(s)
