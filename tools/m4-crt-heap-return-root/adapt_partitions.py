"""One-time fresh admission adaptation for bounded disjoint archives."""
from pathlib import Path
p=Path(__file__).with_name('accept.py')
s=p.read_text();a=s.index('    archives=[];verified_stages=[]');b=s.index("    need(native['native_checks']==sum",a)
s=s[:a]+'''    archives=[];verified_stages=[]
    packaging_path=add(native['packaging_path'],native['packaging_sha256'])
    need(sha_file(packaging_path)==native['packaging_sha256'],'Exact unchanged-tree partition publication')
    packaging=read(packaging_path)
    need(packaging['passed'] is True and packaging['native_rerun'] is False and
        packaging['transport_limits_changed'] is False,'Bounded partitions retain original transport checks')
    for kind,levels in (('author',values['author_execution']['levels']),('independent',native['levels'])):
        need(set(levels)=={'O0','O2'},'Exact optimization levels '+kind)
        for level,info in levels.items():
            expected_worker=(values['build']['workers'][level] if kind=='author' else
                str(Path(config['receipts']['compiled_build']['path']).parent/level/'controls.exe'))
            need(normalized(info['worker'])==normalized(expected_worker),'Exact compiled worker')
            owner=values['build'] if kind=='author' else fixture
            worker_sha={normalized(p):h for p,h in owner['artifacts'].items()}[normalized(info['worker'])]
            need(sha_file(info['worker'])==worker_sha,'Worker equals build artifact')
            s=Path(info['native_stage']);receipt=add(s/'stage.json');h=sha_file(receipt);checked=verify_stage(s,h)
            need(checked['recorded_stage_passed'],'Successful original actual native stage')
            if kind=='independent':need(h==info['native_stage_sha256'],'Fixed independent native stage')
            command=read(receipt);native_outputs={normalized(p):h for p,h in command['artifact_sha256'].items()}
            need([normalized(p) for p in command['argv']]==[normalized(p) for p in info['argv']],
                 'Exact native request paths')
            need(normalized(command['argv'][0])==normalized(info['worker']) and
                {normalized(p):h for p,h in command['input_sha256'].items()}.get(
                    normalized(info['worker']))==worker_sha,'Actual isolated compiled worker hash')
            need(native_outputs.get(normalized(str(Path(info['argv'][-1])/'COMPLETE')))==
                hashlib.sha256(b'COMPLETE').hexdigest(),'Native closed output association')
            for name in ('stdout.bin','stderr.bin'):add(s/name)
            verified_stages.append(dict(kind=kind,level=level,role='native_stage',verification=checked))
            parts=[dict(info,pack_source=info['argv'][-1])] if kind=='author' else info['bundles']
            need(len(parts)==(1 if kind=='author' else 2),'Exact bounded archive partitions')
            whole={};seen=set();controls=None;complete=None
            for part in parts:
                s=Path(part['pack_stage']);receipt=add(s/'stage.json');h=sha_file(receipt);checked=verify_stage(s,h)
                need(checked['recorded_stage_passed'],'Successful strict bounded archive stage')
                if kind=='independent':need(h==part['pack_stage_sha256'],'Fixed independent pack stage')
                command=read(receipt);outputs={normalized(p):h for p,h in command['artifact_sha256'].items()}
                need(outputs.get(normalized(part['bundle']))==part['bundle_sha256'],'Exact pack output archive')
                wanted=[str(Path(sys.executable)),str(ROOT/'tools/m4-pipeline/capture_bundle.py'),
                        'pack',part['pack_source'],part['bundle']]
                need(len(command['argv'])==5 and command['argv'][2]=='pack' and
                    [normalized(command['argv'][i]) for i in (0,1,3,4)]==
                    [normalized(wanted[i]) for i in (0,1,3,4)],'Exact strict pack request, source and output')
                for name in ('stdout.bin','stderr.bin'):add(s/name)
                verified_stages.append(dict(kind=kind,level=level,role='pack_stage',verification=checked))
                h=part['bundle_sha256']
                with CaptureBundle(add(part['bundle'],h),h) as reader:
                    need(len(reader.names())==part['logical_files'],'Externally bound bounded archive inventory')
                    for name in reader.names():
                        need(name.casefold() not in seen,'No duplicated logical path across strict partitions')
                        seen.add(name.casefold());raw=reader.read_bytes(name)
                        whole[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                        if name=='COMPLETE':complete=raw
                        if name=='controls.json':controls=raw
                    if kind=='author':
                        need(info['logical_files']==96068,'Exact observed author archive size')
                        need({n.split('/')[0] for n in reader.names()}=={'COMPLETE','units'}|{f'row-{i}' for i in range(36)},
                             'Complete author top-level inventory')
                        for i in range(36):
                            result=json.loads(reader.read_bytes(f'row-{i}/result.json'),object_pairs_hook=unique_object)
                            need(result['passed'] is True and result['scenario']==i and result['control']==(0 if i<24 else i+133),
                                 'Complete author ordinary/fault requests')
                archives.append(dict(kind=kind,level=level,path=part['bundle'],sha256=h,logical_files=part['logical_files']))
            need(complete==b'COMPLETE' and len(whole)==info['logical_files'],'Exact disjoint complete archive union')
            if kind=='independent':
                inventory=add(info['inventory_path'],info['inventory_sha256'])
                need(sha_file(inventory)==info['inventory_sha256'] and read(inventory)['files']==whole,
                     'Exact complete original relative-path/hash inventory across partitions')
                level_package=packaging['levels'][level]
                need(normalized(level_package['source_tree'])==normalized(info['argv'][-1]) and
                    level_package['native_stage_sha256']==info['native_stage_sha256'] and
                    level_package['inventory_sha256']==info['inventory_sha256'] and
                    level_package['bundles']==parts,'Partition proof binds original closed native tree and exact archives')
                need(native_outputs.get(normalized(str(Path(info['argv'][-1])/'controls.json')))==
                    hashlib.sha256(controls).hexdigest(),'Exact native result/archive union association')
                result=json.loads(controls,object_pairs_hook=unique_object)
                need(result==info['result'] and result['passed'] is True and result['scenarios']==122 and
                    result['malformed_token_denials']==22 and result['direct_host_failure_queries']==2 and
                    result['synthetic_API_results'] is False,'Complete independent actual requests')
''' +s[b:]
p.write_text(s)
