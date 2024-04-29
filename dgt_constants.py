# Messages to board that are not responded to.
# Reset the board back to idle mode. Cancels any update mode requested.
DGT_SEND_RESET  = 0x40
# Put the board in bus mode.
DGT_TO_BUSMODE  = 0x4a
# Reboot the board? Poorly documented from DGT.
DGT_STARTBOOTLOADER = 0x4e

# Messages that generate responses.
# Request the current clock state.
DGT_SEND_CLK = 0x41
# Request the current board state.
DGT_SEND_BRD = 0x42
# Request periodic updates.
DGT_SEND_UPDATE  = 0x43
# Request updates for board state.
DGT_SEND_UPDATE_BRD  = 0x44
# Request the board's serial number.
DGT_RETURN_SERIALNR  = 0x45
# Request the board's bus adress.
DGT_RETURN_BUSADRES  = 0x46
# Request the trademark message.
DGT_SEND_TRADEMARK = 0x47
# Request transmission of moves stored in the board's EEPROM.
DGT_SEND_EE_MOVES= 0x49
# Request updates when board or clock state changes.
DGT_SEND_UPDATE_NICE = 0x4b
# Request battery status.
DGT_SEND_BATTERY_STATUS  = 0x4c
# Request the board's version information.
DGT_SEND_VERSION = 0x4d
# (Draughts) Requests the state of the black squares.
DGT_SEND_BRD_50B = 0x50
# (Draughts) Set the board to scan only the black squares.
DGT_SCAN_50B = 0x51
# (Draughts) Requests the state of the white squares.
DGT_SEND_BRD_50W = 0x52
# (Draughts) Set the board to scan only the white squares.
DGT_SCAN_50W = 0x53
# (Draughts) Set the board to scan the whole board.
DGT_SCAN_100 = 0x54
# Request the board's long serial number.
DGT_RETURN_LONG_SERIALNR = 0x55

# Clock messages.
# Set clock state.
DGT_CLOCK_MESSAGE = 0x2b
# Change main display.
DGT_CMD_CLOCK_DISPLAY = 0x01
# Change icons on clock.
DGT_CMD_CLOCK_ICONS = 0x02
# End custom display.
DGT_CMD_CLOCK_END = 0x03
# Request current button pressed.
DGT_CMD_CLOCK_BUTTON= 0x08
# Request clock version.
DGT_CMD_CLOCK_VERSION = 0x09
# Programmatically set clock times and running state.
DGT_CMD_CLOCK_SETNRUN = 0x0a
# Change beep state.
DGT_CMD_CLOCK_BEEP  = 0x0b
# Start of clock message.
DGT_CMD_CLOCK_START_MESSAGE = 0x03
# End of clock message.
DGT_CMD_CLOCK_END_MESSAGE = 0x00

# Messages from board.
# Empty message.
DGT_NONE = 0x00
# Board dump message.
DGT_BOARD_DUMP = 0x06
# Clock status message.
DGT_BWTIME = 0x0d
# Field change message.
DGT_FIELD_UPDATE = 0x0e
# Moves from EEPROM.
DGT_EE_MOVES = 0x0f
# Board bus adress.
DGT_BUSADRES = 0x10
# Board serial number.
DGT_SERIALNR = 0x11
# Trademark message.
DGT_TRADEMARK  = 0x12
# Version information.
DGT_VERSION= 0x13
# (Draughts) Black square board dump.
DGT_BOARD_DUMP_50B = 0x14
# (Draughts) White square board dump.
DGT_BOARD_DUMP_50W = 0x15
# Battery status.
DGT_BATTERY_STATUS = 0x20
# Board long serial number.
DGT_LONG_SERIALNR  = 0x22

# Piece codes for chess.
# Empty square.
EMPTY = 0x00
# White pawn.
WPAWN = 0x01
# White rook.
WROOK = 0x02
# White knight.
WKNIGHT = 0x03
# White bishop.
WBISHOP = 0x04
# White king.
WKING = 0x05
# White queen.
WQUEEN  = 0x06
# Black pawn.
BPAWN = 0x07
# Black rook.
BROOK = 0x08
# Black knight.
BKNIGHT = 0x09
# Black bishop.
BBISHOP = 0x0a
# Black king.
BKING = 0x0b
# Black queen.
BQUEEN  = 0x0c
# Special piece to signal draw.
PIECE1  = 0x0d;  # Magic piece: Draw
# Special piece to signal white win.
PIECE2  = 0x0e;  # Magic piece: White win
# Special piece to signal black win.
PIECE3  = 0x0f;  # Magic piece: Black win

# Piece codes for draughts.
# White draughts piece.
WDISK  = 0x01
# Black draughts piece.
BDISK  = 0x04
# White draughts crown.
WCROWN = 0x07
# Black draughts crown.
BCROWN = 0x0a;