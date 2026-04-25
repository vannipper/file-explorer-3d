"""
FileExplorer3D - file_tree_node.py
N-ary tree node representing one file-system entry. The tree is the single
source of truth for what the 3D viewport displays.
"""

from __future__ import annotations

import os
import subprocess
from collections import deque
from typing import Generator, List, Optional


def _resolve_shortcut_target(shortcut_path: str) -> Optional[str]:
    """Resolve a Windows .lnk shortcut target path using PowerShell COM."""
    if os.name != "nt":
        return None

    escaped = shortcut_path.replace("'", "''")
    command = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"
        + escaped
        + "');"
        "if ($s.TargetPath) { Write-Output $s.TargetPath }"
    )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    target = (result.stdout or "").strip()
    if not target:
        return None

    if not os.path.isabs(target):
        target = os.path.abspath(os.path.join(os.path.dirname(shortcut_path), target))

    return os.path.normpath(target)


class FileTreeNode:
    __slots__ = (
        "path", "name", "is_dir", "is_symlink", "is_shortcut",
        "link_target_path", "link_is_broken",
        "children", "parent", "is_expanded", "access_denied",
    )

    def __init__(
        self,
        path: str,
        is_dir: bool,
        is_symlink: bool = False,
        is_shortcut: bool = False,
        link_target_path: Optional[str] = None,
        link_is_broken: bool = False,
        parent: Optional[FileTreeNode] = None,
    ) -> None:
        self.path          = path
        self.name          = os.path.basename(path)
        self.is_dir        = is_dir
        self.is_symlink    = is_symlink
        self.is_shortcut   = is_shortcut
        self.link_target_path = link_target_path
        self.link_is_broken = link_is_broken
        self.parent        = parent
        self.children: List[FileTreeNode] = []
        self.is_expanded   = False
        self.access_denied = False

    def expand(self, symlink_graph=None) -> None:
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

        children: List[FileTreeNode] = []
        for entry in (dirs + files):
            is_symlink = entry.is_symlink()
            is_shortcut = os.name == "nt" and entry.name.lower().endswith(".lnk")

            child = FileTreeNode(
                path=entry.path,
                is_dir=entry.is_dir(follow_symlinks=False),
                is_symlink=is_symlink,
                is_shortcut=is_shortcut,
                parent=self,
            )

            if is_symlink or is_shortcut:
                resolved_target: Optional[str] = None

                if is_symlink:
                    try:
                        resolved_target = os.path.realpath(entry.path)
                    except OSError:
                        resolved_target = None
                elif is_shortcut:
                    resolved_target = _resolve_shortcut_target(entry.path)

                if resolved_target:
                    resolved_target = os.path.normpath(os.path.abspath(resolved_target))
                    child.link_target_path = resolved_target
                    child.link_is_broken = not os.path.exists(resolved_target)

                    if symlink_graph is not None:
                        symlink_graph.add_edge(child.path, resolved_target)
                        if child.link_is_broken:
                            symlink_graph.mark_edge_broken(child.path, resolved_target, True)
                else:
                    child.link_is_broken = True

            children.append(child)

        self.children = children
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
