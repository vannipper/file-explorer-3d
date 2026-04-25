param(
    [string]$AppName = "FileExplorer3D",
    [string]$Version = "dev"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Building $AppName ($Version) ..."

# Build a windowed app and intentionally do NOT bundle config files.
pyinstaller --noconfirm --clean --windowed `
    --name $AppName `
    --icon fileexplorer3d_icon.png `
    --collect-submodules OpenGL `
    --add-data "img;img" `
    main.py

$distDir = Join-Path $projectRoot "dist"
$appDir = Join-Path $distDir $AppName
$zipPath = Join-Path $distDir ("{0}-windows-{1}.zip" -f $AppName, $Version)

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path $appDir -DestinationPath $zipPath -Force

Write-Host "Build complete: $appDir"
Write-Host "Release zip: $zipPath"
