import math
import time


class ProgressRecorder:
    """Records (elapsed_ms, value) snapshots for a running solver.

    Wall-clock throttling alone doesn't work here: an easy 9x9 puzzle can
    solve in a couple of milliseconds with thousands of raw placement/
    backtrack events, so a fixed time interval would collapse the whole
    series to 2-3 points. Instead this samples every event up to
    `max_points`, then doubles its stride and halves the existing series
    whenever it overflows — so a fast, low-event solve keeps full
    resolution, and a slow, event-dense one still produces a bounded,
    readable series instead of hundreds of thousands of points.
    """

    def __init__(self, max_points=300):
        self.max_points = max_points
        self.points = []
        self._start_time = time.time()
        self._stride = 1
        self._count = 0

    def record(self, value, force=False):
        """Record a snapshot. `value` may be a plain number, or a zero-arg
        callable — the callable form defers computing the value until we
        know this event will actually be sampled, which matters when
        computing it isn't free (e.g. recounting a board's filled cells)."""
        self._count += 1
        if not force and self._count % self._stride != 0:
            return
        elapsed_ms = (time.time() - self._start_time) * 1000
        resolved_value = value() if callable(value) else value
        self.points.append((round(elapsed_ms, 2), resolved_value))
        if len(self.points) > self.max_points * 2:
            self.points = self.points[::2]
            self._stride *= 2


def box_size(n: int) -> int:
    r = math.isqrt(n)
    if r * r != n:
        raise ValueError(f"Grid size {n} is not a perfect square")
    return r


def get_peers(row, col, n, bs=None):
    """Cells sharing a row, column, or box with (row, col) on an n x n board."""
    bs = bs or box_size(n)
    peers = set()
    peers.update((row, c) for c in range(n) if c != col)
    peers.update((r, col) for r in range(n) if r != row)
    br, bc = bs * (row // bs), bs * (col // bs)
    peers.update((r, c) for r in range(br, br + bs) for c in range(bc, bc + bs) if (r, c) != (row, col))
    return peers


def empty_board(n):
    return [[0] * n for _ in range(n)]
