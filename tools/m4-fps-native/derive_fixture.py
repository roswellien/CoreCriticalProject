"""Only add the seventh route and real literal vsprintf import to the fixture."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];prior=R/'tools/m4-widget-native/fixture_v5.cpp';s=prior.read_text();changes=[]
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append([a,b])
replace('const std::array<unsigned,6>pcs{0x5a013c,0x5a063f,0x5a074b,0x517287,0x5ac11e,0x5ac580},slots{0x5bb070,0x5bb074,0x5bb068,0x5bb064,0x5bb52c,0x5bb530},targets{0x71f00010,0x71f00020,0x71f00030,0,0x78004a36,0};for(unsigned k=0;k<6;++k)','const std::array<unsigned,7>pcs{0x5a013c,0x5a063f,0x5a074b,0x517287,0x5ac11e,0x5ac580,0x5a2f68},slots{0x5bb070,0x5bb074,0x5bb068,0x5bb064,0x5bb52c,0x5bb530,0x5bb53c},targets{0x71f00010,0x71f00020,0x71f00030,0,0x78004a36,0,0x780230dd};for(unsigned k=0;k<7;++k)')
replace('status{1,unsigned(!failed),6,52,','status{1,unsigned(!failed),7,58,')
replace('entire six-root sequence','entire seven-root sequence')
q=R/'tools/m4-fps-native/fixture_v1.cpp';assert not q.exists();q.write_text(s);q=R/'tools/m4-fps-native/fixture-source-relations.json';assert not q.exists();q.write_text(json.dumps(dict(prior_source=str(prior),prior_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),changes=changes,AFTER_or_original_seed=False),indent=2)+'\n')
print('Prepared fixture exact changes',len(changes))
