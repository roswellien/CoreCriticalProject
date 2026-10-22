; Inno Setup Script for MechWarrior 3 Remastered
; Private preview. SourcePreparationIncluded adds signed tools that prepare the
; native runtime locally from the player's verified original files.
; See docs/public-release-readiness.md before assembling any release payload.

#define MyAppName "MechWarrior 3 Remastered"
#ifndef MyAppVersion
#define MyAppVersion "1.0.17-preview"
#endif
#ifndef PublishDirectory
#define PublishDirectory "bin\Release\net8.0-windows\win-x64\publish"
#endif
#ifndef InstallerAppId
#define InstallerAppId "{{6B5D7A9E-3D8B-4C2E-99F1-23F7E5A4B101}"
#endif
#define MyAppPublisher "MW3 Remaster Project"
#define MyAppURL "https://github.com/roswellien/MW3Recomp"
#define MyAppExeName "MW3RemasterLauncher.exe"

[Setup]
AppId={#InstallerAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\MW3Remaster
DisableDirPage=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
AllowNoIcons=yes
#ifdef SourcePreparationIncluded
OutputBaseFilename=MW3Remaster-Playtest-Preview-Setup
#else
OutputBaseFilename=MW3Remaster-Launcher-Preview-Setup
#endif
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
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

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtosteam"; Description: "Add MechWarrior 3 Remastered to my Steam library (with custom grid artwork)"; GroupDescription: "Integrations:"; Flags: unchecked

[Files]
; Publish self-contained and run stage_media_tools.ps1 first (see setup handoff).
; The optional Preparation payload contains tools and metadata, not original
; game files or a precompiled translated game module. Clean Windows remains a gate.
Source: "{#PublishDirectory}\*"; Excludes: "Runtime\*,user\*,hostfxr.dll,Tools\Unshield\unshield.exe,Tools\Unshield\zlib1.dll,Tools\Unshield\LICENSE-unshield.txt,Tools\Unshield\LICENSE-zlib.txt,Tools\Unshield\provenance.json,Tools\Unshield\LOCAL-DEVELOPMENT.txt"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Required explicit entries make missing runtime/extractor staging a compile error.
Source: "{#PublishDirectory}\hostfxr.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\unshield.exe"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\LICENSE-unshield.txt"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\LICENSE-zlib.txt"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
Source: "{#PublishDirectory}\Tools\Unshield\provenance.json"; DestDir: "{app}\Tools\Unshield"; Flags: ignoreversion
Source: "launcher-installation.json"; DestDir: "{app}"; Flags: ignoreversion
; Default asset and font directories
Source: "Assets\*"; DestDir: "{app}\Assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--setup-game"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('addtosteam') then
    Exec(AddBackslash(ExpandConstant('{app}')) + '{#MyAppExeName}',
      '--add-steam --silent', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
