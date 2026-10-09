"""Independent observation-only source-fault and outer FP boundary review.

No fixture, primary comparator, worker, or guest execution is imported or run.
Complete prefixes are tied to the separately reviewed literal-source corpus.
"""
from pathlib import Path
import argparse, importlib.util, json, struct, traceback
import sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('joint27_independent',Path(__file__).with_name('observe.py'))
J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
ROOT=J.ROOT;BASE=J.BASE;SIZE=124604

def routes(kind):
    if kind==0:
        e=[(J.BROKER,a,J.BROKER,0,1) for a in J.ENTRIES]
        e[19:19]=[(0x4c19f3,0x4c1a00,0x4c19f8,0,1),(0x4c1a03,0x5bb4fc,0x4c1a09,1,1)]
        return e
    if kind in (4,15,16):return []
    if kind in (1,2,3,5):return [(J.BROKER,J.ENTRIES[0],J.BROKER,0,0)]
    e=[(J.BROKER,a,J.BROKER,0,1) for a in J.ENTRIES[:18]]
    e.append((J.BROKER,J.NUMERIC,J.BROKER,0,0))
    if kind not in (9,12,13,14):
        e.append((0x4c19f3,0x4c1a00,0x4c19f8,0,int(kind in (8,11))))
        e.append((0x4c1a03,0x5bb4fc,0x4c1a09,1,int(kind!=7)))
    return e

# These fault coordinates follow the admitted source instructions, numeric
# event-prefix guards and the explicitly injected host mutations in fixture.
FAULT={1:(0,J.BROKER,0,0,1),2:(0,J.BROKER,0,0,1),3:(0,0x410910,0,0,1),
       4:(0,J.BROKER,0,0,1),5:(0,0x410910,0,0,1),
       6:(18,0x4c1a09,0x60b368,7,2),7:(18,0x780c10f0,0x78115004,5,2),
       8:(18,0x12345678,0,22,2),9:(18,0x4c19f3,J.FRAME-8,1,2),
       10:(18,0x12345678,0,20,2),11:(18,0x4c19f8,0,22,1),
       12:(18,0x4c19f0,J.FRAME-4,0,2),13:(18,0x4c19f0,0,0,2),
       14:(18,0x4c19f0,0,0,2),15:(0,J.BROKER,0,0,1),16:(0,J.BROKER,0,0,1)}

def viewcheck(c,b,noncanonical=False):
    s=b[40:3544]
    if noncanonical:
        J.need(s[2755]==2,'Deliberate IE nonboolean fixture retained')
        repaired=bytearray(s);repaired[2755]=0;v=bytearray(c.P.view(repaired));v[40:3544]=s
        for offset in (3546,4060):struct.pack_into('<H',v,offset,J.u16(v,offset)|2)
        J.need(bytes(v)==b,'Literal deliberate nonboolean State projection; not an admitted input')
    else:J.need(c.P.view(s)==b,'Entire State/CPU/FX/ENV view coherence')

def hostcheck(b,cw):
    f0,f1=b[8248:8760],b[8760:9272];e0,e1=b[9272:9300],b[9300:9328]
    J.need(J.u16(f0)==cw and J.u16(e0)==cw,'Actual outside caller seeded CW')
    J.need(J.numeric_host(f0)==J.numeric_host(f1),'Direct outside numerical/MXCSR/raw80 preservation')
    J.need(e0==e1,'Direct outside full legacy ENV28 preservation')
    J.need(e0[12:28]!=bytes(16),'Meaningful nonzero caller legacy ENV metadata')

def partial_memory(kind,step,initial,prefix,numeric_events):
    if kind==0:return None
    b=bytearray(prefix if kind>=6 and kind<=14 else initial)
    if kind not in (4,15,16,1,2):J.put(b,J.mo(J.FRAME),J.BROKER)
    if kind in range(6,13):
        for pc,a,v,width,write in struct.iter_unpack('<5I',numeric_events[:20*step]):
            if write:J.put(b,J.mo(a),v)
    if kind==8:J.put(b,J.mo(J.FRAME),0x12345678)
    if kind==10:J.put(b,J.mo(J.FRAME-8),0x12345678)
    if kind==13:J.put(b,J.mo(J.IAT),J.words(b,J.mo(J.IAT))[0]^1)
    if kind==14:J.put(b,J.mo(0x78115004),0x3f800000)
    if kind in (2,7,11):
        page={2:0x20001000,7:0x78115000,11:0x780c1000}[kind]
        b[J.mo(page):J.mo(page)+4096]=bytes(4096)
    return bytes(b)

def sample(c,b,kind,cw,retry,old,baseline):
    t=J.words(b,0,20);success=kind==0 and not retry
    J.need(t[:4]==(kind,cw,int(success),int(success)) and t[15]==int(retry),'Exact scenario and result/refusal tags')
    J.need(t[19]==int(kind==16 and not retry),'Lexical original owner cleanup/preservation')
    hostcheck(b,cw);viewcheck(c,b[80:4164],kind==4 and not retry);viewcheck(c,b[4164:8248],kind==4 and not retry)
    expected_completed=27 if kind==0 else 18 if 6<=kind<=14 else 0
    expected_step=22 if kind==0 else FAULT[kind][3]
    poisoned=int(kind not in (0,4,15,16));numeric_failed=int(kind in (6,7,8,9,10,12,13,14))
    J.need(t[4:10]==(expected_completed,int(not success),poisoned,numeric_failed,expected_step,len(routes(kind))),'Source-derived phase/Session/Runtime closure')
    wanted=(0,0,0,0,0) if success else (0,J.BROKER,0,22,1) if kind==0 else FAULT[kind]
    J.need(t[10:15]==wanted,'Exact first failure POD source coordinates')
    routebytes=b''.join(struct.pack('<5I',*r) for r in routes(kind))
    J.need(b[124024:124604]==routebytes+bytes(580-len(routebytes)),'All real Runtime route targets, sites and completed flags plus inactive slots')
    before_mask=0x3fff-(1<<10) if kind==2 and not retry else 0x3fff
    after_mask=0x3fff-(1<<{2:10,7:13,11:12}[kind]) if kind in (2,7,11) and not retry else 0x3fff
    J.need(J.words(b,124016,2)==(before_mask,after_mask),'Exact mapped-page presence')
    if retry:
        J.need(t[16:19]==(old[4],old[9],old[8]),'Retry begins at actual first completion/route/event extent')
        J.need(b[80:4164]==b[4164:8248] and b[9328:66672]==b[66672:124016],'Whole retry State, view and14pages unchanged after correction')
        J.need(t[4:15]==old[4:15] or kind==0 and t[4:10]==old[4:10][:1]+(1,)+old[6:10],'Retry first failure is retained; successful one-use context now records refusal')
    else:
        J.need(t[16:19]==(0,0,0),'Fresh context has no prior guest work')
        initial,prefix,events,final_view,final_mem=baseline
        if kind==0:J.need(b[4164:8248]==final_view and b[66672:124016]==final_mem,'Successful whole State/pages match independently accepted literal original/native corpus')
        else:
            want=partial_memory(kind,expected_step,initial,prefix,events)
            J.need(b[66672:124016]==want,'Entire source-prefix14pages plus declared injection, no invented later writes')
        if kind in (4,15,16):J.need(b[80:4164]==b[4164:8248] and b[9328:66672]==b[66672:124016],'Unentered refusal retains complete State/pages')
    return t

def main(build,run,out):
    J.need(out.parent==BASE and out.name.startswith('independent-') and not out.exists(),'Fresh independent control review receipt');out.mkdir()
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes());controls=[]
    try:
        m,c,_,_=J.models()
        review=BASE/'independent-paired-r2';r=json.loads(J.pin(review/'report.json').read_text());J.need(r['passed'],'Separately modeled complete source corpus')
        for p,h in json.loads(J.pin(review/'pins.json').read_text())['files'].items():J.pin(p,h)
        d=json.loads(J.pin(BASE/'boundary-derivation-r1/derivation.json').read_text())
        for section in ('ancestors','generated'):
            for p,h in d[section].items():J.pin(p,h)
        a=Path(next(p for p in d['ancestors'] if p.endswith('native_main.cpp'))).read_text()
        change=' bool invoke_selected_table(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept{\n  ni::NumericHostBoundary boundary(admitted_cw_);bool ok=false;unsigned phase=0;'
        replace=' [[clang::noinline]] bool invoke_selected_table(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept{\n  // Save caller numerical/legacy state before the private large frame probes.\n  ni::NumericHostBoundary boundary(admitted_cw_);return invoke_selected_body(sequence,repeat,top,records);\n }\n [[clang::noinline]] bool invoke_selected_body(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept{\n  bool ok=false;unsigned phase=0;'
        J.need(a.count(change)==1 and a.replace(change,replace)==(ROOT/'tools/m4-joint-startup27/native_main.cpp').read_text(),'Exact sole boundary wrapper split; private body unchanged')
        J.need((ROOT/'tools/m4-joint27-startup/controls/fixture.cpp').read_text()==(ROOT/'tools/m4-joint-startup27/controls/fixture.cpp').read_text(),'Unchanged actual fault fixture')
        b=json.loads(J.pin(build/'build.json').read_text());J.need(b['passed'] and not b['diagnostic'],'Repaired compiled actual control workers')
        for group in ('sources','tools','artifacts'):
            for p,h in b[group].items():J.pin(p,h)
        r=json.loads(J.pin(run/'report.json').read_text());J.need(r['passed'] and r['actual_records']==204 and r['scenarios']==102,'Full real control recipe')
        rows=0
        for level in ('O0','O2'):
            command=next(q for q in r['commands'] if 'build-'+level in q['arguments'][0]);J.need(command['exit_code']==0,'Actual compiled worker completion');worker=J.pin(command['arguments'][0],command['worker_sha256'])
            pe=worker.read_bytes();J.need(J.u16(pe,J.words(pe,60)[0]+4)==0x8664,'Actual AMD64 worker')
            n=J.pin(ROOT/f'reports/m4-joint27-startup/capture-r1/{level}/native.bin').read_bytes();summaries=J.pin(ROOT/f'reports/m4-joint27-startup/capture-r1/{level}/sequences.bin').read_bytes()
            raw=J.pin(run/level/'controls.bin').read_bytes();J.need(raw[:8]==b'MW4J27C1' and J.words(raw,8,4)==(1,0,SIZE,14) and len(raw)==24+102*SIZE,'Full packed control schema and complete51two-call scenarios')
            for ci,cw in enumerate((0x7f,0x37f,0xb7f)):
                sequence=m.CW.index(cw)*2;summary=summaries[24+sequence*J.SUMMARY:24+(sequence+1)*J.SUMMARY]
                initial=summary[8136:65480];row=n[32+(sequence*27+18)*J.NATIVE:32+(sequence*27+19)*J.NATIVE]
                baseline=(initial,J.memory(row),row[132128:132568],c.P.view(summary[4632:8136]),summary[65480:J.SUMMARY])
                for kind in range(17):
                    idx=(ci*17+kind)*2;first=raw[24+idx*SIZE:24+(idx+1)*SIZE];second=raw[24+(idx+1)*SIZE:24+(idx+2)*SIZE]
                    old=sample(c,first,kind,cw,False,None,baseline);sample(c,second,kind,cw,True,old,baseline);rows+=2
                    for retry,record in ((False,first),(True,second)):
                        check=lambda changed:sample(c,changed,kind,cw,retry,old if retry else None,baseline)
                        offsets=[0,8,16,32,40,56,76,4164,8760,8760+2,8760+24,8760+32,9300+12,124016,124020,124024]
                        if retry:offsets += [4164+40+3433,66672+J.mo(0x60b368)]
                        controls.extend(J.corruptions(check,record,offsets,level+f'/CW{cw:x}/kind{kind}/retry{int(retry)}'))
        report=dict(passed=True,scope='Independent compiled source-fault closure and direct outer numerical/full legacy ENV preservation; repaired boundary only',actual_records=rows,scenarios=rows//2,corruption_rejections=len(controls),complete_State_bytes=3504,complete_owned_pages=14,old_O2_ENV_loss_preserved=True,old_stack_probe_cause='Inference from pre-capture __chkstk and changed stack/code layout; not proven root cause',derivative='Sole noinline small outer boundary before unchanged private large body; all actual source fault fixture and frozen translated objects unchanged',full_partial_State_semantics='Complete view coherence and immutable refusals checked; entered partial State retained literally, page/event-prefix and route extent modeled. All complete27 positive State semantics covered by separate original/native receipt.',FP_scope='Direct outside caller CW/SW/FTW/MXCSR and eight raw80 plus all28 legacyENV; volatile SIMD/reservedFX remain observed, not equality claim',whole_M4_complete=False)
        (out/'corruptions.json').write_text(json.dumps(controls,indent=2)+'\n');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        J.pin(__file__);J.pin(Path(__file__).with_name('observe.py'));(out/'pins.json').write_text(json.dumps(dict(files=J.PINS),indent=2)+'\n');print(json.dumps(report))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('run',type=Path);p.add_argument('output',type=Path);a=p.parse_args();main(a.build.resolve(),a.run.resolve(),a.output.resolve())
