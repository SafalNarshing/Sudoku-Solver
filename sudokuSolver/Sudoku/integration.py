from exact_cover_matrix import build_exact_cover_matrix, get_forced_rows, decode_row_index
from dlx_node import build_dlx_grid
from dlx_solver import DLXSolver


def solve_sudoku(board):
    """
    Solve a Sudoku puzzle using DLX (Algorithm X with Dancing Links).
    :param board: 2D list representing the Sudoku grid (0 for empty cells).
    :return: Solved Sudoku grid as a 2D list, or None if no solution exists.
    """
    # Step 1: Build the exact cover matrix
    matrix = build_exact_cover_matrix()
    forced_rows = get_forced_rows(board)

    # Step 2: Build the Dancing Links structure
    root, column_nodes = build_dlx_grid(matrix)

    # Step 3: Pre-cover rows for pre-filled cells
    for row_idx in forced_rows:
        # Find the first node in the row corresponding to row_idx
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
            raise ValueError(f"Row index {row_idx} not found in the Dancing Links structure.")

        # Cover all columns satisfied by this row
        right_node = row_node.right
        while right_node != row_node:
            solver.cover(right_node.column)
            right_node = right_node.right

    # Step 4: Solve the exact cover problem
    solver = DLXSolver(root)
    if solver.search():
        # Step 5: Decode the solution into a Sudoku grid
        solution = solver.solution
        solved_board = [[0 for _ in range(9)] for _ in range(9)]
        for row_node in solution:
            i, j, v = decode_row_index(row_node.row_idx)
            solved_board[i][j] = v + 1  # Convert 0-based index to 1-based digit
        return solved_board

    # No solution exists
    return None


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