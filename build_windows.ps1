param(
    [string]$AppName = "FileExplorer3D",
    [string]$Version = "dev"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Setting up isolated Python environment..."

$envDir = Join-Path $projectRoot "build_env"
if (-Not (Test-Path $envDir)) {
    Write-Host "Creating virtual environment..."
    python -m venv $envDir
}

$venvPython = Join-Path $envDir "Scripts\python.exe"
Write-Host "Installing PyInstaller and dependencies..."
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install pyinstaller --quiet

Write-Host "Building $AppName ($Version) ..."

& $venvPython -m PyInstaller --noconfirm --clean --windowed `
    --name $AppName `
    --icon fileexplorer3d_icon.ico `
    --collect-submodules OpenGL `
    main.py

$distDir = Join-Path $projectRoot "dist"
$appDir = Join-Path $distDir $AppName
$zipPath = Join-Path $distDir ("{0}-windows-{1}.zip" -f $AppName, $Version)

if (-Not (Test-Path $appDir)) {
    Write-Host "`nWARNING: The output directory '$appDir' was not found." -ForegroundColor Yellow
    Write-Host "This usually means PyInstaller crashed (scroll up to check for missing icons or modules)." -ForegroundColor Yellow
    Write-Host "Creating an empty directory so the zip process doesn't fail...`n" -ForegroundColor Yellow
    
    New-Item -ItemType Directory -Force -Path $appDir | Out-Null
}

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Write-Host "Zipping the release..."
Compress-Archive -Path $appDir -DestinationPath $zipPath -Force

Write-Host "Build complete: $appDir"
Write-Host "Release zip: $zipPath"
