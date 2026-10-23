"""Remove bulk service-history compaction from the live native host thread."""
from pathlib import Path
import argparse
import shutil


def apply(host):
    host = Path(host)
    path = host / 'mfc_stage.hpp'
    text = path.read_text(encoding='utf-8')
    pairs = [('#include "heap_partitions.hpp"', '#include "heap_partitions.hpp"\n#include "service_history.hpp"'),
             ('std::vector<std::string>apis;', 'mw34::ServiceHistory apis;'),
             ('mutable std::string label[3];', 'mutable const std::string*label[3]{};'),
             ('std::vector<Import>imports,crt_imports,game_imports;',
              'std::vector<Import>imports,crt_imports,game_imports;std::deque<std::string>service_labels;'),
             ('if(apis.size()>=400000){apis.erase(apis.begin(),apis.begin()+200000);apis_dropped+=200000;}',
              'if(apis.size()>=400000)++apis_dropped;'),
             ('if(lb.empty())lb=(crt?"MSVCRT>":gi?"GAME>":"")+imp->dll+"!"+n;apis.push_back(lb);',
              'if(!lb){host.service_labels.push_back((crt?"MSVCRT>":gi?"GAME>":"")+imp->dll+"!"+n);lb=&host.service_labels.back();}apis.push_back(lb);')]
    for before, after in pairs:
        if text.count(before) != 1:
            raise ValueError('Unexpected service history source: ' + before)
        text = text.replace(before, after)
    shutil.copy2(Path(__file__).with_name('native-overrides') / 'service_history.hpp', host / 'service_history.hpp')
    path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
