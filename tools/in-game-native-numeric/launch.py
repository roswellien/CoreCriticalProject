"""Build, validate and launch the live numeric initializer x64 experiment."""
import argparse
import ctypes
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).resolve().parent
PWSH=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def hidden(command, **kwargs):
    return subprocess.Popen([str(x) for x in command], cwd=ROOT,
                            creationflags=subprocess.CREATE_NO_WINDOW, **kwargs)

def fresh_run():
    run=ROOT/'reports/mw3-live-native-numeric'/(datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-'+uuid.uuid4().hex[:8])
    run.mkdir(parents=True,exist_ok=False)
    return run

def start_worker(manifest,run,tag):
    spec=manifest['workers']['O2']
    worker=Path(spec['worker']); obj=Path(spec['object'])
    if sha(worker)!=spec['sha256'] or sha(obj)!=spec['object_sha256']:
        raise RuntimeError('Prepared worker/object identity changed')
    pipe=r'\\.\pipe\mw34-numeric-'+uuid.uuid4().hex
    env=os.environ.copy();env['MW34_NUMERIC_PIPE']=pipe
    out=(run/(tag+'-worker.stdout.log')).open('xb')
    err=(run/(tag+'-worker.stderr.log')).open('xb')
    try:
        process=hidden([worker,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',obj,pipe],
                       env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
    finally:
        out.close();err.close()
    return process,env,pipe

def run_hook(manifest,run,selftest):
    tag='selftest' if selftest else 'game'
    worker,env,pipe=start_worker(manifest,run,tag)
    command=[manifest['launcher']]
    if selftest: command.append('--selftest')
    command += [str(ROOT/'MW3/Mech3.exe'),manifest['hook'],str(run/(tag+'.jsonl'))]
    with (run/(tag+'-launcher.stdout.log')).open('xb') as out, (run/(tag+'-launcher.stderr.log')).open('xb') as err:
        try:
            result=subprocess.run(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                                  creationflags=subprocess.CREATE_NO_WINDOW,timeout=55)
        except Exception:
            if worker.poll() is None: worker.terminate();worker.wait(timeout=5)
            raise
    if result.returncode:
        if worker.poll() is None: worker.terminate();worker.wait(timeout=5)
        detail=(run/(tag+'-launcher.stderr.log')).read_text(errors='replace')
        raise RuntimeError(f'{tag} launcher failed ({result.returncode}): {detail}')
    if selftest:
        if worker.wait(timeout=12)!=0:
            raise RuntimeError('Selftest worker did not exit cleanly')
    return worker,pipe

def start_monitor(run,pid):
    session=ROOT/'reports/mw3-monitor'/('numeric-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
    command=[sys.executable,ROOT/'tools/game-monitor/monitor.py','attach','--game',ROOT/'MW3/Mech3.exe',
             '--pid',str(pid),'--session',session,'--log',run/'game.jsonl']
    with (run/'monitor.stdout.log').open('xb') as out, (run/'monitor.stderr.log').open('xb') as err:
        collector=hidden(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
    return collector.pid,str(session)

def hold_game(run,pid):
    # Keep the foreground research owner alive while the game is running. Some
    # execution hosts tie background child lifetime to their owner process.
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    kernel.WaitForSingleObject.restype=ctypes.c_uint32
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
    kernel.GetExitCodeProcess.restype=ctypes.c_int
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x100000|0x1000,False,pid)
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    try:
        while True:
            state=kernel.WaitForSingleObject(handle,1000)
            if state==0: break
            if state!=258: raise ctypes.WinError(ctypes.get_last_error())
        code=ctypes.c_uint32()
        if not kernel.GetExitCodeProcess(handle,ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        (run/'game-exit.json').write_text(json.dumps({'game_pid':pid,'exit_code':code.value,'observed_utc':datetime.now().astimezone().isoformat()},indent=2))
        print(f'Game exited with code {code.value}. Evidence: {run}',flush=True)
    finally: kernel.CloseHandle(handle)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--build-report',type=Path)
    parser.add_argument('--hold',action='store_true',help='keep the research owner alive until this game exits')
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT/'tools/game-monitor'))
    from win32 import pids_for_image
    if not args.prepare_only and pids_for_image(ROOT/'MW3/Mech3.exe'):
        raise RuntimeError('Close the existing MW3 session before this live test')
    if args.build_report:
        report=args.build_report.resolve()
    else:
        result=subprocess.run([str(PWSH),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(SOURCE/'build.ps1')],
                              cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(result.stdout,flush=True)
        if result.returncode: raise RuntimeError('Numeric bridge build failed; retained build logs show the failure')
        marker='NUMERIC_BUILD_REPORT='
        report=Path(next(line[len(marker):] for line in result.stdout.splitlines() if line.startswith(marker)))
    manifest=json.loads(report.read_text(encoding='utf-8-sig'))
    if not manifest['passed']: raise RuntimeError('Build report failed')
    for path,digest in manifest['source_files'].items():
        if sha(path)!=digest: raise RuntimeError(f'Prepared source changed: {path}')
    run=fresh_run()
    (run/'build-report.json').write_text(json.dumps({'path':str(report),'sha256':sha(report)},indent=2))
    print(f'Numeric test evidence: {run}',flush=True)
    for level,spec in manifest['workers'].items():
        command=[sys.executable,SOURCE/'worker_preflight.py','--worker',spec['worker'],'--game',ROOT/'MW3/Mech3.exe',
                 '--provider',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','--object',spec['object'],'--output',run/(level+'-preflight')]
        subprocess.run([str(x) for x in command],cwd=ROOT,check=True,timeout=50)
    run_hook(manifest,run,True)
    record={'build_report':str(report),'build_report_sha256':sha(report),
            'hook_sha256':sha(manifest['hook']),'launcher_sha256':sha(manifest['launcher']),
            'game_sha256':sha(ROOT/'MW3/Mech3.exe'),'workers':manifest['workers'],
            'preflight_passed':True,'game_launched':False,'full_M4_complete':False}
    if args.prepare_only:
        (run/'launch.json').write_text(json.dumps(record,indent=2))
        print('Preflight passed. Live numeric launcher is ready.',flush=True)
        return 0
    worker,pipe=run_hook(manifest,run,False)
    deadline=time.monotonic()+12
    events=[]
    while time.monotonic()<deadline:
        events=[json.loads(line) for line in (run/'game.jsonl').read_text().splitlines()]
        if any(e.get('event') in ('game_call','fatal') for e in events): break
        if worker.poll() is not None: break
        time.sleep(.1)
    installed=next((e for e in events if e.get('event')=='installed'),None)
    if not installed: raise RuntimeError('Game installation receipt missing; inspect new trace before retrying')
    fatal=next((e for e in events if e.get('event')=='fatal'),None)
    if fatal: raise RuntimeError(f'Live callback stopped before continuation: {fatal}')
    record.update(game_launched=True,game_pid=installed['pid'],worker_pid=worker.pid,pipe=pipe)
    collector,session=start_monitor(run,installed['pid'])
    record.update(collector_pid=collector,monitor_session=session)
    (run/'launch.json').write_text(json.dumps(record,indent=2))
    actual=[e for e in events if e.get('event')=='game_call']
    if not actual: print('Game launched; no initializer result yet. Inspect game.jsonl.',flush=True)
    elif actual[-1].get('native_applied'):
        print(f"Live numeric x64 result verified and applied. Game PID {installed['pid']}; worker PID {worker.pid}.",flush=True)
    else:
        print('Game callback observed; x64 input was rejected. Original result used; no native test credit.',flush=True)
    print(f'Passive monitor: {session}',flush=True)
    if args.hold: hold_game(run,installed['pid'])
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as error:
        print(f'Numeric launch failed: {error}',file=sys.stderr)
        raise SystemExit(1)
