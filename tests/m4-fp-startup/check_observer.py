"""Corrupt actual saved observations; each must reject for its intended cause."""
from pathlib import Path
import importlib.util
import json
import sys
ROOT=Path(__file__).resolve().parents[2]
specification=importlib.util.spec_from_file_location('m4_fp_analyzer',ROOT/'tools/m4-fp-startup/analyze.py')
module=importlib.util.module_from_spec(specification);specification.loader.exec_module(module)
extract,run,out=map(Path,sys.argv[1:4])
spec=json.loads((extract/'extraction.json').read_text());pack=(extract/'pages.bin').read_bytes()
blob=(run/'original.bin').read_bytes();module.analyze(blob,spec,pack)
controls=[('magic',0,'Output magic'),('case order',24,'case tag/order'),('entry CPU',44,'entry CPU'),
          ('return ESP',24+60+16,'preserved CPU'),('host CW',24+100+1536,'Host control'),
          ('host x87',24+100+1536+32,'Host x87'),('host XMM',24+100+1536+160,'Host x87'),
          ('input CW',24+100,'starting FP domain'),('input metadata',24+100+8,'starting FP domain'),
          ('input ENV',24+2148+12,'starting legacy'),('completion CW',24+100+512,'FX/ENV'),
          ('legacy FIP',24+2176+12,'last-instruction'),('legacy FOP',24+2176+18,'last-instruction'),
          ('legacy FDP',24+2176+20,'last-instruction'),('input memory',24+2260,'data/stack input'),
          ('escaped memory write',24+2260+module.MEMORY_BYTES,'write escaped'),
          ('repeat output',24+240*module.RECORD_BYTES+2260+module.MEMORY_BYTES+6*4096+0xe40,'Repeated original')]
results=[]
for name,offset,cause in controls:
    changed=bytearray(blob);changed[offset]^=1
    try:module.analyze(changed,spec,pack)
    except ValueError as error:
        if cause not in str(error):raise ValueError('Wrong corruption cause: '+name+': '+str(error))
        results.append({'name':name,'offset':offset,'cause':str(error)})
    else:raise ValueError('Observer accepted corruption: '+name)
try:module.analyze(blob[:-1],spec,pack)
except ValueError as error:
    if 'Output extent' not in str(error):raise
    results.append({'name':'truncated output','cause':str(error)})
else:raise ValueError('Observer accepted truncation')
if out.exists():raise ValueError('Fresh observer report required')
out.write_text(json.dumps({'passed':True,'controls':results,'source':module.bind(__file__),
                           'analyzer':module.bind(module.__file__),'original':module.bind(run/'original.bin')},indent=2)+'\n')
print('Observer corruptions rejected:',len(results))
