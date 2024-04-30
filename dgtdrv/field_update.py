from dgt_constants import DgtConstants

class FieldUpdate:
    """
    Update of the state of a single square. Note that in the case where a piece
    A standing on a square is replaced by another piece B, the board may
    generate a single message (piece B on square) or two messages (square
    empty, then piece B on square) depending on the how the physical act of
    replacing the pieces on the board intersects with the scanning of the
    board. Furthermore, the coordinates are in the <em>board's internal</em>
    coordinate system, not necessarily the coordinates of the game; it's
    perfectly possible to play a game with white on the board's seventh and
    eighth ranks and black on the first and second.
    """
    def __init__(self, data):
        if len(data) != 2:
            raise ValueError("Field update expects exactly two bytes of data")

        self.square = DgtConstants.dgtCodeToSquare(data[0])
        self.color = DgtConstants.dgtCodeToColor(data[1])
        self.role = DgtConstants.dgtCodeToRole(data[1])


