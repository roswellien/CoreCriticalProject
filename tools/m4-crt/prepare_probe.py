"""Extract four complete measured provider bodies to a private, closed RX pack."""
from pathlib import Path
import argparse,hashlib,json,struct
from recover_provider import PE,PROVIDER_SHA,ROOT,bind
BODIES=[(0x780014f8,28,'960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678'),(0x78004625,10,'9b66387e70a4c7ae6a23115f73296e1b72fac54610ee6db3966b843ac9dafbef'),(0x7800462f,6,'eb5afece8f5f8fe130abe78bd2cfbc4c94f0f86caf8621da8a7ad51a9e26e578'),(0x78004635,6,'9d67fcd948d000a76431acfa77f662559957af257c435e5f9d229c365d7ad7e4')]
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);o=Path(a.parse_args().out).resolve()
 if not o.is_relative_to(ROOT/'reports/m4-crt') or o.exists():raise ValueError('Fresh private CRT extraction required')
 p=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA);pages={0x78001000:bytearray(b'\xcc'*4096),0x78004000:bytearray(b'\xcc'*4096)};records=[]
 for addr,size,sha in BODIES:
  code=p.read(addr-p.base,size)
  if hashlib.sha256(code).hexdigest()!=sha:raise ValueError('Exact body source identity')
  section=[s for s in p.sections if s[0]<=addr-p.base and addr-p.base+size<=s[0]+min(s[1],s[2])]
  if len(section)!=1 or section[0][4]&0xe0000000!=0x60000000:raise ValueError('Exact raw RX provider source')
  page=addr&~4095;pages[page][addr-page:addr-page+size]=code;records.append({'address':addr,'size':size,'sha256':sha,'raw_offset':p.offset(addr-p.base,size)})
 glob=p.read(0x38ee8,12);gs=[s for s in p.sections if s[0]<=0x38ee8 and 0x38ef4<=s[0]+min(s[1],s[2])]
 if glob!=bytes(12) or len(gs)!=1 or gs[0][4]&0xe0000000!=0xc0000000:raise ValueError('Exact raw RW zero globals')
 pack=b'MW4CRPK1'+struct.pack('<I',2)+b''.join(struct.pack('<II',base,1)+bytes(data) for base,data in pages.items())
 o.mkdir(parents=True);(o/'provider-pages.bin').write_bytes(pack);sha=hashlib.sha256(pack).hexdigest()
 (o/'probe_spec.hpp').write_text('#pragma once\nnamespace mw34::m4_crt_probe { inline constexpr auto pack_sha="'+sha+'"; }\n')
 report={'passed':True,'scope':'Four complete staged CRT bodies only; no DLL load/game execution','provider':bind(p.path),'bodies':records,'pages':list(pages),'globals':{'address':0x78038ee8,'size':12,'raw_offset':p.offset(0x38ee8,12),'source_hex':glob.hex(),'section':gs[0]},'pack':bind(o/'provider-pages.bin'),'sources':[bind(__file__),bind(ROOT/'tools/m4-crt/recover_provider.py')],'whole_M4_complete':False}
 (o/'report.json').write_text(json.dumps(report,indent=2)+'\n');(o/'pins.json').write_text(json.dumps({'files':{str(x.resolve()):bind(x)['sha256'] for x in [*o.iterdir(),p.path,Path(__file__),ROOT/'tools/m4-crt/recover_provider.py']}},indent=2)+'\n')
 print('Exact private four-body CRT extraction passed')
if __name__=='__main__':main()
