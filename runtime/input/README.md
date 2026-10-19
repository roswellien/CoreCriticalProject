# Input compatibility boundary

The [current plan](../../docs/faithful-modernization-plan.md) integrates modern
remapping and device handling through the recovered original input contract.
Preserve action ordering, acquisition and simulation timing; test each affected
original behavior before enabling an enhanced control mode.

Reserved for the game's observed input state and device contracts. No input
backend exists yet. Keyboard/mouse behavior comes before optional modern
controller, HOTAS, pedals, multiple joystick and force-feedback support.

The user-selected gamepad target is Xbox and PlayStation controllers on Windows,
with a portable input/action layer for possible future Linux support. Both
Traditional and FPS-style profiles are intended. See the
[controller investigation](../../docs/controls-modernization-investigation-2026-10-18.md#controller-direction-selected-by-the-user)
for the proposed input-only SDL3 backend, device/transport test scope and remaining
integration work. This directory still has no implemented gamepad backend; the
experimental native host's existing DirectInput bridge is a separate component.
