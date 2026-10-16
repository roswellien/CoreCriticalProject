"""Analyze the bounded live replacement-model CPU/GPU comparison, not a full engine benchmark."""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_case(path, gpu, first, last):
    record = json.loads((path / 'run.json').read_text(encoding='utf-8-sig'))
    env = record['environment']
    require(record['exit_code'] == 1, f'{path}: unexpected exit')
    budget = int(env['MW34_FRAME_BUDGET'])
    require(f'Presentation frame budget reached: {budget} frames presented' in
            (path / 'stderr.txt').read_text(), f'{path}: incomplete budget')
    require(env.get('MW34_GPU_MODELS', '0') == str(int(gpu)), f'{path}: wrong path')
    draws = [line.split() for line in (path / 'draw-log.txt').read_text().splitlines()]
    require(len(draws) == budget, f'{path}: incomplete draw stream')
    require(any(int(row[1]) for row in draws), f'{path}: no original geometry')
    with (path / 'geometry.csv').open(newline='') as stream:
        geometry = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    require([r['frame'] for r in geometry] == list(range(1, budget+1)), f'{path}: profile gaps')
    selected = [r for r in geometry if first <= r['frame'] <= last]
    key = 'gpu_vertices' if gpu else 'cpu_vertices'
    require(selected and sum(r[key] for r in selected) > 0, f'{path}: no measured model activity')
    if not gpu:
        require(not sum(r['gpu_vertices'] for r in geometry), f'{path}: mixed CPU case')
    times = [line.split() for line in (path / 'frame-times.txt').read_text().splitlines()]
    require([int(r[0]) for r in times] == list(range(1,budget+1)), f'{path}: timing gaps')
    deltas = [float(times[i][1])-float(times[i-1][1]) for i in range(1,len(times))
              if first <= int(times[i][0]) <= last]
    require(all(int(r[2]) > 0 for r in times if first <= int(r[0]) <= last), f'{path}: menu-only interval')
    require(len(deltas) == last-first+1, f'{path}: incomplete measured interval')
    require(all(v > 0 for v in deltas), f'{path}: invalid presentation timing')
    p95 = sorted(deltas)[int((len(deltas)-1)*.95)]
    tags = dict(zip(draws[-1][3::2], map(int, draws[-1][4::2])))
    if gpu:
        require(tags.get('model_draw',0)>0 and tags.get('model_up',0)>0, f'{path}: no actual GPU model execution')
    mean = lambda key: statistics.mean(r[key] for r in selected)
    cpu_ms = lambda key: statistics.mean(r[key] * 1000 / r['qpc_hz'] for r in selected)
    metrics = {'presentation_mean_ms': statistics.mean(deltas),
               'presentation_median_ms': statistics.median(deltas), 'presentation_p95_ms': p95,
               'replacement_emit_cpu_ms': cpu_ms('emit_ticks'),
               'original_51fb30_inclusive_cpu_ms': cpu_ms('source_ticks'),
               'cpu_vertices_per_frame': mean('cpu_vertices'), 'gpu_vertices_per_frame': mean('gpu_vertices'),
               'replacement_tl_bytes_per_frame': mean('tl_bytes'),
               'near_plane_cpu_batches': sum(r['near_batches'] for r in selected),
               'gpu_uploads_end':tags.get('model_up',0), 'gpu_model_bytes_end':tags.get('model_bytes',0)}
    asset_keys = [k for k in env if k.endswith(('_MESH','_TEXTURES')) or k in
                  ('MW34_BUSHWACKER_TEST','MW34_REMASTER_BANKS')]
    identity = {'executable': record['executable_sha256'], 'input': sha(path/'input-script.txt'),
                'registry': sha(path/'registry.txt'), 'protected': record['protected_originals'],
                'assets': {k: sha(Path(env[k])) for k in sorted(asset_keys)},
                'settings':{k:env.get(k) for k in ('MW34_REMASTER_WIDTH','MW34_REMASTER_HEIGHT',
                    'MW34_REMASTER_AA','MW34_REMASTER_AF','MW34_REMASTER_DRAW_DISTANCE',
                    'MW34_GPU_HUD','MW34_LAZY_RT','MW34_VIRTUAL_CLOCK','MW34_PERF_OVERLAY')}}
    uploads=[dict(zip(r[3::2],map(int,r[4::2]))).get('model_up',0) for r in draws[first-1:last]]
    metrics['gpu_uploads_during_interval']=max(uploads)-min(uploads)
    return identity, [r[:3] for r in draws], metrics, [(r[0],r[2],r[3]) for r in times]


def ppm(path):
    data=path.read_bytes()
    pieces=data.split(b'\n',3)
    require(len(pieces)==4 and pieces[0]==b'P6' and pieces[2]==b'255', 'Unexpected PPM format')
    w,h=map(int,pieces[1].split())
    require(len(pieces[3])==w*h*3, 'Invalid PPM payload')
    return (w,h),pieces[3]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs',type=Path)
    parser.add_argument('--prefix',default='geometry-r1')
    parser.add_argument('--first',type=int,default=800)
    parser.add_argument('--last',type=int,default=1600)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result={'scope':'Existing replacement-model CPU versus GPU handoff; original producers retained',
            'frames':[args.first,args.last], 'cases':{}}
    reference=None
    for name in ('cpu-a','gpu-a','gpu-b','cpu-b'):
        identity,draws,metrics,clocks=load_case(args.runs/f'{args.prefix}-{name}', name.startswith('gpu'), args.first,args.last)
        if reference is None: reference=(identity,draws,clocks)
        require(identity==reference[0], f'{name}: inputs/build/settings differ')
        require(draws==reference[1], f'{name}: original draws diverged')
        require(clocks==reference[2], f'{name}: original scene/clock sequence diverged')
        result['cases'][name]=metrics
    result['identity']=reference[0]
    # Captures have their own timings and never enter the performance statistics.
    for name in ('cpu-image','gpu-image'):
        identity,draws,_,clocks=load_case(args.runs/f'{args.prefix}-{name}',name.startswith('gpu'),800,1050)
        require(identity==reference[0], f'{name}: capture inputs differ')
        require(draws==reference[1][:len(draws)], f'{name}: capture draws diverged')
        require(clocks==reference[2][:len(clocks)], f'{name}: capture clock diverged')
    size,a=ppm(args.runs/f'{args.prefix}-cpu-image/target-1000.ppm')
    other,b=ppm(args.runs/f'{args.prefix}-gpu-image/target-1000.ppm')
    require(size==other, 'Capture sizes differ')
    differences=[abs(x-y) for x,y in zip(a,b)]
    result['capture']={'size':size,'changed_pixels':sum(a[i:i+3]!=b[i:i+3] for i in range(0,len(a),3)),
                       'max_channel_difference':max(differences),'mean_absolute_channel_difference':statistics.mean(differences),
                       'requires_visual_review':True}
    cpu=statistics.mean(result['cases'][n]['presentation_mean_ms'] for n in ('cpu-a','cpu-b'))
    gpu=statistics.mean(result['cases'][n]['presentation_mean_ms'] for n in ('gpu-a','gpu-b'))
    result['comparison']={'cpu_mean_ms':cpu,'gpu_mean_ms':gpu,'frame_time_reduction_percent':100*(cpu-gpu)/cpu,
                          'throughput_ratio':cpu/gpu,'gpu_timestamp_measurement':False}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cases':result['cases'],'comparison':result['comparison'],'capture':result['capture']},indent=2))


if __name__=='__main__': main()
