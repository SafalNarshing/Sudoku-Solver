from .dlx_node import ColumnNode, count_column
from .sudoku_utils import ProgressRecorder


class DLXSolver:
    def __init__(self, root: ColumnNode, progress: list = None, recorder: ProgressRecorder = None):
        """
        Initialize the DLX solver with the root header node of the Dancing Links structure.

        If `progress` is a list, it is populated with (elapsed_ms,
        cells_filled) snapshots as rows are added to/removed from the
        solution — each row corresponds to placing one digit in one cell,
        so len(self.solution) doubles as the cells-filled count.

        `recorder` lets a caller supply a `ProgressRecorder` whose clock
        already started before this solver was constructed (e.g. before
        building the exact-cover matrix), so the recorded timeline reflects
        total elapsed time rather than just the search phase. Falls back to
        starting a fresh one here if omitted.
        """
        self.root = root
        self.solution = []  # Stores the solution rows
        self._progress = progress
        self._recorder = recorder if recorder is not None else (ProgressRecorder() if progress is not None else None)

    def record_progress(self, force=False):
        if self._recorder:
            self._recorder.record(len(self.solution), force=force)

    def finalize_progress(self):
        if self._recorder:
            self.record_progress(force=True)
            self._progress.extend(self._recorder.points)

    def search(self, k=0):
        """
        Recursive implementation of Algorithm X.
        :param k: Depth of the search tree (used for debugging or tracking recursion depth).
        :return: True if a solution is found, False otherwise.
        """
        # Base case: If the root header has no columns, all constraints are satisfied
        if self.root.right == self.root:
            return True

        # Choose a column (heuristic: choose the column with the fewest 1s)
        column = self.choose_column()

        # Cover the chosen column
        self.cover(column)

        # Iterate through each row in the chosen column
        row = column.down
        while row != column:
            # Add the row to the solution
            self.solution.append(row)
            self.record_progress()

            # Cover all columns satisfied by this row
            right_node = row.right
            while right_node != row:
                self.cover(right_node.column)
                right_node = right_node.right

            # Recur to solve the reduced problem
            if self.search(k + 1):
                return True

            # Backtrack: Uncover all columns satisfied by this row
            left_node = row.left
            while left_node != row:
                self.uncover(left_node.column)
                left_node = left_node.left

            # Remove the row from the solution
            self.solution.pop()
            self.record_progress()

            # Move to the next row
            row = row.down

        # Uncover the chosen column
        self.uncover(column)

        return False

    def choose_column(self) -> ColumnNode:
        """
        Choose the column with the fewest 1s (heuristic to minimize branching).
        """
        column = self.root.right
        min_size = float('inf')
        chosen_column = column

        while column != self.root:
            if column.size < min_size:
                min_size = column.size
                chosen_column = column
            column = column.right

        return chosen_column

    def cover(self, column: ColumnNode):
        """
        Cover a column and remove all rows that intersect it from the matrix.
        """
        column.right.left = column.left
        column.left.right = column.right

        row = column.down
        while row != column:
            right_node = row.right
            while right_node != row:
                right_node.down.up = right_node.up
                right_node.up.down = right_node.down
                right_node.column.size -= 1
                right_node = right_node.right
            row = row.down

    def uncover(self, column: ColumnNode):
        """
        Uncover a column and restore all rows that intersect it to the matrix.
        """
        row = column.up
        while row != column:
            left_node = row.left
            while left_node != row:
                left_node.column.size += 1
                left_node.down.up = left_node
                left_node.up.down = left_node
                left_node = left_node.left
            row = row.up

        column.right.left = column
        column.left.right = column