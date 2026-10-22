# WinMain → AfxWinMain → InitInstance: static path (2026-10-12)

This is a static analysis of `Mech3.exe` (U.S. 1.2) with the staged `MFC42.DLL`. It covers
the code that runs after the main `_initterm` table. None of it has executed natively yet; the
current native stop is main initializer root 14 (see
[E0](e0-application-execution-path.md)). Addresses are source addresses. Names in quotes are
literal strings in the image.

## 1. Game CRT entry tail (`5AC480`–`5AC4FA`)

This is the standard VC6 `WinMainCRTStartup` tail, after `_initterm(5E0000,5E0244)`:

1. Skip the program name in `_acmdln` (the quoted or unquoted first token), then any spaces.
2. `GetStartupInfoA` (`5BB170`). `nShowCmd` is `si.wShowWindow` if `STARTF_USESHOWWINDOW` is
   set, else `SW_SHOWDEFAULT` (10).
3. `GetModuleHandleA(NULL)` (`5BB16C`) supplies `hInstance`.
4. Call `WinMain(hInstance, NULL, lpCmdLine, nShowCmd)` at `5AE390`.
5. Pass the return value to `exit` (`MSVCRT!exit`, `5BB5C0`).

The host already models the MSVCRT side of `exit`: the onexit table that holds the 13
destructors registered so far.

## 2. `WinMain` (`5AE390`) and `AfxWinMain` (MFC42 ordinal 1576, `5F40B35D`)

`WinMain` forwards its four arguments to `5AE3F4`, which is `JMP [5BB438]` (MFC42 ordinal
1576). `AfxWinMain` then runs:

| Step | Code | Role |
| --- | --- | --- |
| 1 | `5F401083` | Module state. `ESI = state+4` is the current `CWinApp` (`608C88`), which the application ctor (`5E010C→47F760→47F7A0`, a later main root) stores there |
| 2 | `5F40AFB7` | `AfxWinInit(hInst, hPrev, cmdLine, nShow)`. A zero return skips to termination |
| 3 | app vtable `+8C` = `5ABE82` | `InitApplication`: thunk `JMP [5BB1DC]`, MFC42 ordinal 3922 (MFC default) |
| 4 | app vtable `+58` = `480000` | `InitInstance` (game) |
| 5 | if `InitInstance` fails | if `m_pMainWnd` (app`+20`) is set, the destroy path at `5F41D2E4`; then `+70` = `47FA10` (`ExitInstance`, game) |
| 6 | else app vtable `+5C` = `58FD70` | `Run` (a game override; drives the startup/state queue) |
| 7 | `5F4112CB` | `AfxWinTerm`, then return the exit code |

Dependencies: steps 1–2 read MFC42 module and thread state, which MFC42 DLL attach normally
creates. That attach is **not native yet** (E0 item 2). The app object must already be
constructed and registered by its main root.

## 3. `InitInstance` (`480000`–`480318`)

The function returns 0 on any failure: three early returns, plus a `MessageBoxA` then
`ExitProcess(0)` path for fatal checks.

**Phase A: environment and instance checks (`480000`–`480122`)**
- `4854C0` → flag `608F70`. If set, `482970(4)` → app`+1DC` (the selector the run path reads
  later).
- `5899B0` → flag `608E24`:
  - if clear, the single-instance path `480340`;
  - if set, `4803A0`, then app`+18D`=1 and `47FED0(1)`.
  - Both helpers use `FindWindowA`, `GetLastActivePopup`, `IsIconic`, `SetForegroundWindow` and
    `PostMessageA` to hand off to an existing instance.
- `575E30` is a requirement check. On failure it formats `"%d.%d"` with `sprintf` and string
  IDs `0xF60`/`0xD78` (`575FD0`/`576040`), shows `MessageBoxA(608F80 owner, MB_ICONEXCLAMATION)`
  and calls `ExitProcess(0)`.
- `589A50(5C3F28)`, a GUID-keyed check, must succeed or `InitInstance` returns 0.

**Phase B: window class (`480123`–`4801BB`)**
- A `WNDCLASS` with `DefWindowProcA` (`5BB714`), MFC42 ordinals 1168 (three times) and 1146,
  `LoadIconA`, `LoadCursorA` and `GetStockObject`, and the class name via `5E5D98`.
- MFC42 ordinal 1232 registers the class; failure returns 0. Success sets `608F6C`=1.

**Phase C: configuration and data (`4801C5`–`480285`)**
- `4AF280`, then string `576040`, then `598210("MicroProse")` (registry key), then
  `51C630("DefaultCmdMap")` (input command map), then `555CD0`, then
  `556170("..\data\common\zrdr")` (data path).
- `40C420("detail.zrd")`. If that fails, `557320("zbd\reader.zbd")` and retry. A second
  failure gives `MessageBeep`, `MessageBoxA` and `ExitProcess`.

**Phase D: services and main frame (`48028D`–`480318`)**
- Service initializers in order: `47FB80`, `5A8B30`, `5090D0`, `50D1E0`, `50D1F0`, `583740`,
  `501F90`, `4F8F60`, then MFC42 ordinal 2621.
- App vtable `+BC`: main frame creation (`47FF90 → 482D10`, per the application workahead;
  the frame is stored at app`+20`, resource 147 menu).
- `47FFF0`, then (`40D4D0`, `47FE10`), then `58FC70`. If that fails, return 0; otherwise
  `InitInstance` returns 1.

## 4. What this means for the native host

- **Order of blockers after the initializers:**
  - MFC42 DLL attach (module/thread state) before `AfxWinMain` step 1;
  - the application root (`47F760`, one of the three never-executed roots) so that state`+4`
    holds the app;
  - then `AfxWinInit`.
- **Host services `InitInstance` needs, all real platform services:**
  - kernel32: `GetStartupInfoA`, `GetModuleHandleA`, `ExitProcess`;
  - USER32: window class registration (through MFC42), `LoadIconA`, `LoadCursorA`,
    `FindWindowA`, `GetLastActivePopup`, `IsIconic`, `SetForegroundWindow`, `PostMessageA`,
    `MessageBoxA`, `MessageBeep`, `UpdateWindow`, `GetFocus`;
  - GDI32: `GetStockObject`;
  - registry access under "MicroProse";
  - file and archive access for `detail.zrd` / `zbd\reader.zbd` under
    `..\data\common\zrdr`.
- **Main-frame and service phase:** the existing reader/widget, video (DirectDraw → Vulkan)
  and input/audio contracts plug in at Phase D and later in `Run`.
- **Failure behaviour to preserve:** every check above has an original failure behaviour
  (MessageBox + `ExitProcess`, or return 0). A native host must reproduce those, not mask them.

Open items:
- The MFC42 ordinals are listed by number only; no ordinal-to-name map exists in the repo.
- The purpose of `589A50`'s GUID check and of the `4854C0`/`5899B0` flags needs their bodies.
- The service initializers in Phase D are mapped by address only.
