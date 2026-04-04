"""
FileExplorer3D - directory_scanner.py
Scans a directory and populates the World with FileObjects.
"""

from explorer.file_object import FileObject
from explorer.file_tree_node import FileTreeNode, make_root


class DirectoryScanner:

    COLS    = 10
    SPACING = 2.0

    @staticmethod
    def fill_world_from_node(world, node: FileTreeNode) -> bool:
        """Clear the world and populate it from a FileTreeNode.
        Returns True on success, False on permission error.
        """
        world.clear()
        children = node.get_children()

        if not children:
            if node.access_denied:
                print("access denied") # TODO: make this a visual cube within the program
                return False
            return True

        world.current_directory = node.path

        cols    = DirectoryScanner.COLS
        spacing = DirectoryScanner.SPACING

        for idx, child in enumerate(children):
            obj = FileObject(file_path=child.path, is_dir=child.is_dir)

            x = (idx % cols) * spacing
            z = (idx // cols) * spacing
            y = obj.height / 2

            obj.set_position(x, y, z)
            world.add_object(obj)

        print(f"DirectoryScanner: Spawned {len(children)} object(s) from '{node.path}'")
        return True

    @staticmethod
    def fill_world(world, path: str) -> bool:
        """Convenience wrapper: create a root node from path and fill the world."""
        node = make_root(path)
        return DirectoryScanner.fill_world_from_node(world, node)
