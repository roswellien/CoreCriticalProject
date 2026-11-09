#ifndef PublishDirectory
  #error Supply the signed alpha launcher publish directory
#endif
#define AlphaName "Core Critical Launcher (MW3-RE Alpha)"
#define AlphaVersion "1.0.49-alpha.1"
#define LauncherExe "Core Critical Launcher.exe"

[Setup]
AppId={{81448EF4-D139-48C9-BADF-55043A39D7A1}
AppName={#AlphaName}
AppVersion={#AlphaVersion}
AppPublisher=Core Critical
DefaultDirName={localappdata}\Programs\Core Critical MW3-RE Alpha
UsePreviousAppDir=no
DisableDirPage=yes
DefaultGroupName={#AlphaName}
OutputBaseFilename=corecriticalinstaller-{#AlphaVersion}
UninstallDisplayIcon={app}\{#LauncherExe}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SignTool=artifact-signing
SignedUninstaller=yes
Compression=lzma2
SolidCompression=yes

[Files]
Source: "{#PublishDirectory}\*"; DestDir: "{app}"; Excludes: "Runtime\*,MW3-RE-Alpha\*,user\*,native-inputs\*,launcher-installation.json"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#AlphaName}"; Filename: "{app}\{#LauncherExe}"; WorkingDir: "{app}"
