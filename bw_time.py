
import datetime

"""
<p>Clock state. <em>IMPORTANT:</em> The clock state operates purely in
terms of the <em>left</em> and <em>right</em> player; there is no inherent
conception of white or black (but see
{@link org.riisholt.dgtdriver.moveparser.PlayedMove#clockInfo}). This class
contains the time remaining for the left and right players (encoded as a
{@link Duration}), as well as status flags for each player and general
status information. For each player, the following flags are indicated:</p>

<ul>
    <li>Is the player's flag fallen and the clock blocked at zero?</li>
    <li>Is the player's time per move indicator on?</li>
    <li>Is the flag signal indicated for the player? This is a distinct
    case from the first flag, as the flag is also indicated when multiple
    time periods are used (such as two hours for 40 moves, etc.), in which
    case the arbiter must ensure that enough moves are played before the
    flag falls.</li>
</ul>

<p>The following general clock state flags are also indicated:</p>

<ul>
    <li>Is a clock connected?</li>
    <li>Is the clock running?</li>
    <li>Is the tumbler high to the left?</li>
    <li>Is the tumbler high to the right?</li>
    <li>Does the clock indicate low battery?</li>
    <li>Is it the left player to move?</li>
    <li>Is it the right player to move?</li>
</ul>
"""

class BWTime:
    """ Time left on the left player's clock. """
    left: datetime.timedelta
    """ Time left on the right player's clock. """
    right: datetime.timedelta

    """
    Status byte for the left clock. Information <em>can</em> be extracted
    from this byte, but more convenient is probably the helper methods
    defined in this class.

    @see #leftFinalFlag()
    @see #leftFlag()
    @see #leftTimePerMove()
    """
    left_flags: int

    """
    Status byte for the right clock. Information <em>can</em> be extracted
    from this byte, but more convenient is probably the helper methods
    defined in this class.

    @see #rightFinalFlag()
    @see #rightFlag()
    @see #rightTimePerMove()
    """
    right_flags: int

    """
    Status byte for general flags. Information <em>can</em> be extracted
    from this byte, but more convenient is probably the helper methods
    defined in this class.

    @see #clockConnected()
    @see #clockRunning()
    @see #leftHigh()
    @see #rightHigh()
    @see #batteryLow()
    @see #leftToMove()
    @see #rightToMove()
    """
    clock_status_flags: int

    """ Construct an object from a board data payload. """
    def __init__(self, data: bytes):
        if len(data) != 7:
            raise ValueError(f"BWTime expects exactly 7 bytes of data (got {len(data)})")

        self.right_flags = (data[0] & 0xf0) >> 4
        self.right = datetime.timedelta(
            hours=data[0] & 0x0f,
            minutes=self.decode_bcd(data[1]),
            seconds=self.decode_bcd(data[2])
        )

        self.left_flags = (data[3] & 0xf0) >> 4
        self.left = datetime.timedelta(
            hours=data[3] & 0x0f,
            minutes=self.decode_bcd(data[4]),
            seconds=self.decode_bcd(data[5])
        )

        self.clock_status_flags = data[6]

    def __init__(self, left: datetime.timedelta, left_flags: int, right: datetime.timedelta, right_flags: int, clock_status_flags: int):
        self.left = left
        self.left_flags = left_flags
        self.right = right
        self.right_flags = right_flags
        self.clock_status_flags = clock_status_flags

    """
    Has the left player's final flag fallen?

    @return True if the final flag has fallen
    """
    def left_final_flag(self) -> bool:
        return (self.left_flags & 0x01) != 0

    """
    Is the left player's time per move indicator on?

    @return True if the time per move indicator is on
    """
    def left_time_per_move(self) -> bool:
        return (self.left_flags & 0x02) != 0

    """
    Has the left player's flag fallen?

    @return True if the flag has fallen
    """
    def left_flag(self) -> bool:
        return (self.left_flags & 0x04) != 0

    """
    Has the right player's final flag fallen?

    @return True if the final flag has fallen
    """
    def right_final_flag(self) -> bool:
        return (self.right_flags & 0x01) != 0

    """
    Is the right player's time per move indicator on?

    @return True if the time per move indicator is on
    """
    def right_time_per_move(self) -> bool:
        return (self.right_flags & 0x02) != 0

    """
    Has the right player's flag fallen?

    @return True if the flag has fallen
    """
    def right_flag(self) -> bool:
        return (self.right_flags & 0x04) != 0

    """
    Is the clock running?

    @return True if the clock is running
    """
    def clock_running(self) -> bool:
        return (self.clock_status_flags & 0x01) != 0

    """
    Is the left side of the clock tumbler high?

    @return True if the left tumbler is high
    """
    def left_high(self) -> bool:
        return (self.clock_status_flags & 0x02) == 0

    """
    Is the right side of the clock tumbler high?

    @return True if the right tumbler is high
    """
    def right_high(self) -> bool:
        return (self.clock_status_flags & 0x02) != 0

    """
    Is the clock indicating low battery?

    @return True if the battery is low
    """
    def battery_low(self) -> bool:
        return (self.clock_status_flags & 0x04) != 0

    """
    Is it the left player's turn to move?

    @return True if the left player is to move
    """
    def left_to_move(self) -> bool:
        return (self.clock_status_flags & 0x08) != 0

    """
    Is it the right player's turn to move?

    @return True if the right player is to move
    """
    def right_to_move(self) -> bool:
        return (self.clock_status_flags & 0x10) != 0

    """
    Is a clock connected to the board?

    @return True if a clock is connected
    """
    def clock_connected(self) -> bool:
        return (self.clock_status_flags & 0x20) != 0

    """
    The time remaining on the left clock, formatted as "HH:MM:ss". The
    minute and second fields are zero padded to always be two characters
    wide.

    @return The left player's time
    """
    def left_time_string(self) -> str:
        return self.time_string(self.left)

    """
    The time remaining on the right clock, formatted as "HH:MM:ss". The
    minute and second fields are zero padded to always be two characters
    wide.

    @return The right player's time
    """
    def right_time_string(self) -> str:
        return self.time_string(self.right)

    """
    Rotate the clock info. This swaps all the position-dependent
    information around, so that it's as if the left player is on the right
    and vice versa. This is a helper intended for the case where the game
    is played with white seated at the "black" side of the board, so that
    most of the code can assume that white is always on the left and the
    board's A1 is the game's A1.

    @return A rotated copy
    """
    def rotate(self) -> 'BWTime':
        # The flags for left/right high, left to move, and right to move
        # depend on the orientation of the board (assuming the clock is
        # always on the same side of the board). We flip those bits by
        # XOR-ing in a one in the appropriate position.
        new_clock_status = self.clock_status_flags ^ 0x1a
        return BWTime(self.right, self.right_flags, self.left, self.left_flags, new_clock_status)

    @staticmethod
    def decode_bcd(b: int) -> int:
        return ((b & 0xf0) >> 4) * 10 + (b & 0x0f)

    def time_string(self, t: datetime.timedelta) -> str:
        seconds = t.total_seconds()
        hours = int(seconds // 3600)
        seconds -= hours * 3600
        minutes = int(seconds // 60)
        seconds -= minutes * 60
        return f"{hours}:{minutes:02d}.{int(seconds):02d}"

