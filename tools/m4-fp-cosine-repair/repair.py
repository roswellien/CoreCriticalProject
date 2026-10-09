"""Measured exact cosine status repairs; all numerical IR stays unchanged."""
from pathlib import Path
import json
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-fp-native'))
from adapt_first import digest,require
HOST_SHAS={
 '4ce5a0':'207ec0e809895cf7346a30b720f950aeaeabcfd5c651d347a717a6384dd9768a',
 '4ce5c0':'8de31a721309aa9bf1dd24bfc5647f6f7b6df08e3885e441612427ebcafc9377',
 '4ce5e0':'89cfb2e34ea58f2f79b937f0187721be7e5ad75ca5d99362f2daf1f94932fcb3',
 '4ce600':'7c0b8ec3ef64eedaca93156a81be2a4ca8ded94a75dc0b511b66f758dba6fb96'}

def main():
    directory=Path(sys.argv[1]).resolve()
    require(directory.is_relative_to(ROOT/'reports/m4-fp-transcendental') and not directory.exists(),'Fresh private status repair directory required')
    directory.mkdir(parents=True);records=[]
    for stem,sha in HOST_SHAS.items():
        original=ROOT/'reports/m4-fp-transcendental/cosine-host-r1'/f'{stem}.ll'
        require(digest(original)==sha,'Exact baseline cosine host required')
        source=original.read_text();transformed=source
        before='  call void @mw34_actual_fcos_raw80(ptr %mw.cos.input, ptr %mw.cos.output)'
        require(transformed.count(before)==1,'Exact FCOS pointer boundary required')
        transformed=transformed.replace(before,'  call void @mw34_actual_fcos_status_raw80(ptr %state, ptr %mw.cos.input, ptr %mw.cos.output)')
        before='declare void @mw34_actual_fcos_raw80(ptr, ptr)'
        require(transformed.count(before)==1,'Exact FCOS declaration required')
        transformed=transformed.replace(before,'declare void @mw34_actual_fcos_status_raw80(ptr, ptr, ptr)')
        before='  %186 = call i32 @__remill_fpu_exception_test(i32 noundef 127) #6'
        require(transformed.count(before)==1,'Exact second exception test required')
        transformed=transformed.replace(before,'  %186 = call i32 @mw34_fp_store_exception_test(ptr %state, i32 127)')
        transformed+='\ndeclare i32 @mw34_fp_store_exception_test(ptr, i32)\n'
        for site,value,pointer in [('fcos','%115','%116'),('fstp','%183','%184')]:
            before=f'  store i8 {value}, ptr {pointer}, align 1'
            require(transformed.count(before)==1,'Exact DE overwrite required '+site)
            after=(f'  %mw.{site}.old.de = load i8, ptr {pointer}, align 1\n'
             f'  %mw.{site}.sticky.de = or i8 {value}, %mw.{site}.old.de\n'
             f'  store i8 %mw.{site}.sticky.de, ptr {pointer}, align 1')
            transformed=transformed.replace(before,after)
        host=directory/f'{stem}.ll';host.write_text(transformed)
        records.append({'entry':int(stem,16),'baseline_host_sha256':sha,'host_sha256':digest(host),
          'repairs':['Typed real FCOS C2 capture','Typed real final FSTP C1 capture','Preserve prior DE at FCOS and FSTP overwrite'],
          'numerical_IR_changed':False,'native_admitted':False})
    bindings={str(p):digest(p) for p in directory.iterdir()}
    for p in (Path(__file__).resolve(),ROOT/'tools/m4-fp-native/adapt_first.py'):bindings[str(p)]=digest(p)
    (directory/'adapter.json').write_text(json.dumps({'passed':True,'scope':'Exact measured status-only static IR repair',
      'records':records,'bindings':bindings},indent=2)+'\n')
    print(json.dumps({'status_repaired_candidates':len(records),'native_admitted':False}))

if __name__=='__main__':main()
