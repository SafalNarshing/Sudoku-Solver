"""
dlx_node.py
-----------
The two building blocks of the Dancing Links data structure:

    Node       — represents a single 1 in the exact-cover matrix
    ColumnNode — a special Node that sits at the top of each column
                 and also acts as the root header (h)

Nothing in this file knows about Sudoku.  It is pure DLX plumbing.
"""


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class Node:
    """
    One node in the circular doubly-linked grid.
    Represents a single 1-entry in the exact-cover matrix.

    Links (all initialise to self → valid 1-node circular list):
        left / right  — neighbours in the same matrix row
        up   / down   — neighbours in the same matrix column
        column        — the ColumnNode that heads this column
    """

    __slots__ = ("left", "right", "up", "down", "column")

    def __init__(self):
        self.left   = self
        self.right  = self
        self.up     = self
        self.down   = self
        self.column: "ColumnNode" = None   # set when inserted into a column

    # ------------------------------------------------------------------
    # Linking helpers
    # ------------------------------------------------------------------

    def link_right(self, node: "Node") -> "Node":
        """
        Insert `node` immediately to the right of self in the row list.
        Returns `node` so calls can be chained.

        Before:  ... self <-> self.right ...
        After:   ... self <-> node <-> old_right ...
        """
        node.right      = self.right
        node.left       = self
        self.right.left = node
        self.right      = node
        return node

    def link_down(self, node: "Node") -> "Node":
        """
        Insert `node` immediately above the column header
        (i.e. at the *bottom* of the column list, just before wrapping).
        Returns `node`.

        Before:  ... self.up <-> self ...
        After:   ... old_up  <-> node <-> self ...
        """
        node.down      = self
        node.up        = self.up
        self.up.down   = node
        self.up        = node
        node.column.size += 1
        return node

    def __repr__(self) -> str:
        col_name = self.column.name if self.column else "?"
        return f"Node(col={col_name})"


# ---------------------------------------------------------------------------
# ColumnNode
# ---------------------------------------------------------------------------

class ColumnNode(Node):
    """
    Column header node.  Sits above every column in the matrix and is also
    used as the root header (h) that anchors the left-right list of columns.

    Extra fields vs Node:
        name  — human-readable label, invaluable for debugging
        size  — number of 1-entries currently visible in this column
                (decremented on cover, incremented on uncover)
    """

    __slots__ = ("name", "size")

    def __init__(self, name: str = ""):
        super().__init__()
        self.column = self      # a ColumnNode is its own column
        self.name   = name
        self.size   = 0         # starts empty; incremented by link_down

    def __repr__(self) -> str:
        return f"ColumnNode(name={self.name!r}, size={self.size})"


# ---------------------------------------------------------------------------
# Builder helper
# ---------------------------------------------------------------------------

def build_dlx_grid(matrix, col_names=None):
    """
    Converts a 2-D list-of-lists (0/1) into the circular linked-list
    structure used by DLX.

    Parameters
    ----------
    matrix    : list[list[int]]  — the exact-cover matrix (0s and 1s)
    col_names : list[str] | None — optional labels for each column;
                                   defaults to "c0", "c1", ...

    Returns
    -------
    header : ColumnNode  — the root node (h); entry point for Algorithm X
    columns: list[ColumnNode]  — the column headers in order (handy for
                                  pre-covering forced rows)
    """
    num_rows = len(matrix)
    num_cols = len(matrix[0])

    if col_names is None:
        col_names = [f"c{c}" for c in range(num_cols)]

    # --- Create root header and one ColumnNode per column ---------------
    header = ColumnNode("h")
    columns = []

    for c in range(num_cols):
        col_node = ColumnNode(col_names[c])
        header.link_right(col_node)   # appends to the right of what came before
        # NOTE: link_right inserts immediately right of header each time,
        # so we must walk right to find the tail. Instead we chain via the
        # last inserted node. Re-use tail pointer below.
        columns.append(col_node)

    # The above loop inserts every column immediately right of header,
    # which reverses the order. Fix: rebuild using a running tail pointer.
    # Reset and redo:
    header.right = header
    header.left  = header
    tail = header
    for col_node in columns:
        col_node.right = header     # circular: last col's right = header
        col_node.left  = tail
        tail.right     = col_node
        header.left    = col_node
        tail           = col_node

    # --- Create data nodes and link them --------------------------------
    for r in range(num_rows):
        row_tail = None     # rightmost node in the current row so far

        for c in range(num_cols):
            if matrix[r][c] != 1:
                continue

            node        = Node()
            node.column = columns[c]

            # Vertical link: insert at bottom of column
            # (link_down inserts just above the column header)
            col_head = columns[c]
            node.down          = col_head
            node.up            = col_head.up
            col_head.up.down   = node
            col_head.up        = node
            col_head.size     += 1

            # Horizontal link: append to the right of the row so far
            if row_tail is None:
                row_tail = node     # first node in this row
            else:
                # insert to the right of row_tail's leftmost position
                node.right          = row_tail
                node.left           = row_tail.left
                row_tail.left.right = node
                row_tail.left       = node

    return header, columns


# ---------------------------------------------------------------------------
# Verification helpers  (small matrix only — for unit testing)
# ---------------------------------------------------------------------------

def count_column(col: ColumnNode) -> int:
    """Walk a column top-to-bottom and count data nodes."""
    count = 0
    node  = col.down
    while node is not col:
        count += 1
        node   = node.down
    return count


def count_header_row(header: ColumnNode) -> int:
    """Count how many column headers are reachable from header (excluding header itself)."""
    count = 0
    node  = header.right
    while node is not header:
        count += 1
        node   = node.right
    return count


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Knuth's example matrix from his original DLX paper:
    #        c0 c1 c2 c3 c4 c5 c6
    # row 0:  0  0  1  0  1  1  0
    # row 1:  1  0  0  1  0  0  1
    # row 2:  0  1  1  0  0  1  0
    # row 3:  1  0  0  1  0  0  0
    # row 4:  0  1  0  0  0  0  1
    # row 5:  0  0  0  1  1  0  1

    knuth_matrix = [
        [0, 0, 1, 0, 1, 1, 0],
        [1, 0, 0, 1, 0, 0, 1],
        [0, 1, 1, 0, 0, 1, 0],
        [1, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 1],
        [0, 0, 0, 1, 1, 0, 1],
    ]

    header, cols = build_dlx_grid(knuth_matrix, col_names=list("ABCDEFG"))

    # Every column should have the correct number of 1s
    expected_sizes = [2, 2, 2, 3, 2, 2, 3]
    for i, col in enumerate(cols):
        actual = count_column(col)
        assert actual == expected_sizes[i], \
            f"Col {col.name}: expected size {expected_sizes[i]}, got {actual}"
        assert col.size == expected_sizes[i], \
            f"Col {col.name}: .size field {col.size} != walk count {actual}"

    # All 7 columns reachable from header
    assert count_header_row(header) == 7, "Expected 7 columns in header row"

    # Circular check: walking left from header should also visit all 7
    count = 0
    node  = header.left
    while node is not header:
        count += 1
        node   = node.left
    assert count == 7, "Left-walk from header should also find 7 columns"

    print("dlx_node smoke test passed.")
    print(f"  header  : {header}")
    print(f"  columns : {cols}")
    for col in cols:
        print(f"  {col.name}: size={col.size}")