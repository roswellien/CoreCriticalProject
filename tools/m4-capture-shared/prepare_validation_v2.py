from pathlib import Path
H=Path(__file__).resolve().parent
def main():
 p=H/'validate_pilot.py';t=p.read_text().replace('from capture_shared_v2 import','from capture_shared_v3 import')
 t=t.replace("('capture_shared_v2.py','prepare_reader_v2.py','validate_pilot.py')","('capture_shared_v2.py','capture_shared_v3.py','prepare_reader_v2.py','prepare_reader_v3.py','validate_pilot.py','validate_pilot_v2.py','prepare_validation_v2.py')")
 t=t.replace("    return build","    pin(files,ROOT/'reports/m4-capture-shared/reader-repair-r2/report.json');pin(files,ROOT/'reports/m4-capture-shared/reader-repair-r2/reader.diff')\n    return build",1)
 t=t.replace("==0x400,'Actual set direction flag'","==0,'Actual ABI clear direction flag'")
 t=t.replace("'raw_sha256':sha_file(path)","'direction_flag_domain':'Actual ABI-clear DF before/after equality; set-DF callers not claimed','raw_sha256':sha_file(path)")
 t=t.replace("reject('truncated',raw[:-1],'exact extent')","reject('truncated',raw[:-1],'blob SHA256')")
 needle="    for name,expected,mutate in cases:index=copy.deepcopy(base);mutate(index);reject(name,archive(index,payload),expected)"
 assert t.count(needle)==1
 t=t.replace(needle,needle+"""
    for kind in ('bool','float'):
        transform=(lambda n:True) if kind=='bool' else (lambda n:float(n))
        for key in ('logical_bytes','unique_bytes'):
            index=copy.deepcopy(base);index[key]=transform(index[key]);reject(key+'-'+kind,archive(index,payload),'Invalid')
        for key in ('offset','size'):
            index=copy.deepcopy(base);index['blobs'][0][key]=transform(index['blobs'][0][key]);reject('blob-'+key+'-'+kind,archive(index,payload),'Invalid')
        index=copy.deepcopy(base);index['files'][0]['blob_id']=transform(index['files'][0]['blob_id']);reject('blob-id-'+kind,archive(index,payload),'reference')
""")
 needle="    test('extra-physical',lambda x:None,'physical inventory','extra.bin')"
 t=t.replace(needle,needle+"""
    for kind in ('bool','float'):
        transform=(lambda n:True) if kind=='bool' else (lambda n:float(n))
        for key in ('logical_files','payload_bytes','unique_blobs','unique_payload_bytes'):
            test('set-'+key+'-'+kind,lambda x,key=key:x.update({key:transform(x[key])}),'count mismatch')
        for key in ('bundle_bytes','index_bytes','logical_files','payload_bytes','unique_blobs','unique_payload_bytes'):
            test('part-'+key+'-'+kind,lambda x,key=key:x['parts'][0].update({key:transform(x['parts'][0][key])}),'extent type' if key in ('bundle_bytes','index_bytes') else 'count mismatch')
""")
 target=H/'validate_pilot_v2.py';assert not target.exists();target.write_text(t,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
