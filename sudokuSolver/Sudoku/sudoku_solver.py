from copy import deepcopy
import time
from .heuristicSolver2 import solve_with_performance_tracking
from .recursiveBacktracking import solve_backtracking
from .integration import solve_sudoku as solve_dlx

def solve_with_comparison(board):
    """Compare both solving methods on identical boards"""
    # Create deep copies of the board for each solver
    board_heuristic = deepcopy(board)
    board_backtrack = deepcopy(board)
    board_dlx = deepcopy(board)
    
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

    #-- DLX Solver --
    start_time  = time.time()
    dlx_result  = solve_dlx(board_dlx)       # returns solved board or None
    dlx_time    = (time.time() - start_time) * 1000
    dlx_success = dlx_result is not None
    
    # Final solution — prefer heuristic, fall back to DLX result
    final_solution = heuristic_solution if heuristic_success else (dlx_result if dlx_success else board_backtrack)

    # backtrack_success is informational only (benchmarking comparison) — the
    # naive solver has no move-ordering heuristic and is time-boxed, so it can
    # legitimately time out on a solvable board without that being a failure.
    overall_success = heuristic_success or dlx_success

    return overall_success, final_solution, heuristic_time, backtrack_time, dlx_time  # ← now returns 5 values