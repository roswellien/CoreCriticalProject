$wsh = New-Object -ComObject WScript.Shell
$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$targetExe = Join-Path $rootDir "tools\remaster-launcher\Core Critical Launcher.exe"
if (!(Test-Path -LiteralPath $targetExe)) {
    throw 'Publish the launcher to tools/remaster-launcher before creating shortcuts.'
}
$iconPath = Join-Path $rootDir "tools\mw3-remaster-launcher\Assets\app-icon.ico"

$shortcutPath = Join-Path $rootDir "Core Critical Launcher.lnk"
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetExe
$shortcut.WorkingDirectory = $rootDir.Path
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = "Core Critical Launcher"
$shortcut.Save()
Write-Host "Created shortcut: $shortcutPath"
