"""Keep the original IV50 CPU-calibration workload observable to its clocks.

The codec at guest entry 0x1103ab10 measures 500,000 iterations of eighteen
one-byte NOPs using QueryPerformanceCounter and RDTSC. Ordinary optimization
can erase the side-effect-free lifted loop and turn its corrected elapsed-time
denominator into zero. Emit those exact NOPs in the existing loop, and disable
loop unrolling/vectorization. Guest state, clocks, arithmetic and the codec's
unsupported-frequency paths are unchanged.

Apply before any optimizer. Only the complete, pinned original host-lowered
module is accepted; a changed module for this entry fails visibly. Other bodies
are returned byte-for-byte. No original media or generated IR is embedded here.
"""
import hashlib
import re

ENTRY = 0x1103ab10
BODY = 'mw34_attach_m_1103ab10_body'
CODEC_SHA256 = '9d066dbdb0b9903c2afb07284d609c7d3ed3278245040490e9805d4cd717958f'
GUEST_IR_SHA256 = '7536ce16b7d161d9a1b1ecfff5f7d5008ccbd9fbe59849603cd43de8024ede96'
NORMALIZED_HOST_SHA256 = '3b1b03e02eb6fc937ab9c7342ff2d1dc7c6072db5448e77225ace732ad81f1c1'
ITERATIONS = 500000
NOP_COUNT = 18  # Original bytes 0x1103abae through 0x1103abbf, inclusive.
HEADER = '826:                                              ; preds = %929, %822\n'
BACKEDGE = '  br i1 %943, label %826, label %944'
ASM_MARKER = '  call void asm sideeffect "' + '\\0A'.join(['nop'] * NOP_COUNT) + '", ""() #991\n'
METADATA = '''
attributes #991 = { nounwind memory(inaccessiblemem: readwrite) }
!9900 = distinct !{!9900, !9901, !9902}
!9901 = !{!"llvm.loop.unroll.disable"}
!9902 = !{!"llvm.loop.vectorize.enable", i1 false}
'''

def normalized_host(text):
    """LLVM's output path is the sole allowed module identity variation."""
    return re.sub(r'^; ModuleID = .*\n', '', text.replace('\r\n', '\n'))

def transform(text):
    definitions = re.findall(r'^define [^\n]*@' + re.escape(BODY) + r'\(', text, re.M)
    if not definitions:
        return text, dict(codec_timing_preserved=0)
    normalized = normalized_host(text)
    digest = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    if len(definitions) != 1 or digest != NORMALIZED_HOST_SHA256:
        raise ValueError('IV50 timing preservation requires the complete pinned host IR for 0x1103ab10; got ' + digest)
    checks = [
        normalized.count(HEADER) == 1,
        normalized.count(BACKEDGE) == 1,
        normalized.count('store i32 500000, ptr %ECX, align 4') == 1,
        normalized.count('i32 noundef 259)') == 2,
        '#991' not in normalized and '!9900' not in normalized,
    ]
    if not all(checks):
        raise ValueError('IV50 timing preservation requires its exact bound, header, backedge and two RDTSC endpoints')
    result = text.replace('\r\n', '\n').replace(HEADER, HEADER + ASM_MARKER).replace(BACKEDGE, BACKEDGE + ', !llvm.loop !9900')
    result += METADATA
    if result.count(ASM_MARKER) != 1 or result.count(BACKEDGE + ', !llvm.loop !9900') != 1:
        raise ValueError('IV50 timing preservation did not produce exactly one marker and bounded backedge')
    return result, dict(codec_timing_preserved=1, entry=hex(ENTRY), iterations=ITERATIONS,
                        native_nops_per_iteration=NOP_COUNT, normalized_host_sha256=digest,
                        original_loop_header='0x1103abae', original_backedge='0x1103abc1')
