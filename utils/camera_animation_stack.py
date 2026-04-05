"""
FileExplorer3D - camera_animation_stack.py
Stack-based camera animation system for smooth 3D viewport transitions.

Unit 7 — Stacks: camera animation tasks are pushed onto a stack and popped
when complete, allowing queued transitions to play in sequence.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


def smoothstep(t: float) -> float:
    """Smoothstep easing: 3t² - 2t³. O(1)."""
    return t * t * (3 - 2 * t)


@dataclass
class CameraAnimation:
    """
    Represents a single camera transition between two positions/orientations.

    Fields:
        start_position: camera (x, y, z) at animation start
        end_position:   camera (x, y, z) at animation end
        start_yaw:      horizontal look angle at start (degrees)
        start_pitch:    vertical look angle at start (degrees)
        end_yaw:        target horizontal look angle (degrees)
        end_pitch:      target vertical look angle (degrees)
        duration:       total animation length in seconds
        elapsed:        time elapsed so far in seconds
        easing:         function mapping [0,1] → [0,1] (default: smoothstep)
    """
    start_position: tuple[float, float, float]
    end_position:   tuple[float, float, float]
    start_yaw:      float
    start_pitch:    float
    end_yaw:        float
    end_pitch:      float
    duration:       float
    elapsed:        float = 0.0
    easing:         Callable[[float], float] = field(default=smoothstep)


class CameraAnimationStack:
    """
    Stack of pending camera animations. Animations are executed top-first;
    when the top animation completes it is popped and the next begins.

    Big-O:
        push()   O(1)
        pop()    O(1)
        peek()   O(1)
        update() O(1) — constant interpolation math per frame
        clear()  O(k) where k = queued animations (typically 1-2)
        Space:   O(k)
    """

    def __init__(self):
        self._stack: list[CameraAnimation] = []

    def push(self, animation: CameraAnimation) -> None:
        """Add a new animation to the top of the stack. O(1)."""
        self._stack.append(animation)

    def pop(self) -> Optional[CameraAnimation]:
        """Remove and return the top animation, or None if empty. O(1)."""
        return self._stack.pop() if self._stack else None

    def peek(self) -> Optional[CameraAnimation]:
        """Return the top animation without removing it, or None if empty. O(1)."""
        return self._stack[-1] if self._stack else None

    def is_animating(self) -> bool:
        """Return True if there is an active animation on the stack."""
        return bool(self._stack)

    def clear(self) -> None:
        """Cancel all pending animations."""
        self._stack.clear()

    def update(self, delta_time: float) -> Optional[tuple]:
        """
        Advance the top animation by delta_time seconds and return the
        interpolated camera state as (position, yaw, pitch), where
        position is (x, y, z). Returns None if the stack is empty.

        When an animation completes it is popped; the next animation (if any)
        begins on the following update() call. O(1).
        """
        if not self._stack:
            return None

        anim = self._stack[-1]
        anim.elapsed += delta_time
        t = min(anim.elapsed / anim.duration, 1.0)
        s = anim.easing(t)

        # Interpolate position
        sx, sy, sz = anim.start_position
        ex, ey, ez = anim.end_position
        pos = (
            sx + (ex - sx) * s,
            sy + (ey - sy) * s,
            sz + (ez - sz) * s,
        )

        # Interpolate yaw with shortest-path wrap-around
        # (e.g. 350° → 10° goes through 360°, not backwards through 180°)
        dyaw = ((anim.end_yaw - anim.start_yaw) + 180) % 360 - 180
        yaw = anim.start_yaw + dyaw * s

        # Interpolate pitch
        pitch = anim.start_pitch + (anim.end_pitch - anim.start_pitch) * s

        if t >= 1.0:
            self._stack.pop()

        return pos, yaw, pitch
