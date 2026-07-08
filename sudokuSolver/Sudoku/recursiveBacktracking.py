import time
from .sudoku_utils import box_size, ProgressRecorder


def is_valid(board, row, col, num, n, bs=None):
    bs = bs or box_size(n)

    # Check row
    if num in [board[row][i] for i in range(n)]:
        return False

    # Check column
    if num in [board[i][col] for i in range(n)]:
        return False

    # Check box
    start_row, start_col = bs * (row // bs), bs * (col // bs)
    for i in range(start_row, start_row + bs):
        for j in range(start_col, start_col + bs):
            if board[i][j] == num:
                return False

    return True


def solve_backtracking(board, time_limit=5.0, n=None, progress=None):
    """Naive brute-force backtracking, bounded by time_limit seconds.

    This solver has no move-ordering heuristics, so on sparse or
    unsolvable boards it can explore an enormous search space. It's
    only used for benchmarking comparison, so it must bail out rather
    than run unbounded and hang the request.

    If `progress` is a list, it is populated with (elapsed_ms,
    cells_filled) snapshots recorded on every placement and backtrack —
    this is what makes the naive solver's search visibly "saw-tooth" up
    and down, unlike DLX/heuristic which mostly climb.
    """
    n = n or len(board)
    bs = box_size(n)
    start_time = time.time()
    filled_count = sum(1 for r in board for v in r if v != 0)
    recorder = ProgressRecorder() if progress is not None else None

    if recorder:
        recorder.record(filled_count, force=True)

    def _solve():
        nonlocal filled_count
        if time.time() - start_time > time_limit:
            return False
        for row in range(n):
            for col in range(n):
                if board[row][col] == 0:
                    for num in range(1, n + 1):
                        if is_valid(board, row, col, num, n, bs):
                            board[row][col] = num
                            filled_count += 1
                            if recorder:
                                recorder.record(filled_count)
                            if _solve():
                                return True
                            board[row][col] = 0
                            filled_count -= 1
                            if recorder:
                                recorder.record(filled_count)
                    return False
        return True

    result = _solve()
    if recorder:
        recorder.record(filled_count, force=True)
        progress.extend(recorder.points)
    return result
