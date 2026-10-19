$wsh = New-Object -ComObject WScript.Shell
$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$targetExe = Join-Path $rootDir "tools\mw3-remaster-launcher\bin\Debug\net8.0-windows\MW3RemasterLauncher.exe"
$iconPath = Join-Path $rootDir "tools\mw3-remaster-launcher\Assets\app-icon.ico"

# 1. Root folder shortcut: "MechWarrior 3 Remastered.lnk"
$lnkPath1 = Join-Path $rootDir "MechWarrior 3 Remastered.lnk"
$s1 = $wsh.CreateShortcut($lnkPath1)
$s1.TargetPath = $targetExe
$s1.WorkingDirectory = $rootDir.Path
$s1.IconLocation = "$iconPath,0"
$s1.Description = "Launch MechWarrior 3 Remastered"
$s1.Save()

# 2. Also create "MW3 Launcher.lnk"
$lnkPath2 = Join-Path $rootDir "MW3 Launcher.lnk"
$s2 = $wsh.CreateShortcut($lnkPath2)
$s2.TargetPath = $targetExe
$s2.WorkingDirectory = $rootDir.Path
$s2.IconLocation = "$iconPath,0"
$s2.Description = "MechWarrior 3 Remaster Launcher"
$s2.Save()

Write-Host "Created shortcuts:"
Write-Host "  $lnkPath1"
Write-Host "  $lnkPath2"
