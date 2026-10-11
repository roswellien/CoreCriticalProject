"""Retain genuine producer and each-root BEFORE provider inputs additively."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';P=R/'reports/m4-widget-original/preparation-r3/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact unique derivation '+a[:90])
 return s.replace(a,b,1)
parent=json.loads(P.read_text());p=T/'prepare_v2.py'
if sha(P)!='86f4a947c7cc870a0519ab9a49128beb751174718ebdf73713a1f9535d463172' or sha(p)!=parent['files'][str(p.resolve())]:raise ValueError('Immutable preparation source')
s=p.read_text()
anchor=" ref=one(ref,'        lockit_allocation_count=0;', '        widget_resource_count=0;std::memset(widget_resources,0,sizeof(widget_resources));\\n        lockit_allocation_count=0;')"
addition='''
 producer='''+"'''"+'''        out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-count.bin",&registry_API_count,4);out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));
        require(registry_API_count<=256,"Bounded actual source producer API ledger");
        for(unsigned ai=0;ai<registry_API_count;++ai)if(registry_API_ledger[ai].kind==0&&registry_API_ledger[ai].after.eax){const auto stem="bootstrap/"+std::to_string(sequence)+"/producer-api-initial/"+std::to_string(ai);require(registry_initial_sizes[ai]&&registry_initial_sizes[ai]<=1024,"Actual producer full initial HeapAlloc input");out.append(stem+"/size.bin",&registry_initial_sizes[ai],4);out.append(stem+"/bytes.bin",registry_initial_bytes[ai],registry_initial_sizes[ai]);}
'''+"'''"+'''
 ref=one(ref,'        // One external game-caller projection',producer+'        // One external game-caller projection')
 initial='''+"'''"+'''            const auto registry_cap_before=HeapSize(*reinterpret_cast<HANDLE*>(0x78035000),0,reinterpret_cast<void*>(*crtbegin));require(registry_cap_before!=SIZE_T(-1)&&registry_cap_before<=512&&*crtnext>=*crtbegin&&*crtnext-*crtbegin<=registry_cap_before,"Actual entire current registry BEFORE backing");const std::array<unsigned,4> registry_before{*crtbegin,*crtnext,static_cast<unsigned>(registry_cap_before),*reinterpret_cast<unsigned*>(0x78035004)};out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/registry-before-meta.bin",registry_before.data(),sizeof(registry_before));out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/registry-before-backing.bin",reinterpret_cast<void*>(*crtbegin),registry_cap_before);
            for(unsigned i=0;i<64;++i)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/CRT-before/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);
'''+"'''"+'''
 ref=one(ref,'            r->tag.status=execute();',initial+'            r->tag.status=execute();')
 provider_after='''+"'''"+'''            for(unsigned i=0;i<64;++i)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/CRT-after/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);
'''+"'''"+'''
 ref=one(ref,'            require(registry_API_count<=256,',provider_after+'            require(registry_API_count<=256,')
'''
s=one(s,anchor,anchor+addition)
s=one(s," pin(__file__);pin(R/'tools/m4-widget-original/prepare.py');", " pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v3.py');pin(R/'tools/m4-widget-original/prepare_v2.py');pin(R/'reports/m4-widget-original/preparation-r3/report.json','86f4a947c7cc870a0519ab9a49128beb751174718ebdf73713a1f9535d463172');pin(R/'tools/m4-widget-original/prepare.py');")
s=one(s,"snapshot_count_bound=384,FS_event_bytes", "snapshot_count_bound=384,whole_CRT_phase_endpoint_pages=64,actual_registry_BEFORE_full_capacity=True,authentic_producer_API_initial_inputs_retained=True,FS_event_bytes")
q=T/'prepare_v3.py'
if q.exists():raise ValueError('Fresh additive source')
q.write_text(s)
print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
