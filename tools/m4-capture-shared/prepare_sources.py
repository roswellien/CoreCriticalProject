"""Additive pilot source derivation. Never writes a canonical capture file."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'tools/m4-capture-direct'
PINS={
 'capture_direct_v3.hpp':'a3ebcc1f62393a55b9996c608a7fbb6db139a875f17b72be1bca9b4539ec81ea',
 'capture_direct_v3.cpp':'1a14d008bf2ba395f361ecb836e1ec3aa1887212d60ecadd38342043a6f406f4',
 'preserve_v2.s':'4a6658025e37778b06f71ec343252b52b4f55d8980af0468a5d362b24c665963',
 'driver_v3.cpp':'baae96182a16af7269fde8dfc36c90b7b243a83e45e6f63daa7263cef1d3c7b7',
}
def changed(text,old,new):
 assert text.count(old)==1,(old[:100],text.count(old))
 return text.replace(old,new)
def main():
 for name,pin in PINS.items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==pin,name
 h=(BASE/'capture_direct_v3.hpp').read_text().replace('capture_direct','capture_shared')
 h=changed(h,'std::uint64_t fail_after_written_bytes=UINT64_MAX;',
 '''std::uint64_t fail_after_written_bytes=UINT64_MAX;
    // Fixture-only lookup collision; stored SHA256 always remains genuine.
    bool force_hash_key_collision=false;''')
 h=h.replace('payload_bytes=0,bundle_bytes=0,index_bytes=0;', 'payload_bytes=0,bundle_bytes=0,index_bytes=0,unique_blobs=0,unique_payload_bytes=0;')
 h=h.replace('logical_files=0,payload_bytes=0;', 'logical_files=0,payload_bytes=0,unique_blobs=0,unique_payload_bytes=0;')
 c=(BASE/'capture_direct_v3.cpp').read_text().replace('capture_direct_v3.hpp','capture_shared.hpp').replace('namespace mw34::capture_direct','namespace mw34::capture_shared')
 c=c.replace('#include <set>','#include <set>\n#include <map>\n#include <cstring>')
 c=changed(c,'struct Entry {std::string name,digest;std::uint64_t spool_offset=0,size=0;};',
 '''struct Entry {std::string name;std::uint64_t blob_id=0;};
    struct Blob {std::string digest;std::uint64_t spool_offset=0,size=0;};''')
 c=changed(c,'std::vector<Entry> entries;',
 '''std::vector<Entry> entries;
    std::vector<Blob> blobs;
    std::map<std::string,std::vector<std::uint64_t>> lookup;''')
 c=c.replace('index_estimate=70','index_estimate=128').replace('index_bytes_per_part>=70','index_bytes_per_part>=128')
 a=c.index('    void append(std::string_view name,const void* data,std::size_t size){')
 b=c.index('    void finish(){',a)
 c=c[:a]+r'''    std::uint64_t find_blob(const std::string& key,const std::vector<unsigned char>& bytes){
        auto found=lookup.find(key);if(found==lookup.end())return UINT64_MAX;
        std::vector<unsigned char> block(std::min<std::size_t>(bytes.size(),1u<<20));
        for(auto id:found->second){const auto& old=blobs.at(id);if(old.size!=bytes.size())continue;
            seek(spool,old.spool_offset);std::size_t at=0;bool same=true;
            while(at<bytes.size()){auto n=std::min(block.size(),bytes.size()-at);read(spool,block.data(),n);if(std::memcmp(block.data(),bytes.data()+at,n)!=0){same=false;break;}at+=n;}
            if(same)return id;
        }
        return UINT64_MAX;
    }
    void append(std::string_view name,const void* data,std::size_t size){
        alive();auto normalized=name_key(name);need(size<=max_file&&(size==0||data!=nullptr),"Capture entry extent/pointer");need(!names.contains(normalized),"Duplicate normalized capture name");
        auto started=Clock::now();
        // Owned immutable snapshot: no caller buffer survives the append boundary.
        std::vector<unsigned char> snapshot(size);if(size)std::memcpy(snapshot.data(),data,size);
        auto actual_digest=hex(digest(snapshot.data(),snapshot.size()));
        const std::string key=options.force_hash_key_collision?"forced-fixture-key":actual_digest+":"+number(size);
        auto id=find_blob(key,snapshot);
        const std::uint64_t logical_cost=name.size()+80,blob_cost=140;
        need(logical_cost+blob_cost+128<=options.index_bytes_per_part&&size<=options.bytes_per_part,"Entry fits unchanged part limits");
        auto added_bytes=id==UINT64_MAX?size:0;auto cost=logical_cost+(id==UINT64_MAX?blob_cost:0);
        if(!entries.empty()&&(entries.size()>=options.files_per_part||added_bytes>options.bytes_per_part-spool_bytes||cost>options.index_bytes_per_part-index_estimate)){close_part();id=UINT64_MAX;cost=logical_cost+blob_cost;}
        if(entries.empty()){spool_path=temporary/("part-"+number(receipt.parts.size()+1)+".spool");spool=create(spool_path);}
        if(id==UINT64_MAX){id=blobs.size();seek(spool,spool_bytes);write(spool,snapshot.data(),snapshot.size());blobs.push_back({actual_digest,spool_bytes,size});lookup[key].push_back(id);spool_bytes+=size;}
        names.insert(std::move(normalized));entries.push_back({std::string(name),id});index_estimate+=cost;
        ++receipt.logical_files;receipt.payload_bytes+=size;receipt.emit_seconds+=std::chrono::duration<double>(Clock::now()-started).count();
    }
    void close_part(){
        if(entries.empty())return;
        auto started=Clock::now();win(FlushFileBuffers(spool.value)!=0,"Flush compact spool");
        std::sort(entries.begin(),entries.end(),[](const Entry& a,const Entry& b){return a.name<b.name;});
        std::string index="{\"blobs\":[";std::uint64_t offset=0,logical_bytes=0;
        for(std::size_t i=0;i<blobs.size();++i){const auto& b=blobs[i];if(i)index+=',';index+="{\"offset\":"+number(offset)+",\"sha256\":\""+b.digest+"\",\"size\":"+number(b.size)+"}";offset+=b.size;}
        index+="],\"files\":[";
        for(std::size_t i=0;i<entries.size();++i){const auto& e=entries[i];if(i)index+=',';index+="{\"blob_id\":"+number(e.blob_id)+",\"path\":\""+e.name+"\"}";logical_bytes+=blobs.at(e.blob_id).size;}
        index+="],\"format\":\"mw34.capture.shared.v1\",\"logical_bytes\":"+number(logical_bytes)+",\"unique_bytes\":"+number(offset)+"}";
        need(index.size()<=options.index_bytes_per_part&&offset==spool_bytes&&offset<=options.bytes_per_part&&entries.size()<=options.files_per_part,"Exact shared canonical archive limits");
        auto index_digest=digest(index.data(),index.size());std::vector<unsigned char> header{'M','W','3','4','S','H','R','1'};little(header,index.size(),8);header.insert(header.end(),index_digest.begin(),index_digest.end());need(header.size()==48,"Exact shared archive header");
        auto relative="part-"+number(receipt.parts.size()+1)+".mwb";auto path=temporary/relative;File archive=create(path);Hash whole(algorithm);write(archive,header.data(),header.size());whole.add(header.data(),header.size());write(archive,index.data(),index.size());whole.add(index.data(),index.size());
        std::vector<unsigned char> block(1u<<20);
        for(const auto& b:blobs){seek(spool,b.spool_offset);Hash actual(algorithm);std::uint64_t remaining=b.size;while(remaining){auto step=static_cast<std::size_t>(std::min<std::uint64_t>(remaining,block.size()));read(spool,block.data(),step);actual.add(block.data(),step);write(archive,block.data(),step);whole.add(block.data(),step);remaining-=step;}need(hex(actual.finish())==b.digest,"Owned unique spool record changed before closure");}
        auto expected=hex(whole.finish());win(FlushFileBuffers(archive.value)!=0,"Flush finalized archive");
        seek(archive,0);Hash check(algorithm);std::uint64_t remaining=header.size()+index.size()+offset;while(remaining){auto step=static_cast<std::size_t>(std::min<std::uint64_t>(remaining,block.size()));read(archive,block.data(),step);check.add(block.data(),step);remaining-=step;}need(hex(check.finish())==expected,"Written archive verification hash");
        LARGE_INTEGER extent{};win(GetFileSizeEx(archive.value,&extent)!=0,"Final archive extent");need(static_cast<std::uint64_t>(extent.QuadPart)==header.size()+index.size()+offset,"Final archive exact extent");archive.close();spool.close();win(DeleteFileW(spool_path.c_str())!=0,"Remove completed compact spool");
        receipt.parts.push_back({target/relative,expected,hex(index_digest),entries.size(),logical_bytes,static_cast<std::uint64_t>(extent.QuadPart),index.size(),blobs.size(),offset});receipt.unique_blobs+=blobs.size();receipt.unique_payload_bytes+=offset;
        entries.clear();blobs.clear();lookup.clear();spool_bytes=0;index_estimate=128;receipt.finalize_seconds+=std::chrono::duration<double>(Clock::now()-started).count();
    }
''' +c[b:]
 c=c.replace('mw34.capture.direct.v1','mw34.capture.direct.shared.v1')
 c=changed(c,'+p.sha256+"\\\"}";', '+p.sha256+"\\\",\\\"unique_blobs\\\":"+number(p.unique_blobs)+",\\\"unique_payload_bytes\\\":"+number(p.unique_payload_bytes)+"}";')
 c=changed(c,'+number(receipt.payload_bytes)+",\\\"transport_only\\\":true}";', '+number(receipt.payload_bytes)+",\\\"transport_only\\\":true,\\\"unique_blobs\\\":"+number(receipt.unique_blobs)+",\\\"unique_payload_bytes\\\":"+number(receipt.unique_payload_bytes)+"}";')
 d=(BASE/'driver_v3.cpp').read_text().replace('capture_direct_v3.hpp','capture_shared.hpp').replace('mw34::capture_direct','mw34::capture_shared')
 d=changed(d,'else if(key=="--fail-after")options.fail_after_written_bytes=value;', 'else if(key=="--fail-after")options.fail_after_written_bytes=value;else if(key=="--force-key-collision"){need(value<=1,"Boolean collision fixture");options.force_hash_key_collision=value!=0;}')
 d=changed(d,'<<r.payload_bytes<<",\\\"transport_only\\\":true,', '<<r.payload_bytes<<",\\\"unique_blobs\\\":"<<r.unique_blobs<<",\\\"unique_payload_bytes\\\":"<<r.unique_payload_bytes<<",\\\"transport_only\\\":true,')
 for name,text in [('capture_shared.hpp',h),('capture_shared.cpp',c),('driver.cpp',d)]:
  path=HERE/name;assert not path.exists(),path;path.write_text(text,encoding='utf-8',newline='\n')
 for name in ['preserve_v2.s','hardware.s']:
  path=HERE/name;assert not path.exists();path.write_bytes((BASE/name).read_bytes())
 receipt={'passed':True,'transport_only':True,'game_executed':False,'canonical_inputs_unchanged':PINS,'outputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()},'scope':'Additive pilot derivation only; no capture-format adoption'}
 out=ROOT/'reports/m4-capture-shared/preparation-r1';out.mkdir(parents=True,exist_ok=False);(out/'report.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
