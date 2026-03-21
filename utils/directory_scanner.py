"""
FileExplorer3D - directory_scanner.py
Scans a directory with os.scandir() and fills the World with FileObjects.
"""

import os
from explorer.file_object import FileObject


class DirectoryScanner:

    COLS    = 10
    SPACING = 2.0
    Y_POS   = 0.5

    @staticmethod
    def scan(path: str) -> list:
        try:
            entries = [e for e in os.scandir(path) if not e.name.startswith('.')]
        except PermissionError:
            print(f"DirectoryScanner: Permission denied — {path}")
            return []

        folders = sorted([e for e in entries if e.is_dir()],  key=lambda e: e.name.lower())
        files   = sorted([e for e in entries if e.is_file()], key=lambda e: e.name.lower())
        return folders + files

    @staticmethod
    def fill_world(world, path: str) -> None:
        world.clear()

        entries = DirectoryScanner.scan(path)

        if not entries:
            print(f"DirectoryScanner: Directory is empty or unreadable — {path}")
            return

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
