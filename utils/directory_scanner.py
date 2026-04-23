"""
FileExplorer3D - directory_scanner.py
Scans a directory and populates the World with FileObjects.
"""

from explorer.file_object import FileObject
from explorer.file_tree_node import FileTreeNode, make_root
from utils.metadata_cache import MetadataCache


class DirectoryScanner:

    COLS    = 10
    SPACING = 2.0

    @staticmethod
    def fill_world_from_node(world, node: FileTreeNode) -> bool:
        """Clear the world and populate it from a FileTreeNode.
        Returns True on success, False on permission error.
        """
        symlink_graph = getattr(world, "symlink_graph", None)
        node.expand(symlink_graph)
        children = node.children

        if node.access_denied:
            print("access denied") # TODO: make this a visual cube within the program
            return False

        world.clear()

        if not children:
            return True

        world.current_directory = node.path

        cols    = DirectoryScanner.COLS
        spacing = DirectoryScanner.SPACING

        for idx, child in enumerate(children):
            obj = FileObject(
                file_path=child.path,
                is_dir=child.is_dir,
                is_symlink=child.is_symlink,
                is_shortcut=child.is_shortcut,
                link_target_path=child.link_target_path,
                link_broken=child.link_is_broken,
            )

            x = (idx % cols) * spacing
            z = (idx // cols) * spacing
            y = obj.height / 2

            obj.set_position(x, y, z)
            world.add_object(obj)

        cycle_nodes = set()
        if symlink_graph is not None:
            cycle_nodes = symlink_graph.get_cycle_nodes()
        for obj in world.objects:
            obj.in_cycle = obj.file_path in cycle_nodes
            obj.link_target_in_view = bool(obj.link_target_path and world.get_object_by_path(obj.link_target_path))

        if hasattr(world, 'metadata_cache') and isinstance(world.metadata_cache, MetadataCache):
            world.metadata_cache.preload([obj.file_path for obj in world.objects])

        print(f"DirectoryScanner: Spawned {len(children)} object(s) from '{node.path}'")
        return True

    @staticmethod
    def fill_world(world, path: str) -> bool:
        """Convenience wrapper: create a root node from path and fill the world."""
        node = make_root(path)
        return DirectoryScanner.fill_world_from_node(world, node)
