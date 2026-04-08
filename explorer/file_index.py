"""
FileExplorer3D - file_index.py
Sorted list index for file name search within the current directory.

Entries are stored as (lowercased_name, file_path) tuples, kept in
alphabetical order. Since DirectoryScanner already returns entries sorted,
building the index is O(n) with no extra sorting needed.

search()        — O(log n) via bisect
search_prefix() — O(log n + m), m = number of matches
"""

import bisect


class FileIndex:

    def __init__(self):
        self._entries: list[tuple[str, str]] = []  # (lowercased_name, path)

    def build(self, objects: list) -> None:
        """Build the index from a list of FileObjects. O(n)."""
        self._entries = [(obj.file_name.lower(), obj.file_path) for obj in objects]

    def clear(self) -> None:
        self._entries = []

    def search(self, name: str) -> str | None:
        """Exact match. Returns path or None. O(log n)."""
        key = name.lower()
        i = bisect.bisect_left(self._entries, (key,))
        if i < len(self._entries) and self._entries[i][0] == key:
            return self._entries[i][1]
        return None

    def search_prefix(self, prefix: str) -> list[tuple[str, str]]:
        """Returns all (name, path) pairs where name starts with prefix. O(log n + m)."""
        prefix = prefix.lower()
        i = bisect.bisect_left(self._entries, (prefix,))
        results = []
        while i < len(self._entries) and self._entries[i][0].startswith(prefix):
            results.append(self._entries[i])
            i += 1
        return results

    def delete(self, name: str, path: str) -> None:
        """Remove a specific (name, path) entry. O(log n) to find, O(n) to remove."""
        key = name.lower()
        i = bisect.bisect_left(self._entries, (key,))
        while i < len(self._entries) and self._entries[i][0] == key:
            if self._entries[i][1] == path:
                self._entries.pop(i)
                return
            i += 1

    @property
    def size(self) -> int:
        return len(self._entries)