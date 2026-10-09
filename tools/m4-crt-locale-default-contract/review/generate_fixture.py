"""Reuse frozen independent caller/setup machinery; add new locale tests."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).absolute().parents[3]
HERE = Path(__file__).absolute().parent
source = ROOT / 'tools/m4-crt-parser-prefix-review/controls.cpp'
old = source.read_text()
prefix = old[:old.index(' void verify(bool clean)')]
prefix = prefix.replace('MW34_CRT_PARSER_PREFIX_NO_MAIN', 'MW34_CRT_LOCALE_DEFAULT_NO_MAIN')
prefix = prefix.replace('std::array<std::byte,16*4096>', 'std::array<std::byte,17*4096>')
prefix = prefix.replace('void review_parser(pp::Binding&,unsigned);', 'void review_parser(pp::Binding&,unsigned);void review_locale(ld::Binding&,unsigned);')
prefix = prefix.replace(' std::unique_ptr<pp::Binding>parser,stale_parser;', ' std::unique_ptr<pp::Binding>parser,stale_parser;std::unique_ptr<ld::Binding>stale_locale;')
prefix = prefix.replace('mainargs=std::make_unique<MainargsBinding>(r,review_provider,0);', 'mainargs=std::make_unique<MainargsBinding>(r,review_provider,which>=97?which:0);')
prefix = prefix.replace('  fdiv=std::make_unique<fd::Registry>(r);', '  {const auto page=provider_raw_page(review_provider,0x78003000);r.memory().map({0x78003000},4096,Permissions::read|Permissions::write);r.memory().write({0x78003000},page);r.memory().protect({0x78003000},Permissions::read|Permissions::execute);}\n  fdiv=std::make_unique<fd::Registry>(r);')
prefix = prefix.replace('stale_parser=std::make_unique<pp::Binding>(*stale_context,*stale_commandline,review_provider);', 'stale_parser=std::make_unique<pp::Binding>(*stale_context,*stale_commandline,review_provider);mainargs->locale.extra=&review_locale;stale_locale=std::make_unique<ld::Binding>(*stale_context,review_provider);')
prefix = prefix.replace('~ReviewFixture(){', '~ReviewFixture(){ld::binding=nullptr;ld::admitted_binding=nullptr;ld::owner=nullptr;')
prefix = prefix.replace('pp::admitted_binding=parser.get();SetLastError', 'pp::admitted_binding=parser.get();ld::binding=&mainargs->locale;ld::admitted_binding=&mainargs->locale;SetLastError')
prefix = prefix.replace('pp::admitted_binding=nullptr;\n  if', 'pp::admitted_binding=nullptr;ld::binding=nullptr;ld::admitted_binding=nullptr;\n  if')
prefix = prefix.replace('!parser->active&&!parser->depth&&!pp::owner', '!parser->active&&!parser->depth&&!pp::owner&&!mainargs->locale.active&&!mainargs->locale.depth&&!ld::owner')
prefix = prefix.replace('last_job=job;', 'review_need(mainargs->locale.caller_error==mainargs->locale.restored_error,"Actual explicit locale caller LastError restored on clean/fault exits");last_job=job;')
old_return = 'raw_output(row/"parser-status.bin",ps);return job;'
new_return = 'raw_output(row/"parser-status.bin",ps);auto&l=mainargs->locale;raw_output(row/"locale-accesses.bin",l.accesses);raw_output(row/"locale-events.bin",l.events);std::array<unsigned,24>ls{mode,l.control,l.frame,l.parent_frame,l.access_count,l.event_count,l.stage,l.depth,l.fault_pc,l.fault_address,unsigned(l.used),unsigned(l.active),unsigned(l.failed),unsigned(l.malloc_reached),l.caller_error,l.restored_error,ld::entry,ld::setmbcp,ld::lock,ld::malloc_call,ld::malloc_entry,ld::malloc_ret,ld::lock_slot,269};raw_output(row/"locale-status.bin",ls);return job;'
if prefix.count(old_return) != 1:
    raise ValueError('One unchanged independent caller output return')
prefix = prefix.replace(old_return, new_return)
prefix = prefix.replace('void retry(){auto&c=mainargs->context;', 'void retry(){auto&c=mainargs->context;std::array<std::byte,sizeof(ld::Binding)>locale_object{};std::memcpy(locale_object.data(),&mainargs->locale,locale_object.size());')
prefix = prefix.replace('"Poisoned retry preserves full parser Binding/first fault/lifecycle/ledgers/private source identity");', '"Poisoned retry preserves full parser Binding/first fault/lifecycle/ledgers/private source identity");review_need(!std::memcmp(locale_object.data(),&mainargs->locale,locale_object.size()),"Poisoned retry preserves complete public/private locale object and immutable source/parent/firstfault identity");')
(HERE / 'controls.cpp').write_text(prefix + (HERE / 'fixture_tail.inc').read_text(), encoding='utf-8')
print(hashlib.sha256((HERE / 'controls.cpp').read_bytes()).hexdigest())
