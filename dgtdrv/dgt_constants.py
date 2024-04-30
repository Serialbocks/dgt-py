
import enum

class Role(enum.Enum):
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

# Constants used in board communication, and conversion utilities.
class DgtConstants:
    # Messages to board that are not responded to.
    DGT_SEND_RESET = 0x40  # Reset the board back to idle mode. Cancels any update mode requested.
    DGT_TO_BUSMODE = 0x4a  # Put the board in bus mode.
    DGT_STARTBOOTLOADER = 0x4e  # Reboot the board? Poorly documented from DGT.

    # Messages that generate responses.
    DGT_SEND_CLK = 0x41  # Request the current clock state.
    DGT_SEND_BRD = 0x42  # Request the current board state.
    DGT_SEND_UPDATE = 0x43  # Request periodic updates.
    DGT_SEND_UPDATE_BRD = 0x44  # Request updates for board state.
    DGT_RETURN_SERIALNR = 0x45  # Request the board's serial number.
    DGT_RETURN_BUSADRES = 0x46  # Request the board's bus adress.
    DGT_SEND_TRADEMARK = 0x47  # Request the trademark message.
    DGT_SEND_EE_MOVES = 0x49  # Request transmission of moves stored in the board's EEPROM.
    DGT_SEND_UPDATE_NICE = 0x4b  # Request updates when board or clock state changes.
    DGT_SEND_BATTERY_STATUS = 0x4c  # Request battery status.
    DGT_SEND_VERSION = 0x4d  # Request the board's version information.
    DGT_SEND_BRD_50B = 0x50  # (Draughts) Requests the state of the black squares.
    DGT_SCAN_50B = 0x51  # (Draughts) Set the board to scan only the black squares.
    DGT_SEND_BRD_50W = 0x52  # (Draughts) Requests the state of the white squares.
    DGT_SCAN_50W = 0x53  # (Draughts) Set the board to scan only the white squares.
    DGT_SCAN_100 = 0x54  # (Draughts) Set the board to scan the whole board.
    DGT_RETURN_LONG_SERIALNR = 0x55  # Request the board's long serial number.

    # Clock messages.
    DGT_CLOCK_MESSAGE = 0x2b  # Set clock state.
    DGT_CMD_CLOCK_DISPLAY = 0x01  # Change main display.
    DGT_CMD_CLOCK_ICONS = 0x02  # Change icons on clock.
    DGT_CMD_CLOCK_END = 0x03  # End custom display.
    DGT_CMD_CLOCK_BUTTON = 0x08  # Request current button pressed.
    DGT_CMD_CLOCK_VERSION = 0x09  # Request clock version.
    DGT_CMD_CLOCK_SETNRUN = 0x0a  # Programmatically set clock times and running state.
    DGT_CMD_CLOCK_BEEP = 0x0b  # Change beep state.
    DGT_CMD_CLOCK_START_MESSAGE = 0x03  # Start of clock message.
    DGT_CMD_CLOCK_END_MESSAGE = 0x00  # End of clock message.

    # Messages from board.
    DGT_NONE = 0x00  # Empty message.
    DGT_BOARD_DUMP = 0x06  # Board dump message.
    DGT_BWTIME = 0x0d  # Clock status message.
    DGT_FIELD_UPDATE = 0x0e  # Field change message.
    DGT_EE_MOVES = 0x0f  # Moves from EEPROM.
    DGT_BUSADRES = 0x10  # Board bus adress.
    DGT_SERIALNR = 0x11  # Board serial number.
    DGT_TRADEMARK = 0x12  # Trademark message.
    DGT_VERSION = 0x13  # Version information.
    DGT_BOARD_DUMP_50B = 0x14  # (Draughts) Black square board dump.
    DGT_BOARD_DUMP_50W = 0x15  # (Draughts) White square board dump.
    DGT_BATTERY_STATUS = 0x20  # Battery status.
    DGT_LONG_SERIALNR = 0x22  # Board long serial number.

    # Piece codes for chess.
    EMPTY = 0x00  # Empty square.
    WPAWN = 0x01  # White pawn.
    WROOK = 0x02  # White rook.
    WKNIGHT = 0x03  # White knight.
    WBISHOP = 0x04  # White bishop.
    WKING = 0x05  # White king.
    WQUEEN = 0x06  # White queen.
    BPAWN = 0x07  # Black pawn.
    BROOK = 0x08  # Black rook.
    BKNIGHT = 0x09  # Black knight.
    BBISHOP = 0x0a  # Black bishop.
    BKING = 0x0b  # Black king.
    BQUEEN = 0x0c  # Black queen.
    PIECE1 = 0x0d  # Special piece to signal draw.
    PIECE2 = 0x0e  # Special piece to signal white win.
    PIECE3 = 0x0f  # Special piece to signal black win.

    # Piece codes for draughts.
    WDISK = 0x01  # White draughts piece.
    BDISK = 0x04  # Black draughts piece.
    WCROWN = 0x07  # White draughts crown.
    BCROWN = 0x0a  # Black draughts crown.

    @staticmethod
    def dgt_code_to_square(dgt_code):
        """
        Converts DGT square code to the coordinate system used by the game code
        in `org.riisholt.dgtdriver.game`.

        Args:
            dgt_code (int): A dgt square code from 0 to 63.

        Returns:
            int: A square code in the coordinate system used by `org.riisholt.dgtdriver.game.Board`

        Raises:
            DgtProtocolException: If square code is outside of [0,63].
        """
        # The DGT board numbers squares back to front, left to right, as
        # viewed by white. Thus A8 is 0, B8 is 1, A7 is8, and so on.
        if dgt_code >= 64 or dgt_code < 0:
            raise DgtProtocolException(f"Invalid square code {dgt_code}")
        file = dgt_code % 8
        rank = 7 - (dgt_code // 8)
        return rank * 8 + file

    @staticmethod
    def dgt_code_to_color(dgt_code):
        """
        Converts a DGT piece code to game code. The DGT piece codes contain
        both piece and colour in a single code, whereas the game code uses
        separate variables for the role and colour attributes.

        Args:
            dgt_code (int): A DGT piece code.

        Returns:
            bool: Corresponding game code colour. True for white, False for black

        Raises:
            DgtProtocolException: If the input code is invalid.
        """
        if dgt_code == DgtConstants.EMPTY:
            return True  # XXX: Empty arbitrarily decreed to be white.
        elif DgtConstants.WPAWN <= dgt_code < DgtConstants.BPAWN:
            return True
        elif DgtConstants.BPAWN <= dgt_code < DgtConstants.PIECE1:
            return False
        # XXX: Make draws arbitratrily white, because we don't have null to work with.
        elif dgt_code == DgtConstants.PIECE1:
            return True
        elif dgt_code == DgtConstants.PIECE2:
            return True
        elif dgt_code == DgtConstants.PIECE3:
            return False
        else:
            raise DgtProtocolException(f"Invalid piece code 0x{dgt_code:x}")

    @staticmethod
    def dgt_code_to_role(dgt_code):
        """
        Converts a DGT piece code to game code role.

        Args:
            dgt_code (int): A DGT piece code.

        Returns:
            Role: Corresponding game code role

        Raises:
            DgtProtocolException: If the input code is invalid.
        """
        if dgt_code == DgtConstants.EMPTY:
            return None
        elif dgt_code in (DgtConstants.WPAWN, DgtConstants.BPAWN):
            return Role.PAWN
        elif dgt_code in (DgtConstants.WKNIGHT, DgtConstants.BKNIGHT):
            return Role.KNIGHT
        elif dgt_code in (DgtConstants.WBISHOP, DgtConstants.BBISHOP):
            return Role.BISHOP
        elif dgt_code in (DgtConstants.WROOK, DgtConstants.BROOK):
            return Role.ROOK
        elif dgt_code in (DgtConstants.WQUEEN, DgtConstants.BQUEEN):
            return Role.QUEEN
        elif dgt_code in (DgtConstants.WKING, DgtConstants.BKING):
            return Role.KING
        # TODO: Handle PIECE1-3 for win/draw signaling.
        else:
            raise DgtProtocolException(f"Invalid piece code {dgt_code:x}")

class DgtProtocolException(Exception):
    pass

