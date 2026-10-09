"""Independent byte/PE recovery for the bounded command-line producer carry.

Read-only legacy artifacts; no original or native candidate execution.
"""
import hashlib, json, pathlib, struct, sys, traceback
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT/'reports/m4-crt-commandline-carry'
PINS = {}

def need(ok, why):
    if not ok: raise ValueError(why)

def read(path):
    path = pathlib.Path(path).resolve(); raw = path.read_bytes()
    PINS[str(path)] = hashlib.sha256(raw).hexdigest(); return raw

class PE:
    def __init__(self, path):
        self.raw = read(path); nt = struct.unpack_from('<I', self.raw, 0x3c)[0]
        need(self.raw[:2] == b'MZ' and self.raw[nt:nt+4] == b'PE\0\0', 'DOS/PE signature')
        machine, count, _, _, _, size, _ = struct.unpack_from('<HHIIIHH', self.raw, nt+4)
        optional = nt+24
        need(machine == 0x14c and struct.unpack_from('<H', self.raw, optional)[0] == 0x10b,
             'Exact x86 PE32 source')
        self.base = struct.unpack_from('<I', self.raw, optional+28)[0]
        self.import_rva = struct.unpack_from('<I', self.raw, optional+104)[0]
        self.sections = []
        for n in range(count):
            at = optional+size+n*40
            virtual, rva, raw_size, offset = struct.unpack_from('<IIII', self.raw, at+8)
            self.sections.append((rva, virtual, raw_size, offset))

    def bytes(self, address, count):
        rva = address-self.base
        for begin, virtual, raw_size, offset in self.sections:
            if begin <= rva and rva+count <= begin+max(virtual, raw_size):
                delta = rva-begin; available = max(0, min(count, raw_size-delta))
                return self.raw[offset+delta:offset+delta+available] + bytes(count-available)
        raise ValueError('Unowned source RVA')

    def string(self, rva):
        raw = self.bytes(self.base+rva, 256); end = raw.index(0)
        return raw[:end].decode('ascii')

    def imports(self):
        result = {}
        for n in range(128):
            oft, _, _, name, ft = struct.unpack('<5I', self.bytes(self.base+self.import_rva+n*20, 20))
            if not any((oft, name, ft)): return result
            library = self.string(name)
            for k in range(4096):
                item = struct.unpack('<I', self.bytes(self.base+(oft or ft)+k*4, 4))[0]
                if not item: break
                symbol = '#'+str(item&0xffff) if item&0x80000000 else self.string(item+2)
                address = self.base+ft+k*4
                need(address not in result, 'Unique source import cell')
                result[address] = (library, symbol)
        raise ValueError('Import descriptor bound')

def main(output):
    need(output.parent == BASE and output.name.startswith('independent-') and not output.exists(),
         'Fresh immediate independent source receipt')
    provider = PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')
    need(PINS[str((ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').resolve())] ==
         '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7', 'Frozen exact provider')
    writer = provider.bytes(0x7800188c, 11)
    need(writer == bytes.fromhex('ff1534e00278a374710378'), 'Exact CALL and DWORD writer bytes')
    need(hashlib.sha256(writer).hexdigest() == '6300f3f77dc2f2ce6ea36590028dd7f3b078c721a08d6daac27ebc8c636b5ac3',
         'Frozen measured producer source hash')
    need(provider.imports()[0x7802e034] == ('KERNEL32.dll', 'GetCommandLineA'), 'Named OS producer import')
    following = provider.bytes(0x78001897, 5)
    need(following[0] == 0xe8 and 0x7800189c+struct.unpack('<i',following[1:])[0] == 0x78003d9a,
         'Fragment stops before actual following attach helper CALL')
    consumer = provider.bytes(0x7800bbd6, 38)
    need(consumer == bytes.fromhex('a1747103788935e0b303788bfe80380074028bf88d45f8508d45fc506a006a0057e84c000000'),
         'Exact consumer global read, byte test, argument PUSH and parser CALL source')
    need(0x7800bbfc+struct.unpack('<i',consumer[-4:])[0] == 0x7800bc48, 'Actual first parser target')
    need(provider.bytes(0x78037174,4) == bytes(4), 'File source zero is uninitialized, not a production value')
    filename_header = read(ROOT/'reports/m4-crt-filename/preparation-r8/filename.hpp')
    composition = read(ROOT/'reports/m4-crt-filename/preparation-r8/composition.cpp')
    need(b'constexpr unsigned buffer=0x7803b3f0,capacity=260,commandline=0x78037174,stop_pc=0x7800bbd6' in filename_header,
         'Frozen filename gate declares the same blocked consumer load')
    need(b'Only declared outer ESP/EIP transition permitted' in composition,
         'Frozen root requires State/RuntimeCPU carry except explicit outer transition')
    read(__file__)
    output.mkdir(parents=True)
    report = dict(passed=True, scope='Independent exact-byte source and integration prerequisite recovery; candidate admission pending',
        producer=dict(begin=0x7800188c,end_exclusive=0x78001897,source_bytes=11,source_hex=writer.hex(),
            OS_import_IAT=0x7802e034,real_stdcall_return=0x78001892,provider_global=0x78037174,
            following_unexecuted_CALL=0x78001897,following_target=0x78003d9a,fragment_RET=False),
        consumer=dict(load_PC=0x7800bbd6,provider_global=0x78037174,filename_pointer_store_PC=0x7800bbdb,
            filename_pointer_global=0x7803b3e0,first_byte_test_PC=0x7800bbe3,
            first_parser_CALL=0x7800bbf7,parser_target=0x7800bc48,real_parser_return=0x7800bbfc,
            bounded_normal_frame=0x20001860,parser_frame=0x2000182c,parser_arguments=['owned guest command-line pointer',0,0,0x20001850,0x2000184c]),
        hazards=['Frozen matherr literal whole-page guard rejects earlier _acmdln publication without an explicit later seam or narrow new evidence',
            'Native host pointer requires an owned guest allocation and explicit source/guest ownership proof',
            'Live allocation, exact immutable bytes/global and ready state must be checked at consumer use',
            'Producer GPR/FX effects must be carried into RuntimeCPU coherently, with no State reseed',
            'Source fragment has no RET and does not close DllMain/process attach'],
        candidate_review_pending=True, original_executed=False, game_launched=False,
        production_initialized_service=False, argv_outputs=False, whole_M4_complete=False, files=PINS)
    for path, digest in PINS.items():
        need(hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() == digest, 'Stable final physical source')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True, source_files=len(PINS), producer_bytes=11, parser_target=hex(0x7800bc48))))

if __name__ == '__main__':
    try:
        need(len(sys.argv)==2, 'recover_contract.py fresh-report-directory')
        main(pathlib.Path(sys.argv[1]).resolve())
    except Exception:
        traceback.print_exc();sys.exit(1)
