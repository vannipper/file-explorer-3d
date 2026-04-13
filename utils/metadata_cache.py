"""
FileExplorer3D - metadata_cache.py
Dictionary-based cache mapping file paths to their metadata.

Unit 11 — Sets & Dicts: MetadataCache wraps a dict[str, FileMetadata],
providing O(1) average-case lookup and insertion. File paths serve as
unique hash keys, making a dictionary the natural data structure.
"""

import os
import stat
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def format_size(size_bytes: int) -> str:
    """
    Convert a byte count to a human-readable string.

    Thresholds:
        < 1 KB  → "N B"
        < 1 MB  → "N.N KB"
        < 1 GB  → "N.N MB"
        else    → "N.N GB"

    O(1) — constant number of comparisons.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.1f} GB"


@dataclass
class FileMetadata:
    """
    Snapshot of a file's stat data.

    Fields:
        size_bytes:     raw byte count from os.lstat()
        file_type:      file extension (e.g. ".py") or "directory" or "file"
        modified_date:  last modification timestamp
        created_date:   creation / inode-change timestamp
        permissions:    POSIX permission string (e.g. "drwxr-xr-x")
        is_symlink:     True if path is a symbolic link
        symlink_target: readlink() result, or None if not a symlink
    """
    size_bytes:     int
    file_type:      str
    modified_date:  datetime
    created_date:   datetime
    permissions:    str
    is_symlink:     bool
    symlink_target: Optional[str]


class MetadataCache:
    """
    Cache mapping file paths (str) to FileMetadata objects.

    Wraps a dict[str, FileMetadata | None]. None values represent paths
    where stat failed (permission denied, file missing), preventing
    repeated failed stat calls for the same inaccessible path.

    Big-O:
        get()                  O(1) avg — dict lookup; miss: one os.lstat() + insert
        get_if_cached()        O(1) avg — dict lookup only, no I/O
        invalidate()           O(1)     — dict.pop() by key
        invalidate_directory() O(n)     — scans all n cached keys for prefix match
        preload()              O(k)     — k stat() calls, one per path
        size (property)        O(1)     — len() on dict
        clear()                O(n)     — clears all n entries

    Why a dictionary: file paths are unique strings — ideal hash keys. The
    cache pattern (lookup → miss → stat → insert → return) is the textbook
    dictionary use case, giving O(1) average access vs. O(n) linear scan of
    a list.
    """

    def __init__(self):
        self._cache: dict[str, Optional[FileMetadata]] = {}

    def get(self, path: str) -> Optional[FileMetadata]:
        """
        Return FileMetadata for path, calling os.lstat() on first access.
        Caches None for paths that raised an OS error.
        O(1) average.
        """
        if path not in self._cache:
            self._cache[path] = self._stat(path)
        return self._cache[path]

    def get_if_cached(self, path: str) -> Optional[FileMetadata]:
        """
        Return cached metadata without triggering a stat call. O(1) average.
        Returns None if path has not been cached yet.
        """
        return self._cache.get(path)

    def invalidate(self, path: str) -> None:
        """Remove a single cached entry. O(1)."""
        self._cache.pop(path, None)

    def invalidate_directory(self, dir_path: str) -> None:
        """
        Remove all cached entries whose path starts with dir_path. O(n)
        where n = total cached entries. Called when a directory's contents
        change (e.g. after a file operation).
        """
        prefix = dir_path if dir_path.endswith(os.sep) else dir_path + os.sep
        to_remove = [
            k for k in self._cache
            if k == dir_path or k.startswith(prefix)
        ]
        for key in to_remove:
            del self._cache[key]

    def preload(self, paths: list[str]) -> None:
        """
        Batch-populate the cache for a list of paths. O(k) where k = len(paths).
        Only stat()s paths not already cached. Called when entering a directory
        to warm the cache for all visible items before they are selected.
        """
        for path in paths:
            if path not in self._cache:
                self._cache[path] = self._stat(path)

    @property
    def size(self) -> int:
        """Number of cached entries. O(1)."""
        return len(self._cache)

    def clear(self) -> None:
        """Flush the entire cache. O(n)."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _stat(self, path: str) -> Optional[FileMetadata]:
        """
        Call os.lstat() and build a FileMetadata. Returns None on any OS error.
        Uses lstat() so that symlinks are not followed — metadata describes
        the link itself, not its target.
        """
        try:
            s = os.lstat(path)
        except OSError:
            return None

        is_symlink = stat.S_ISLNK(s.st_mode)
        symlink_target: Optional[str] = None
        if is_symlink:
            try:
                symlink_target = os.readlink(path)
            except OSError:
                pass

        if stat.S_ISDIR(s.st_mode):
            file_type = "directory"
        else:
            _, ext = os.path.splitext(path)
            file_type = ext.lower() if ext else "file"

        return FileMetadata(
            size_bytes    = s.st_size,
            file_type     = file_type,
            modified_date = datetime.fromtimestamp(s.st_mtime),
            created_date  = datetime.fromtimestamp(s.st_ctime),
            permissions   = stat.filemode(s.st_mode),
            is_symlink    = is_symlink,
            symlink_target= symlink_target,
        )
