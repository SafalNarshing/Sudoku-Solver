from typing import List, Tuple


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
# Rows : 729  = 9 grid-rows × 9 grid-cols × 9 digits
#               each row represents one possible move: "place digit v at [i][j]"
#
# Cols : 324  = 81 cell + 81 row + 81 col + 81 box
#               each column represents one constraint that must be satisfied
#               exactly once
#
# Column layout:
#   [0   .. 80 ]  cell constraints  – cell (i,j) has exactly one digit
#   [81  .. 161]  row constraints   – digit v appears exactly once in grid-row i
#   [162 .. 242]  col constraints   – digit v appears exactly once in grid-col j
#   [243 .. 323]  box constraints   – digit v appears exactly once in 3×3 box b
# ---------------------------------------------------------------------------

NUM_ROWS = 729   # 9 * 9 * 9
NUM_COLS = 324   # 81 * 4


# ---------------------------------------------------------------------------
# Core index function
# ---------------------------------------------------------------------------

def get_row_index(i: int, j: int, v: int) -> int:
    """
    Returns the exact-cover matrix row index for placing digit v at grid[i][j].

    Parameters
    ----------
    i : grid row    (0-8)
    j : grid col    (0-8)
    v : digit value (0-8, i.e. digit-1)

    Think of it as a 3-digit base-9 number:  i*81 + j*9 + v
    Outermost cycle is i, then j, innermost is v.
    """
    return i * 81 + j * 9 + v


# ---------------------------------------------------------------------------
# Matrix builder
# ---------------------------------------------------------------------------

def build_exact_cover_matrix() -> List[List[int]]:
    """
    Builds and returns the 729 × 324 exact-cover matrix for a standard 9×9
    Sudoku puzzle (all cells empty — pre-filled cells are handled separately).

    Each data row has exactly 4 ones, one per constraint group.
    Each column has exactly 9 ones, one per digit (or one per candidate cell).
    """
    matrix = [[0] * NUM_COLS for _ in range(NUM_ROWS)]

    # -----------------------------------------------------------------------
    # 1. Cell constraints  (cols 0 .. 80)
    #    One column per cell (i, j).
    #    All 9 digits placed at the same cell satisfy the same column.
    #    Loop order: i → j → v  (v is innermost so all 9 share the same col)
    # -----------------------------------------------------------------------
    col = 0
    for i in range(9):
        for j in range(9):
            for v in range(9):
                matrix[get_row_index(i, j, v)][col] = 1
            col += 1        # advance only after all 9 digits are marked

    # -----------------------------------------------------------------------
    # 2. Row constraints  (cols 81 .. 161)
    #    One column per (i, v) pair.
    #    All 9 grid-columns place the same digit v in the same grid-row i,
    #    so they all satisfy the same constraint column.
    #    Loop order: i → v → j  (j is innermost)
    # -----------------------------------------------------------------------
    col = 81
    for i in range(9):
        for v in range(9):
            for j in range(9):
                matrix[get_row_index(i, j, v)][col] = 1
            col += 1

    # -----------------------------------------------------------------------
    # 3. Column constraints  (cols 162 .. 242)
    #    One column per (j, v) pair.
    #    All 9 grid-rows place the same digit v in the same grid-col j.
    #    Loop order: j → v → i  (i is innermost)
    # -----------------------------------------------------------------------
    col = 162
    for j in range(9):
        for v in range(9):
            for i in range(9):
                matrix[get_row_index(i, j, v)][col] = 1
            col += 1

    # -----------------------------------------------------------------------
    # 4. Box constraints  (cols 243 .. 323)
    #    One column per (box, v) pair.  There are 9 boxes, 9 digits → 81 cols.
    #    All 9 cells inside the same box, with the same digit v, satisfy the
    #    same constraint column.
    #    Loop order: box_row → box_col → v → i → j  (i,j innermost)
    # -----------------------------------------------------------------------
    col = 243
    for box_row in range(0, 9, 3):          # 0, 3, 6
        for box_col in range(0, 9, 3):      # 0, 3, 6
            for v in range(9):
                for i in range(box_row, box_row + 3):
                    for j in range(box_col, box_col + 3):
                        matrix[get_row_index(i, j, v)][col] = 1
                col += 1

    return matrix


# ---------------------------------------------------------------------------
# Pre-filled cell handling
# ---------------------------------------------------------------------------

def get_forced_rows(board: List[List[int]]) -> List[int]:
    """
    Given a partially-filled 9×9 board (0 = empty), returns the list of
    exact-cover matrix row indices that are forced by the pre-filled cells.

    These rows will be used by DLX to pre-cover their 4 constraint columns
    before the search begins, effectively locking in the givens.

    Parameters
    ----------
    board : 9×9 list of ints, 0 = empty, 1-9 = given digit
    """
    forced = []
    for i in range(9):
        for j in range(9):
            if board[i][j] != 0:
                v = board[i][j] - 1     # convert to 0-indexed
                forced.append(get_row_index(i, j, v))
    return forced


def decode_row_index(row_idx: int) -> Tuple[int, int, int]:
    """
    Inverse of get_row_index.
    Returns (i, j, v) where v is 0-indexed (digit = v + 1).
    Useful when DLX returns a solution as a list of row indices.
    """
    i = row_idx // 81
    j = (row_idx % 81) // 9
    v = row_idx % 9
    return i, j, v


# ---------------------------------------------------------------------------
# Verification  (run once to confirm the matrix is correct)
# ---------------------------------------------------------------------------

def verify_matrix(matrix: List[List[int]]) -> None:
    """
    Asserts structural correctness of the exact-cover matrix:
      - Every data row  has exactly 4 ones  (one per constraint group)
      - Every column    has exactly 9 ones  (one per candidate in that constraint)

    Raises AssertionError with a descriptive message if anything is wrong.
    Prints a confirmation message on success.
    """
    assert len(matrix) == NUM_ROWS, \
        f"Expected {NUM_ROWS} rows, got {len(matrix)}"
    assert len(matrix[0]) == NUM_COLS, \
        f"Expected {NUM_COLS} cols, got {len(matrix[0])}"

    for r in range(NUM_ROWS):
        ones = sum(matrix[r])
        assert ones == 4, \
            f"Row {r} (i={r//81}, j={(r%81)//9}, v={r%9}) has {ones} ones, expected 4"

    for c in range(NUM_COLS):
        ones = sum(matrix[r][c] for r in range(NUM_ROWS))
        assert ones == 9, \
            f"Col {c} has {ones} ones, expected 9"

    print(f"Matrix verified: {NUM_ROWS} rows × {NUM_COLS} cols — "
          f"every row has 4 ones, every col has 9 ones.")


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mat = build_exact_cover_matrix()
    verify_matrix(mat)

    # spot-check: placing digit 5 (v=4) at cell [0][0] should mark cols:
    #   cell  (0,0)      → col 0
    #   row   (i=0, v=4) → col 81 + 0*9 + 4 = 85
    #   col   (j=0, v=4) → col 162 + 0*9 + 4 = 166
    #   box   (b=0, v=4) → col 243 + 0*9 + 4 = 247
    row = get_row_index(0, 0, 4)
    expected_cols = {0, 85, 166, 247}
    actual_cols   = {c for c, val in enumerate(mat[row]) if val == 1}
    assert actual_cols == expected_cols, \
        f"Spot-check failed: expected {expected_cols}, got {actual_cols}"
    print(f"Spot-check passed: row {row} marks cols {sorted(actual_cols)}")

    # test decode round-trip
    for test_row in [0, 80, 364, 728]:
        i, j, v = decode_row_index(test_row)
        assert get_row_index(i, j, v) == test_row, \
            f"Round-trip failed for row {test_row}"
    print("Round-trip decode test passed.")