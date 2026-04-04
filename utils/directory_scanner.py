"""
FileExplorer3D - directory_scanner.py
Scans a directory and populates the World with FileObjects.
"""

import os
from explorer.file_object import FileObject
from explorer.file_tree_node import FileTreeNode

class DirectoryScanner:

    COLS    = 10
    SPACING = 2.0

    @staticmethod
    def fill_world_from_node(world, node: FileTreeNode) -> None:
        world.clear()
        children = node.get_children()

        if not children:
            if node.access_denied:
                print("access denied") # TODO: make this a visual cube within the program
            return

        cols = DirectoryScanner.COLS
        spacing = DirectoryScanner.SPACING

        for idx, child in enumerate(children):
            obj = FileObject(file_path=child.path, is_dir=child.is_dir)

            x = (idx % cols) * spacing
            z = (idx // cols) * spacing
            y = obj.height / 2

            obj.set_position(x, y, z)
            world.add_object(obj)

    @staticmethod
    def scan(path: str) -> list:
        """Return sorted directory entries (folders first), excluding dotfiles.
        Returns None on PermissionError so callers can distinguish from empty dirs.
        """
        try:
            entries = [e for e in os.scandir(path) if not e.name.startswith('.')]
        except PermissionError:
            print(f"DirectoryScanner: Permission denied — {path}")
            return None

        folders = sorted([e for e in entries if e.is_dir()],  key=lambda e: e.name.lower())
        files   = sorted([e for e in entries if e.is_file()], key=lambda e: e.name.lower())
        return folders + files

    @staticmethod
    def fill_world(world, path):
        """Clear the world and populate it with FileObjects from path.
        Returns True on success, False on permission error.
        """
        entries = DirectoryScanner.scan(path)
        if entries is None:
            return False

        world.clear()
        world.current_directory = path

        if not entries:
            print(f"DirectoryScanner: '{path}' is empty")
            return True

        cols    = DirectoryScanner.COLS
        spacing = DirectoryScanner.SPACING

        for i, entry in enumerate(entries):
            obj = FileObject(file_path=entry.path, is_dir=entry.is_dir())
            x = (i % cols) * spacing
            z = (i // cols) * spacing
            y = obj.height / 2
            obj.set_position(x, y, z)
            world.add_object(obj)

        print(f"DirectoryScanner: Spawned {len(entries)} object(s) from '{path}'")
        return True
    