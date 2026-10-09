"""Retain frozen native caller/setup; add independently authored heap tests."""
import hashlib
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
HERE=Path(__file__).absolute().parent
old=(ROOT/'tools/m4-crt-locale-default-contract/review/controls.cpp').read_text()
prefix=old[:old.index(' void verify(bool clean)')]
def replace(a,b):
    global prefix
    if a not in prefix: raise ValueError('Frozen caller setup association: '+a)
    prefix=prefix.replace(a,b)
replace('MW34_CRT_LOCALE_DEFAULT_NO_MAIN','MW34_CRT_HEAP_INIT_NO_MAIN')
replace('which>=97?which:0','which>=109?which:0')
start=prefix.index('auto&l=mainargs->locale;raw_output(row/"locale-accesses.bin"')
end=prefix.index('return job;',start)
prefix=prefix[:start]+'''auto&h=mainargs->heap;raw_output(row/"heap-accesses.bin",h.accesses);raw_output(row/"heap-events.bin",h.events);raw_output(row/"heap-undefined-sites.bin",h.undefined_sites);raw_output(row/"heap-scheduler.bin",h.scheduler);std::array<unsigned,26>hs{mode,h.control,h.frame,h.parent_frame,h.access_count,h.event_count,h.undefined_count,h.stage,h.depth,h.fault_pc,h.fault_address,unsigned(h.used),unsigned(h.active),unsigned(h.failed),unsigned(h.api_reached),h.caller_error,h.restored_error,hi::fragment,hi::entry,hi::site,hi::ret,hi::api_site,hi::iat,hi::api_ret,hi::raw_import,84};raw_output(row/"heap-status.bin",hs);'''+prefix[end:]
replace('ld::','hi::')
replace('locale','heap')
replace('parser->heap_reached','parser->locale_reached')
replace('!mainargs->heap.depth&&!hi::owner','!mainargs->heap.depth&&!hi::owner&&!hi::has_authority()')
replace('16 pages/runtime CPU','17 pages/runtime CPU')
replace('std::memcpy(heap_object.data(),&mainargs->heap,heap_object.size());','std::memcpy(heap_object.data(),&mainargs->heap,heap_object.size());std::array<std::byte,sizeof(ld::Binding)>unused_locale{};std::memcpy(unused_locale.data(),&mainargs->locale,unused_locale.size());')
replace('"Poisoned retry preserves complete public/private heap object and immutable source/parent/firstfault identity");','"Poisoned retry preserves complete public/private heap object and immutable source/parent/firstfault identity");review_need(!std::memcmp(unused_locale.data(),&mainargs->locale,unused_locale.size()),"Unused accepted locale object remains intact during poisoned retry");')
(HERE/'controls.cpp').write_text(prefix+(HERE/'fixture_tail.inc').read_text(),encoding='utf-8')
print(hashlib.sha256((HERE/'controls.cpp').read_bytes()).hexdigest())
