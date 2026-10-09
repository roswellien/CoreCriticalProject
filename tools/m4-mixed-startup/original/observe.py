"""Reparse hardware provenance/carry; never execute an expected guest body."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3]
SIZE=92388;PAGE_SIZE=4096;PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000)
CW=(0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f)
INITIAL=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def require(ok,reason):
    if not ok:raise ValueError(reason)
def host_equal(a,b,e,f):
    return a[:5]==b[:5] and a[24:28]==b[24:28] and e==f and a[160:288]==b[160:288] and all(a[32+i*16:42+i*16]==b[32+i*16:42+i*16] for i in range(8))
def fields(record):
    return {'tag':struct.unpack_from('<9I',record),'before':struct.unpack_from('<10I',record,36),'after':struct.unpack_from('<10I',record,76),
            'fx0':record[116:628],'fx1':record[628:1140],'host0':record[1140:1652],'host1':record[1652:2164],
            'env0':record[2164:2192],'env1':record[2192:2220],'hostenv0':record[2220:2248],'hostenv1':record[2248:2276],
            'memory0':record[2276:47332],'memory1':record[47332:92388]}
def inspect(raw,extraction):
    require(len(raw)>=32,'Truncated mixed header')
    require(raw[:8]==b'MW4MXO01' and struct.unpack_from('<6I',raw,8)==(1,48,26,1248,11,SIZE),'Mixed header differs')
    require(len(raw)==32+1248*SIZE,'Incomplete/extra mixed phase stream')
    roots=extraction['selected_table_slots'];require(len(roots)==26,'Exact table root count differs')
    default={x['address']:x for x in extraction['pages']};phase_rows=[];previous=None;repeated={};checks=0
    for index in range(1248):
        r=fields(raw[32+index*SIZE:32+(index+1)*SIZE]);sequence,repeat,phase,slot,entry,cw,top,status,restored=r['tag']
        expected_sequence,expected_phase=divmod(index,26);expected_repeat=expected_sequence//24;expected_cw=CW[(expected_sequence%24)//2];expected_top=(0,7)[expected_sequence%2]
        require((sequence,repeat,phase,slot,entry,cw,top,status,restored)==(expected_sequence,expected_repeat,expected_phase,roots[expected_phase]['slot'],roots[expected_phase]['entry'],expected_cw,expected_top,0,1),'Phase tag/order/domain/fault/restoration differs')
        require(r['before'][4]==0x20001800 and r['before'][9]==entry and r['after'][4]==0x20001804 and r['after'][9]==0x410a80,'Synthetic entry/actual return frame differs')
        require(host_equal(r['host0'],r['host1'],r['hostenv0'],r['hostenv1']),'Host raw FP restoration differs')
        for fx,env in ((r['fx0'],r['env0']),(r['fx1'],r['env1'])):
            require(struct.unpack_from('<H',fx)[0]==cw and fx[4]==0 and (struct.unpack_from('<H',fx,2)[0]>>11)&7==top,'Empty persistent CW/TOP/tag differs')
            require(struct.unpack_from('<H',env)[0]==cw and struct.unpack_from('<H',env,8)[0]==0xffff and (struct.unpack_from('<H',env,4)[0]>>11)&7==top,'Legacy empty persistent CW/TOP/tag differs')
            require(struct.unpack_from('<H',env,4)[0]==struct.unpack_from('<H',fx,2)[0],'Legacy/FX status disagreement')
        require(struct.unpack_from('<I',r['memory0'],10*4096+0x800)[0]==0x410a80,'Observed frame is not agreed capture PC')
        for i,address in enumerate(PAGES):
            if default.get(address,{}).get('permission')==0:
                for view in (r['memory0'],r['memory1']):require(hashlib.sha256(view[i*4096:(i+1)*4096]).hexdigest()==default[address]['sha256'],'Exact protected page changed')
        if phase:
            before=list(previous['after']);before[4]=0x20001800;before[9]=entry
            require(r['before']==tuple(before),'CPU carry differs outside synthetic EIP/ESP framing')
            require(r['fx0']==previous['fx1'],'Actual hardware FX carry differs')
            require(r['env0']==previous['env1'],'Actual legacy ENV carry differs')
            require(r['memory0']==previous['memory1'],'Whole-page carry differs')
            checks+=4
        else:
            require(r['before']==INITIAL+(entry,),'Initial authored CPU differs')
            require(struct.unpack_from('<H',r['fx0'],2)[0]==top<<11 and r['fx0'][6:24]==bytes(18),'Initial actual FP clean/status/metadata differs')
            for i,address in enumerate(PAGES[:-1]):require(hashlib.sha256(r['memory0'][i*4096:(i+1)*4096]).hexdigest()==default[address]['sha256'],'Fresh default sequence page differs')
            stack=bytearray(b'\xa5'*4096);struct.pack_into('<I',stack,0x800,0x410a80);require(r['memory0'][-4096:]==stack,'Fresh authored stack differs')
        key=(cw,top,phase);observable=(r['before'],r['after'],r['fx0'],r['fx1'],r['env0'],r['env1'],r['memory0'],r['memory1'])
        if repeat:require(repeated[key]==observable,'Actual guest repeated sequence differs')
        else:repeated[key]=observable
        previous=r;checks+=1
        phase_rows.append({'sequence':sequence,'phase':phase,'slot':slot,'entry':entry,'cw':cw,'initial_top':top,
                           'cpu_before':r['before'],'cpu_after':r['after'],'guest_sw_before':struct.unpack_from('<H',r['fx0'],2)[0],
                           'guest_sw_after':struct.unpack_from('<H',r['fx1'],2)[0],'legacy_fip_before':struct.unpack_from('<I',r['env0'],12)[0],
                           'legacy_fip_after':struct.unpack_from('<I',r['env1'],12)[0],'memory_after_sha256':hashlib.sha256(r['memory1']).hexdigest()})
    return {'passed':True,'sequences':48,'phases':1248,'root_count':26,'whole_page_carry_checks':1200,'cpu_carry_checks':1200,'hardware_FX_carry_checks':1200,'legacy_ENV_carry_checks':1200,'repeated_guest_phase_checks':624,'checks':checks,'phase_observations':phase_rows}
def main():
    raw_path,extract_path,out=map(lambda x:Path(x).resolve(),sys.argv[1:4])
    require(out.parent==ROOT/'reports/m4-mixed-startup' and out.name.startswith('original-') and not out.exists(),'Fresh assigned private observation directory required')
    out.mkdir();raw=raw_path.read_bytes();extraction=json.loads(extract_path.read_text())
    try:report=inspect(raw,extraction)
    except Exception as e:report={'passed':False,'error':str(e),'raw_bytes':len(raw),'complete_records':max(0,(len(raw)-32)//SIZE)}
    report['scope']='Actual connected original default26 selected-root observations and carry; no expected guest computation or native/full-ledger acceptance'
    report['bindings']={str(p):sha(p) for p in (raw_path,extract_path,Path(__file__),ROOT/'tools/m4-mixed-startup/original/protocol.hpp')}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('phase_observations','bindings')}))
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
