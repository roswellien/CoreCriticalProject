"""Recheck a narrow MFC prerequisite inventory against frozen source bindings."""
import argparse
import hashlib
import importlib.util
import json
import ntpath
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('owned_mfc_recovery',Path(__file__).with_name('recover.py'))
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inventory',default='reports/m4-mfc-provider-state/recovery-r1/inventory.json')
    parser.add_argument('--out',default='reports/m4-mfc-provider-state/check-r1')
    args=parser.parse_args()
    source=ROOT/args.inventory
    out=ROOT/args.out
    M.need(not out.exists(),'Fresh owned checker output required')
    expected_root=ntpath.normcase(ntpath.normpath(str(ROOT/'reports/m4-mfc-provider-state')))
    out_key=ntpath.normcase(ntpath.normpath(str(out.absolute())))
    M.need(out_key.startswith(expected_root+'\\'),'Output must stay in owned report namespace')
    receipt=json.loads(source.with_name('report.json').read_text())
    pins=json.loads(source.with_name('pins.json').read_text())
    M.need(receipt['passed'] and M.digest(source.read_bytes())==receipt['inventory_sha256'] and
           M.digest(source.with_name('pins.json').read_bytes())==receipt['pins_sha256'],'Exact successful source receipt')
    observed={}
    for item in pins['files']:
        path=Path(item['path']);key=ntpath.normcase(ntpath.normpath(str(path.absolute())))
        data=path.read_bytes()
        M.need(len(data)==item['size_bytes'] and M.digest(data)==item['sha256'],'Current physical source pin')
        M.need(key not in observed or observed[key]==item['sha256'],'No path association conflict')
        observed[key]=item['sha256']
    doc=json.loads(source.read_text())
    images={name:M.PEImage(Path(info['path']).read_bytes()) for name,info in doc['images'].items()}
    old={name:json.loads(Path(info['path']).read_text()) for name,info in doc['prior_receipts'].items()}
    rows={name:M.decoded_rows(Path(info['path']).read_text(),images[name])
          for name,info in doc['source_disassemblies'].items()}
    M.validate(doc,images,old,rows)
    own=Path(__file__).absolute()
    report=dict(passed=True,scope='Rechecked original-byte local CFGs and explicit prerequisite ordering; no code execution',
                source_report_sha256=M.digest(source.with_name('report.json').read_bytes()),
                source_inventory_sha256=M.digest(source.read_bytes()),source_pins_sha256=M.digest(source.with_name('pins.json').read_bytes()),
                checker=dict(path=str(own),sha256=M.digest(own.read_bytes())),
                unique_physical_bindings=len(observed),selected_local_CFGs=len(doc['bodies']),
                gates=len(doc['gates']),native_execution_credit=False,actual_loaded_mfc_provider=None)
    out.mkdir(parents=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(report=report,report_sha256=M.digest((out/'report.json').read_bytes()))))


if __name__=='__main__':main()
