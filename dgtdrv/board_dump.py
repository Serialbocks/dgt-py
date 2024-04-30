from board import Board
from dgt_constants import DgtConstants

class DgtProtocolException(Exception):
    pass

class BoardDump:
    def __init__(self, data):
        if len(data) != 64:
            print(data)
            raise DgtProtocolException("BoardDump expects exactly 64 bytes of data")
        
        self.board = Board.empty_board()
        for i in range(len(data)):
            if data[i] != DgtConstants.EMPTY:
                square = DgtConstants.dgt_code_to_square(i)
                color = DgtConstants.dgt_code_to_color(data[i])
                role = DgtConstants.dgt_code_to_role(data[i])
                self.board.put(square, color, role)


