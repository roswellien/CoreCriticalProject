.intel_syntax noprefix
.text
.globl _fixture_load_store
_fixture_load_store:
    fldcw word ptr [ecx]
    fnstcw word ptr [edx]
    ret
