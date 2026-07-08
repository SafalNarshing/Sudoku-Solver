import random
import copy
from .sudoku_utils import box_size


def is_valid_move(grid, row, col, num, n, bs=None):
    bs = bs or box_size(n)

    # Check row
    if num in grid[row]:
        return False

    # Check column
    if num in [grid[i][col] for i in range(n)]:
        return False

    # Check box
    start_row, start_col = bs * (row // bs), bs * (col // bs)
    for i in range(bs):
        for j in range(bs):
            if grid[start_row + i][start_col + j] == num:
                return False

    return True


def solve_sudoku(grid, n, bs=None):
    bs = bs or box_size(n)
    empty = find_empty(grid, n)
    if not empty:
        return True

    row, col = empty
    for num in random.sample(range(1, n + 1), n):
        if is_valid_move(grid, row, col, num, n, bs):
            grid[row][col] = num
            if solve_sudoku(grid, n, bs):
                return True
            grid[row][col] = 0
    return False


def find_empty(grid, n):
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 0:
                return (i, j)
    return None


def generate_sudoku(clues, n=9):
    bs = box_size(n)

    # Create empty grid
    grid = [[0 for _ in range(n)] for _ in range(n)]

    # Generate a solved sudoku by filling diagonal boxes and solving
    for i in range(0, n, bs):
        nums = list(range(1, n + 1))
        random.shuffle(nums)
        for j in range(bs):
            for k in range(bs):
                grid[i + j][i + k] = nums.pop()

    # Solve the grid
    solve_sudoku(grid, n, bs)

    # Create a deep copy of the solved grid
    solution = [row[:] for row in grid]

    # Remove numbers to create puzzle
    cells = [(i, j) for i in range(n) for j in range(n)]
    random.shuffle(cells)

    # Calculate how many cells to empty
    cells_to_empty = n * n - clues

    # Remove numbers
    for i in range(cells_to_empty):
        if i < len(cells):
            row, col = cells[i]
            grid[row][col] = 0

    return grid, solution
