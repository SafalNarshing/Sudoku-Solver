from copy import deepcopy
import time
from .heuristicSolver2 import solve_with_performance_tracking
from .recursiveBacktracking import solve_backtracking
def solve_with_comparison(board):
    """Compare both solving methods on identical boards"""
    # Create deep copies of the board for each solver
    board_heuristic = deepcopy(board)
    board_backtrack = deepcopy(board)
    
    # Run heuristic solver (returns a dict with keys like 'solved' and 'solution')
    start_time = time.time()
    heuristic_result = solve_with_performance_tracking(board_heuristic)
    # normalize result
    heuristic_success = bool(heuristic_result.get('solved', False)) if isinstance(heuristic_result, dict) else bool(heuristic_result)
    # prefer solver-provided timing/solution when available
    heuristic_time = (heuristic_result.get('time_taken', time.time() - start_time) if isinstance(heuristic_result, dict) else (time.time() - start_time)) * 1000
    heuristic_solution = heuristic_result.get('solution', board_heuristic) if isinstance(heuristic_result, dict) else board_heuristic
    
    # Run backtracking solver
    start_time = time.time()
    backtrack_success = solve_backtracking(board_backtrack)
    backtrack_time = (time.time() - start_time) * 1000
    
    # Use the heuristic solution if both were successful
    final_solution = board_heuristic
    if heuristic_success and backtrack_success:
        # prefer explicit solution returned by heuristic solver when present
        final_solution = heuristic_solution

    return (heuristic_success and backtrack_success), final_solution, heuristic_time, backtrack_time
