"""
FileExplorer3D - navigation_stack.py
Browser-style back/forward navigation using two stacks (Unit 7 — Stacks).

Big-O summary
─────────────
navigate_to : O(1) amortized  — list.append + list.clear
go_back     : O(1) amortized  — list.pop + list.append
go_forward  : O(1) amortized  — list.pop + list.append
can_go_*    : O(1)            — len() on a list
get_*_history: O(n)           — copies the stack for safe external access
Space       : O(n)            — where n = number of navigation actions

Why two stacks instead of a list with an index pointer
───────────────────────────────────────────────────────
A stack enforces LIFO discipline naturally. When the user navigates to a new
folder after going back, the forward history must be invalidated — that maps
directly to clearing the forward stack. A list-with-index approach would need
explicit truncation logic and is more error-prone.
"""

MAX_DEPTH = 100  # cap to prevent unbounded memory growth in long sessions


class NavigationStack:
    """
    Manages browser-style back/forward navigation history with two stacks.

    Attributes:
        back_stack    (list[str]): previously visited paths (LIFO)
        forward_stack (list[str]): paths available after going back (LIFO)
        current_path  (str):       the path currently displayed
    """

    def __init__(self):
        self.back_stack:    list[str] = []
        self.forward_stack: list[str] = []
        self.current_path:  str       = ""

    # ─── core navigation ────────────────────────────────────────────────────

    def navigate_to(self, path: str) -> None:
        """Push current_path onto back_stack, clear forward_stack, set current_path.

        Complexity: O(1) amortized.
        The forward stack is cleared because branching into a new location
        invalidates any previously rewound history — identical to browser behaviour.
        """
        if self.current_path:
            self.back_stack.append(self.current_path)
            if len(self.back_stack) > MAX_DEPTH:
                self.back_stack.pop(0)   # drop oldest entry to stay within cap
        self.forward_stack.clear()
        self.current_path = path

    def go_back(self) -> str | None:
        """Pop from back_stack, push current_path to forward_stack, update current_path.

        Complexity: O(1) amortized.
        Returns the new path, or None if the back stack is empty.
        """
        if not self.back_stack:
            return None
        self.forward_stack.append(self.current_path)
        self.current_path = self.back_stack.pop()
        return self.current_path

    def go_forward(self) -> str | None:
        """Pop from forward_stack, push current_path to back_stack, update current_path.

        Complexity: O(1) amortized.
        Returns the new path, or None if the forward stack is empty.
        """
        if not self.forward_stack:
            return None
        self.back_stack.append(self.current_path)
        self.current_path = self.forward_stack.pop()
        return self.current_path

    # ─── predicates ─────────────────────────────────────────────────────────

    def can_go_back(self) -> bool:
        """O(1) — len() on a Python list."""
        return len(self.back_stack) > 0

    def can_go_forward(self) -> bool:
        """O(1) — len() on a Python list."""
        return len(self.forward_stack) > 0

    # ─── inspection ─────────────────────────────────────────────────────────

    def get_back_history(self) -> list[str]:
        """Return a copy of the back stack contents (oldest → most recent).

        Complexity: O(n).
        Returns a copy so callers cannot mutate internal state.
        """
        return list(self.back_stack)

    def get_forward_history(self) -> list[str]:
        """Return a copy of the forward stack contents (most recent → oldest).

        Complexity: O(n).
        Returns a copy so callers cannot mutate internal state.
        """
        return list(self.forward_stack)
