"""Unit tests for NavigationStack (browser-style two-stack history)."""
import pytest

from utils.navigation_stack import NavigationStack, MAX_DEPTH


# ── construction ─────────────────────────────────────────────────────────


def test_empty_stack_initial_state() -> None:
    nav = NavigationStack()
    assert nav.current_path == ""
    assert nav.back_stack == []
    assert nav.forward_stack == []
    assert nav.can_go_back() is False
    assert nav.can_go_forward() is False


# ── navigate_to ──────────────────────────────────────────────────────────


def test_navigate_to_first_path_sets_current_only() -> None:
    nav = NavigationStack()
    nav.navigate_to("/home")
    assert nav.current_path == "/home"
    # No prior current_path, so back stack is still empty
    assert nav.back_stack == []
    assert nav.can_go_back() is False


def test_navigate_to_grows_back_stack() -> None:
    nav = NavigationStack()
    nav.navigate_to("/home")
    nav.navigate_to("/home/docs")
    nav.navigate_to("/home/docs/work")
    assert nav.current_path == "/home/docs/work"
    assert nav.back_stack == ["/home", "/home/docs"]
    assert nav.can_go_back() is True


def test_navigate_to_clears_forward_stack() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    nav.navigate_to("/b")
    nav.go_back()  # forward stack now has /b
    assert nav.forward_stack == ["/b"]

    nav.navigate_to("/c")
    assert nav.forward_stack == [], "forward history must be invalidated on branch"
    assert nav.can_go_forward() is False


# ── go_back ──────────────────────────────────────────────────────────────


def test_go_back_returns_previous_path() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    nav.navigate_to("/b")

    result = nav.go_back()
    assert result == "/a"
    assert nav.current_path == "/a"
    assert nav.forward_stack == ["/b"]


def test_go_back_on_empty_returns_none() -> None:
    nav = NavigationStack()
    assert nav.go_back() is None
    assert nav.current_path == ""


def test_go_back_then_navigate_clears_forward() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    nav.navigate_to("/b")
    nav.navigate_to("/c")
    nav.go_back()  # back at /b, forward = [/c]
    assert nav.forward_stack == ["/c"]

    nav.navigate_to("/x")  # branches off — forward must clear
    assert nav.forward_stack == []
    assert nav.back_stack[-1] == "/b"


# ── go_forward ───────────────────────────────────────────────────────────


def test_go_forward_returns_path_when_available() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    nav.navigate_to("/b")
    nav.go_back()  # /a current, forward = [/b]

    result = nav.go_forward()
    assert result == "/b"
    assert nav.current_path == "/b"
    assert nav.back_stack[-1] == "/a"


def test_go_forward_on_empty_returns_none() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    assert nav.go_forward() is None
    assert nav.current_path == "/a"


# ── can_go_back / can_go_forward ─────────────────────────────────────────


def test_can_go_back_reflects_back_stack() -> None:
    nav = NavigationStack()
    assert nav.can_go_back() is False
    nav.navigate_to("/a")
    assert nav.can_go_back() is False  # nothing to go back to yet
    nav.navigate_to("/b")
    assert nav.can_go_back() is True


def test_can_go_forward_reflects_forward_stack() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    nav.navigate_to("/b")
    assert nav.can_go_forward() is False
    nav.go_back()
    assert nav.can_go_forward() is True


# ── inspection ───────────────────────────────────────────────────────────


def test_get_back_history_returns_copy() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    nav.navigate_to("/b")

    history = nav.get_back_history()
    history.append("/should_not_persist")
    assert nav.back_stack == ["/a"], "external mutation must not leak into the stack"


def test_get_forward_history_returns_copy() -> None:
    nav = NavigationStack()
    nav.navigate_to("/a")
    nav.navigate_to("/b")
    nav.go_back()

    history = nav.get_forward_history()
    history.clear()
    assert nav.forward_stack == ["/b"], "external mutation must not leak into the stack"


# ── depth cap ────────────────────────────────────────────────────────────


def test_back_stack_caps_at_max_depth() -> None:
    nav = NavigationStack()
    for i in range(MAX_DEPTH + 25):
        nav.navigate_to(f"/dir_{i}")
    assert len(nav.back_stack) == MAX_DEPTH
    # Oldest entries dropped first → /dir_0 should no longer be present
    assert "/dir_0" not in nav.back_stack
