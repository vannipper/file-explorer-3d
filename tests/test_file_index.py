"""Unit tests for FileIndex (sorted-list search index, BST analogue).

The capstone uses a sorted-list index for O(log n) prefix search instead
of a BST — both deliver the same guarantees over an alphabetised key set.
These tests cover the behaviour required of the BST issue (#6).
"""
from dataclasses import dataclass

import pytest

from explorer.file_index import FileIndex


@dataclass
class _StubObject:
    """Minimal stand-in for FileObject; FileIndex only reads two attrs."""
    file_name: str
    file_path: str


def _make_objs(*names: str) -> list[_StubObject]:
    """Sorted-by-name stubs (lower-case) — matches DirectoryScanner output."""
    paired = sorted(((n.lower(), n) for n in names), key=lambda p: p[0])
    return [_StubObject(file_name=display, file_path=f"/tmp/{display}") for _, display in paired]


# ── construction ─────────────────────────────────────────────────────────


def test_empty_index_size_zero() -> None:
    idx = FileIndex()
    assert idx.size == 0


def test_build_populates_index() -> None:
    idx = FileIndex()
    idx.build(_make_objs("alpha.py", "beta.txt", "gamma.md"))
    assert idx.size == 3


def test_clear_empties_index() -> None:
    idx = FileIndex()
    idx.build(_make_objs("alpha.py"))
    idx.clear()
    assert idx.size == 0


# ── insert + search (exact) ──────────────────────────────────────────────


def test_search_finds_inserted_entries() -> None:
    idx = FileIndex()
    idx.build(_make_objs("alpha.py", "beta.txt", "gamma.md", "delta.json"))
    assert idx.search("alpha.py") == "/tmp/alpha.py"
    assert idx.search("beta.txt") == "/tmp/beta.txt"
    assert idx.search("delta.json") == "/tmp/delta.json"


def test_search_is_case_insensitive() -> None:
    idx = FileIndex()
    idx.build(_make_objs("Alpha.py"))
    assert idx.search("ALPHA.PY") == "/tmp/Alpha.py"
    assert idx.search("alpha.py") == "/tmp/Alpha.py"


def test_search_missing_returns_none() -> None:
    idx = FileIndex()
    idx.build(_make_objs("alpha.py"))
    assert idx.search("missing.txt") is None


def test_search_on_empty_index_returns_none() -> None:
    idx = FileIndex()
    assert idx.search("anything") is None


# ── search_prefix ────────────────────────────────────────────────────────


def test_prefix_matches_only_starts_with() -> None:
    idx = FileIndex()
    idx.build(_make_objs("apple.py", "apricot.txt", "banana.md", "ant.json"))
    results = idx.search_prefix("ap")
    names = [name for name, _ in results]
    assert names == ["apple.py", "apricot.txt"]


def test_prefix_returns_empty_when_no_matches() -> None:
    idx = FileIndex()
    idx.build(_make_objs("apple.py", "banana.txt"))
    assert idx.search_prefix("zzz") == []


def test_prefix_case_insensitive() -> None:
    idx = FileIndex()
    idx.build(_make_objs("Apple.py", "Apricot.txt"))
    results = idx.search_prefix("AP")
    assert len(results) == 2


def test_prefix_no_false_positives_for_substring() -> None:
    """'pp' appears inside 'apple' but should not match a prefix search."""
    idx = FileIndex()
    idx.build(_make_objs("apple.py", "applet.js"))
    assert idx.search_prefix("pp") == []


def test_prefix_returns_sorted_alphabetical_order() -> None:
    """sorted-list backing means traversal yields results in alphabetical order."""
    idx = FileIndex()
    idx.build(_make_objs("cat.txt", "car.py", "card.md"))
    results = idx.search_prefix("ca")
    names = [name for name, _ in results]
    assert names == sorted(names)


# ── delete ───────────────────────────────────────────────────────────────


def test_delete_removes_entry() -> None:
    idx = FileIndex()
    idx.build(_make_objs("alpha.py", "beta.txt"))
    idx.delete("alpha.py", "/tmp/alpha.py")
    assert idx.size == 1
    assert idx.search("alpha.py") is None
    assert idx.search("beta.txt") == "/tmp/beta.txt"


def test_delete_with_unmatched_path_is_noop() -> None:
    """Same name but different path should not be removed."""
    idx = FileIndex()
    idx.build(_make_objs("alpha.py"))
    idx.delete("alpha.py", "/elsewhere/alpha.py")
    assert idx.size == 1
    assert idx.search("alpha.py") == "/tmp/alpha.py"


def test_delete_on_empty_index_is_silent() -> None:
    idx = FileIndex()
    idx.delete("alpha.py", "/tmp/alpha.py")
    assert idx.size == 0


# ── degenerate cases ─────────────────────────────────────────────────────


def test_search_prefix_with_empty_string_returns_all() -> None:
    """An empty prefix string is a prefix of everything."""
    idx = FileIndex()
    idx.build(_make_objs("alpha.py", "beta.txt", "gamma.md"))
    results = idx.search_prefix("")
    assert len(results) == 3


def test_already_sorted_input_works_correctly() -> None:
    """Mirrors degenerate BST input (sorted) — sorted list handles it natively."""
    idx = FileIndex()
    objs = [_StubObject(file_name=n, file_path=f"/tmp/{n}") for n in
            ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]]
    idx.build(objs)
    assert idx.search("c.txt") == "/tmp/c.txt"
    assert [n for n, _ in idx.search_prefix("c")] == ["c.txt"]
