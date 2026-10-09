"""Read the literal stopped original provider CONTEXT as secondary evidence.

The direct original sequence remains the complete legacy ENV/carry oracle.
Debugger pointer metadata is retained literally, never inferred or normalized
into a claimed observation, and never supplies inputs to native execution.
"""
from pathlib import Path
import argparse, importlib.util, json, struct, traceback
import sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('joint27_checkpoint_independent',Path(__file__).with_name('observe.py'))
J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)

def checkpoint(c,record,cp,tag):
    J.need(J.words(record,0,7)==tag,'Actual secondary source/order/domain')
    b=record[J.COMMON:];J.need(len(b)==720 and J.words(b,716)[0]==1 and J.words(b,0)[0]==0x1002f,'Literal full CONTEXT716 and seen checkpoint')
    expected=list(c.P.cpu(cp));expected[9]=0x4c1a0a
    regs=tuple(J.words(b,o)[0] for o in (176,172,168,164,196,180,160,156,192,184))
    J.cpu_equal(regs,expected,0xcc5,'Actual provider checkpoint registers/defined flags/stack versus BEFORE source oracle; CC increments EIP by1')
    J.need(J.words(b,188)[0]==0x23 and J.words(b,200)[0]==0x2b,'Actual source code/stack selectors')
    fx=b[204:716];v=c.P.view(cp)
    J.need(c.O.fxparts(fx)==c.O.fxparts(v[3544:4056]),'Original stopped architectural CW/SW/FTW/MXCSR/raw80/XMM0..7 versus independent source checkpoint')
    return fx[6:24].hex(),b[28:56].hex()

def main(run,native_run,out):
    J.need(out.parent==J.BASE and out.name.startswith('independent-') and not out.exists(),'Fresh private checkpoint receipt');out.mkdir();(out/'review-source.py').write_bytes(Path(__file__).read_bytes());controls=[]
    try:
        m,c,_,_=J.models()
        paired=J.BASE/'independent-repaired-paired-r1';p=json.loads(J.pin(paired/'report.json').read_text());J.need(p['passed'] and p['source_fault_controls_accepted'] and p['connected_roots']==27,'Repaired direct paired plus independent controls required')
        for path,h in json.loads(J.pin(paired/'pins.json').read_text())['files'].items():J.pin(path,h)
        receipt=json.loads(J.pin(run/'report.json').read_text());J.need(receipt['passed'] and receipt['debugger_secondary'] and not receipt['direct_primary'] and receipt['provider_checkpoint_count']==48,'Secondary actual capture scope')
        for path,h in json.loads(J.pin(run/'pins.json').read_text())['files'].items():J.pin(path,h)
        original_build=json.loads((J.BASE/'original-build-r2/build.json').read_text())
        command=receipt['commands'][0];J.need(command['exit_code']==0 and command['arguments'][0]==original_build['worker'] and command['arguments'][-1]=='--checkpoint','Actual secondary source-bound worker invocation')
        J.pin(command['arguments'][0],original_build['worker_sha256'])
        raw=J.pin(run/'raw.bin').read_bytes();J.need(raw[:8]==b'MW4J27D1' and J.words(raw,8,6)==(1,48,27,1296,14,117684) and len(raw)==32+1296*117684,'Complete literal secondary observation header/extent')
        native={level:J.pin(native_run/level/'native.bin').read_bytes() for level in ('O0','O2')};notes=[]
        for sequence in range(48):
            for phase in range(27):
                idx=sequence*27+phase;r=raw[32+idx*117684:32+(idx+1)*117684]
                J.need(J.words(r,0,3)==(sequence,sequence//24,phase) and J.words(r,16)[0]==J.ENTRIES[phase],'Actual secondary complete27 table order')
                if phase!=18:J.need(r[J.COMMON:]==bytes(720),'No invented secondary checkpoint outside provider phase');continue
                tag=J.words(r,0,7)
                for level,n in native.items():
                    row=n[32+idx*J.NATIVE:32+(idx+1)*J.NATIVE];sb=J.state(row);sa,cp,output,_=c.effects(sb,0x7f7fffff)
                    metadata=checkpoint(c,r,cp,tag)
                    J.need(row[128044:132128]==c.P.view(cp),'Whole native checkpoint tied to source-predicted persistent BEFORE')
                    if level=='O0':notes.append(dict(sequence=sequence,rawFX_pointer_metadata=metadata[0],literal_FloatSave_metadata=metadata[1],legacy_ENV_claimed=False))
                    for off in (0,16,J.COMMON,J.COMMON+716,J.COMMON+176,J.COMMON+180,J.COMMON+184,J.COMMON+192,J.COMMON+196,J.COMMON+188,J.COMMON+200,J.COMMON+204,J.COMMON+206,J.COMMON+208,J.COMMON+228,J.COMMON+236,J.COMMON+364):
                        controls.extend(J.corruptions(lambda b:checkpoint(c,b,cp,tag),r,[off],level+f'/sequence{sequence}/actualcheckpoint'))
        report=dict(passed=True,scope='Secondary literal original provider-return checkpoint joined to repaired direct persistent source/native proof',actual_checkpoints=48,O0_O2_bridges=96,secondary_sequence_phases=1296,observer_corruption_rejections=len(controls),literal_CONTEXT_bytes=716,software_checkpoint_bytes=4084,direct_primary='reports/m4-joint-startup27/original-capture-r1/raw.bin',paired_receipt='reports/m4-joint-startup27/independent-repaired-paired-r1/report.json',controls_receipt='reports/m4-joint-startup27/independent-controls-r3/report.json',connected_roots=27,numeric_actual_table_slot=0x5e016c,scope_cap='Selected27 roots only; other118 table slots, full CRT/entry/startup, SEH exception dispatch and ordinary game launch remain unproved',checkpoint_EIP_projection='Original breakpoint reports4C1A0A; source checkpoint and native are4C1A09; only the one CC instruction-byte offset is declared',debugger_legacyENV_metadata_observed=False,original_software_State_observed=False,ordinary_game_launched=False,whole_M4_complete=False)
        (out/'raw-metadata.json').write_text(json.dumps(notes,indent=2)+'\n');(out/'corruptions.json').write_text(json.dumps(controls,indent=2)+'\n');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        J.pin(__file__)
        for path in out.iterdir():
            if path.is_file():J.pin(path)
        (out/'pins.json').write_text(json.dumps(dict(files=J.PINS),indent=2)+'\n');print(json.dumps(report))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('secondary',type=Path);p.add_argument('native_run',type=Path);p.add_argument('output',type=Path);a=p.parse_args();main(a.secondary.resolve(),a.native_run.resolve(),a.output.resolve())
