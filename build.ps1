# Godot build for Hula Vaquero: the update packs (Code/Assets) and, if the Android SDK + JDK are configured,
# the debug APK. Mirrors .github/workflows/godot-apk.yml locally.
param([switch]$Apk)
# native stderr (e.g. the "Unable to open Android 'build-tools'" warning when no SDK is present) must not abort the build
$ErrorActionPreference = "Continue"
$godot = "C:\Users\Camden\AppData\Local\Programs\Godot\4.6.3\Godot_v4.6.3-stable_win64_console.exe"
$proj  = "C:\Users\Camden\Documents\Default Project\godot-build\godot\hula"
$keystore = "C:\Users\Camden\Documents\Default Project\godot-build\godot\debug.keystore"
$out   = "C:\Users\Camden\Documents\Default Project\godot-build\build"
New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host "== 1. boot smoke test =="
# "-- --smoke" marks this as a test run: the updater then leaves the packs alone, so a 3 s run cannot count as a failed
# start for a pack that is waiting to be confirmed (see updater.gd _test)
$errs = (& $godot --path $proj --resolution 800x600 main.tscn --quit-after 180 -- --smoke 2>&1 | Select-String -Pattern "SCRIPT ERROR|Parse Error|ERROR:")
Write-Host ("   boot errors: " + $errs.Count)

Write-Host "== 2. import =="
& $godot --headless --path $proj --import 2>&1 | Select-String -Pattern "ERROR|Parse Error" | Select-Object -First 10

Write-Host "== 3. update packs =="
& $godot --headless --path $proj --export-pack Code "$out\code.pck" 2>&1 | Select-String -Pattern "ERROR|DONE" | Select-Object -First 3
& $godot --headless --path $proj --export-pack Assets "$out\assets.pck" 2>&1 | Select-String -Pattern "ERROR|DONE" | Select-Object -First 3

if ($Apk) {
  Write-Host "== 4. Android APK =="
  if (-not (Test-Path $keystore)) { throw "missing keystore: $keystore" }
  $preset = Join-Path $proj "export_presets.cfg"
  (Get-Content $preset -Raw) -replace "KEYSTORE_PATH", ($keystore -replace '\\', '/') | Set-Content $preset -NoNewline
  & $godot --headless --path $proj --export-debug Android "$out\HulaVaquero.apk" 2>&1 | Select-Object -Last 6
}

Write-Host "== artifacts =="
Get-ChildItem $out -File | ForEach-Object {
  $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
  "{0,-20} {1,12:N0} bytes  sha256 {2}" -f $_.Name, $_.Length, $h.Substring(0, 16)
}
