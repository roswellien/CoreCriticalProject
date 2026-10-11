"""Read-only audit of removable cinematic stages with retained validated outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import time


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    root=a.workspace.resolve();work=root/'local/work-ahead'
    batch=work/'cinematics-2160p-30fps-batch-v1'
    plans=[]
    for folder in sorted(batch.iterdir()):
        if folder.is_dir() and (folder/'manifest.json').exists():
            plans.append((folder,'master-2160p-30fps.mkv',folder.name+'-2160p-30fps.mp4',
                ['general4x.mkv','upscaled-2160p-15fps.mkv','rife-30fps-raw.mkv']))
    if len(plans)!=18:raise ValueError('Expected 18 batch clips')
    plans.append((work/'opening-cinematic-30fps-full-v1','opening-2160p-30fps-master.mkv',
                  'opening-2160p-30fps-review.mp4',['rife-30fps-raw.mkv']))
    report={'scope':'No deletion; retained output hashes checked against prior technical validation; no fresh decode or subjective visual approval',
        'preserve_policy':'Keep originals, 19 30fps masters, exports, packages, manifests, logs and tools',
        'clips':[],'removal_candidates':[],'blocked':[]}
    start=time.time()
    for folder,master,export,stages in plans:
        print('Verifying '+folder.name,flush=True)
        try:
            manifest=folder/'manifest.json';data=json.loads(manifest.read_text())
            checks={item['file']:item for item in data['checks']}
            if not data['status'].startswith('technical validation passed'):
                raise ValueError('Incomplete clip status')
            if any(command['exit_code']!=0 for command in data['commands']):
                raise ValueError('Failed recorded stage')
            retained=[]
            for name in [master,export]:
                path=(folder/name).resolve();check=checks[name]
                if not path.is_relative_to(work) or path.is_symlink():raise ValueError('Unadmitted path')
                if path.stat().st_size!=check['bytes'] or digest(path)!=check['sha256']:
                    raise ValueError('Retained output differs from validated identity: '+name)
                if check['dimensions']!=[2880,2160] or check.get('rate',check.get('frame_rate'))!=30:
                    raise ValueError('Wrong output profile')
                retained.append({'path':str(path),'bytes':check['bytes'],'sha256':check['sha256'],'frames':check['frames']})
            if checks[export]['decoded_frames']!=checks[master]['frames']:
                raise ValueError('Export full-decode receipt differs from master frame count')
            expected_pcm=data.get('source_pcm_sha256',data.get('source',{}).get('pcm_sha256'))
            if not expected_pcm or checks[master]['pcm_sha256']!=expected_pcm:
                raise ValueError('Master original-audio receipt mismatch')
            candidates=[]
            for name in stages:
                path=(folder/name).resolve();check=checks[name]
                if not path.is_relative_to(work) or path.is_symlink() or path.stat().st_size!=check['bytes']:
                    raise ValueError('Intermediate path/size differs: '+name)
                candidates.append({'path':str(path),'bytes':path.stat().st_size,
                    'historical_sha256':check['sha256'],
                    'reason':'Completed upstream stage; validated lossless downstream master and export retained',
                    'candidate_hash_rechecked':False})
            clip={'clip':folder.name,'retained':retained,'manifest_sha256':digest(manifest),'status':'verified'}
            report['clips'].append(clip);report['removal_candidates'].extend(candidates)
        except (OSError,ValueError,KeyError) as error:
            report['blocked'].append({'clip':folder.name,'reason':str(error)})
        report['candidate_bytes']=sum(c['bytes'] for c in report['removal_candidates'])
        report['elapsed_seconds']=round(time.time()-start)
        a.output.write_text(json.dumps(report,indent=2))
    print(json.dumps({'verified_clips':len(report['clips']),'blocked':report['blocked'],
        'candidate_files':len(report['removal_candidates']),'candidate_GiB':report['candidate_bytes']/1024**3},indent=2))


if __name__=='__main__':main()
