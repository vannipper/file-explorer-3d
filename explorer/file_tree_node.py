"""
FileExplorer3D - file_tree_node.py
N-ary tree node representing one file-system entry. The tree is the single
source of truth for what the 3D viewport displays.
"""

from __future__ import annotations

import os
from collections import deque
from typing import Generator, List, Optional

class FileTreeNode:
    __slots__ = (
        "path", "name", "is_dir", "is_symlink",
        "children", "parent", "is_expanded", "access_denied",
    )

    def __init__(
        self,
        path: str,
        is_dir: bool,
        is_symlink: bool = False,
        parent: Optional[FileTreeNode] = None,
    ) -> None:
        self.path          = path
        self.name          = os.path.basename(path)
        self.is_dir        = is_dir
        self.is_symlink    = is_symlink
        self.parent        = parent
        self.children: List[FileTreeNode] = []
        self.is_expanded   = False
        self.access_denied = False

    def expand(self) -> None:
        """Scan the directory and populate children. O(k), k = entry count."""
        if not self.is_dir or self.is_expanded:
            return

        try:
            raw = [e for e in os.scandir(self.path) if not e.name.startswith(".")]
        except PermissionError:
            print(f"FileTreeNode: Permission denied — {self.path}")
            self.access_denied = True
            self.is_expanded = True
            return

        dirs  = sorted([e for e in raw if     e.is_dir(follow_symlinks=False)], key=lambda e: e.name.lower())
        files = sorted([e for e in raw if not e.is_dir(follow_symlinks=False)], key=lambda e: e.name.lower())

        self.children = [
            FileTreeNode(
                path=entry.path,
                is_dir=entry.is_dir(follow_symlinks=False),
                is_symlink=entry.is_symlink(),
                parent=self,
            )
            for entry in (dirs + files)
        ]
        self.is_expanded = True

    def collapse(self) -> None:
        """Clear children and free the subtree. O(1)."""
        self.children = []
        self.is_expanded = False

    def get_children(self) -> List[FileTreeNode]:
        """Return children, expanding first if needed. O(k) first call, O(1) after."""
        if not self.is_expanded:
            self.expand()
        return self.children

    def find_child(self, name: str) -> Optional[FileTreeNode]:
        """Find a direct child by name (case-sensitive). O(k)."""
        for child in self.get_children():
            if child.name == name:
                return child
        return None

    def walk_preorder(self) -> Generator[FileTreeNode, None, None]:
        """Depth-first pre-order over already-expanded nodes. O(n)."""
        yield self
        for child in self.children:
            yield from child.walk_preorder()

    def walk_breadth_first(self) -> Generator[FileTreeNode, None, None]:
        """Breadth-first over already-expanded nodes. O(n)."""
        queue: deque[FileTreeNode] = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    def get_path_from_root(self) -> List[FileTreeNode]:
        """Return ancestor chain from root to self (for breadcrumbs). O(d)."""
        chain: List[FileTreeNode] = []
        node: Optional[FileTreeNode] = self
        while node is not None:
            chain.append(node)
            node = node.parent
        chain.reverse()
        return chain

    def __repr__(self) -> str:
        kind = "dir" if self.is_dir else "file"
        return f"FileTreeNode({kind}, {'expanded' if self.is_expanded else 'lazy'}, children={len(self.children)}, name={self.name!r})"


def make_root(path: str) -> FileTreeNode:
    """Create an unexpanded root node for a user-selected directory. O(1)."""
    return FileTreeNode(path=os.path.abspath(path), is_dir=True, is_symlink=False, parent=None)
