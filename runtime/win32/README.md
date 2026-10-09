# Win32 compatibility boundary

Reserved for evidence-backed import thunks. No Win32 compatibility APIs are
implemented. Guest pointers, structures, handles, errors and calling conventions
must be marshalled explicitly. Unimplemented imports must fail with binary
identity and guest address; never return fake success.
