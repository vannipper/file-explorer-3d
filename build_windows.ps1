param(
    [string]$AppName = "FileExplorer3D",
    [string]$Version = "dev",
    [string]$EnvName = "FileExplorer3D" # Matches your environment.yml name
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Checking Conda environment..."

# 1. Check if the environment already exists
$envExists = conda env list | Select-String "\b$EnvName\b"

if (-Not $envExists) {
    Write-Host "Environment '$EnvName' not found. Creating it from environment.yml..."
    conda env create -f environment.yml
} else {
    Write-Host "Environment '$EnvName' found. Updating dependencies to match environment.yml..."
    # --prune removes any packages you might have deleted from the .yml
    conda env update -f environment.yml --prune 
}

Write-Host "`nBuilding $AppName ($Version) ..."

# 2. Run PyInstaller safely inside the Conda environment
conda run -n $EnvName python -m PyInstaller --noconfirm --clean --windowed `
    --name $AppName `
    --icon fileexplorer3d_icon.ico `
    --collect-submodules OpenGL `
    main.py

$distDir = Join-Path $projectRoot "dist"
$appDir = Join-Path $distDir $AppName

# 3. Verify the build succeeded
if (-Not (Test-Path $appDir)) {
    Write-Host "`nWARNING: The output directory '$appDir' was not found." -ForegroundColor Yellow
    Write-Host "This usually means PyInstaller crashed (scroll up to check for missing icons or modules)." -ForegroundColor Yellow
    exit
}

Write-Host "`nBuild complete!" -ForegroundColor Green
Write-Host "Your executable and files are ready at: $appDir"
