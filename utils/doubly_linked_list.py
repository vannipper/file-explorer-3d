"""
FileExplorer3D - doubly_linked_list.py
Reusable doubly-linked list with optional O(1) membership tracking.

This structure is shared by features that need stable insertion-order
semantics with fast front insertion and removal by path key.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(slots=True)
class DoublyLinkedListNode:
    name: str
    full_path: str
    is_dir: bool
    prev: DoublyLinkedListNode | None = None
    next: DoublyLinkedListNode | None = None


class DoublyLinkedList:
    """Doubly-linked list keyed by full path."""

    def __init__(self):
        self.head: DoublyLinkedListNode | None = None
        self.tail: DoublyLinkedListNode | None = None
        self._index: dict[str, DoublyLinkedListNode] = {}

    def __len__(self) -> int:
        return len(self._index)

    def __contains__(self, full_path: str) -> bool:
        return full_path in self._index

    def __iter__(self) -> Iterator[DoublyLinkedListNode]:
        current = self.head
        while current is not None:
            yield current
            current = current.next

    def clear(self) -> None:
        self.head = None
        self.tail = None
        self._index.clear()

    def get(self, full_path: str) -> DoublyLinkedListNode | None:
        return self._index.get(full_path)

    def contains(self, full_path: str) -> bool:
        return full_path in self._index

    def add_to_front(self, name: str, full_path: str, is_dir: bool) -> DoublyLinkedListNode:
        """Insert a node at the front, moving an existing node if needed."""
        existing = self._index.get(full_path)
        if existing is not None:
            existing.name = name
            existing.is_dir = is_dir
            self._detach(existing)
            self._attach_front(existing)
            return existing

        node = DoublyLinkedListNode(name=name, full_path=full_path, is_dir=is_dir)
        self._attach_front(node)
        self._index[full_path] = node
        return node

    def remove(self, full_path: str) -> bool:
        node = self._index.pop(full_path, None)
        if node is None:
            return False
        self._detach(node)
        node.prev = None
        node.next = None
        return True

    def to_records(self) -> list[dict[str, object]]:
        return [
            {
                "name": node.name,
                "path": node.full_path,
                "is_dir": node.is_dir,
            }
            for node in self
        ]

    @classmethod
    def from_records(cls, records: list[dict[str, object]] | None) -> DoublyLinkedList:
        linked_list = cls()
        if not records:
            return linked_list

        for record in reversed(records):
            try:
                name = str(record.get("name", ""))
                full_path = str(record.get("path", ""))
                is_dir = bool(record.get("is_dir", False))
            except AttributeError:
                continue
            if not full_path:
                continue
            if not name:
                name = full_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1] or full_path
            linked_list.add_to_front(name, full_path, is_dir)

        return linked_list

    def _detach(self, node: DoublyLinkedListNode) -> None:
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

    def _attach_front(self, node: DoublyLinkedListNode) -> None:
        node.prev = None
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        else:
            self.tail = node
        self.head = node
