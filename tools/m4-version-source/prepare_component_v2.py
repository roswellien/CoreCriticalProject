"""Namespaced ten-body version component with genuine current Session services."""
from pathlib import Path
import hashlib,json,re,shutil,sys,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-version-source'/name;need(not out.exists(),'Fresh version component preparation');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact current physical component input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  pp=R/'reports/m4-version-source/preparation-r2/report.json';prior=read(pp,'137c214307a28b0e120b600ee53f14fcfacac0a72a7ef64b437178f3b3b17c75');liftp=R/'reports/m4-version-source/lifts-r1/report.json';lift=read(liftp,'25ffc35323d700254f64f42316985a50ac47abd93f282c918ee498a92ef3ed5a');servicep=R/'reports/m4-version-source/service-preparation-r4/report.json';service=read(servicep,'f35a730b53c0299e42d0955a89d29ce2e3289569f5a47fbad538344f55a0dbc5');service_build=read(R/'reports/m4-version-source/service-build-r4/build.json','9c9426e2e70b24c6b71ae102581c625a155ccc61acecc0c914dcc065904ea133');need(all(x['passed']for x in(prior,lift,service,service_build)),'Exact compiled concrete current service')
  oldp=R/'reports/m4-widget-native/preparation-r6/report.json';old=read(oldp,'714a5f0093a62e68911f78c93a07d34e4bd9f4b39e79e0931a4812bee6877ed9')
  relations=[];irs=[];entries=[];symbols=set()
  bodies=[dict(entry=v['entry'],IR=str(liftp.parent/(k+'-host.ll')),sha256=v['host_sha256'],prefix='mw34_onexit_game_')for k,v in lift['source_bodies'].items()]+[dict(entry=x['entry'],IR=x['component_IR'],sha256=x['component_sha256'],prefix='mw34_widget_game_')for x in old['namespace_relations']if x['entry']in(0x5ac110,0x5ac140)]
  for x in bodies:
   p=pin(x['IR'],x['sha256']);before=p.read_text();after=before.replace(x['prefix'],'mw34_version_game_');need(after.replace('mw34_version_game_',x['prefix'])==before,'Exact symbol-prefix-only literal relation');q=out/p.name;q.write_text(after);irs.append(str(q));entries.append(x['entry']);symbols|=set(re.findall(r'@(mw34_version_game_[A-Za-z0-9_]+)',after));relations.append(dict(entry=x['entry'],original_IR=str(p),original_sha256=sha(p),component_IR=str(q),component_sha256=sha(q),change='Exact symbol-prefix substitution only'))
  need(len(entries)==len(set(entries))==10,'Eight version plus two exact accepted literal onexit bodies')
  graphp=R/'reports/m4-remaining-service-source/preparation-r1/all-seven-graphs.json';graphs=read(graphp);rows={x['pc']:x for x in read(pp.parent/'source-rows.json',prior['files'][str((pp.parent/'source-rows.json').resolve())])}
  for e in(0x5ac110,0x5ac140):
   for x in graphs[str(e)]['instructions']:need(x['pc']not in rows or rows[x['pc']]==x,'Shared physical source row');rows[x['pc']]=x
  sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
  pin(R/'tools/analysis/pe.py');game_path=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game_path.read_bytes());physical=[]
  h=['#pragma once','#include "component.hpp"','#include <array>','namespace mw34::m4_version_native::literal {','struct Instruction {unsigned pc,size;bool call,ret;std::array<unsigned char,16>bytes;};','inline constexpr Instruction instructions[]{']
  for pc,x in sorted(rows.items()):
   b=bytes.fromhex(x['bytes']);off,_=pe.rva_range(pc-pe.image_base,len(b));need(pe.data[off:off+len(b)]==b,'Every entire physical component source row');physical.append(dict(pc=pc,file_offset=off,bytes_hex=b.hex()));h.append('{%d,%d,%s,%s,{%s}},'%(pc,len(b),str(x['mnemonic']=='call').lower(),str(x['mnemonic'].startswith('ret')).lower(),','.join(map(str,b))))
  h+=['};','inline const Instruction*instruction(unsigned pc){for(auto&v:instructions)if(v.pc==pc)return &v;return nullptr;}','struct Import {unsigned pc,slot,raw,projected;};','inline constexpr std::array<Import,4>imports{{{0x4eac9c,0x5bb748,0x1de90c,0x71f01010},{0x4eac96,0x5bb74c,0x1de8f6,0x71f01020},{0x4eac90,0x5bb750,0x1de8e4,0x71f01030},{0x5ac11e,0x5bb52c,0x1decb0,0x78004a36}}};','using Body=void*(*)(State*,unsigned,void*);']+['extern "C" void*mw34_version_game_f_%x_body(State*,unsigned,void*);'%e for e in entries]+['inline Body body(unsigned pc){switch(pc){']+['case %d:return mw34_version_game_f_%x_body;'%(e,e)for e in entries]+['default:return nullptr;}}','}'];(out/'literals.hpp').write_text('\n'.join(h)+'\n')
  bridges=[]
  for n in sorted(symbols):
   if '_direct_'in n:bridges.append('extern "C" void*%s(State*s,unsigned a,void*p){return mw34_version_game_call(s,a,p);}'%n)
   elif n.endswith('_undefined_8'):bridges.append('extern "C" std::uint8_t %s(){return 0;}'%n)
  (out/'bridges.inc').write_text('\n'.join(bridges)+'\n')
  for dst,src in [('component.hpp',R/'tools/m4-version-source/component_v1.hpp'),('component.cpp',R/'tools/m4-version-source/component_v1.cpp')]:shutil.copyfile(pin(src),out/dst)
  p=pin(R/'tools/m4-widget-native/native_api.s','692b17f008c0cdc69c9cc4ea57959df76f520d4913e40a49ee281e212f9e1e7a');s=p.read_text();s='.text\n'+s[s.index('.globl mw34_widget_hardware_call'):].replace('mw34_widget_','mw34_version_');(out/'caller_hardware.s').write_text(s)
  q=out/'physical-instruction-relations.json';q.write_text(json.dumps(physical,indent=2)+'\n')
  for p in out.iterdir():pin(p)
  pin(__file__);pin(R/'tools/m4-version-source/prepare_component_v1.py','1bfb9dbfe6862a0d09efd94f616f7e725819d9db0f31b4f9f6fe578aa23ba50e');pin(R/'tools/m4-version-source/derive_component_v2.py')
  report=dict(passed=True,scope='One real version Runtime route, ten literal bodies, actual VERSION.dll services and true MFC/onexit whole-buffer ownership; compile preparation only',IRs=irs,namespace_relations=relations,literal_bodies=10,instructions=len(rows),root=0x4af240,service_include=str(servicep.parent),service_build=str(R/'reports/m4-version-source/service-build-r4/build.json'),actual_VERSION_APIs=3,genuine_source_MFC_NULL_free_retained=True,native_query_pointer_same_owner=True,no_original_outputs_or_AFTER_seed=True,native_executed=False,original_executed=False,initializer_credit=0,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),bodies=10,instructions=len(rows))))
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
