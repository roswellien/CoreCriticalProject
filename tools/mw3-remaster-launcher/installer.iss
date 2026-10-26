; Core Critical installer. Branding follows the launcher's charcoal/amber art.
; The full private playtest bundles the precompiled native runtime; the player
; supplies original game data through the first-run setup flow.
; See docs/public-release-readiness.md before assembling any release payload.

#define MyAppName "Core Critical Launcher"
#ifndef MyAppVersion
#define MyAppVersion "1.0.28-preview"
#endif
#ifndef PublishDirectory
#define PublishDirectory "bin\Release\net8.0-windows\win-x64\publish"
#endif
#ifndef InstallerAppId
#define InstallerAppId "{{6B5D7A9E-3D8B-4C2E-99F1-23F7E5A4B101}"
#endif
#define MyAppPublisher "Core Critical"
#define MyAppURL "https://github.com/roswellien/MW3Recomp"
#define MyAppExeName "Core Critical Launcher.exe"

[Setup]
AppId={#InstallerAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={sd}\Games\Core Critical\Launcher
UsePreviousAppDir=yes
DisableDirPage=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
AllowNoIcons=yes
OutputBaseFilename=corecriticalinstaller-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern dark includetitlebar hidebevels
WizardBackColor=#141717
WizardImageBackColor=#0F1212
WizardSmallImageBackColor=#141717
WizardImageFile=Assets\Installer\wizard-welcome.png
WizardSmallImageFile=Assets\Installer\wizard-mark.png
WizardImageStretch=yes
WizardSizePercent=120,120
SetupIconFile=Assets\app-icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableWelcomePage=no
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
PrivilegesRequired=lowest
#ifdef WindowsSigning
SignTool=artifact-signing
SignedUninstaller=yes
#endif
OutputDir=dist

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Set up Core Critical
#ifdef PrecompiledRuntimeIncluded
WelcomeLabel2=Install the Core Critical Launcher and native MechWarrior 3 runtime.%n%nAfter installation, select your original game files and choose your display and graphics settings.%n%nStart with stock game content, then enable optional packs whenever you want.
#else
WelcomeLabel2=Install or update the Core Critical Launcher.%n%nYour selected game runtime and saved preferences are preserved. Game updates and optional content packs are managed in the launcher.
#endif
FinishedHeadingLabel=Core Critical is ready
FinishedLabel=Open Core Critical to verify your original game files, choose graphics settings, and manage optional content packs.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtosteam"; Description: "Add Core Critical Launcher to my Steam library (with custom grid artwork)"; GroupDescription: "Integrations:"; Flags: unchecked

[Files]
; Publish self-contained and run stage_media_tools.ps1 first (see setup handoff).
; The optional Preparation payload contains tools and metadata, not original
; game files or a precompiled translated game module. Clean Windows remains a gate.
Source: "{#PublishDirectory}\*"; Excludes: "Runtime\*,user\*,hostfxr.dll,Tools\Unshield\unshield.exe,Tools\Unshield\zlib1.dll,Tools\Unshield\LICENSE-unshield.txt,Tools\Unshield\LICENSE-zlib.txt,Tools\Unshield\provenance.json,Tools\Unshield\LOCAL-DEVELOPMENT.txt"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifdef PrecompiledRuntimeIncluded
Source: "{#PublishDirectory}\Runtime\*"; DestDir: "{app}\Runtime"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif
; Required explicit entries make missing runtime/extractor staging a compile error.
Source: "{#PublishDirectory}\hostfxr.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\unshield.exe"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\LICENSE-unshield.txt"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\LICENSE-zlib.txt"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\provenance.json"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
#ifdef PrecompiledRuntimeIncluded
Source: "launcher-precompiled-installation.json"; DestDir: "{app}"; DestName: "launcher-installation.json"; Flags: ignoreversion
#else
; A launcher-only upgrade preserves the installed native-runtime delivery marker.
Source: "launcher-installation.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
#endif
; Default asset and font directories
Source: "Assets\*"; Excludes: "Installer\*"; DestDir: "{app}\Assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[InstallDelete]
; Retire only the old installer-owned application files and shortcuts. The
; AppId, installation directory and external user data store remain stable.
Type: files; Name: "{app}\MW3RemasterLauncher.exe"
Type: files; Name: "{app}\MW3RemasterLauncher.dll"
Type: files; Name: "{app}\MW3RemasterLauncher.deps.json"
Type: files; Name: "{app}\MW3RemasterLauncher.runtimeconfig.json"
Type: files; Name: "{autodesktop}\Core Critical.lnk"
Type: files; Name: "{autoprograms}\Core Critical\Core Critical.lnk"
#ifdef PrecompiledRuntimeIncluded
; Retire only the old installer-owned compilation trigger and archive.
Type: files; Name: "{app}\Preparation\initial.mw3update"
Type: files; Name: "{app}\Preparation\initial.zip"
#endif

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--setup-game"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('addtosteam') then
      if not Exec(AddBackslash(ExpandConstant('{app}')) + '{#MyAppExeName}',
        '--add-steam --silent', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
        MsgBox('The Steam shortcut could not be added. Exit Steam completely, then open Core Critical and use Settings & Steam > Add to Steam Library. Your launcher installation is ready.', mbInformation, MB_OK);
end;
