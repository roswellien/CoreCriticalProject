"""Copy proven caller/setup helpers into a new parser-prefix fixture."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
old = (ROOT/'tools/m4-crt-commandline-carry-review/controls.cpp').read_text()
prefix = old[:old.index(' void verify(bool clean)')]
prefix = prefix.replace('MW34_CRT_COMMANDLINE_CARRY_NO_MAIN', 'MW34_CRT_PARSER_PREFIX_NO_MAIN')
prefix = prefix.replace('void review_carry(cm::Binding&,unsigned);', 'void review_parser(pp::Binding&,unsigned);')
prefix = prefix.replace(' std::filesystem::path row;', ' std::unique_ptr<pp::Binding>parser,stale_parser;\n std::filesystem::path row;')
prefix = prefix.replace('review_provider,which>=73?which:0', 'review_provider,0')
prefix = prefix.replace('commandline->extra=&review_carry;', 'commandline->extra=nullptr;')
prefix = prefix.replace('stale_commandline=std::make_unique<cm::Binding>(*stale_context,review_provider);', 'stale_commandline=std::make_unique<cm::Binding>(*stale_context,review_provider);parser=std::make_unique<pp::Binding>(mainargs->context,*commandline,review_provider,which>=85?which:0);parser->extra=&review_parser;stale_parser=std::make_unique<pp::Binding>(*stale_context,*stale_commandline,review_provider);')
prefix = prefix.replace('~ReviewFixture(){', '~ReviewFixture(){pp::binding=nullptr;pp::admitted_binding=nullptr;pp::owner=nullptr;')
prefix = prefix.replace('cm::admitted_binding=commandline.get();SetLastError', 'cm::admitted_binding=commandline.get();pp::binding=parser.get();pp::admitted_binding=parser.get();SetLastError')
prefix = prefix.replace('cm::admitted_binding=nullptr;\n  if', 'cm::admitted_binding=nullptr;pp::binding=nullptr;pp::admitted_binding=nullptr;\n  if')
prefix = prefix.replace('!filename->active&&!commandline->active', '!filename->active&&!parser->active&&!parser->depth&&!pp::owner&&!commandline->active')
prefix = prefix.replace('return job;\n }', 'raw_output(row/"parser-accesses.bin",parser->accesses);raw_output(row/"parser-events.bin",parser->events);raw_output(row/"parser-undefined-sites.bin",parser->undefined_sites);std::array<unsigned,16>ps{mode,parser->control,parser->frame,parser->parent_frame,parser->access_count,parser->event_count,parser->undefined_count,parser->stage,parser->depth,parser->fault_pc,parser->fault_address,unsigned(parser->used),unsigned(parser->active),unsigned(parser->failed),unsigned(parser->locale_reached),0};raw_output(row/"parser-status.bin",ps);return job;\n }')
prefix = prefix.replace('void retry(){auto&c=mainargs->context;', 'void retry(){auto&c=mainargs->context;std::array<std::byte,sizeof(pp::Binding)>parser_object{};std::memcpy(parser_object.data(),parser.get(),parser_object.size());')
prefix = prefix.replace('"Retry cannot change owned NUL-inclusive buffer");}', '"Retry cannot change owned NUL-inclusive buffer");}review_need(!std::memcmp(parser_object.data(),parser.get(),parser_object.size()),"Poisoned retry preserves full parser Binding/first fault/lifecycle/ledgers/private source identity");')
(Path(__file__).parent/'controls.cpp').write_text(prefix+(Path(__file__).parent/'fixture_tail.inc').read_text())
