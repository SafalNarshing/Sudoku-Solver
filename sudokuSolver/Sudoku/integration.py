from .exact_cover_matrix import build_exact_cover_matrix, get_forced_rows, decode_row_index
from .dlx_node import build_dlx_grid
from .dlx_solver import DLXSolver
from .sudoku_utils import empty_board


def solve_sudoku(board, n=None, progress=None):
    n = n or len(board)

    # Step 1: Build exact cover matrix
    matrix = build_exact_cover_matrix(n)
    forced_rows = get_forced_rows(board, n)

    # Step 2: Build Dancing Links structure
    root, column_nodes = build_dlx_grid(matrix)

    # Step 3: Create solver FIRST
    solver = DLXSolver(root, progress=progress)

    # Step 4: Pre-cover forced rows (given digits)
    for row_idx in forced_rows:
        # Find the node for this row_idx in any column
        row_node = None
        for col in column_nodes:
            node = col.down
            while node != col:
                if node.row_idx == row_idx:
                    row_node = node
                    break
                node = node.down
            if row_node:
                break

        if not row_node:
            raise ValueError(f"Row index {row_idx} not found in DLX structure.")

        # Cover this row's column first, then all columns to the right
        solver.cover(row_node.column)
        right_node = row_node.right
        while right_node != row_node:
            solver.cover(right_node.column)
            right_node = right_node.right

        # Add to solution so decode works correctly
        solver.solution.append(row_node)

    # The forced (given) rows above were appended directly, bypassing
    # record_progress — record one snapshot now so the series' starting
    # point reflects the puzzle's givens before the search begins.
    solver.record_progress(force=True)

    # Step 5: Search
    try:
        if solver.search():
            solved_board = empty_board(n)
            for node in solver.solution:
                i, j, v = decode_row_index(node.row_idx, n)
                solved_board[i][j] = v + 1
            return solved_board

        return None
    finally:
        solver.finalize_progress()


def print_sudoku(board):
    """
    Print a Sudoku grid in a readable format.
    :param board: 2D list representing the Sudoku grid.
    """
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("-" * 21)
        print(" | ".join(
            " ".join(str(cell) if cell != 0 else "." for cell in row[j:j + 3])
            for j in range(0, 9, 3)
        ))


if __name__ == "__main__":
    # Example Sudoku puzzle (0 represents empty cells)
    puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]

    print("Original Sudoku Puzzle:")
    print_sudoku(puzzle)

    solved = solve_sudoku(puzzle)
    if solved:
        print("\nSolved Sudoku Puzzle:")
        print_sudoku(solved)
    else:
        print("\nNo solution exists for the given Sudoku puzzle.")