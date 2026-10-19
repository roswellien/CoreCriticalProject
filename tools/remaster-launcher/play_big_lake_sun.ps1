param(
 [switch]$Original,
 [ValidateRange(-360,360)][double]$Azimuth=225,
 [ValidateRange(1,89)][double]$Elevation=35,
 [ValidateRange(0,4)][double]$Strength=.85,
 [ValidateRange(0,2)][double]$Ambient=.20,
 [string]$Preset='',
 [string]$SunColor='',
 [string]$AmbientColor='',
 [string]$SkyTint='',
 [string]$HazeColor='',
 [switch]$OriginalSky,
 [string]$SkyBrightness='',
 [string]$SkyGlow='',
 [string]$SkyGlowColor='',
 [string]$SkyGlowFocus='',
 [string]$SkyGradient='',
 [string]$SkyAntiSaturation='',
 [string]$HazeGradient='',
 [string]$HorizonBlend='',
 [ValidateRange(0,20)][double]$NormalStrength=3.4,
 [ValidateRange(0,20)][double]$GroundNormalStrength=1.0,
 [switch]$Normals,
 [switch]$NoShadows,
 [switch]$NoPerfOverlay,
 [switch]$TextureMarkers,
 [switch]$PathDebug,
 [switch]$Vsync,
 [switch]$OriginalEdges,
 [ValidateRange(0,1000)][int]$MenuFps=0,
 [ValidateSet(0,800,1200,1600)][int]$DrawDistance=0,
 [ValidateRange(16,2000)][double]$ShadowRange=200,
 [ValidateRange(0,1)][double]$ShadowDarkness=1,
 [ValidateRange(0,1000000)][int]$Frames=0,
 [string]$Script='',
 [string]$ProfileOut='',
 [int]$ProfileFrom=0,
 [ValidateSet('0','1')][string]$InstantReplay='0'
)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$profilePath=Join-Path $root 'local/remaster/big-lake-sun-tests.json'
$config=Get-Content -LiteralPath $profilePath -Raw | ConvertFrom-Json
# Per-map lighting: tools/remaster-launcher/sun-presets.json, keyed by the profile's map.
# The map's default preset applies unless -Preset names another; explicit arguments win.
$presets=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'sun-presets.json') -Raw | ConvertFrom-Json
$mapLighting=$presets.maps.PSObject.Properties[[string]$config.map]
if($mapLighting){
 $name=if($Preset){$Preset}else{[string]$mapLighting.Value.default}
 $chosen=$mapLighting.Value.presets.PSObject.Properties[$name]
 if(!$chosen){throw "Unknown lighting preset '$name' for $($config.map): $(($mapLighting.Value.presets.PSObject.Properties.Name) -join ', ')"}
 $p=$chosen.Value
 foreach($pair in @(@('Azimuth','azimuth'),@('Elevation','elevation'),@('Strength','strength'),@('Ambient','ambient'))){
  if(!$PSBoundParameters.ContainsKey($pair[0]) -and $null -ne $p.($pair[1])){Set-Variable -Name $pair[0] -Value ([double]$p.($pair[1]))}
 }
 if(!$SunColor -and $p.sun_color){$SunColor=($p.sun_color | ForEach-Object {([double]$_).ToString([Globalization.CultureInfo]::InvariantCulture)}) -join ','}
 if(!$SkyTint -and $p.sky_tint){$SkyTint=($p.sky_tint | ForEach-Object {([double]$_).ToString([Globalization.CultureInfo]::InvariantCulture)}) -join ','}
 if(!$HazeColor -and $p.haze_color){$HazeColor=($p.haze_color | ForEach-Object {([double]$_).ToString([Globalization.CultureInfo]::InvariantCulture)}) -join ','}
 # Sky gradient/glow: preset keys feed any argument not given explicitly (auto otherwise).
 $skyKeys=@{SkyBrightness='sky_brightness';SkyGlow='sky_glow';SkyGlowFocus='sky_glow_focus';SkyGradient='sky_gradient';SkyAntiSaturation='sky_anti_saturation';HazeGradient='haze_gradient';HorizonBlend='horizon_blend'}
 foreach($k in $skyKeys.Keys){if(!(Get-Variable -Name $k -ValueOnly) -and $null -ne $p.($skyKeys[$k])){Set-Variable -Name $k -Value ([double]$p.($skyKeys[$k])).ToString([Globalization.CultureInfo]::InvariantCulture)}}
 if(!$SkyGlowColor -and $p.sky_glow_color){$SkyGlowColor=($p.sky_glow_color | ForEach-Object {([double]$_).ToString([Globalization.CultureInfo]::InvariantCulture)}) -join ','}
 if(!$AmbientColor -and $p.ambient_color){$AmbientColor=($p.ambient_color | ForEach-Object {([double]$_).ToString([Globalization.CultureInfo]::InvariantCulture)}) -join ','}
 Write-Output "Lighting preset: $($config.map) / $name"
}elseif($Preset){throw "No lighting presets for map $($config.map)"}
foreach($colour in @($SunColor,$AmbientColor,$SkyTint,$HazeColor,$SkyGlowColor)){if($colour -and $colour -notmatch '^\d+(\.\d+)?,\d+(\.\d+)?,\d+(\.\d+)?$'){throw "Colours are r,g,b (e.g. 1,0.6,0.3): $colour"}}
$active=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(entry_commandline|mech3|mw3)\.exe$'})
if($active.Count){throw "A game session is already running: $($active.ProcessId -join ', ')"}
$exe=(Resolve-Path -LiteralPath $config.executable).Path
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $config.executable_sha256){throw 'Sun test build changed; validation/profile must be refreshed'}
$game=(Resolve-Path -LiteralPath $config.private_game).Path
if($game.StartsWith((Join-Path $root 'MW3'),[StringComparison]::OrdinalIgnoreCase)){throw 'Sun test requires its private game instance'}
$run=Join-Path $config.output_root ('play-runs/'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $run | Out-Null
$saved=@{}
Get-ChildItem Env:MW34_* | ForEach-Object {$saved[$_.Name]=$_.Value;Remove-Item -LiteralPath ('Env:'+$_.Name)}
try {
 foreach($binding in $config.environment.PSObject.Properties){
  if($binding.Name -notlike 'MW34_*'){throw 'Invalid sun runtime environment name'}
  [Environment]::SetEnvironmentVariable($binding.Name,[string]$binding.Value,'Process')
 }
 $env:MW34_INSTANT_REPLAY=$InstantReplay
 $env:MW34_SUN=if($Original){'0'}else{'1'}
 $culture=[Globalization.CultureInfo]::InvariantCulture
 $env:MW34_SUN_AZIMUTH=$Azimuth.ToString($culture);$env:MW34_SUN_ELEVATION=$Elevation.ToString($culture)
 $env:MW34_SUN_STRENGTH=$Strength.ToString($culture);$env:MW34_SUN_AMBIENT=$Ambient.ToString($culture)
 # Mech normal maps at the project's 12x target (12 x the MW5 material's 0.85); terrain keeps its own strength.
 $env:MW34_SUN_NORMAL_STRENGTH=$NormalStrength.ToString($culture);$env:MW34_SUN_GROUND_NORMAL_STRENGTH=$GroundNormalStrength.ToString($culture)
 if($Normals){$env:MW34_SUN_NORMALS='1'}
 if($SunColor){$env:MW34_SUN_COLOR=$SunColor}
 if($AmbientColor){$env:MW34_SUN_AMBIENT_COLOR=$AmbientColor}
 # Sky/haze: manual values when given, otherwise automatic from the sun and ambient colours.
 if($SkyTint){$env:MW34_SKY_TINT=$SkyTint}
 if($HazeColor){$env:MW34_HAZE_COLOR=$HazeColor}
 if($OriginalSky){$env:MW34_SKY_AUTO='0'}
 foreach($pair in @(@($SkyBrightness,'MW34_SKY_BRIGHTNESS'),@($SkyGlow,'MW34_SKY_GLOW'),@($SkyGlowFocus,'MW34_SKY_GLOW_FOCUS'),@($SkyGradient,'MW34_SKY_GRADIENT'),@($SkyAntiSaturation,'MW34_SKY_ANTI_SATURATION'),@($HazeGradient,'MW34_SKY_ANTI_HAZE'),@($HorizonBlend,'MW34_SKY_HORIZON'))){
  if($pair[0]){if($pair[0] -notmatch '^\d+(\.\d+)?$'){throw "Expected a number for $($pair[1]): $($pair[0])"};[Environment]::SetEnvironmentVariable($pair[1],$pair[0],'Process')}}
 if($SkyGlowColor){$env:MW34_SKY_GLOW_COLOR=$SkyGlowColor}
 # Mech sun shadows: on when the profile's build provides them, unless -NoShadows/-Original.
 if($config.shadows -and !$Original -and !$NoShadows){$env:MW34_SUN_SHADOWS='1';$env:MW34_SUN_SHADOW_RANGE=$ShadowRange.ToString($culture);$env:MW34_SUN_SHADOW_DARKNESS=$ShadowDarkness.ToString($culture)}
 # Performance monitor (FPS, average and worst frame time) in the top-left corner; -NoPerfOverlay hides it.
 if(!$NoPerfOverlay){$env:MW34_PERF_OVERLAY='1'}
 # Vsync off by default (-Vsync restores FIFO); screen-edge world polygons stay on the GPU path (-OriginalEdges restores the fallback).
 # With vsync off, menus/briefings are capped (their backgrounds animate per frame); -MenuFps 0 removes the cap.
 if(!$Vsync){$env:MW34_VSYNC='0';if($MenuFps){$env:MW34_MENU_FPS=[string]$MenuFps}}
 # The front-end scrolling background advances by real time (60 steps/s, its original vsynced pace), not per frame.
 $env:MW34_MENU_SCROLL_HZ='60'
 if(!$OriginalEdges){$env:MW34_WORLD_EDGE_ADMIT='1'}
 # Diagnostics for the ground-line investigation.
 if($DrawDistance){$env:MW34_REMASTER_DRAW_DISTANCE=[string]$DrawDistance;$env:MW34_REMASTER_FOG_DISTANCE=if($DrawDistance -eq 800){'0'}else{[string]($DrawDistance-100)}}
 if($PathDebug){$env:MW34_SKY_DEBUG='3';Write-Output 'Path debug: green = per-frame terrain, blue = GPU-kept world geometry, magenta = mechs, yellow = sky/haze-only; original colours = not sun-lit'}
 if($TextureMarkers){
  $env:MW34_TL_TEXTURE_MARK='72a76a267ac87ac8,7a657204828582a6,8ac68ac692c68ac6,7a2572257a458265,7a457a657a457a45,7a057a0582458225,8246824692a792c8,93eb93ebac8d9c2c,92e792e792c792e7,8ae78ae78ac78ae7,5aa9528852685288,4a674a674a674a67'
  Write-Output 'Texture markers: magenta DKSAND (base sand), green CRATRC1, blue #69, yellow beach02, cyan txgter_1 (desert ground), red mesa cliff, white #78, purple #84, teal #85, orange #86, lavender #41, black #50'
 }
 $env:MW34_REG_OVERLAY=Join-Path $config.output_root 'private-registry.txt'
 $env:MW34_FRAME_BUDGET=[string]$Frames;$env:MW34_FRAME_DUMP='0';$env:MW34_FRAME_TIMES=Join-Path $run 'frame-times.txt'
 # Host sampling profiler (diagnostics): module-offset histogram written at exit.
 if($ProfileOut){$env:MW34_PROFILE=$ProfileOut;if($ProfileFrom){$env:MW34_PROFILE_FROM=[string]$ProfileFrom}}
 if($Script){$env:MW34_INPUT_SCRIPT=(Resolve-Path -LiteralPath $Script).Path;$env:MW34_VIRTUAL_CLOCK='50'}
 $env:MW34_WORLD_LOG=Join-Path $run 'world.jsonl';$env:MW34_MODELS_LOG=Join-Path $run 'models.jsonl'
 if($env:MW34_MUSIC_PACK){$env:MW34_MUSIC_LOG=Join-Path $run 'music.log'}
 $argsList=@((Join-Path $game 'Mech3.exe'),(Join-Path $root 'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj'),
  (Join-Path $root 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $root 'reports/m4-crt-fdiv/native-derived-r1/pack.bin'),
  (Join-Path $root 'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin'),(Join-Path $run 'native'))
 $envRecord=@{};Get-ChildItem Env:MW34_* | ForEach-Object {$envRecord[$_.Name]=$_.Value}
 @{map='Big Lake (Instant Action)';profile=$profilePath;executable=$exe;executable_sha256=$config.executable_sha256;private_game=$game;environment=$envRecord} |
  ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $run 'run.json')
 Set-Location $root
 $process=Start-Process -FilePath $exe -ArgumentList $argsList -WindowStyle Normal -PassThru -RedirectStandardOutput (Join-Path $run 'stdout.txt') -RedirectStandardError (Join-Path $run 'stderr.txt')
 Write-Output "Big Lake sun test PID $($process.Id). Choose Instant Action / Big Lake. Logs: $run"
 $process.WaitForExit();exit $process.ExitCode
} finally {
 Get-ChildItem Env:MW34_* | ForEach-Object {Remove-Item -LiteralPath ('Env:'+$_.Name)}
 foreach($key in $saved.Keys){[Environment]::SetEnvironmentVariable($key,$saved[$key],'Process')}
}
