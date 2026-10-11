"""Create additive120 proof readers from frozen accepted116 checks.

The current original producer paths are explicit. Only new order/page counts,
the one normal FS frame and the actual compiled observer span inventory change.
All allocation/string/import/numeric policies keep their accepted inputs.
"""
from pathlib import Path
import hashlib, json, re
ROOT=Path(__file__).resolve().parents[2]
T=ROOT/'tools/m4-next-source'
OLD=ROOT/'tools/m4-container-source'
ORIGINAL='reports/m4-vtable-original'
SOURCE='reports/m4-next-source'
pins={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)
def read(name):
 p=OLD/name;pins[str(p.resolve())]=sha(p);return p.read_text()
def write(name,s):
 p=T/name;assert not p.exists();compile(s,str(p),'exec');p.write_text(s);pins[str(p.resolve())]=sha(p)
def pages(s):
 return one(s,'0x736000,0x5f4cc000)','0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000)')
def original_paths(s):
 # Frozen parent receipts remain unchanged; final current producer receipts
 # are pinned when read rather than incorrectly asserted against parentSHA.
 for directory in ('original-validation-r1','original-preparation-r2','original-build-r2','original-execution-r1'):
  target={'original-preparation-r2':'preparation-r1','original-build-r2':'build-r1','original-execution-r1':'execution-r1','original-validation-r1':'validation-r1'}[directory]
  s=s.replace('reports/m4-container-source/'+directory,ORIGINAL+'/'+target)
  s=s.replace("BASE/'"+directory, "ORIG/'"+target)
 for h in ('4012b8c62c821131469e012f1e10ba31b621c524c6b0a9b042d5150dd2f3067b','fc3ce8ef54040236bced7072b3c121a0a7121c19ca81ef6e19ae0f54d5a06c49','8b1e7694bf3d9a651b729dc6740310c72c1b7409918de62c9411394da3021541','8a326c950272031da3423a4462a16ff9a408e1e9c83bb794cde67218ae3731bc'):
  s=s.replace(",'"+h+"'",'')
 return s
def current_sources(s):
 for old,new in (('original-game-source-r6','original-game-source-r1'),('connected-native-source-r4','connected-native-source-r1')):
  s=s.replace('reports/m4-container-source/'+old,SOURCE+'/'+new)
  s=s.replace("BASE/'"+old,"NEW/'"+new)
 s=s.replace(",'6f3f23261d711ce6a8a423b79d82410a2e75ab7e1ffcd6e27def7c27d0a408a5'",'')
 return s
def order_contract(s):
 s=s.replace('reports/m4-container-source/recovery-r3/instruction-contracts.json',SOURCE+'/recovery-r1/instruction-contracts.json')
 s=s.replace("BASE/'recovery-r3/instruction-contracts.json'", "NEW/'recovery-r1/instruction-contracts.json'")
 s=s.replace(",'3aeed69c05122c689a2f0951c2d49052db307beba917f5bcf756969aa7bbb09d'",",'a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108'")
 return s
def add_roots(s):
 path="'reports/m4-container-source/recovery-r3/container-roots.json'"
 return one(s,path,path+",'reports/m4-next-source/recovery-r1/fixed-roots.json'") if 'for path in(' in s else one(s,"+json.loads(pin(ROOT/"+path+").read_bytes());", "+json.loads(pin(ROOT/"+path+").read_bytes())+json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/fixed-roots.json').read_bytes());")
def names(s):
 return s.replace('116','120').replace('entire37pages','entire40pages').replace('all36 nonstack pages','all39 nonstack pages').replace('All35 actual original game pages','All40 actual original game pages').replace('entire37page','entire40page')

# A full native source machine, one bootstrap and all120 roots.
s=read('compare_connected_v4.py');s=pages(s);s=original_paths(s);s=order_contract(s)
s=s.replace("ROOT/'tools/m4-container-source/game_model.py'","ROOT/'tools/m4-next-source/game_model.py'")
s=one(s,"out=ROOT/'reports/m4-container-source'/name","out=ROOT/'reports/m4-next-source'/name")
s=add_roots(s)
s=one(s,"  for level in ('O0','O2'):","  for f in json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/FS-frame-contracts.json').read_bytes()):\n   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])\n  for level in ('O0','O2'):")
s=s.replace('153828','166116').replace('305380','329956')
s=s.replace('==88','==92').replace('All88','All92').replace('==42','==45').replace('All42','All45').replace('==14','==15').replace('==28','==30').replace('Actual14','Actual15').replace('and28 complete','and30 complete')
s=names(s);write('compare_connected.py',s)

# Actual original full-prefix source, inherited finite API and owner lifecycle.
s=read('compare_original_game_v6.py');s=original_paths(s);s=order_contract(s)
s=one(s,"BASE=ROOT/'reports/m4-container-source';PINS={}","BASE=ROOT/'reports/m4-container-source';NEW=ROOT/'reports/m4-next-source';ORIG=ROOT/'reports/m4-vtable-original';PINS={}")
s=one(s,'out=BASE/name','out=NEW/name');s=add_roots(s)
s=s.replace("ROOT/'tools/m4-container-source/game_model.py'","ROOT/'tools/m4-next-source/game_model.py'")
s=s.replace('153828','166116').replace('305380','329956').replace('307840','332416').replace('307328','331904')
s=s.replace('==88','==92').replace('All88','All92').replace('sequence_events==57','sequence_events==60')
s=names(s).replace('"""Original109 game prefixes','"""Original120 game prefixes');write('compare_original_game.py',s)

# Paired raw page policy. Six exactly authenticated observed-page hook spans.
s=read('compare_paired_policy_v4.py');s=pages(s);s=original_paths(s);s=current_sources(s);s=order_contract(s);s=add_roots(s)
s=one(s,"out=ROOT/'reports/m4-container-source'/name","out=ROOT/'reports/m4-next-source'/name")
s=s.replace('153828','166116').replace('305380','329956')
s=s.replace("ROOT/'reports/m4-container-review/observer-compiled-r3/report.json','9cd673ab15e2a6e06baa617a7d84ee341e85fb80d41531e253a7449933642e59'","ROOT/'reports/m4-vtable-original/observer-compiled-r1/report.json'")
s=one(s,"need([(r['PC'],r['width'])for r in observer_spans]==[(0x482b47,6),(0x482b4e,7),(0x482b8e,7)],'Only three exact observed-page original observer spans')","need(sorted((r['PC'],r['width'])for r in observer_spans)==[(0x4824a7,6),(0x4824ae,7),(0x4824ed,7),(0x482b47,6),(0x482b4e,7),(0x482b8e,7)],'Only six exact observed-page original observer spans')")
s=names(s);write('compare_paired_policy.py',s)

# Typed old/new116 owners retain exact original and current120 endpoints.
s=read('compare_owned_policy.py');s=original_paths(s);s=current_sources(s);s=order_contract(s)
s=one(s,"BASE=ROOT/'reports/m4-container-source';PINS={}","BASE=ROOT/'reports/m4-container-source';NEW=ROOT/'reports/m4-next-source';ORIG=ROOT/'reports/m4-vtable-original';PINS={}")
s=one(s,'out=BASE/name','out=NEW/name')
s=s.replace(",'0a852e3714e4b3dbc069f5a9b83e0107780c810796090b24537fd335e78c0e5a'",'').replace('/115/','/119/')
s=names(s);write('compare_owned_policy.py',s)

# FS join readers use complete own-branch original event records.
for filename in ('compare_FS_policy.py','validate_FS_observations_v2.py'):
 s=read(filename);s=current_sources(s);s=original_paths(s);s=order_contract(s)
 s=one(s,"BASE=ROOT/'reports/m4-container-source'","BASE=ROOT/'reports/m4-next-source';NEW=BASE;ORIG=ROOT/'reports/m4-vtable-original'")
 s=s.replace("ROOT/'tools/m4-container-source/game_model.py'","ROOT/'tools/m4-next-source/game_model.py'")
 s=s.replace("ROOT/'reports/m4-joint-startup116-root/execution-r1/report.json','0a852e3714e4b3dbc069f5a9b83e0107780c810796090b24537fd335e78c0e5a'","ROOT/'reports/m4-joint-startup120-root/execution-r1/report.json'")
 s=s.replace("ROOT/'reports/m4-container-review/observer-compiled-r3/report.json','9cd673ab15e2a6e06baa617a7d84ee341e85fb80d41531e253a7449933642e59'","ROOT/'reports/m4-vtable-original/observer-compiled-r1/report.json'")
 s=s.replace('==342','==360').replace('==504','==540').replace('==42','==45').replace('==57','==60').replace('==114','==120').replace('==168','==180').replace('==336','==360')
 s=s.replace('57 actual original','60 actual original').replace('42 literal native','45 literal native').replace('fourteen','fifteen').replace('14game','15game').replace('57 authentic','60 authentic').replace('all57 FS0','all60 FS0')
 s=s.replace('0x48f210)else','0x48f210,0x47f5f0)else')
 s=names(s);write(filename.replace('_v2',''),s)

out=ROOT/'reports/m4-next-source/proof-preparation-r1';assert not out.exists();out.mkdir()
pins[str(Path(__file__).resolve())]=sha(Path(__file__))
(out/'report.json').write_text(json.dumps(dict(passed=True,scope='Additive120 proof readers, syntax checked; no executions or new admission',source_model_sha256=sha(T/'game_model.py'),files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),tools=list(pins)[-7:])))
