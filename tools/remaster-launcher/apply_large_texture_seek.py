"""Apply the unsigned replacement texture offset adapter to a derived host."""
from pathlib import Path
import argparse
import shutil


def apply(host):
    host = Path(host)
    shutil.copy2(Path(__file__).with_name('native-overrides') / 'large_texture_seek.hpp',
                 host / 'large_texture_seek.hpp')
    path = host / 'remaster_banks.inc'
    text = path.read_text(encoding='utf-8')
    old = 'std::string remaster_bank(const std::filesystem::path&path,const std::filesystem::path&game){\n static const auto banks='
    if text.count(old) != 1:
        raise ValueError('Unexpected bank map reader')
    text = text.replace(old, 'const std::map<std::string,std::string>& remaster_banks(){\n static const auto banks=')
    old = 'return result;}();\n auto key='
    if text.count(old) != 1:
        raise ValueError('Unexpected bank map closure')
    text = text.replace(old, '''return result;}();return banks;
}
bool remaster_bank_target(const std::string&path){
 const auto& banks=remaster_banks();return std::any_of(banks.begin(),banks.end(),[&](const auto&entry){return entry.second==path;});
}
std::string remaster_bank(const std::filesystem::path&path,const std::filesystem::path&game){
 const auto& banks=remaster_banks();auto key=''')
    path.write_text(text, encoding='utf-8')
    path = host / 'mfc_stage.hpp'
    text = path.read_text(encoding='utf-8')

    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('Unexpected host seam: ' + old[:90])
        text = text.replace(old, new)

    replace('#include "heap_partitions.hpp"', '#include "heap_partitions.hpp"\n#include "large_texture_seek.hpp"')
    replace('std::string cwd;std::vector<unsigned>files;',
            'std::string cwd;std::vector<unsigned>files;std::set<unsigned>replacement_bank_files;unsigned large_texture_seeks{};')
    replace('const unsigned g2=ghandle(h);host.files.push_back(g2);return done(g2,7);}',
            'const unsigned g2=ghandle(h);host.files.push_back(g2);if(!writes&&(acc&GENERIC_READ)&&disp==OPEN_EXISTING&&remaster_bank_target(q))host.replacement_bank_files.insert(g2);return done(g2,7);}')
    replace('DWORD r{};{LastError l(host);r=::SetFilePointer(hhandle(h),LONG(arg(1)),ph?&hi:nullptr,arg(3));}if(ph)store(ph,unsigned(hi));return done(r,4);}',
            '''const bool wide=mw34::texture_banks::unsigned_archive_seek(host.replacement_bank_files.count(h)!=0,arg(1),ph,arg(3),std::span<const unsigned>(returns.data(),depth));
   DWORD r{};{LastError l(host);r=::SetFilePointer(hhandle(h),LONG(arg(1)),(ph||wide)?&hi:nullptr,arg(3));}
   if(wide&&(++host.large_texture_seeks<=8||r==INVALID_SET_FILE_POINTER))std::fprintf(stderr,"Replacement texture seek: unsigned offset=%08x result=%08x error=%u\\n",arg(1),unsigned(r),host.last_error);
   if(ph)store(ph,unsigned(hi));return done(r,4);}''')
    replace('host.files.erase(it);return done(ok?1U:0U,1);}',
            'host.files.erase(it);host.replacement_bank_files.erase(h);return done(ok?1U:0U,1);}')
    path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
