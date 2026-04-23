"""
FileExplorer3D - symlink_graph.py
Directed graph for symlink/shortcut relationships.

The graph is stored as adjacency lists:
- adjacency[source] -> [target1, target2, ...]
- reverse_adjacency[target] -> [source1, source2, ...]

Big-O:
- add_edge: O(1) amortized (dict access + append)
- get_targets / get_sources: O(1) lookup + O(k) output size
- detect_cycles: O(V + E)
- get_connected_component: O(V + E)
- storage: O(V + E)
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple


class SymlinkGraph:
    """Directed adjacency-list graph for discovered symlink/shortcut edges."""

    def __init__(self) -> None:
        self.adjacency: Dict[str, List[str]] = {}
        self.reverse_adjacency: Dict[str, List[str]] = {}
        self._edge_set: Set[Tuple[str, str]] = set()
        self._broken_edges: Set[Tuple[str, str]] = set()

    def add_edge(self, source: str, target: str) -> None:
        """Add a directed edge source -> target."""
        edge = (source, target)
        if edge in self._edge_set:
            return

        self._edge_set.add(edge)
        self.adjacency.setdefault(source, []).append(target)
        self.reverse_adjacency.setdefault(target, []).append(source)

    def remove_edge(self, source: str, target: str) -> None:
        """Remove a directed edge source -> target if it exists."""
        edge = (source, target)
        if edge not in self._edge_set:
            return

        self._edge_set.remove(edge)
        self._broken_edges.discard(edge)

        if source in self.adjacency:
            targets = self.adjacency[source]
            if target in targets:
                targets.remove(target)
            if not targets:
                del self.adjacency[source]

        if target in self.reverse_adjacency:
            sources = self.reverse_adjacency[target]
            if source in sources:
                sources.remove(source)
            if not sources:
                del self.reverse_adjacency[target]

    def get_targets(self, source: str) -> List[str]:
        """Return all targets for a source path."""
        return list(self.adjacency.get(source, []))

    def get_sources(self, target: str) -> List[str]:
        """Return all source paths that point to target."""
        return list(self.reverse_adjacency.get(target, []))

    def has_edge(self, source: str, target: str) -> bool:
        """True if source -> target exists."""
        return (source, target) in self._edge_set

    def get_all_nodes(self) -> Set[str]:
        """Return every path that appears as a source or target."""
        nodes = set(self.adjacency.keys())
        nodes.update(self.reverse_adjacency.keys())
        return nodes

    def get_all_edges(self) -> List[Tuple[str, str]]:
        """Return all directed edges as (source, target) tuples."""
        return list(self._edge_set)

    def mark_edge_broken(self, source: str, target: str, broken: bool = True) -> None:
        """Mark or unmark an existing edge as broken."""
        edge = (source, target)
        if edge not in self._edge_set:
            return
        if broken:
            self._broken_edges.add(edge)
        else:
            self._broken_edges.discard(edge)

    def is_edge_broken(self, source: str, target: str) -> bool:
        """Return True when source -> target is marked broken."""
        return (source, target) in self._broken_edges

    def detect_cycles(self) -> List[List[str]]:
        """Detect directed cycles using DFS color-state traversal."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {node: WHITE for node in self.get_all_nodes()}
        stack: List[str] = []
        active_pos: Dict[str, int] = {}
        cycles: List[List[str]] = []
        seen_cycles: Set[Tuple[str, ...]] = set()

        def canonical_cycle(cycle: List[str]) -> Tuple[str, ...]:
            if not cycle:
                return tuple()
            rotations = [tuple(cycle[i:] + cycle[:i]) for i in range(len(cycle))]
            return min(rotations)

        def dfs(node: str) -> None:
            color[node] = GRAY
            active_pos[node] = len(stack)
            stack.append(node)

            for nxt in self.adjacency.get(node, []):
                if color.get(nxt, WHITE) == WHITE:
                    dfs(nxt)
                elif color.get(nxt, WHITE) == GRAY and nxt in active_pos:
                    cycle = stack[active_pos[nxt]:]
                    key = canonical_cycle(cycle)
                    if key and key not in seen_cycles:
                        seen_cycles.add(key)
                        cycles.append(cycle[:])

            stack.pop()
            active_pos.pop(node, None)
            color[node] = BLACK

        for node in list(color.keys()):
            if color[node] == WHITE:
                dfs(node)

        return cycles

    def get_cycle_nodes(self) -> Set[str]:
        """Return the set of nodes that appear in at least one cycle."""
        nodes: Set[str] = set()
        for cycle in self.detect_cycles():
            nodes.update(cycle)
        return nodes

    def get_connected_component(self, path: str) -> Set[str]:
        """Return all nodes reachable from path in either direction."""
        if path not in self.get_all_nodes():
            return set()

        visited: Set[str] = set()
        queue: deque[str] = deque([path])

        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)

            neighbors = self.adjacency.get(node, []) + self.reverse_adjacency.get(node, [])
            for nxt in neighbors:
                if nxt not in visited:
                    queue.append(nxt)

        return visited
