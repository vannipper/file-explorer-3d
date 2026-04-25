import unittest

from explorer.symlink_graph import SymlinkGraph


class SymlinkGraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = SymlinkGraph()

    def test_add_and_has_edge(self):
        self.graph.add_edge("a", "b")
        self.assertTrue(self.graph.has_edge("a", "b"))
        self.assertEqual(self.graph.get_targets("a"), ["b"])
        self.assertEqual(self.graph.get_sources("b"), ["a"])

    def test_add_edge_is_deduplicated(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("a", "b")
        self.assertEqual(self.graph.get_targets("a"), ["b"])
        self.assertEqual(self.graph.get_sources("b"), ["a"])
        self.assertEqual(self.graph.get_all_edges(), [("a", "b")])

    def test_remove_edge(self):
        self.graph.add_edge("a", "b")
        self.graph.remove_edge("a", "b")
        self.assertFalse(self.graph.has_edge("a", "b"))
        self.assertEqual(self.graph.get_targets("a"), [])
        self.assertEqual(self.graph.get_sources("b"), [])

    def test_get_all_nodes_and_edges(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        self.assertEqual(self.graph.get_all_nodes(), {"a", "b", "c"})
        self.assertEqual(set(self.graph.get_all_edges()), {("a", "b"), ("b", "c")})

    def test_detect_cycles(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        self.graph.add_edge("c", "a")
        cycles = self.graph.detect_cycles()
        self.assertEqual(len(cycles), 1)
        self.assertEqual(set(cycles[0]), {"a", "b", "c"})

    def test_detect_self_cycle(self):
        self.graph.add_edge("self", "self")
        cycles = self.graph.detect_cycles()
        self.assertEqual(cycles, [["self"]])

    def test_detect_multiple_disjoint_cycles(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "a")
        self.graph.add_edge("x", "y")
        self.graph.add_edge("y", "z")
        self.graph.add_edge("z", "x")
        cycle_nodes = [set(cycle) for cycle in self.graph.detect_cycles()]
        self.assertIn({"a", "b"}, cycle_nodes)
        self.assertIn({"x", "y", "z"}, cycle_nodes)

    def test_connected_component_uses_both_directions(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        self.graph.add_edge("x", "y")
        self.assertEqual(self.graph.get_connected_component("b"), {"a", "b", "c"})
        self.assertEqual(self.graph.get_connected_component("x"), {"x", "y"})
        self.assertEqual(self.graph.get_connected_component("missing"), set())

    def test_broken_edge_marking(self):
        self.graph.add_edge("a", "b")
        self.graph.mark_edge_broken("a", "b", True)
        self.assertTrue(self.graph.is_edge_broken("a", "b"))
        self.graph.mark_edge_broken("a", "b", False)
        self.assertFalse(self.graph.is_edge_broken("a", "b"))


if __name__ == "__main__":
    unittest.main()
