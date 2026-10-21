; Inno Setup Script for MechWarrior 3 Remastered
; Development GUI installer only: the portable native-runtime preparation path
; is not included. Do not publish this as a playable game installer.
; See docs/public-release-readiness.md before assembling any release payload.

#define MyAppName "MechWarrior 3 Remastered"
#define MyAppVersion "0.1.0-preview"
#define MyAppPublisher "MW3 Remaster Project"
#define MyAppURL "https://github.com/roswellien/MW3Recomp"
#define MyAppExeName "MW3RemasterLauncher.exe"

[Setup]
AppId={{6B5D7A9E-3D8B-4C2E-99F1-23F7E5A4B101}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName=C:\Games\MW3Remaster
DisableDirPage=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=MW3Remaster-GUI-Development-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
OutputDir=dist

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtosteam"; Description: "Add MechWarrior 3 Remastered to my Steam library (with custom grid artwork)"; GroupDescription: "Integrations:"; Flags: checkedonce
Name: "installpacks"; Description: "Select and install downloaded Asset / Music packs (.mw3pack or .zip)"; GroupDescription: "Packs & Content:"; Flags: unchecked

[Files]
; Core Launcher & Host binaries
Source: "bin\Release\net8.0-windows\win-x64\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Default asset and font directories
Source: "Assets\*"; DestDir: "{app}\Assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  MW3DirPage: TInputDirWizardPage;
  MW3Path: string;

function AutoDetectMW3(): string;
var
  RegPath: string;
begin
  Result := '';
  // Check Registry
  if RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\MicroProse\MechWarrior 3', 'InstallDir', RegPath) then
  begin
    if FileExists(AddBackslash(RegPath) + 'Mech3.exe') then
    begin
      Result := RegPath;
      Exit;
    end;
  end;

  if RegQueryStringValue(HKLM, 'SOFTWARE\MicroProse\MechWarrior 3', 'InstallDir', RegPath) then
  begin
    if FileExists(AddBackslash(RegPath) + 'Mech3.exe') then
    begin
      Result := RegPath;
      Exit;
    end;
  end;

  // Check Common paths
  if FileExists('C:\Games\MW3\Mech3.exe') then Result := 'C:\Games\MW3'
  else if FileExists('C:\Program Files (x86)\MicroProse\MechWarrior 3\Mech3.exe') then Result := 'C:\Program Files (x86)\MicroProse\MechWarrior 3'
  else if FileExists('C:\Games\MechWarrior 3\Mech3.exe') then Result := 'C:\Games\MechWarrior 3'
  else if FileExists('D:\Games\MW3\Mech3.exe') then Result := 'D:\Games\MW3';
end;

procedure InitializeWizard;
begin
  MW3Path := AutoDetectMW3();
  if MW3Path = '' then MW3Path := 'C:\Games\MW3';

  MW3DirPage := CreateInputDirPage(wpSelectDir,
    'Select Original MechWarrior 3 Folder',
    'Where is your legally owned MechWarrior 3 installed?',
    'MechWarrior 3 Remastered requires the original game files (Mech3.exe and data archives). ' +
    'The installer will verify these files without modifying your original installation.'#13#10#13#10 +
    'Please select your MechWarrior 3 directory below:',
    False, '');

  MW3DirPage.Add('');
  MW3DirPage.Values[0] := MW3Path;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  SelectedDir: string;
begin
  Result := True;
  if CurPageID = MW3DirPage.ID then
  begin
    SelectedDir := MW3DirPage.Values[0];
    if not FileExists(AddBackslash(SelectedDir) + 'Mech3.exe') then
    begin
      MsgBox('Could not find Mech3.exe in the selected folder: '#13#10 + SelectedDir + #13#10#13#10 +
             'Please select a valid MechWarrior 3 installation directory containing Mech3.exe.', mbError, MB_OK);
      Result := False;
    end
    else
    begin
      MW3Path := SelectedDir;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  SettingsFile: string;
  JsonContent: string;
  SelectedFiles: string;
  ModsDir: string;
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Write detected MW3 path into user settings.json
    SettingsFile := AddBackslash(ExpandConstant('{app}')) + 'user\settings.json';
    ForceDirectories(AddBackslash(ExpandConstant('{app}')) + 'user');

    // Save initial settings
    JsonContent := '{"GamePath": "' + ReplaceStr(MW3Path, '\', '\\') + '", "Width": 1920, "Height": 1080, "Fullscreen": true, "AntiAliasing": "fxaa", "AnisotropicFiltering": 16, "DrawDistance": 2400, "FogDistance": 1100, "LocalCdAudio": true, "ActivePacks": []}';
    SaveStringToFile(SettingsFile, JsonContent, False);

    ModsDir := AddBackslash(ExpandConstant('{app}')) + 'mods';
    ForceDirectories(ModsDir);

    // If player checked "Install downloaded asset and music packs"
    if WizardIsTaskSelected('installpacks') then
    begin
      if GetOpenFileName('Select downloaded asset/music pack (.mw3pack or .zip)', SelectedFiles, '',
                         'MechWarrior 3 Packs (*.mw3pack;*.zip)|*.mw3pack;*.zip|All Files (*.*)|*.*', 'mw3pack') then
      begin
        // Copy chosen pack into mods directory
        FileCopy(SelectedFiles, AddBackslash(ModsDir) + ExtractFileName(SelectedFiles), False);
      end;
    end;

    // If player checked "Add to Steam Library"
    if WizardIsTaskSelected('addtosteam') then
    begin
      // Run launcher with silent steam injection flag
      Exec(AddBackslash(ExpandConstant('{app}')) + '{#MyAppExeName}', '--add-steam --silent', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;

function ReplaceStr(const S, FromStr, ToStr: string): string;
var
  P: Integer;
begin
  Result := S;
  P := Pos(FromStr, Result);
  while P > 0 do
  begin
    Delete(Result, P, Length(FromStr));
    Insert(ToStr, Result, P);
    P := Pos(FromStr, Result);
  end;
end;
