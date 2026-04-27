"""Additional SymlinkGraph tests covering cases not in test_symlink_graph.py."""
import pytest

from explorer.symlink_graph import SymlinkGraph


# ── multi-edge cases ─────────────────────────────────────────────────────


def test_one_source_multiple_targets() -> None:
    """A folder of shortcuts can point at many different files."""
    g = SymlinkGraph()
    g.add_edge("/source", "/t1")
    g.add_edge("/source", "/t2")
    g.add_edge("/source", "/t3")
    assert set(g.get_targets("/source")) == {"/t1", "/t2", "/t3"}


def test_one_target_multiple_sources() -> None:
    """Many shortcuts can point to the same file."""
    g = SymlinkGraph()
    g.add_edge("/s1", "/target")
    g.add_edge("/s2", "/target")
    g.add_edge("/s3", "/target")
    assert set(g.get_sources("/target")) == {"/s1", "/s2", "/s3"}


def test_get_targets_for_unknown_source_returns_empty_list() -> None:
    g = SymlinkGraph()
    assert g.get_targets("/nope") == []


def test_get_sources_for_unknown_target_returns_empty_list() -> None:
    g = SymlinkGraph()
    assert g.get_sources("/nope") == []


# ── cycle detection ──────────────────────────────────────────────────────


def test_acyclic_graph_returns_no_cycles() -> None:
    g = SymlinkGraph()
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    g.add_edge("a", "c")
    assert g.detect_cycles() == []


def test_get_cycle_nodes_returns_all_cycle_members() -> None:
    g = SymlinkGraph()
    g.add_edge("a", "b")
    g.add_edge("b", "a")
    g.add_edge("c", "d")  # acyclic chain
    nodes = g.get_cycle_nodes()
    assert nodes == {"a", "b"}


def test_get_cycle_nodes_empty_when_no_cycles() -> None:
    g = SymlinkGraph()
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    assert g.get_cycle_nodes() == set()


# ── connected component ─────────────────────────────────────────────────


def test_connected_component_in_disconnected_graph() -> None:
    g = SymlinkGraph()
    g.add_edge("a", "b")
    g.add_edge("c", "d")
    assert g.get_connected_component("a") == {"a", "b"}
    assert g.get_connected_component("c") == {"c", "d"}


def test_connected_component_includes_starting_node() -> None:
    g = SymlinkGraph()
    g.add_edge("solo", "other")
    component = g.get_connected_component("solo")
    assert "solo" in component


def test_connected_component_handles_self_loop() -> None:
    g = SymlinkGraph()
    g.add_edge("loop", "loop")
    assert g.get_connected_component("loop") == {"loop"}


# ── remove_edge cleanup ──────────────────────────────────────────────────


def test_remove_edge_clears_empty_adjacency_entries() -> None:
    """When the last outgoing edge is removed, the source key should be gone."""
    g = SymlinkGraph()
    g.add_edge("a", "b")
    g.remove_edge("a", "b")
    assert "a" not in g.adjacency
    assert "b" not in g.reverse_adjacency


def test_remove_unknown_edge_is_silent() -> None:
    g = SymlinkGraph()
    g.remove_edge("a", "b")  # never added
    assert g.has_edge("a", "b") is False


def test_remove_edge_clears_broken_marker() -> None:
    g = SymlinkGraph()
    g.add_edge("a", "b")
    g.mark_edge_broken("a", "b", True)
    g.remove_edge("a", "b")
    assert g.is_edge_broken("a", "b") is False


# ── broken-edge marking on non-existent edges ────────────────────────────


def test_mark_edge_broken_on_unknown_edge_is_silent() -> None:
    g = SymlinkGraph()
    g.mark_edge_broken("a", "b", True)
    assert g.is_edge_broken("a", "b") is False
    # And no nodes should have been added implicitly
    assert g.get_all_nodes() == set()
