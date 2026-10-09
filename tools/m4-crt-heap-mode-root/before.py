"""Original BEFORE plus explicitly admitted source page and owned stack input."""
import importlib.util
import types
from consumer import F,M,OLD

path = F.pin(F.ROOT/'tools/m4-crt-heap-create-root/before.py',
    '58377061d16a0ac4d6085b3f41156b3af8042af4723b6e5c16488f0e112a33b1')
spec = importlib.util.spec_from_file_location('heap_mode_frozen_before',path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
PAGE,PROBE_PAGE,STACK_PAGE = 0x78035000,0x78005000,0x20000000
SELECTOR,SELECTOR_BYTES,PROBE,PROBE_BYTES = 0x78003a0c,37,0x780058b5,49


def stage(state,fx,cpu,memory):
    result = prior.stage(state,fx,cpu,memory)
    for address in (PROBE_PAGE,STACK_PAGE):
        result['page-'+str(address)+'.bin'] = bytes(memory[address])
    for address,size,name in ((SELECTOR,SELECTOR_BYTES,'heap-mode-selector.bin'),
                              (PROBE,PROBE_BYTES,'heap-stack-probe.bin')):
        result[name] = bytes(memory[address&~4095][address&4095:(address&4095)+size])
    return result


def expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,
             source,level='O0',stack_input=bytes(4096)):
    F.require(isinstance(stack_input,bytes) and len(stack_input)==4096,
              'Declared owned lower stack page input, not original captured bytes')

    def memory(*values):
        result = OLD.base_memory(*values)
        for address in (0x78003000,PAGE,PROBE_PAGE):
            result[address] = bytearray(source[address])
        result[STACK_PAGE] = bytearray(stack_input)
        return result

    writer = types.FunctionType(F.writer.__code__,dict(F.writer.__globals__,base_memory=memory,stage=stage))
    frozen = prior.prior.OLD_BEFORE
    predict = types.FunctionType(OLD.expected.__code__,
        dict(OLD.expected.__globals__,M=types.SimpleNamespace(Entry=frozen.LocaleEntry),
             writer_result=writer,stage=stage))
    entry,phases = predict(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,0,level)
    phases.pop('entry-after-fault')
    phases.pop('retry-after')
    return entry,phases
