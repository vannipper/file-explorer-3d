"""Unit tests for MetadataCache (path → FileMetadata dict cache)."""
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

from utils.metadata_cache import (
    FileMetadata,
    MetadataCache,
    format_size,
)


# ── format_size helper ───────────────────────────────────────────────────


def test_format_size_bytes() -> None:
    assert format_size(0) == "0 B"
    assert format_size(512) == "512 B"
    assert format_size(1023) == "1023 B"


def test_format_size_kilobytes() -> None:
    assert format_size(1024) == "1.0 KB"
    assert format_size(2048) == "2.0 KB"


def test_format_size_megabytes() -> None:
    assert format_size(1024 ** 2) == "1.0 MB"


def test_format_size_gigabytes() -> None:
    assert format_size(1024 ** 3) == "1.0 GB"


# ── basic dict semantics ─────────────────────────────────────────────────


def test_new_cache_is_empty() -> None:
    cache = MetadataCache()
    assert cache.size == 0


@pytest.mark.slow
def test_get_populates_cache_on_miss(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("hello")

    cache = MetadataCache()
    assert cache.get_if_cached(str(target)) is None  # not cached yet

    meta = cache.get(str(target))
    assert isinstance(meta, FileMetadata)
    assert meta.size_bytes == 5
    assert meta.file_type == ".txt"
    assert cache.size == 1


@pytest.mark.slow
def test_get_hit_does_not_call_lstat_again(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("x")

    cache = MetadataCache()
    cache.get(str(target))  # populate

    with mock.patch("utils.metadata_cache.os.lstat") as fake_lstat:
        cache.get(str(target))
        fake_lstat.assert_not_called()


@pytest.mark.slow
def test_get_if_cached_does_not_populate(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("x")

    cache = MetadataCache()
    assert cache.get_if_cached(str(target)) is None
    assert cache.size == 0  # still empty — no I/O happened


# ── invalidate ───────────────────────────────────────────────────────────


@pytest.mark.slow
def test_invalidate_removes_entry(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("x")

    cache = MetadataCache()
    cache.get(str(target))
    cache.invalidate(str(target))
    assert cache.size == 0
    assert cache.get_if_cached(str(target)) is None


def test_invalidate_missing_path_is_noop() -> None:
    cache = MetadataCache()
    cache.invalidate("/nonexistent/path")
    assert cache.size == 0


# ── invalidate_directory ─────────────────────────────────────────────────


@pytest.mark.slow
def test_invalidate_directory_removes_only_descendants(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "a.txt").write_text("a")
    (sub / "b.txt").write_text("b")
    sibling = tmp_path / "sibling.txt"
    sibling.write_text("s")

    cache = MetadataCache()
    cache.get(str(sub / "a.txt"))
    cache.get(str(sub / "b.txt"))
    cache.get(str(sibling))
    assert cache.size == 3

    cache.invalidate_directory(str(sub))
    # sub/a.txt and sub/b.txt removed; sibling.txt remains
    assert cache.size == 1
    assert cache.get_if_cached(str(sibling)) is not None
    assert cache.get_if_cached(str(sub / "a.txt")) is None


@pytest.mark.slow
def test_invalidate_directory_does_not_match_prefix_neighbours(tmp_path: Path) -> None:
    """invalidate_directory('/foo') must NOT delete '/foobar/baz'."""
    foo = tmp_path / "foo"
    foo.mkdir()
    foobar = tmp_path / "foobar"
    foobar.mkdir()
    inside_foo = foo / "x.txt"
    inside_foo.write_text("x")
    inside_foobar = foobar / "y.txt"
    inside_foobar.write_text("y")

    cache = MetadataCache()
    cache.get(str(inside_foo))
    cache.get(str(inside_foobar))

    cache.invalidate_directory(str(foo))
    assert cache.get_if_cached(str(inside_foobar)) is not None, (
        "files under '/foobar' must not be invalidated when invalidating '/foo'"
    )


# ── preload ──────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_preload_caches_all_paths(tmp_path: Path) -> None:
    paths = []
    for n in ("a.txt", "b.txt", "c.txt"):
        p = tmp_path / n
        p.write_text("x")
        paths.append(str(p))

    cache = MetadataCache()
    cache.preload(paths)
    assert cache.size == 3
    for p in paths:
        assert cache.get_if_cached(p) is not None


@pytest.mark.slow
def test_preload_skips_already_cached(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("x")

    cache = MetadataCache()
    cache.get(str(target))

    with mock.patch("utils.metadata_cache.os.lstat") as fake_lstat:
        cache.preload([str(target)])
        fake_lstat.assert_not_called()


# ── error handling ───────────────────────────────────────────────────────


def test_get_on_missing_file_caches_none() -> None:
    cache = MetadataCache()
    result = cache.get("/definitely/does/not/exist/asdf12345")
    assert result is None
    # The None entry should now be cached so we don't keep stat'ing.
    assert cache.size == 1


def test_subsequent_get_on_failed_path_does_not_retry_stat() -> None:
    cache = MetadataCache()
    cache.get("/nope/asdfqwer")

    with mock.patch("utils.metadata_cache.os.lstat") as fake_lstat:
        cache.get("/nope/asdfqwer")
        fake_lstat.assert_not_called()


# ── clear ────────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_clear_empties_cache(tmp_path: Path) -> None:
    target = tmp_path / "x.txt"
    target.write_text("x")

    cache = MetadataCache()
    cache.get(str(target))
    cache.clear()
    assert cache.size == 0


# ── symlink metadata ─────────────────────────────────────────────────────


@pytest.mark.slow
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX symlink semantics")
def test_lstat_used_for_symlink_so_target_metadata_is_not_followed(tmp_path: Path) -> None:
    real = tmp_path / "real.txt"
    real.write_text("hello world")
    link = tmp_path / "link.txt"
    os.symlink(real, link)

    cache = MetadataCache()
    meta = cache.get(str(link))
    assert meta is not None
    assert meta.is_symlink is True
    assert meta.symlink_target == str(real)
