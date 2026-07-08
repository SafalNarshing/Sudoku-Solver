import time
import random
from typing import List, Dict, Set, Tuple
from .sudoku_utils import get_peers, box_size, ProgressRecorder

def get_affected_cells(row: int, col: int, n: int = 9) -> Set[Tuple[int, int]]:
    """
    Returns set of cells that would be affected by placing a number at (row, col)

    Args:
        row (int): Row index
        col (int): Column index
        n (int): Grid size

    Returns:
        Set of affected cell coordinates
    """
    return get_peers(row, col, n)

def initialize_possibilities(board: List[List[int]], n: int = 9) -> Dict[Tuple[int, int], Set[int]]:
    """
    Create initial dictionary of possibilities for all empty cells

    Args:
        board (List[List[int]]): n x n Sudoku grid
        n (int): Grid size

    Returns:
        Dictionary of cell coordinates and possible values
    """
    possibilities = {}

    # Set all empty cells to have all possibilities
    for row in range(n):
        for col in range(n):
            if board[row][col] == 0:
                possibilities[(row, col)] = set(range(1, n + 1))

    # Remove possibilities based on existing numbers
    for row in range(n):
        for col in range(n):
            if board[row][col] != 0:
                value = board[row][col]
                # Remove this value from all affected cells
                for r, c in get_affected_cells(row, col, n):
                    if (r, c) in possibilities:
                        possibilities[(r, c)].discard(value)

    return possibilities

def find_most_constrained_cell(possibilities: Dict[Tuple[int, int], Set[int]], n: int = 9) -> Tuple[int, int, List[int]]:
    """  
    Find the empty cell with fewest possible values  
    
    Args:  
        possibilities (Dict): Dictionary of cell possibilities  
    
    Returns:  
        Tuple containing row, column, and possible values  
    """  
    if not possibilities:  # If no empty cells left  
        return -1, -1, []  
        
    # Find cell with minimum number of possibilities
    min_possibilities = n + 1
    best_cell = (-1, -1)  
    best_values = []  
    
    for (row, col), possible_values in possibilities.items():  
        if len(possible_values) < min_possibilities:  
            min_possibilities = len(possible_values)  
            best_cell = (row, col)  
            best_values = possible_values  
            
    return best_cell[0], best_cell[1], list(best_values)  

def solve_sudoku(board: List[List[int]],
                 time_limit: float = 5.0,
                 use_randomization: bool = True,
                 n: int = None,
                 progress: list = None) -> Dict:
    """
    Comprehensive Sudoku solving function with optimized constraint propagation

    Args:
        board (List[List[int]]): n x n Sudoku grid
        time_limit (float): Maximum solving time in seconds
        use_randomization (bool): Enable value randomization
        n (int): Grid size (defaults to len(board))
        progress (list): if provided, populated with (elapsed_ms, cells_filled)
            snapshots recorded as constraint propagation and guesses fill
            cells, and as guesses get reverted on backtrack.

    Returns:
        Dictionary with solving results
    """
    n = n or len(board)
    start_time = time.time()
    original_board = [row[:] for row in board]
    recorder = ProgressRecorder() if progress is not None else None

    def count_filled():
        # Recounted from the board rather than tracked incrementally:
        # constraint-propagation fills are never explicitly reverted on
        # backtrack (only manual guesses are), so an incremental counter
        # can drift from the board's true state. Recounting is O(n^2),
        # which is cheap and only ever runs for events that actually get
        # sampled (see ProgressRecorder.record's callable form).
        return sum(1 for r in board for v in r if v != 0)

    if recorder:
        recorder.record(count_filled(), force=True)

    results = {
        'solved': False,
        'solution': None,
        'time_taken': 0,
        'error': None
    }

    # Pre-compute affected cells for each position (cache)
    affected_cache = {}
    for r in range(n):
        for c in range(n):
            affected_cache[(r, c)] = get_affected_cells(r, c, n)
    
    def propagate_constraints(possibilities: Dict[Tuple[int, int], Set[int]], 
                            row: int, col: int, num: int) -> bool:
        """
        Propagate constraints after placing a number.
        Returns False if contradiction found, True otherwise.
        """
        # Remove num from all affected cells
        for r, c in affected_cache[(row, col)]:
            if (r, c) in possibilities:
                possibilities[(r, c)].discard(num)
                # Early contradiction detection
                if len(possibilities[(r, c)]) == 0:
                    return False
        return True
    
    def apply_naked_singles(board: List[List[int]], 
                           possibilities: Dict[Tuple[int, int], Set[int]]) -> bool:
        """
        Apply naked singles (cells with only one possibility).
        Returns True if any cell was filled.
        """
        changed = False
        cells_to_fill = []

        for (row, col), possible_values in list(possibilities.items()):
            if len(possible_values) == 1:
                cells_to_fill.append((row, col, list(possible_values)[0]))

        for row, col, num in cells_to_fill:
            board[row][col] = num
            if recorder:
                recorder.record(count_filled)
            del possibilities[(row, col)]
            if not propagate_constraints(possibilities, row, col, num):
                return False
            changed = True

        return changed
    
    def backtrack_solve(board: List[List[int]],
                       possibilities: Dict[Tuple[int, int], Set[int]]) -> bool:
        """Recursive backtracking solver with constraint propagation"""
        # Check time limit
        if time.time() - start_time > time_limit:  
            return False  
        
        # Apply constraint propagation (naked singles)
        while apply_naked_singles(board, possibilities):
            if not possibilities:  # All cells filled
                results['solved'] = True  
                results['solution'] = [row[:] for row in board]  
                return True
        
        # Check if puzzle is solved
        if not possibilities:
            results['solved'] = True  
            results['solution'] = [row[:] for row in board]  
            return True
        
        # Find most constrained cell
        row, col, possible_values = find_most_constrained_cell(possibilities, n)
        
        # If no possibilities for a cell, backtrack
        if not possible_values:
            return False
        
        # Try each possible value
        values = possible_values[:]
        if use_randomization:  
            random.shuffle(values)  
        
        for num in values:
            # Save state
            board[row][col] = num
            if recorder:
                recorder.record(count_filled)
            new_possibilities = {k: v.copy() for k, v in possibilities.items()}
            del new_possibilities[(row, col)]

            # Propagate constraints
            if propagate_constraints(new_possibilities, row, col, num):
                if backtrack_solve(board, new_possibilities):
                    return True

            # Backtrack
            board[row][col] = 0
            if recorder:
                recorder.record(count_filled)

        return False
    
    try:
        # Initialize possibilities
        initial_possibilities = initialize_possibilities(board, n)
        
        # Check for immediate contradictions
        if any(len(poss) == 0 for poss in initial_possibilities.values()):
            results['error'] = 'Unsolvable puzzle (contradiction found)'
        else:
            # Attempt to solve  
            backtrack_solve(board, initial_possibilities)  
    except Exception as e:
        results['error'] = str(e)
    finally:
        results['time_taken'] = time.time() - start_time
        if recorder:
            recorder.record(count_filled, force=True)
            progress.extend(recorder.points)

    return results

# Optional: Performance measurement wrapper
def solve_with_performance_tracking(board: List[List[int]], n: int = None, progress: list = None) -> Dict:
    """
    Wrapper function to track solving performance

    Args:
        board (List[List[int]]): n x n Sudoku grid
        n (int): Grid size (defaults to len(board))
        progress (list): if provided, populated with (elapsed_ms, cells_filled) snapshots

    Returns:
        Dictionary with detailed solving metrics
    """
    n = n or len(board)
    start_time = time.time()
    result = solve_sudoku(board, n=n, progress=progress)
    
    # Add additional performance metrics  
    result['start_time'] = start_time  
    result['end_time'] = time.time()  
    result['board'] = board  
    
    return result