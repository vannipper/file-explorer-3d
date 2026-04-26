"""Unit tests for FileTreeNode (n-ary lazy file-system tree)."""
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from explorer.file_tree_node import FileTreeNode, make_root
from explorer.symlink_graph import SymlinkGraph


def _build_sample_tree(root: Path) -> None:
    """Create a known directory structure for tests.

        root/
        ├── alpha/
        │   ├── one.txt
        │   └── two.txt
        ├── beta/
        │   └── nested/
        │       └── three.txt
        ├── gamma/        (empty)
        └── readme.md
    """
    (root / "alpha").mkdir()
    (root / "alpha" / "one.txt").write_text("1")
    (root / "alpha" / "two.txt").write_text("2")
    (root / "beta" / "nested").mkdir(parents=True)
    (root / "beta" / "nested" / "three.txt").write_text("3")
    (root / "gamma").mkdir()
    (root / "readme.md").write_text("readme")


@pytest.fixture
def tmp_tree(tmp_path: Path) -> Path:
    _build_sample_tree(tmp_path)
    return tmp_path


# ── construction & expansion ─────────────────────────────────────────────


@pytest.mark.slow
def test_make_root_creates_unexpanded_dir_node(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    assert root.is_dir is True
    assert root.is_expanded is False
    assert root.children == []
    assert root.parent is None
    assert root.path == os.path.abspath(str(tmp_tree))


@pytest.mark.slow
def test_expand_populates_children_with_dirs_first(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()

    names = [c.name for c in root.children]
    # alpha, beta, gamma are dirs and come before files (alphabetized within each group)
    assert names == ["alpha", "beta", "gamma", "readme.md"]
    assert root.is_expanded is True


@pytest.mark.slow
def test_expand_is_idempotent(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    children_first = list(root.children)
    root.expand()  # should not re-scan
    assert root.children == children_first


@pytest.mark.slow
def test_lazy_children_until_expand(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    assert root.children == []
    assert root.is_expanded is False

    children = root.get_children()
    assert root.is_expanded is True
    assert len(children) == 4


@pytest.mark.slow
def test_collapse_clears_children(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    assert root.children
    root.collapse()
    assert root.children == []
    assert root.is_expanded is False


# ── find_child ───────────────────────────────────────────────────────────


@pytest.mark.slow
def test_find_child_returns_match(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    alpha = root.find_child("alpha")
    assert alpha is not None
    assert alpha.is_dir is True


@pytest.mark.slow
def test_find_child_returns_none_for_missing(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    assert root.find_child("does_not_exist") is None


@pytest.mark.slow
def test_find_child_is_case_sensitive(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    assert root.find_child("ALPHA") is None
    assert root.find_child("alpha") is not None


# ── walk_preorder (DFS) ──────────────────────────────────────────────────


@pytest.mark.slow
def test_walk_preorder_visits_self_then_descendants(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    alpha = root.find_child("alpha")
    alpha.expand()

    visited = [n.name for n in root.walk_preorder()]
    # root first, then alpha and its files, then siblings (which are unexpanded)
    assert visited[0] == os.path.basename(str(tmp_tree))
    assert visited[1] == "alpha"
    # alpha's children should appear right after alpha (DFS ordering)
    one_idx = visited.index("one.txt")
    two_idx = visited.index("two.txt")
    beta_idx = visited.index("beta")
    assert one_idx < beta_idx and two_idx < beta_idx


# ── walk_breadth_first (BFS) ─────────────────────────────────────────────


@pytest.mark.slow
def test_walk_breadth_first_visits_level_by_level(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    beta = root.find_child("beta")
    beta.expand()
    nested = beta.find_child("nested")
    nested.expand()

    visited = [n.name for n in root.walk_breadth_first()]
    # All depth-1 nodes appear before any depth-2 node.
    depth_1 = {"alpha", "beta", "gamma", "readme.md"}
    nested_idx = visited.index("nested")
    for name in depth_1:
        if name in visited:
            assert visited.index(name) < nested_idx, (
                f"{name} (depth 1) should come before nested (depth 2)"
            )


# ── get_path_from_root ───────────────────────────────────────────────────


@pytest.mark.slow
def test_get_path_from_root_returns_full_chain(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    root.expand()
    beta = root.find_child("beta")
    beta.expand()
    nested = beta.find_child("nested")

    chain = nested.get_path_from_root()
    assert [n.name for n in chain] == [root.name, "beta", "nested"]


@pytest.mark.slow
def test_get_path_from_root_for_root_is_self_only(tmp_tree: Path) -> None:
    root = make_root(str(tmp_tree))
    chain = root.get_path_from_root()
    assert chain == [root]


# ── edge cases ───────────────────────────────────────────────────────────


@pytest.mark.slow
def test_expand_empty_directory(tmp_path: Path) -> None:
    root = make_root(str(tmp_path))
    root.expand()
    assert root.children == []
    assert root.is_expanded is True
    assert root.access_denied is False


@pytest.mark.slow
def test_expand_handles_permission_denied(tmp_path: Path) -> None:
    root = make_root(str(tmp_path))

    with mock.patch("explorer.file_tree_node.os.scandir", side_effect=PermissionError):
        root.expand()

    assert root.access_denied is True
    assert root.is_expanded is True
    assert root.children == []


@pytest.mark.slow
def test_expand_skips_dotfiles(tmp_path: Path) -> None:
    (tmp_path / ".hidden").write_text("nope")
    (tmp_path / "visible.txt").write_text("yes")

    root = make_root(str(tmp_path))
    root.expand()
    names = [c.name for c in root.children]
    assert ".hidden" not in names
    assert "visible.txt" in names


@pytest.mark.slow
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX symlink semantics")
def test_expand_records_symlink_children(tmp_path: Path) -> None:
    target = tmp_path / "real_target.txt"
    target.write_text("hi")
    link_path = tmp_path / "link_to_target"
    os.symlink(target, link_path)

    graph = SymlinkGraph()
    root = make_root(str(tmp_path))
    root.expand(symlink_graph=graph)

    link_node = root.find_child("link_to_target")
    assert link_node is not None
    assert link_node.is_symlink is True
    assert link_node.link_target_path == os.path.normpath(os.path.abspath(str(target)))
    assert link_node.link_is_broken is False
    assert (link_node.path, link_node.link_target_path) in graph.get_all_edges()


@pytest.mark.slow
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX symlink semantics")
def test_broken_symlink_is_flagged(tmp_path: Path) -> None:
    link_path = tmp_path / "broken"
    os.symlink(tmp_path / "missing_target", link_path)

    graph = SymlinkGraph()
    root = make_root(str(tmp_path))
    root.expand(symlink_graph=graph)

    broken = root.find_child("broken")
    assert broken is not None
    assert broken.is_symlink is True
    assert broken.link_is_broken is True
