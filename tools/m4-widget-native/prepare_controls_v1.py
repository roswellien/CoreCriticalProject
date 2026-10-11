"""Prepare eight meaningful current-widget refusal seams without launching.

All positive widget bodies and service semantics are reused unchanged. Each
process starts with its own admitted image and actual registry bootstrap;
authored fault inputs precede the attempted root. Retained snapshots bound the
observable retry claim, including whole game/stack/TIB and provider exports.
"""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()

def main(name):
    out = R / 'reports/m4-widget-native' / name
    assert not out.exists(); out.mkdir()
    parent_path = R / 'reports/m4-widget-native/fixture-preparation-r16/report.json'
    assert sha(parent_path) == '58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401'
    parent = json.loads(parent_path.read_bytes()); assert parent['passed']
    files = dict(parent['files']); files[str(parent_path)] = sha(parent_path)
    for path, identity in files.items(): assert sha(path) == identity
    fixture = (parent_path.parent / 'fixture.cpp').read_text()
    fixture = fixture.replace('need(argc==7,"worker game CRT MFC MSVCP fresh-output independent-review-sha")','need(argc==8,"worker game CRT MFC MSVCP fresh-output independent-review-sha control-mode")')
    start = fixture.index(' W::Component component(')
    end = fixture.index(' }catch(const std::exception&e)', start)
    replacement = r''' W::Component component(r,services,input,&Writer::sink,&writer);
 const unsigned mode=unsigned(std::stoul(argv[7]));need(mode>=1&&mode<=8,"Finite eight authored widget fault inputs");
 auto&s=*reinterpret_cast<State*>(r.remill_state().data());
 auto protect_image=[&](unsigned address,Permissions permission){for(const auto&region:r.image_metadata().mapped_regions)if(address>=region.start.value&&std::uint64_t(address)<std::uint64_t(region.start.value)+region.size){r.memory().protect(region.start,permission);return;}throw std::runtime_error("Fault input must lie in one actual admitted image region");};
 if(mode==1)s.addr.ds_base.dword=4;
 if(mode==2){s.aflag.df=1;r.cpu().eflags|=0x400;s.rflag.flat|=0x400;}
 if(mode==3){protect_image(0x5bb070,Permissions::read|Permissions::write);r.memory().store<unsigned>({0x5bb070},0);protect_image(0x5bb070,Permissions::read);}
 if(mode==4){protect_image(0x40e250,Permissions::read|Permissions::write);auto b=r.memory().load<std::uint8_t>({0x40e250});r.memory().store<std::uint8_t>({0x40e250},b^1);protect_image(0x40e250,Permissions::read|Permissions::execute);}
 if(mode==5)protect_image(0x5f4d78,Permissions::read);
 if(mode==6)r.memory().protect({0x20001000},Permissions::read);
 if(mode==7)r.memory().protect(r.fs_base(),Permissions::read);
 const unsigned target=mode==8?0x40ef50:0x40e250;
 writer.prefix="control/";whole_current_game(r,writer,"authored-before");component.checkpoint("authored-before");
 W::HostBoundary hardware{};bool refused{};std::string reason;
 try{component.execute(target,hardware);}catch(const std::exception&e){refused=true;reason=e.what();}
 need(refused&&r.poisoned()&&!reason.empty(),"Actual required widget seam refused and Runtime poisoned");writer.bytes("refusal.txt",reason.data(),reason.size());writer.bytes("caller-hardware.bin",&hardware,sizeof(hardware));
 const auto captured_calls=r.calls().size();
 writer.prefix="retry-before/";whole_current_game(r,writer,"runtime");component.checkpoint("component");registry.dump(&Writer::sink,&writer);
 W::HostBoundary retry{};bool retry_refused{};
 try{component.execute(target,retry);}catch(const std::exception&e){retry_refused=true;writer.bytes("retry-reason.txt",e.what(),std::strlen(e.what()));}
 writer.prefix="retry-after/";whole_current_game(r,writer,"runtime");component.checkpoint("component");registry.dump(&Writer::sink,&writer);
 need(retry_refused&&r.poisoned()&&r.calls().size()==captured_calls,"Same poisoned Runtime cannot advance on retry");
 writer.prefix="control/";writer.bytes("retry-hardware.bin",&retry,sizeof(retry));
 writer.prefix="cleanup/";W::HostBoundary cleanup{};component.cleanup_fonts(cleanup);writer.bytes("font-caller-hardware.bin",&cleanup,sizeof(cleanup));registry.finish();registry.dump(&Writer::sink,&writer);whole_current_game(r,writer,"after");
 const std::array<unsigned,8>status{1,mode,unsigned(refused),unsigned(retry_refused),unsigned(r.poisoned()),unsigned(captured_calls),unsigned(r.calls().size()),1};writer.bytes("status.bin",status.data(),sizeof(status));return 0;
'''
    fixture = fixture[:start] + replacement + fixture[end:]
    assert 'std::array<unsigned,8>status{1,mode' in fixture
    for leaf in ('inherited_main.cpp','widget_bindings.hpp','contiguous-registration-spans.json'):
        payload = (parent_path.parent / leaf).read_bytes(); (out / leaf).write_bytes(payload)
    (out / 'fixture.cpp').write_text(fixture)
    for path in out.iterdir(): files[str(path.resolve())] = sha(path)
    files[str(Path(__file__).resolve())] = sha(__file__)
    report = dict(parent)
    report.update(passed=True, scope='Eight authored current widget fault inputs and observable unchanged-poisoned retries; build-only recipe', parent_preparation_sha256=sha(parent_path), files=files, control_modes=8, refusal_classes=['flat source DS','forward source DF','own raw GDI IAT preimage','physical literal source bytes','whole own object storage permission','whole actual stack permission','guest FS-head write permission','current ordered root route'], original_CPU_or_GDI_seeds=False, AFTER_machine_seed=False, native_executed=False, initializer_credit=0, whole_hidden_Runtime_private_retry_claim=False, whole_permissions_retry_claim=False)
    path = out / 'report.json'; path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(path=str(path),sha256=sha(path),passed=True,control_modes=8)))

if __name__ == '__main__': main(sys.argv[1])
