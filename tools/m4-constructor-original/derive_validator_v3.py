"""Join every measured ownership transition and cleanup to the raw API facts."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=here/'validate_v2.py';target=here/'validate_v3.py'
assert not target.exists();text=source.read_text()
def one(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new,1)
one("        patches={row['return_PC']:row for row in read(prep/'constructor-hook-bindings.json')}", """        patches={row['return_PC']:row for row in read(prep/'constructor-hook-bindings.json')}
        chain=read(BASE/'entry-chain-r1/report.json',contracts['source_MFC_entry_chain_sha256']);need(chain['passed'],'Exact physical named export and finite affine source frame')
        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)
        need(provider_entries==(1,chain['MFC_exports']['823']['target'],chain['MFC_exports']['825']['target'],chain['MFC_exports']['823']['target'],chain['MFC_exports']['825']['target'],chain['CRT_named_exports']['malloc']['target'],chain['CRT_named_exports']['free']['target']),'Actual loaded owning named MFC/CRT targets and whole observation')""")
one("                previous=live_byserial;live_byserial=current", """                previous=live_byserial
                need(set(previous)<=set(current),'No missing carried allocation occurrence')
                new_by_api={v[3]:v for serial,v in current.items()if serial not in previous}
                need(len(new_by_api)==len(current)-len(previous),'Every new occurrence has one distinct actual API invocation')
                replay={serial:list(v)for serial,v in previous.items()};matched_new=set()
                for api_index in range(api_count):
                    api=words(ledger,api_index*104,26);kind=api[24];result=api[10]
                    if kind==0 and result:
                        need(api_index in new_by_api,'Every successful HeapAlloc produces a measured occurrence')
                        v=new_by_api[api_index]
                        need(v[2]==phase and v[4]==0 and(v[5],v[6],v[7],v[10])==(api[20],api[22],result,0),'Actual new allocation metadata/request/result')
                        need(not any(x[9]and(x[5],x[7])==(v[5],v[7])for x in replay.values()),'No already-live heap/address allocation alias')
                        replay[v[1]]=list(v);replay[v[1]][9]=1;matched_new.add(v[1])
                    elif kind in(1,3)and result:
                        candidates=[serial for serial,v in replay.items()if v[9]and(v[5],v[7])==(api[20],api[22])]
                        need(len(candidates)==1,'Successful free/reallocation joins one current live heap/address occurrence')
                        predecessor=candidates[0];replay[predecessor][9]=0
                        if kind==3:
                            need(api_index in new_by_api,'Successful reallocation has a measured successor revision');v=new_by_api[api_index]
                            need(v[2]==phase and v[4]==3 and(v[5],v[6],v[7],v[10],v[11])==(api[20],api[23],result,predecessor,0),'Exact real reallocation request/result/predecessor')
                            need(not any(x[9]and(x[5],x[7])==(v[5],v[7])for x in replay.values()),'Fresh live reallocation successor heap/address')
                            replay[v[1]]=list(v);replay[v[1]][9]=1;matched_new.add(v[1])
                        counts['actual_API_joined_ownership_retirements']+=1
                need(matched_new==set(current)-set(previous)and set(replay)==set(current)and all(tuple(v)==current[serial]for serial,v in replay.items()),'Complete allocation/free/reallocation chronology and final occurrence metadata')
                live_byserial=current""")
one("need(v[6]==requested and api[4]+104==a[4]and meta[10]>v[3],'Exact requested bytes and genuine HeapAlloc caller frame within MFC')", "need(v[6]==requested and api[4]-chain['MFC823_entry_to_HeapAlloc_before_delta']==a[4]and api[25]==chain['HeapAlloc_source_saved_return']and meta[10]>v[3],'Exact physical MFC/malloc/HeapAlloc frame chain and requested bytes')")
one("                            g=getter['CPU'];expected=list(g);expected[0]=words(getter['pages_raw'],allpages.index(g[1]&~4095)*4096+(g[1]&4095)+4)[0];expected[9]=0x40a853", """                            g=getter['CPU'];need((g[1]&~4095)in allpages and(g[1]&4095)+8<=4096,'Actual getter object field belongs to one complete declared source page; no owner AFTER seed')
                            expected=list(g);expected[0]=words(getter['pages_raw'],allpages.index(g[1]&~4095)*4096+(g[1]&4095)+4)[0];expected[9]=0x40a853""")
one("v=occ(reader.data(key));need(v[1]in source_new_serials and v[2]<len(order)and order[v[2]]['entry']in NEW and v[9],'Actual new owner before research-only cleanup')", "v=occ(reader.data(key));need(v[1]not in observed_cleaned and v[1]in source_new_serials and v[1]in live_byserial and v==live_byserial[v[1]]and v[2]<len(order)and order[v[2]]['entry']in NEW and v[9],'Exactly one cleanup joins the whole final live new-owner occurrence')")
one("pin(Path(__file__).with_name('derive_validator_v2.py'));pin(sys.executable);passed=True", "pin(Path(__file__).with_name('derive_validator_v2.py'));pin(Path(__file__).with_name('validate_v2.py'));pin(Path(__file__).with_name('derive_validator_v3.py'));pin(sys.executable);passed=True")
target.write_text(text)
