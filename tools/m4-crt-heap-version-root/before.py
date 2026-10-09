"""Original BEFORE, prior declared stack input, and additional raw RX identity."""
import importlib.util
import types
from consumer import F,M,OLD

path=F.pin(F.ROOT/'tools/m4-crt-heap-mode-root/before.py',
    'f42551f20b4365f663fd22b3d85cb1ae88771b52ac71391ebdacdd55edc221fa')
spec=importlib.util.spec_from_file_location('heap_version_fixed_before',path)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
PAGE,PROBE_PAGE,STACK_PAGE=prior.PAGE,prior.PROBE_PAGE,prior.STACK_PAGE
SELECTOR,PROBE=prior.SELECTOR,prior.PROBE
COLD_PAGE=0x7800c000
SPANS=((0x78003a31,26,'heap-version-branch.bin'),
       (0x78003a4b,23,'heap-version-environment.bin'),
       (0x7800ccc5,8,'heap-version-mode1.bin'),
       (0x78003a7d,3,'heap-version-epilogue.bin'))


def stage(state,fx,cpu,memory):
    result=prior.stage(state,fx,cpu,memory)
    result['page-'+str(COLD_PAGE)+'.bin']=bytes(memory[COLD_PAGE])
    for address,size,name in SPANS:
        result[name]=bytes(memory[address&~4095][address&4095:(address&4095)+size])
    return result


def expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,
             source,level='O0',stack_input=bytes(4096)):
    F.require(isinstance(stack_input,bytes) and len(stack_input)==4096,
              'Declared owned lower-stack input, without original-capture credit')
    def memory(*values):
        result=OLD.base_memory(*values)
        for address in (0x78003000,PAGE,PROBE_PAGE,COLD_PAGE):
            result[address]=bytearray(source[address])
        result[STACK_PAGE]=bytearray(stack_input)
        return result
    writer=types.FunctionType(F.writer.__code__,dict(F.writer.__globals__,base_memory=memory,stage=stage))
    frozen=prior.prior.prior.OLD_BEFORE
    model=types.FunctionType(OLD.expected.__code__,
        dict(OLD.expected.__globals__,M=types.SimpleNamespace(Entry=frozen.LocaleEntry),writer_result=writer,stage=stage))
    entry,phases=model(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,0,level)
    phases.pop('entry-after-fault');phases.pop('retry-after')
    return entry,phases
