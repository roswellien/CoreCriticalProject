# Bounded DirectDraw creation slice

`runtime/graphics/direct_draw_creation.cpp` implements the functional control and
ownership boundary recovered for game routine `0x577D40`, plus the final
DirectDraw-only teardown segment `0x57893A` through `0x578954`. Address-level
sources and unknowns are in the [video contract](../../docs/m4-video-backend-contract-r1.md).
The admitted game remains SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.

The caller supplies checked guest memory, a writable four-byte temporary output
cell, and a `DirectDrawCreationProvider`. Provider methods take guest addresses
and resolved guest COM targets. They must marshal actual arguments and output
writes, including writes on failure. No production provider binding is supplied;
the abstract boundary cannot return placeholder success. The fixture provider
is confined to the test executable.

Creation reads the adapter through the original receiver global, calls creation
with null aggregation, and tests status for exact zero. QI uses the original IID
address and global output destination. Successful QI releases the temporary
object; failed QI follows the recovered report-and-return path without invented
cleanup. Error reporting is delegated and its actual return is propagated.
Neither output cell is cleared in advance. Guest memory faults and provider
exceptions propagate; no substitute status/interface is manufactured.

Teardown requires the caller to have already disposed of all dependent objects.
It restores the display mode, rereads the owned global and Release target, releases
the object, then clears the global. The original ignores the restore HRESULT.
This operation does not implement the preceding surface/device/GDI cleanup.

This is a functional C++ boundary, not a literal instruction lift: it does not
reproduce guest registers/flags, stack pushes, return PCs, FS/SEH, FP environment,
or caller hardware state. The temporary output cell substitutes for the original
stack local; the caller must provide appropriate initial contents and prevent
aliasing with other state. An integrating dispatcher must enforce image identity,
marshal x86 calling conventions, preserve CPU/stack state, and bind actual
provider/error-helper contracts before execution equivalence can be assessed.

No callback setters, window mutations, cooperative/display initialization,
surfaces, palette, GDI fallback, rendering, or application-service success are
implemented. The application/initializer dispatcher is not wired to this slice.
Accepted progress remains 131/144; the 144-root gate and independent verifier are
unchanged. Existing shared build files were left untouched. This standalone
build compiles only the new slice, the existing guest-memory implementation and
authored fixtures.

From a Visual Studio x64 developer shell with CMake/Ninja available:

```powershell
cmake -S tools/m4-video-backend -B build/m4-video-creation-r1 -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/m4-video-creation-r1
ctest --test-dir build/m4-video-creation-r1 --output-on-failure
cmake -S tools/m4-video-backend -B build/m4-video-creation-release-r1 -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/m4-video-creation-release-r1
ctest --test-dir build/m4-video-creation-release-r1 --output-on-failure
```

Fixtures check creation/QI arguments and real guest slot resolution; positive
nonzero and negative-status failures; failure output writes and untouched output
cells; delegated error return; temporary/global reference sequencing; vtable and
global mutations across provider calls; null/repeated teardown; receiver/output
memory faults; and refusal during Release retaining the owned global. These
checks execute authored native code only. They neither launch the game nor load
the historical DirectDraw provider, and do not establish original/native
equivalence or menu readiness.

Remaining integration blockers are the actual provider binding and failure
outputs/reference behavior, admitted CPU/stack dispatch and error-helper closure,
dependent-resource teardown, and the surface/presentation/window prerequisites
listed in the contract. Keep the next unsupported operation as an explicit stop
with carried state, rather than declaring video-service initialization complete.
