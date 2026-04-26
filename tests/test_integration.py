"""End-to-end integration tests across multiple data structures.

Builds a real temporary file tree on disk, then exercises the n-ary
FileTreeNode, SymlinkGraph, FileIndex, NavigationStack, MetadataCache,
and DoublyLinkedList together — the same wiring used by the live app
(minus the rendering layer).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from explorer.file_index import FileIndex
from explorer.file_tree_node import FileTreeNode, make_root
from explorer.symlink_graph import SymlinkGraph
from utils.doubly_linked_list import DoublyLinkedList
from utils.metadata_cache import MetadataCache
from utils.navigation_stack import NavigationStack


@dataclass
class _IndexableObject:
    """Mirrors FileObject's interface for FileIndex without OpenGL."""
    file_name: str
    file_path: str


def _build_sorted_index(nodes) -> FileIndex:
    """FileIndex expects entries pre-sorted by lowercased name."""
    objs = sorted(
        (_IndexableObject(file_name=n.name, file_path=n.path) for n in nodes),
        key=lambda o: o.file_name.lower(),
    )
    idx = FileIndex()
    idx.build(objs)
    return idx


def _build_world(root: Path) -> None:
    """A non-trivial directory layout used by every integration test below.

        root/
        ├── projects/
        │   ├── alpha.py
        │   ├── beta.py
        │   └── docs/
        │       └── readme.md
        ├── archive/
        │   └── old.txt
        ├── shortcut_to_alpha   (symlink → projects/alpha.py)
        └── notes.md
    """
    (root / "projects" / "docs").mkdir(parents=True)
    (root / "projects" / "alpha.py").write_text("alpha content")
    (root / "projects" / "beta.py").write_text("beta")
    (root / "projects" / "docs" / "readme.md").write_text("# readme")
    (root / "archive").mkdir()
    (root / "archive" / "old.txt").write_text("old")
    (root / "notes.md").write_text("notes")

    if sys.platform != "win32":
        link = root / "shortcut_to_alpha"
        os.symlink(root / "projects" / "alpha.py", link)


@pytest.fixture
def world(tmp_path: Path) -> Path:
    _build_world(tmp_path)
    return tmp_path


# ── 1. tree + graph ──────────────────────────────────────────────────────


@pytest.mark.slow
def test_tree_construction_and_symlink_graph(world: Path) -> None:
    """Expanding the tree populates a symlink graph with discovered links."""
    graph = SymlinkGraph()
    root = make_root(str(world))
    root.expand(symlink_graph=graph)

    names = {c.name for c in root.children}
    expected = {"projects", "archive", "notes.md"}
    if sys.platform != "win32":
        expected.add("shortcut_to_alpha")
    assert expected <= names

    if sys.platform != "win32":
        # Confirm the graph captured the symlink edge.
        link_node = root.find_child("shortcut_to_alpha")
        assert link_node is not None
        assert link_node.is_symlink is True
        assert graph.has_edge(link_node.path, link_node.link_target_path)


@pytest.mark.slow
def test_recursive_expansion_walks_full_subtree(world: Path) -> None:
    root = make_root(str(world))
    root.expand()
    projects = root.find_child("projects")
    projects.expand()
    docs = projects.find_child("docs")
    docs.expand()

    seen = {n.name for n in root.walk_preorder()}
    assert {"projects", "alpha.py", "beta.py", "docs", "readme.md"} <= seen


# ── 2. tree + index search ───────────────────────────────────────────────


@pytest.mark.slow
def test_tree_drives_file_index_prefix_search(world: Path) -> None:
    """Children of a directory feed the FileIndex; prefix search returns matches."""
    root = make_root(str(world))
    root.expand()
    projects = root.find_child("projects")
    projects.expand()

    idx = _build_sorted_index(projects.children)

    matches = idx.search_prefix("a")
    names = sorted(name for name, _ in matches)
    assert names == ["alpha.py"]

    py_matches = idx.search_prefix("b")
    assert any(name == "beta.py" for name, _ in py_matches)


# ── 3. navigation + tree ─────────────────────────────────────────────────


@pytest.mark.slow
def test_navigate_into_subdir_and_back(world: Path) -> None:
    nav = NavigationStack()
    nav.navigate_to(str(world))
    assert nav.current_path == str(world)

    sub = world / "projects"
    nav.navigate_to(str(sub))
    assert nav.can_go_back() is True

    back = nav.go_back()
    assert back == str(world)
    assert nav.can_go_forward() is True

    forward = nav.go_forward()
    assert forward == str(sub)


@pytest.mark.slow
def test_navigate_then_branch_clears_forward(world: Path) -> None:
    nav = NavigationStack()
    nav.navigate_to(str(world))
    nav.navigate_to(str(world / "projects"))
    nav.navigate_to(str(world / "projects" / "docs"))

    nav.go_back()  # back to projects
    nav.navigate_to(str(world / "archive"))  # branch — forward must clear

    assert nav.can_go_forward() is False
    # And the back stack has the expected progression.
    assert nav.back_stack[-1] == str(world / "projects")


# ── 4. metadata cache + tree ─────────────────────────────────────────────


@pytest.mark.slow
def test_metadata_cache_preload_for_directory(world: Path) -> None:
    root = make_root(str(world))
    root.expand()

    cache = MetadataCache()
    paths = [c.path for c in root.children]
    cache.preload(paths)

    assert cache.size == len(paths)
    notes = cache.get_if_cached(str(world / "notes.md"))
    assert notes is not None
    assert notes.file_type == ".md"


@pytest.mark.slow
def test_metadata_cache_invalidate_directory_after_navigation(world: Path) -> None:
    cache = MetadataCache()
    cache.get(str(world / "projects" / "alpha.py"))
    cache.get(str(world / "projects" / "beta.py"))
    cache.get(str(world / "notes.md"))
    assert cache.size == 3

    cache.invalidate_directory(str(world / "projects"))
    assert cache.get_if_cached(str(world / "projects" / "alpha.py")) is None
    assert cache.get_if_cached(str(world / "notes.md")) is not None


# ── 5. bookmarks (DLL) + persistence round-trip ──────────────────────────


@pytest.mark.slow
def test_bookmark_workflow_round_trip(world: Path) -> None:
    bookmarks = DoublyLinkedList()
    bookmarks.add_to_front("notes.md", str(world / "notes.md"), False)
    bookmarks.add_to_front("projects", str(world / "projects"), True)
    bookmarks.add_to_front("archive", str(world / "archive"), True)

    # Most-recent-first ordering preserved.
    assert [n.full_path for n in bookmarks][0] == str(world / "archive")

    # Removing one updates linkage.
    bookmarks.remove(str(world / "projects"))
    assert bookmarks.contains(str(world / "projects")) is False
    assert len(bookmarks) == 2

    # Round-trip via to_records / from_records (config persistence path).
    records = bookmarks.to_records()
    rebuilt = DoublyLinkedList.from_records(records)
    assert rebuilt.to_records() == records


# ── 6. cycle detection across multiple symlinks ──────────────────────────


@pytest.mark.slow
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX symlink semantics")
def test_symlink_discovery_records_real_edges(tmp_path: Path) -> None:
    """Expanding a directory feeds the graph with all symlink edges discovered."""
    target_dir = tmp_path / "real_target"
    target_dir.mkdir()
    target_file = tmp_path / "real_target" / "data.txt"
    target_file.write_text("hi")

    os.symlink(target_dir, tmp_path / "link_to_dir")
    os.symlink(target_file, tmp_path / "link_to_file")

    graph = SymlinkGraph()
    root = make_root(str(tmp_path))
    root.expand(symlink_graph=graph)

    edges = set(graph.get_all_edges())
    expected_dir_edge = (str(tmp_path / "link_to_dir"), str(target_dir))
    expected_file_edge = (str(tmp_path / "link_to_file"), str(target_file))
    assert expected_dir_edge in edges
    assert expected_file_edge in edges
    # No spurious cycles in this acyclic structure.
    assert graph.get_cycle_nodes() == set()


# ── 7. full happy path: tree → search → navigate → bookmark → cache ──────


@pytest.mark.slow
def test_full_user_flow(world: Path) -> None:
    """Simulate: open → list → search → enter folder → bookmark → go back."""
    nav = NavigationStack()
    cache = MetadataCache()
    bookmarks = DoublyLinkedList()
    graph = SymlinkGraph()

    # 1. Open the world directory.
    nav.navigate_to(str(world))
    root = make_root(str(world))
    root.expand(symlink_graph=graph)
    cache.preload([c.path for c in root.children])

    # 2. Search for 'no' — expect notes.md.
    idx = _build_sorted_index(root.children)
    hits = idx.search_prefix("no")
    assert any(name == "notes.md" for name, _ in hits)

    # 3. Enter the projects folder.
    projects = root.find_child("projects")
    nav.navigate_to(projects.path)
    projects.expand(symlink_graph=graph)
    cache.preload([c.path for c in projects.children])

    # 4. Bookmark alpha.py.
    alpha = projects.find_child("alpha.py")
    bookmarks.add_to_front(alpha.name, alpha.path, alpha.is_dir)
    assert bookmarks.contains(alpha.path)

    # 5. Go back; bookmark should still be there; cache should still have alpha.
    nav.go_back()
    assert nav.current_path == str(world)
    assert bookmarks.contains(alpha.path)
    assert cache.get_if_cached(alpha.path) is not None
