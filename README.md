# FileExplorer3D
A 3D File Explorer app that uses the Zenith 3D engine to allow the user to traverse through a designated file structure.

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