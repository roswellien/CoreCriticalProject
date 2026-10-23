# Core Critical Launcher executable naming

Starting with the next 1.0.27 release, the installed application is
`Core Critical Launcher.exe`. Its managed assembly, dependency manifest and
runtime configuration use the same basename. The internal C# root namespace
stays stable so embedded resources and settings contracts remain compatible.

Installer files include the complete version, for example
`corecriticalinstaller-1.0.27-preview.exe`. The release builder and receipt
use this same versioned filename. Installer shortcuts, Steam registration,
development shortcut generation and updater helper/restart references use
the renamed launcher. The installer's AppId and default application directory
remain stable. Upgrade removes only the four retired installer-owned launcher
files and the known old Core Critical shortcuts; user data and runtime update
selection remain outside that cleanup.

The executable rename needs one full installer upgrade from 1.0.26 or earlier.
Those older updater helpers hard-code the old assembly and restart filename.
New `.ccupdate` packaging therefore requires launcher 1.0.27 or newer rather
than allowing an old helper to fail after installation. Updates after that
use the new names throughout. Internal launcher update ZIPs retain their
existing `CoreCriticalSetup.exe` member contract; this is a temporary staged
installer, not the installed application or public download filename.

Fresh self-contained publication succeeds with all four renamed files and no
old executable. The assembly reports `Core Critical Launcher 1.0.27.0`.
Content and controls fixtures pass, including embedded resource loading.
Packaging/shortcut scripts parse successfully. Full launcher update tests
were correctly refused while another worker's native capture was active;
that process was left untouched. No full installer upgrade or updater restart
trial is claimed for this name migration. Private publication evidence is under
`D:/MW3LauncherNaming-20261023-r1`.

The already-published 1.0.26 downloads retain their original names. This change
is prepared for the next release; no replacement installer is signed or
uploaded by this naming-only task. Formal acceptance stays 131/144 and no
commit is made.
