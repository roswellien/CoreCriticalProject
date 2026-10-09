"""Exact mapping-base causal controls and observed TEST undefined-site record."""
import hashlib,json,pathlib,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-data'
def sha(p):
 with pathlib.Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rep(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
def main(out):
 out=pathlib.Path(out).resolve();assert out.parent==BASE and not out.exists();previous=BASE/'preparation-r2';files={}
 for p,h in json.loads((previous/'pins.json').read_text())['files'].items():assert sha(p)==h,p;files[p]=h
 s=(previous/'composition.cpp').read_text()
 s=rep(s,'private:std::vector<DataRoute>data_routes_;','private:std::vector<DataRoute>data_routes_;std::vector<unsigned>undefined_sites_;')
 s=rep(s,' const auto&events()const{return events_;}',' unsigned char undefined_flag(){guard();require(s_.gpr.rip.dword==0x5ac41f,"Only source TEST undefined AF site");undefined_sites_.push_back(s_.gpr.rip.dword);return 0;}\n const auto&undefined_sites()const{return undefined_sites_;}\n const auto&events()const{return events_;}')
 s=rep(s,'owner->guard();require(owner->state().gpr.rip.dword==0x5ac41f,"Only original TEST undefined AF admitted");return 0;','return owner->undefined_flag();')
 main_source=(previous/'main_v2.inc').read_text()
 main_source=rep(main_source,'r.memory().protect({address&~4095U},Permissions::read|Permissions::write);','const auto base=address==entry?0x401000U:address&~4095U;r.memory().protect({base},Permissions::read|Permissions::write);')
 main_source=rep(main_source,'if(mode==8)r.memory().store<unsigned>({fd::game_iat},fdiv.original_game_word()^1);','if(mode==8)mutation(r,fd::game_iat,fdiv.original_game_word()^1);')
 main_source=rep(main_source,'if(mode==9)r.memory().store<unsigned>({0x5bb5a4},0);','if(mode==9)mutation(r,0x5bb5a4,0);')
 main_source=rep(main_source,'if(mode==11)r.memory().protect({0x9a1000},Permissions::read);','if(mode==11)r.memory().protect({0x5e0000},Permissions::read);')
 main_source=rep(main_source,'fresh_output(row/"data-routes.bin",','fresh_output(row/"undefined-events.bin",{reinterpret_cast<const std::byte*>(context.undefined_sites().data()),context.undefined_sites().size()*sizeof(unsigned)});\n  fresh_output(row/"data-routes.bin",')
 out.mkdir()
 for name in ('seed.hpp','observations.hpp'):shutil.copyfile(previous/name,out/name)
 shutil.copyfile(previous/'composition.cpp',out/'composition-ancestor.cpp');shutil.copyfile(previous/'main_v2.inc',out/'main-ancestor.inc')
 (out/'composition.cpp').write_text(s);(out/'main_v2.inc').write_text(main_source)
 report=dict(passed=True,State_bytes=3504,State_reseed_after_writer=False,scope='Explicit exact region bases in causal controls; no production semantics change',
  failed_attempt=str(BASE/'run-r1-O0'),positive_prefix_records_retained=24,complete_attempt=False,
  source_mutation_region=0x401000,game_RW_region=0x5e0000,raw_IAT_control_region=0x5bb000,
  TEST_undefined_AF='Zero native representative at only5AC41F, captured separately as one actual DWORD PC; no defined AF equivalence credit',whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for p in out.iterdir():files[str(p)]=sha(p)
 for p in (pathlib.Path(__file__).resolve(),previous/'report.json',previous/'pins.json'):files[str(p)]=sha(p)
 for p in (BASE/'run-r1-O0').rglob('*'):
  if p.is_file():files[str(p)]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])
