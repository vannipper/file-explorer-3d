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
& $venvPython -m pip install Pillow --quiet
& $venvPython -m pip install pygame --quiet

# Added PyOpenGL because main.py imports it!
& $venvPython -m pip install PyOpenGL --quiet 

Write-Host "Building $AppName ($Version) ..."

& $venvPython -m PyInstaller --noconfirm --clean --windowed `
    --name $AppName `
    --icon fileexplorer3d_icon.ico `
    --collect-submodules OpenGL `
    main.py

$distDir = Join-Path $projectRoot "dist"
$appDir = Join-Path $distDir $AppName

if (-Not (Test-Path $appDir)) {
    Write-Host "`nWARNING: The output directory '$appDir' was not found." -ForegroundColor Yellow
    Write-Host "This usually means PyInstaller crashed (scroll up to check for missing icons or modules)." -ForegroundColor Yellow
    exit
}

Write-Host "`nBuild complete!" -ForegroundColor Green
Write-Host "Your executable and files are ready at: $appDir"
