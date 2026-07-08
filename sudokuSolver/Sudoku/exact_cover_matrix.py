from typing import List, Tuple
from .sudoku_utils import box_size


# ---------------------------------------------------------------------------
# Dimensions (for an n x n Sudoku)
# ---------------------------------------------------------------------------
# Rows : n**3  = n grid-rows x n grid-cols x n digits
#               each row represents one possible move: "place digit v at [i][j]"
#
# Cols : n*n*4 = n*n cell + n*n row + n*n col + n*n box
#               each column represents one constraint that must be satisfied
#               exactly once
#
# Column layout (for grid size n):
#   [0            .. n*n-1      ]  cell constraints  - cell (i,j) has exactly one digit
#   [n*n          .. 2*n*n-1    ]  row constraints   - digit v appears exactly once in grid-row i
#   [2*n*n        .. 3*n*n-1    ]  col constraints   - digit v appears exactly once in grid-col j
#   [3*n*n        .. 4*n*n-1    ]  box constraints   - digit v appears exactly once in box b
# ---------------------------------------------------------------------------

NUM_ROWS = 729   # 9 * 9 * 9  (n=9 default, kept for backwards compatibility)
NUM_COLS = 324   # 81 * 4     (n=9 default, kept for backwards compatibility)


# ---------------------------------------------------------------------------
# Core index function
# ---------------------------------------------------------------------------

def get_row_index(i: int, j: int, v: int, n: int = 9) -> int:
    """
    Returns the exact-cover matrix row index for placing digit v at grid[i][j].

    Parameters
    ----------
    i : grid row    (0..n-1)
    j : grid col    (0..n-1)
    v : digit value (0..n-1, i.e. digit-1)
    n : grid size

    Think of it as a 3-digit base-n number:  i*n*n + j*n + v
    Outermost cycle is i, then j, innermost is v.
    """
    return i * n * n + j * n + v


# ---------------------------------------------------------------------------
# Matrix builder
# ---------------------------------------------------------------------------

def build_exact_cover_matrix(n: int = 9) -> List[List[int]]:
    """
    Builds and returns the (n**3) x (n*n*4) exact-cover matrix for an n x n
    Sudoku puzzle (all cells empty - pre-filled cells are handled separately).

    Each data row has exactly 4 ones, one per constraint group.
    Each column has exactly n ones, one per digit (or one per candidate cell).
    """
    bs = box_size(n)
    num_rows = n * n * n
    num_cols = n * n * 4
    matrix = [[0] * num_cols for _ in range(num_rows)]

    # -----------------------------------------------------------------------
    # 1. Cell constraints  (cols 0 .. n*n-1)
    #    One column per cell (i, j).
    #    All n digits placed at the same cell satisfy the same column.
    #    Loop order: i -> j -> v  (v is innermost so all n share the same col)
    # -----------------------------------------------------------------------
    col = 0
    for i in range(n):
        for j in range(n):
            for v in range(n):
                matrix[get_row_index(i, j, v, n)][col] = 1
            col += 1        # advance only after all n digits are marked

    # -----------------------------------------------------------------------
    # 2. Row constraints  (cols n*n .. 2*n*n-1)
    #    One column per (i, v) pair.
    #    All n grid-columns place the same digit v in the same grid-row i,
    #    so they all satisfy the same constraint column.
    #    Loop order: i -> v -> j  (j is innermost)
    # -----------------------------------------------------------------------
    col = n * n
    for i in range(n):
        for v in range(n):
            for j in range(n):
                matrix[get_row_index(i, j, v, n)][col] = 1
            col += 1

    # -----------------------------------------------------------------------
    # 3. Column constraints  (cols 2*n*n .. 3*n*n-1)
    #    One column per (j, v) pair.
    #    All n grid-rows place the same digit v in the same grid-col j.
    #    Loop order: j -> v -> i  (i is innermost)
    # -----------------------------------------------------------------------
    col = 2 * n * n
    for j in range(n):
        for v in range(n):
            for i in range(n):
                matrix[get_row_index(i, j, v, n)][col] = 1
            col += 1

    # -----------------------------------------------------------------------
    # 4. Box constraints  (cols 3*n*n .. 4*n*n-1)
    #    One column per (box, v) pair.  There are n boxes, n digits -> n*n cols.
    #    All n cells inside the same box, with the same digit v, satisfy the
    #    same constraint column.
    #    Loop order: box_row -> box_col -> v -> i -> j  (i,j innermost)
    # -----------------------------------------------------------------------
    col = 3 * n * n
    for box_row in range(0, n, bs):
        for box_col in range(0, n, bs):
            for v in range(n):
                for i in range(box_row, box_row + bs):
                    for j in range(box_col, box_col + bs):
                        matrix[get_row_index(i, j, v, n)][col] = 1
                col += 1

    return matrix


# ---------------------------------------------------------------------------
# Pre-filled cell handling
# ---------------------------------------------------------------------------

def get_forced_rows(board: List[List[int]], n: int = None) -> List[int]:
    """
    Given a partially-filled n x n board (0 = empty), returns the list of
    exact-cover matrix row indices that are forced by the pre-filled cells.

    These rows will be used by DLX to pre-cover their 4 constraint columns
    before the search begins, effectively locking in the givens.

    Parameters
    ----------
    board : n x n list of ints, 0 = empty, 1-n = given digit
    n : grid size (defaults to len(board))
    """
    n = n or len(board)
    forced = []
    for i in range(n):
        for j in range(n):
            if board[i][j] != 0:
                v = board[i][j] - 1     # convert to 0-indexed
                forced.append(get_row_index(i, j, v, n))
    return forced


def decode_row_index(row_idx: int, n: int = 9) -> Tuple[int, int, int]:
    """
    Inverse of get_row_index.
    Returns (i, j, v) where v is 0-indexed (digit = v + 1).
    Useful when DLX returns a solution as a list of row indices.
    """
    i = row_idx // (n * n)
    j = (row_idx % (n * n)) // n
    v = row_idx % n
    return i, j, v


# ---------------------------------------------------------------------------
# Verification  (run once to confirm the matrix is correct)
# ---------------------------------------------------------------------------

def verify_matrix(matrix: List[List[int]], n: int = 9) -> None:
    """
    Asserts structural correctness of the exact-cover matrix:
      - Every data row  has exactly 4 ones  (one per constraint group)
      - Every column    has exactly n ones  (one per candidate in that constraint)

    Raises AssertionError with a descriptive message if anything is wrong.
    Prints a confirmation message on success.
    """
    num_rows = n * n * n
    num_cols = n * n * 4

    assert len(matrix) == num_rows, \
        f"Expected {num_rows} rows, got {len(matrix)}"
    assert len(matrix[0]) == num_cols, \
        f"Expected {num_cols} cols, got {len(matrix[0])}"

    for r in range(num_rows):
        ones = sum(matrix[r])
        assert ones == 4, \
            f"Row {r} (i={r//(n*n)}, j={(r%(n*n))//n}, v={r%n}) has {ones} ones, expected 4"

    for c in range(num_cols):
        ones = sum(matrix[r][c] for r in range(num_rows))
        assert ones == n, \
            f"Col {c} has {ones} ones, expected {n}"

    print(f"Matrix verified: {num_rows} rows x {num_cols} cols - "
          f"every row has 4 ones, every col has {n} ones.")


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mat = build_exact_cover_matrix(9)
    verify_matrix(mat, 9)

    # spot-check: placing digit 5 (v=4) at cell [0][0] should mark cols:
    #   cell  (0,0)      -> col 0
    #   row   (i=0, v=4) -> col 81 + 0*9 + 4 = 85
    #   col   (j=0, v=4) -> col 162 + 0*9 + 4 = 166
    #   box   (b=0, v=4) -> col 243 + 0*9 + 4 = 247
    row = get_row_index(0, 0, 4, 9)
    expected_cols = {0, 85, 166, 247}
    actual_cols   = {c for c, val in enumerate(mat[row]) if val == 1}
    assert actual_cols == expected_cols, \
        f"Spot-check failed: expected {expected_cols}, got {actual_cols}"
    print(f"Spot-check passed: row {row} marks cols {sorted(actual_cols)}")

    # test decode round-trip
    for test_row in [0, 80, 364, 728]:
        i, j, v = decode_row_index(test_row, 9)
        assert get_row_index(i, j, v, 9) == test_row, \
            f"Round-trip failed for row {test_row}"
    print("Round-trip decode test passed.")
