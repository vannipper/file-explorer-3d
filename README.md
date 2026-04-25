# FileExplorer3D
A 3D File Explorer app that uses the Zenith 3D engine to allow the user to traverse through a designated file structure.

## Install (Windows)
No Python installation is required for end users.

1. Open the latest release on GitHub and download the Windows zip file named like `FileExplorer3D-windows-vX.Y.Z.zip`.
2. Right-click the zip and extract it to a folder (for example, Desktop or Program Files).
3. Open the extracted `FileExplorer3D` folder.
4. Run `FileExplorer3D.exe`.

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

### Option B: Use a Release Archive (if provided)
1. Download the archive for your platform from GitHub Releases (for example `FileExplorer3D-linux-vX.Y.Z.tar.gz` or `FileExplorer3D-darwin-vX.Y.Z.tar.gz`).
2. Extract it:

```bash
tar -xzf FileExplorer3D-<platform>-vX.Y.Z.tar.gz
```

3. Open the extracted folder and run the app binary:

```bash
cd FileExplorer3D
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

## Build Release Executable (Maintainers)
Release binaries are distributed through GitHub Releases and are not committed to this repository (`build/` and `dist/` are ignored).

From project root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -Version v0.1.0
```

This creates:
- App folder: `dist\FileExplorer3D`
- Release zip: `dist\FileExplorer3D-windows-v0.1.0.zip`

Upload the zip file to the corresponding GitHub Release.

### Build macOS/Linux release archive
From project root in a Unix shell:

```bash
chmod +x ./build_unix.sh
./build_unix.sh FileExplorer3D v0.1.0
```

This creates:
- App folder: `dist/FileExplorer3D`
- Release archive: `dist/FileExplorer3D-<platform>-v0.1.0.tar.gz`

Upload the archive file to the corresponding GitHub Release.

## Algorithm Implementations
The following section describes each of the units involved in the Python version of the **SSE 554** course and how content from each unit is used

### Directed Graph for Symlinks and Shortcuts

The explorer builds a directed graph while directories are explored to represent
symlink/shortcut relationships:

- Nodes are absolute file/folder paths.
- Directed edges represent link direction: source path -> resolved target path.

Why directed: links have one-way semantics. Path A linking to path B does not
imply B links back to A. Treating this as an undirected graph would lose that
information.

Representation:

- `adjacency: dict[str, list[str]]` for forward lookup.
- `reverse_adjacency: dict[str, list[str]]` for reverse lookup.

Complexity:

- `add_edge()`: O(1) amortized.
- `get_targets()` / `get_sources()`: O(1) lookup + O(k) output size.
- `detect_cycles()`: O(V + E) via DFS coloring.
- `get_connected_component()`: O(V + E) via BFS/DFS.
- Storage: O(V + E).

Implementation notes:

- Symlinks use `os.path.islink(path)` and `os.path.realpath(path)`.
- Windows `.lnk` shortcuts are resolved at discovery time.
- Broken links are preserved in the graph and flagged so they can be rendered
	as warnings without breaking traversal.

## Shortcuts

- `Ctrl+D`: bookmark the selected item, or the current directory if nothing is selected
- `Ctrl+B`: toggle the bookmarks panel
- `Delete`: remove a bookmark from the bookmarks panel