"""Unit tests for CameraAnimationStack and CameraAnimation interpolation."""
import math

import pytest

from utils.camera_animation_stack import (
    CameraAnimation,
    CameraAnimationStack,
    smoothstep,
)


def _linear_anim(
    start=(0.0, 0.0, 0.0),
    end=(10.0, 0.0, 0.0),
    duration=1.0,
    yaw_start=0.0,
    yaw_end=0.0,
    pitch_start=0.0,
    pitch_end=0.0,
) -> CameraAnimation:
    """An animation with linear easing so test math is straightforward."""
    return CameraAnimation(
        start_position=start,
        end_position=end,
        start_yaw=yaw_start,
        start_pitch=pitch_start,
        end_yaw=yaw_end,
        end_pitch=pitch_end,
        duration=duration,
        easing=lambda t: t,  # linear
    )


# ── smoothstep helper ────────────────────────────────────────────────────


def test_smoothstep_endpoints() -> None:
    assert smoothstep(0.0) == 0.0
    assert smoothstep(1.0) == 1.0


def test_smoothstep_midpoint_is_half() -> None:
    """3*0.5^2 - 2*0.5^3 = 0.5"""
    assert math.isclose(smoothstep(0.5), 0.5)


# ── push / pop / peek ────────────────────────────────────────────────────


def test_push_and_peek() -> None:
    stack = CameraAnimationStack()
    anim = _linear_anim()
    stack.push(anim)
    assert stack.peek() is anim
    assert stack.is_animating() is True


def test_pop_returns_top_and_empties_stack() -> None:
    stack = CameraAnimationStack()
    a = _linear_anim()
    b = _linear_anim()
    stack.push(a)
    stack.push(b)
    assert stack.pop() is b
    assert stack.pop() is a
    assert stack.pop() is None
    assert stack.is_animating() is False


def test_peek_on_empty_returns_none() -> None:
    stack = CameraAnimationStack()
    assert stack.peek() is None
    assert stack.is_animating() is False


def test_clear_removes_all() -> None:
    stack = CameraAnimationStack()
    stack.push(_linear_anim())
    stack.push(_linear_anim())
    stack.clear()
    assert stack.is_animating() is False
    assert stack.peek() is None


# ── update interpolation ─────────────────────────────────────────────────


def test_update_at_t0_returns_start_state() -> None:
    stack = CameraAnimationStack()
    stack.push(_linear_anim(start=(0, 0, 0), end=(10, 5, -2)))
    pos, yaw, pitch = stack.update(0.0)
    assert pos == (0.0, 0.0, 0.0)
    assert yaw == 0.0
    assert pitch == 0.0


def test_update_at_half_duration_is_midpoint_with_linear_easing() -> None:
    stack = CameraAnimationStack()
    stack.push(_linear_anim(start=(0, 0, 0), end=(10, 4, -2), duration=1.0))
    pos, _, _ = stack.update(0.5)
    assert math.isclose(pos[0], 5.0)
    assert math.isclose(pos[1], 2.0)
    assert math.isclose(pos[2], -1.0)


def test_update_at_full_duration_returns_end_state_and_pops() -> None:
    stack = CameraAnimationStack()
    stack.push(_linear_anim(start=(0, 0, 0), end=(10, 0, 0), duration=1.0))
    pos, _, _ = stack.update(1.0)
    assert math.isclose(pos[0], 10.0)
    assert stack.is_animating() is False, "completed animation must be popped"


def test_update_clamps_at_full_duration_when_overshooting() -> None:
    stack = CameraAnimationStack()
    stack.push(_linear_anim(start=(0, 0, 0), end=(10, 0, 0), duration=1.0))
    pos, _, _ = stack.update(5.0)  # massively overshoot
    assert math.isclose(pos[0], 10.0)
    assert stack.is_animating() is False


def test_update_on_empty_returns_none() -> None:
    stack = CameraAnimationStack()
    assert stack.update(0.1) is None


# ── yaw shortest-path interpolation ──────────────────────────────────────


def test_yaw_takes_shortest_path_across_360() -> None:
    """350° → 10° should advance forward through 360° (delta = +20°), not
    backward through 180° (delta = -340°)."""
    stack = CameraAnimationStack()
    stack.push(_linear_anim(yaw_start=350.0, yaw_end=10.0, duration=1.0))
    _, yaw_mid, _ = stack.update(0.5)
    # Halfway with linear easing across +20° delta starting at 350° = 360°.
    assert math.isclose(yaw_mid, 360.0)


# ── multi-animation sequencing ───────────────────────────────────────────


def test_multiple_animations_sequence_top_first() -> None:
    """The top of the stack runs to completion, then the next plays."""
    stack = CameraAnimationStack()
    first = _linear_anim(start=(0, 0, 0), end=(1, 0, 0), duration=1.0)
    second = _linear_anim(start=(0, 0, 0), end=(2, 0, 0), duration=1.0)
    stack.push(first)
    stack.push(second)  # 'second' is now on top → runs first

    pos, _, _ = stack.update(0.5)
    assert math.isclose(pos[0], 1.0), "should be interpolating 'second' first"

    stack.update(0.5)  # completes 'second' and pops
    assert stack.peek() is first


def test_pushing_mid_flight_replaces_active_animation() -> None:
    """A push during another animation makes the new one active immediately."""
    stack = CameraAnimationStack()
    in_flight = _linear_anim(start=(0, 0, 0), end=(10, 0, 0), duration=1.0)
    stack.push(in_flight)
    stack.update(0.3)
    assert in_flight.elapsed > 0

    interrupting = _linear_anim(start=(0, 0, 0), end=(99, 0, 0), duration=1.0)
    stack.push(interrupting)

    # New animation starts at zero elapsed; updating advances *it*, not the
    # one that was previously running.
    pos, _, _ = stack.update(0.5)
    assert math.isclose(pos[0], 49.5)
    assert interrupting.elapsed == pytest.approx(0.5)
