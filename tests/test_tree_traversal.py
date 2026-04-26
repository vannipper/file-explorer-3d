"""BFS/DFS traversal tests on FileTreeNode.

The capstone implements DFS via walk_preorder() and BFS via
walk_breadth_first() on the n-ary file tree (Issues #18 and #19).
Tests here exercise traversal ordering, search-by-traversal, and
behaviour on non-trivial topologies with synthetic node trees so we
do not depend on the filesystem.
"""
from __future__ import annotations

from typing import Optional

import pytest

from explorer.file_tree_node import FileTreeNode


def _make_node(name: str, is_dir: bool = True, parent: Optional[FileTreeNode] = None) -> FileTreeNode:
    """Build a synthetic FileTreeNode without touching the filesystem."""
    node = FileTreeNode(path=f"/synthetic/{name}", is_dir=is_dir, parent=parent)
    node.is_expanded = True  # avoid lazy expand on iteration
    return node


def _attach(parent: FileTreeNode, *children: FileTreeNode) -> None:
    for c in children:
        c.parent = parent
    parent.children = list(children)


@pytest.fixture
def synthetic_tree() -> FileTreeNode:
    """
        root
        ├── a
        │   ├── a1
        │   └── a2
        ├── b
        │   └── b1
        │       └── b1x
        └── c
    """
    root = _make_node("root")
    a = _make_node("a")
    b = _make_node("b")
    c = _make_node("c")
    a1 = _make_node("a1", is_dir=False)
    a2 = _make_node("a2", is_dir=False)
    b1 = _make_node("b1")
    b1x = _make_node("b1x", is_dir=False)

    _attach(root, a, b, c)
    _attach(a, a1, a2)
    _attach(b, b1)
    _attach(b1, b1x)
    return root


# ── DFS (walk_preorder) ──────────────────────────────────────────────────


def test_preorder_visits_root_first(synthetic_tree: FileTreeNode) -> None:
    seq = [n.name for n in synthetic_tree.walk_preorder()]
    assert seq[0] == "root"


def test_preorder_full_order(synthetic_tree: FileTreeNode) -> None:
    seq = [n.name for n in synthetic_tree.walk_preorder()]
    assert seq == ["root", "a", "a1", "a2", "b", "b1", "b1x", "c"]


def test_preorder_descends_full_subtree_before_sibling(synthetic_tree: FileTreeNode) -> None:
    seq = [n.name for n in synthetic_tree.walk_preorder()]
    # Every descendant of `a` appears before `b`, every descendant of `b`
    # before `c`.
    assert seq.index("a2") < seq.index("b")
    assert seq.index("b1x") < seq.index("c")


def test_preorder_on_leaf_node_yields_only_self() -> None:
    leaf = _make_node("solo", is_dir=False)
    assert [n.name for n in leaf.walk_preorder()] == ["solo"]


# ── DFS-based search ─────────────────────────────────────────────────────


def test_dfs_search_by_name_finds_correct_node(synthetic_tree: FileTreeNode) -> None:
    target = next(
        (n for n in synthetic_tree.walk_preorder() if n.name == "b1x"),
        None,
    )
    assert target is not None
    assert target.parent.name == "b1"


def test_dfs_search_returns_none_when_not_found(synthetic_tree: FileTreeNode) -> None:
    result = next(
        (n for n in synthetic_tree.walk_preorder() if n.name == "missing"),
        None,
    )
    assert result is None


# ── BFS (walk_breadth_first) ─────────────────────────────────────────────


def test_bfs_visits_root_first(synthetic_tree: FileTreeNode) -> None:
    seq = [n.name for n in synthetic_tree.walk_breadth_first()]
    assert seq[0] == "root"


def test_bfs_visits_level_by_level(synthetic_tree: FileTreeNode) -> None:
    seq = [n.name for n in synthetic_tree.walk_breadth_first()]
    # depth 0: root  | depth 1: a, b, c  | depth 2: a1, a2, b1  | depth 3: b1x
    depth_1 = {"a", "b", "c"}
    depth_2 = {"a1", "a2", "b1"}
    depth_3 = {"b1x"}

    last_idx_d1 = max(seq.index(n) for n in depth_1)
    first_idx_d2 = min(seq.index(n) for n in depth_2)
    last_idx_d2 = max(seq.index(n) for n in depth_2)
    first_idx_d3 = min(seq.index(n) for n in depth_3)

    assert last_idx_d1 < first_idx_d2
    assert last_idx_d2 < first_idx_d3


def test_bfs_returns_shallowest_match_first(synthetic_tree: FileTreeNode) -> None:
    """Add a duplicate-named node deeper and verify BFS hits the shallow one first."""
    deeper = _make_node("dup", is_dir=False)
    shallower = _make_node("dup", is_dir=False)
    a = next(n for n in synthetic_tree.walk_preorder() if n.name == "a")
    b1 = next(n for n in synthetic_tree.walk_preorder() if n.name == "b1")
    a.children = list(a.children) + [shallower]
    b1.children = list(b1.children) + [deeper]
    shallower.parent = a
    deeper.parent = b1

    matches = [n for n in synthetic_tree.walk_breadth_first() if n.name == "dup"]
    assert matches[0] is shallower


def test_bfs_empty_root_yields_only_self() -> None:
    leaf = _make_node("only", is_dir=False)
    assert [n.name for n in leaf.walk_breadth_first()] == ["only"]


# ── DFS-based "size" (recursive count) — analogous to folder size ─────────


def _dfs_count(node: FileTreeNode) -> int:
    """Count nodes via DFS — direct analogue of recursive folder-size."""
    return sum(1 for _ in node.walk_preorder())


def test_dfs_count_matches_known_tree(synthetic_tree: FileTreeNode) -> None:
    assert _dfs_count(synthetic_tree) == 8


def test_dfs_count_on_empty_subtree() -> None:
    leaf = _make_node("leaf", is_dir=False)
    assert _dfs_count(leaf) == 1


def test_dfs_count_subtree_excludes_siblings(synthetic_tree: FileTreeNode) -> None:
    a = next(n for n in synthetic_tree.walk_preorder() if n.name == "a")
    assert _dfs_count(a) == 3  # a, a1, a2
