# FileExplorer3D
A 3D File Explorer app that uses the Zenith 3D engine to allow the user to traverse through a designated file structure.

## Install (Windows)
1. Install [Anaconda or Miniconda](https://www.anaconda.com/download).

2. Open the repository on GitHub, download the source code zip from the `main` branch, and extract it.
3. Open PowerShell in the extracted project root.
4. Build the app:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\build_windows.ps1
```

5. Run the generated app:

```powershell
.\dist\FileExplorer3D\FileExplorer3D.exe
```

## Install (macOS / Linux)

### Option A: Run From Source (recommended)
1. Install [Anaconda or Miniconda](https://www.anaconda.com/download).
2. From project root, create and activate the environment:

```bash
conda env create -f environment.yml
conda activate FileExplorer3D
```

3. Launch the app:

```bash
python main.py
```

### Option B: Build a Native Binary From Source
1. Open a Bash shell in the extracted project root and run:

```bash
chmod +x ./build_unix.sh
./build_unix.sh
```

2. Open the generated folder and run the app binary:

```bash
cd dist/FileExplorer3D
./FileExplorer3D
```

On macOS, if Gatekeeper blocks first launch, right-click the app/binary and choose Open once.

### First Run Behavior
- The app does not ship with a prebuilt config file.
- A new `config.json` is created automatically on first run with default settings.
- User-specific settings (window size, last folder, bookmarks) are then saved there.

## Setup
This project uses Anaconda for environment management. Before beginning development (or viewing using your preferred IDE), ensure Anaconda is installed. You can download it [here](https://www.anaconda.com/download).

### Creating the Anaconda Environment
From the project root, run:
```bash
conda env create -f environment.yml
conda activate fileexplorer3d
```

### Running the Project
To run the project, run:
```bash
python main.py
```

## Algorithm Implementations
The following section describes each of the units involved in the Python version of the **SSE 554** course and how content from each unit is used
