from pathlib import Path
H=Path(__file__).resolve().parent
def main():
 p=H/'benchmark.py';t=p.read_text()
 old="""    with DirectSet(legacy,pinned) as old,SharedDirectSet(shared,sha_file(shared)) as new:
        need(set(old.entries)==set(new.entries)==set(name for name,_ in expected),'Unchanged exact logical consumer inventory')
        for name,data in expected:need(old.data(name)==new.data(name)==data,'Complete logical bytes unchanged '+name)
        return {'exact_full_byte_records':len(expected),'logical_bytes':sum(len(data) for _,data in expected),'shared_unique_blobs':new.meta['unique_blobs'],'shared_unique_payload_bytes':new.meta['unique_payload_bytes']}"""
 new="""    old=DirectSet(legacy,pinned)
    try:
        with SharedDirectSet(shared,sha_file(shared)) as new:
            need(set(old.entries)==set(new.entries)==set(name for name,_ in expected),'Unchanged exact logical consumer inventory')
            for name,data in expected:need(old.data(name)==new.data(name)==data,'Complete logical bytes unchanged '+name)
            return {'exact_full_byte_records':len(expected),'logical_bytes':sum(len(data) for _,data in expected),'shared_unique_blobs':new.meta['unique_blobs'],'shared_unique_payload_bytes':new.meta['unique_payload_bytes']}
    finally:old.close()"""
 assert t.count(old)==1;t=t.replace(old,new)
 t=t.replace('    value=peak(p._handle)\n    if value is not None:observed=max(observed,value);samples+=1','    final_counter=peak(p._handle)\n    if final_counter is not None:observed=max(observed,final_counter);samples+=1')
 t=t.replace("'peak_counter_final_query_succeeded':value is not None","'peak_counter_final_query_succeeded':final_counter is not None")
 t=t.replace("pin(files,H/'benchmark.py');pin(files,H/'read_probe.py')","pin(files,H/'benchmark.py');pin(files,H/'benchmark_v2.py');pin(files,H/'prepare_benchmark_v2.py');pin(files,H/'read_probe.py')")
 out=H/'benchmark_v2.py';assert not out.exists();out.write_text(t,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
