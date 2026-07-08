import time


def is_valid(board, row, col, num):
    # Check row
    if num in [board[row][i] for i in range(9)]:
        return False

    # Check column
    if num in [board[i][col] for i in range(9)]:
        return False

    # Check 3x3 grid
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if board[i][j] == num:
                return False

    return True


def solve_backtracking(board, time_limit=5.0):
    """Naive brute-force backtracking, bounded by time_limit seconds.

    This solver has no move-ordering heuristics, so on sparse or
    unsolvable boards it can explore an enormous search space. It's
    only used for benchmarking comparison, so it must bail out rather
    than run unbounded and hang the request.
    """
    start_time = time.time()

    def _solve():
        if time.time() - start_time > time_limit:
            return False
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    for num in range(1, 10):
                        if is_valid(board, row, col, num):
                            board[row][col] = num
                            if _solve():
                                return True
                            board[row][col] = 0
                    return False
        return True

    return _solve()