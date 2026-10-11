"""Join dedicated readonly getter backing and exact new NULL-free boundaries."""
from pathlib import Path
import ast
h=Path(__file__).resolve().parent;target=h/'validate_v4.py'
if target.exists():raise ValueError('Fresh additive validator required')
t=(h/'validate_v3.py').read_text()
def one(a,b):
    global t
    if t.count(a)!=1:raise ValueError('Exact validator hunk '+a[:90])
    t=t.replace(a,b,1)
one('rows=[];occurrences=[];graph_rows=[];normal_rows=[];cleanup_rows=[]','rows=[];occurrences=[];graph_rows=[];normal_rows=[];cleanup_rows=[];null_rows=[]')
one("                    active=None;getter=None;allocation_pairs=0;getter_pairs=0", """                    backing_blob=reader.data('constructor-prerequisites/'+stem+'/normal/getter-backings.bin');need(len(backing_blob)==n*40,'Complete normal-indexed getter backing companion')
                    null_count=words(reader.data(stem+'/nullfree-count.bin'))[0];null_blob=reader.data(stem+'/nullfree-snapshots.bin')
                    need(null_count<=10 and not null_count%2 and len(null_blob)==null_count*628,'Complete actual bounded NULL-free frame/CPU/FX/ENV observations')
                    if root in(0x4103f0,0x410440):need(null_count>0,'Actual literal normal old-NULL buffer release observed')
                    else:need(null_count==0,'No undeclared new-root NULL-free site')
                    null_active=None
                    for ni in range(null_count):
                        nr=null_blob[ni*628:(ni+1)*628];nm=words(nr,0,8);ncpu=words(nr,32,10);nframe=words(nr,612,4)
                        need(nm[:3]==(1,ni,root)and nm[3]==ni%2 and nm[4]==ncpu[9]and nm[5]==ncpu[4]and 0x20001000<=ncpu[4]<=0x20001ff0 and nframe==(0x5f40178c,0,0x58af9f,0),'Actual normal-zero MFC825/free cdecl frame joins physical58AF9A CALL')
                        need(nm[4]==(0x78001390 if ni%2==0 else 0x78001424),'Actual free entry and source post-epilogue preRET PCs')
                        item=dict(sequence=sequence,phase=phase,root=root,index=ni,metadata=list(nm),CPU=list(ncpu),FX512_hex=nr[72:584].hex(),ENV28_hex=nr[584:612].hex(),frame16_hex=nr[612:628].hex(),whole_raw_sha256=hashlib.sha256(nr).hexdigest(),source_CALL_PC=0x58af9a,source_return_PC=0x58af9f,postRET_observed=False)
                        if ni%2==0:null_active=item
                        else:
                            need(null_active is not None and nm[5:8]==tuple(null_active['metadata'][5:8])and item['frame16_hex']==null_active['frame16_hex']and item['FX512_hex']==null_active['FX512_hex']and item['ENV28_hex']==null_active['ENV28_hex']and all(ncpu[j]==null_active['CPU'][j]for j in(3,4,5,6,7)),'Balanced real NULL free call; complete frame/FS/APIcount/nonvolatile/FP conservation')
                            item['paired_entry_index']=null_active['index'];null_active=None;counts['actual_new_NULL_free_pairs']+=1
                        null_rows.append(item);counts['actual_new_NULL_free_boundaries']+=1
                    need(null_active is None,'No unmatched NULL free observer boundary')
                    active=None;getter=None;allocation_pairs=0;getter_pairs=0""")
one("                        if kind==0:", """                        backing=words(backing_blob,i*40,10)
                        if kind in(10,11):
                            need((cpu[1]&~4095)in allpages and(cpu[1]&4095)+8<=4096,'Full source-owned receiver page and field extent')
                            receiver_page=row['pages_raw'][allpages.index(cpu[1]&~4095)*4096:allpages.index(cpu[1]&~4095)*4096+4096];vptr=words(receiver_page,cpu[1]&4095)[0]
                            need((vptr&~4095)in allpages and(vptr&4095)+0x1c<=4096,'Full declared readonly vptr/slot backing')
                            vpage=row['pages_raw'][allpages.index(vptr&~4095)*4096:allpages.index(vptr&~4095)*4096+4096];target_PC=words(vpage,(vptr&4095)+0x18)[0]
                            need(backing==(1,i,cpu[1],cpu[1]&~4095,vptr,vptr&~4095,vptr+0x18,target_PC,4,2)and cpu[2]==vptr and target_PC==0x40a850,'Measured actual receiver/vptr permissions, held EDX and exact named slot target')
                            row['whole_receiver_page_sha256']=hashlib.sha256(receiver_page).hexdigest();row['whole_vptr_page_sha256']=hashlib.sha256(vpage).hexdigest();row['observed_backing_permissions']=list(backing)
                            counts['whole_source_receiver_readonly_dispatch_joins']+=1
                        else:need(backing==(0,)*10,'No stale getter companion at an unrelated normal boundary')
                        if kind==0:""")
one("('actual-new-owner-cleanup.json',cleanup_rows)", "('actual-new-owner-cleanup.json',cleanup_rows),('actual-new-NULL-free-boundaries.json',null_rows)")
one("pin(Path(__file__).with_name('derive_validator_v3.py'));pin(sys.executable);passed=True", "pin(Path(__file__).with_name('derive_validator_v3.py'));pin(Path(__file__).with_name('validate_v3.py'));pin(Path(__file__).with_name('derive_validator_v4.py'));pin(sys.executable);passed=True")
ast.parse(t);target.write_text(t)
