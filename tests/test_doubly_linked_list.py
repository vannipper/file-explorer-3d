"""Unit tests for DoublyLinkedList (used by the bookmarks panel)."""
import pytest

from utils.doubly_linked_list import DoublyLinkedList, DoublyLinkedListNode


# ── construction ─────────────────────────────────────────────────────────


def test_new_list_is_empty() -> None:
    dll = DoublyLinkedList()
    assert len(dll) == 0
    assert dll.head is None
    assert dll.tail is None


def test_iter_on_empty_yields_nothing() -> None:
    dll = DoublyLinkedList()
    assert list(dll) == []


# ── add_to_front ─────────────────────────────────────────────────────────


def test_add_to_front_first_node_sets_head_and_tail() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    assert len(dll) == 1
    assert dll.head is dll.tail
    assert dll.head.full_path == "/p/a"
    assert dll.head.prev is None
    assert dll.head.next is None


def test_add_to_front_chains_links_correctly() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    dll.add_to_front("b", "/p/b", True)
    dll.add_to_front("c", "/p/c", False)

    assert len(dll) == 3
    assert dll.head.full_path == "/p/c"
    assert dll.head.next.full_path == "/p/b"
    assert dll.head.next.next.full_path == "/p/a"
    assert dll.tail.full_path == "/p/a"
    # Reverse traversal validates prev pointers
    assert dll.tail.prev.full_path == "/p/b"
    assert dll.tail.prev.prev.full_path == "/p/c"


def test_adding_existing_path_moves_to_front() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    dll.add_to_front("b", "/p/b", False)
    dll.add_to_front("c", "/p/c", False)

    moved = dll.add_to_front("a (renamed)", "/p/a", True)

    assert len(dll) == 3, "moving must not duplicate"
    assert dll.head is moved
    assert dll.head.full_path == "/p/a"
    # The metadata also updates in-place when re-adding.
    assert dll.head.name == "a (renamed)"
    assert dll.head.is_dir is True


def test_add_to_front_returns_node_reference() -> None:
    dll = DoublyLinkedList()
    node = dll.add_to_front("a", "/p/a", False)
    assert isinstance(node, DoublyLinkedListNode)
    assert node is dll.head


# ── contains / get / __contains__ ────────────────────────────────────────


def test_contains_true_for_added_path() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    assert dll.contains("/p/a") is True
    assert "/p/a" in dll


def test_contains_false_for_missing_path() -> None:
    dll = DoublyLinkedList()
    assert dll.contains("/p/missing") is False
    assert "/p/missing" not in dll


def test_get_returns_node_or_none() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    assert dll.get("/p/a").full_path == "/p/a"
    assert dll.get("/p/missing") is None


# ── remove (head / middle / tail) ────────────────────────────────────────


def test_remove_head() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    dll.add_to_front("b", "/p/b", False)
    dll.add_to_front("c", "/p/c", False)

    assert dll.remove("/p/c") is True
    assert dll.head.full_path == "/p/b"
    assert dll.head.prev is None
    assert len(dll) == 2


def test_remove_middle() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    dll.add_to_front("b", "/p/b", False)
    dll.add_to_front("c", "/p/c", False)

    assert dll.remove("/p/b") is True
    assert dll.head.full_path == "/p/c"
    assert dll.head.next.full_path == "/p/a"
    assert dll.tail.full_path == "/p/a"
    assert dll.tail.prev.full_path == "/p/c"
    assert len(dll) == 2


def test_remove_tail() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    dll.add_to_front("b", "/p/b", False)
    dll.add_to_front("c", "/p/c", False)

    assert dll.remove("/p/a") is True
    assert dll.tail.full_path == "/p/b"
    assert dll.tail.next is None
    assert len(dll) == 2


def test_remove_only_node_empties_list() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    assert dll.remove("/p/a") is True
    assert len(dll) == 0
    assert dll.head is None
    assert dll.tail is None


def test_remove_missing_returns_false() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    assert dll.remove("/p/missing") is False
    assert len(dll) == 1


# ── records round-trip ───────────────────────────────────────────────────


def test_to_records_returns_insertion_order_most_recent_first() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    dll.add_to_front("b", "/p/b", False)
    dll.add_to_front("c", "/p/c", False)

    records = dll.to_records()
    paths = [r["path"] for r in records]
    assert paths == ["/p/c", "/p/b", "/p/a"]


def test_from_records_preserves_order() -> None:
    records = [
        {"name": "c", "path": "/p/c", "is_dir": False},
        {"name": "b", "path": "/p/b", "is_dir": True},
        {"name": "a", "path": "/p/a", "is_dir": False},
    ]
    dll = DoublyLinkedList.from_records(records)
    assert [n.full_path for n in dll] == ["/p/c", "/p/b", "/p/a"]


def test_from_records_round_trips() -> None:
    original = [
        {"name": "x", "path": "/p/x", "is_dir": False},
        {"name": "y", "path": "/p/y", "is_dir": True},
    ]
    dll = DoublyLinkedList.from_records(original)
    assert dll.to_records() == original


def test_from_records_handles_none_or_empty() -> None:
    dll = DoublyLinkedList.from_records(None)
    assert len(dll) == 0
    dll2 = DoublyLinkedList.from_records([])
    assert len(dll2) == 0


def test_from_records_skips_records_without_path() -> None:
    records = [
        {"name": "x", "path": "/p/x", "is_dir": False},
        {"name": "no_path", "path": "", "is_dir": False},
    ]
    dll = DoublyLinkedList.from_records(records)
    assert len(dll) == 1
    assert dll.head.full_path == "/p/x"


# ── clear ────────────────────────────────────────────────────────────────


def test_clear_resets_state() -> None:
    dll = DoublyLinkedList()
    dll.add_to_front("a", "/p/a", False)
    dll.add_to_front("b", "/p/b", False)
    dll.clear()
    assert len(dll) == 0
    assert dll.head is None
    assert dll.tail is None
    assert dll.contains("/p/a") is False
