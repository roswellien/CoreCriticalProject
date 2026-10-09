.intel_syntax noprefix
.text
.globl _fixture_store
_fixture_store:
    fnstcw word ptr [ecx]
    ret
