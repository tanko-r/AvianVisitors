$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$sdk = "$env:LOCALAPPDATA\Android\Sdk"
$bt = "$sdk\build-tools\36.1.0"
$android = "$sdk\platforms\android-36\android.jar"
$env:PATH = "C:\Program Files\Android\Android Studio\jbr\bin;" + $env:PATH
New-Item -ItemType Directory -Force build\classes | Out-Null
& javac -source 8 -target 8 -classpath $android -d build\classes src\com\avianvisitors\maintenance\MaintenanceGuard.java
if ($LASTEXITCODE -ne 0) { throw 'javac failed' }
$classes = @(Get-ChildItem build\classes -Recurse -Filter *.class | ForEach-Object FullName)
& "$bt\d8.bat" --min-api 23 --lib $android --output build @classes
if ($LASTEXITCODE -ne 0) { throw 'd8 failed' }
& jar cf build\frame-maintenance.jar -C build classes.dex
if ($LASTEXITCODE -ne 0) { throw 'jar failed' }
