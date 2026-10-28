# MFC provider-state prerequisites

This is static work ahead of native application initialization. The exact staged
MFC42 image has been examined, but its selection as the game's actual loaded
provider and its initialized objects have not been demonstrated by this work.

The new inventory records 21 local control-flow graphs, 637 instructions,
82 source edges and eight ordered prerequisite gates. Ten direct helpers remain
outside that bounded recovery. Source bytes, receiver operands, import owners,
raw IAT values and the difference between file zeros and initialized memory
are recorded explicitly.

The first gates require an admitted provider identity, guest exception-chain
operations through `FS:[0]`, TLS manager/key/slot services, and factories backed
by allocation and critical-section state. These dependencies must be implemented
and tested before the MFC module/thread state can safely supply the application
receiver. Completing this inventory does not increase the accepted 27 of 144
initializer count.

One concrete import example illustrates why raw binding values cannot be used
as callable addresses: the staged MFC thunk at `0x5F40107D` reads IAT slot
`0x5F49815C`, whose raw file word is `0x78003F1C`. The exact staged MSVCRT
export `_EH_prolog` is at `0x78001496`. The raw word is preserved as source
identity; resolving the helper requires the named provider contract.

The deterministic checker passed in a fresh root-owned run. Recovery rejected
seven deliberately altered inputs through its shared validator, and the edge
audit rejected six more. No original provider code, native MFC body, initialized
application object, window or menu was executed.

Evidence:

- [Source inventory](../../reports/m4-mfc-provider-state/recovery-r1/inventory.json)
- [Recovery report](../../reports/m4-mfc-provider-state/recovery-r1/report.json)
- [Independent edge audit](../../reports/m4-mfc-provider-state/edge-audit-r1/report.json)
- [Root checker](../../reports/m4-mfc-provider-state/root-check-r1/report.json)
- [Timed root stage](../../reports/m4-mfc-provider-state/root-check-stage-r1/stage.json)

The next application work is to close these service and lifetime contracts,
then execute the recovered state factories against controlled native fixtures.
The CRT command-line/parser work remains a separate prerequisite for complete
startup.
