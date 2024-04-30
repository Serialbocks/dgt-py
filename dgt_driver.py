import array
import sys
from clock_ack import ClockAck
from clock_display_message import ClockDisplayMessage
from clock_icons_message import ClockIconsMessage
from clock_end_message import ClockEndMessage
from clock_button_message import ClockButtonMessage
from clock_version_message import ClockVersionMessage
from clock_set_n_run_message import ClockSetNRunMessage
from clock_beep_message import ClockBeepMessage
from dgt_constants import DgtConstants
from board_dump import BoardDump
from bw_time import BWTime
from field_update import FieldUpdate
from ee_moves import EEMoves
from bus_address import Busadress
from serial_nr_message import SerialnrMessage
from trademark_message import TrademarkMessage
from version_message import VersionMessage
from long_serial_nr_message import LongSerialnrMessage
from dgt_protocol_exception import DgtProtocolException
from dgt_constants import DgtConstants

class DgtDriver:
    def __init__(self, read, write):
        self.readCallback = read
        self.writeCallback = write
        self.buffer = array.array('b', [0] * 128)
        self.position = 0
        self.readyForClockMessage = True

    def reset(self):
        self.write_byte(DgtConstants.DGT_SEND_RESET)

    def to_bus_mode(self):
        self.write_byte(DgtConstants.DGT_TO_BUSMODE)

    def start_boot_loader(self):
        self.write_byte(DgtConstants.DGT_STARTBOOTLOADER)

    def clock(self):
        self.write_byte(DgtConstants.DGT_SEND_CLK)

    def board(self):
        self.write_byte(DgtConstants.DGT_SEND_BRD)

    def update(self):
        self.write_byte(DgtConstants.DGT_SEND_UPDATE)

    def update_nice(self):
        self.write_byte(DgtConstants.DGT_SEND_UPDATE_NICE)

    def update_board(self):
        self.write_byte(DgtConstants.DGT_SEND_UPDATE_BRD)

    def serialnr(self):
        self.write_byte(DgtConstants.DGT_RETURN_SERIALNR)

    def long_serialnr(self):
        self.write_byte(DgtConstants.DGT_RETURN_LONG_SERIALNR)

    def busadress(self):
        self.write_byte(DgtConstants.DGT_RETURN_BUSADRES)

    def trademark(self):
        self.write_byte(DgtConstants.DGT_SEND_TRADEMARK)

    def ee_moves(self):
        self.write_byte(DgtConstants.DGT_SEND_EE_MOVES)

    def battery_status(self):
        self.write_byte(DgtConstants.DGT_SEND_BATTERY_STATUS)

    def version(self):
        self.write_byte(DgtConstants.DGT_SEND_VERSION)

    def send_clock_message(self, message):
        if self.readyForClockMessage:
            self.readyForClockMessage = False
            self.writeCallback(message.toBytes())
            return True
        else:
            return False

    def is_ready_for_clock_message(self):
        return self.readyForClockMessage

    def clock_display(self, aLocation, bLocation, cLocation, dLocation, eLocation, fLocation, dotsAndOnes, beep):
        return self.send_clock_message(ClockDisplayMessage(aLocation, bLocation, cLocation, dLocation, eLocation, fLocation, dotsAndOnes, beep))

    def clock_icons(self, left, right, general):
        return self.send_clock_message(ClockIconsMessage(left, right, general))

    def clock_end(self):
        return self.send_clock_message(ClockEndMessage())

    def clock_button(self):
        return self.send_clock_message(ClockButtonMessage())

    def clock_version(self):
        return self.send_clock_message(ClockVersionMessage())

    def clock_setnrun(self, leftTime, leftCountsUp, rightTime, rightCountsUp, pause, toggleOnLever):
        return self.send_clock_message(ClockSetNRunMessage(leftTime, leftCountsUp, rightTime, rightCountsUp, pause, toggleOnLever))

    def clock_beep(self, duration):
        return self.send_clock_message(ClockBeepMessage(duration))

    def got_bytes(self, bytes):
        if self.position + len(bytes) > len(self.buffer):
            self.buffer = array.array('b', self.buffer) + array.array('b', [0] * len(bytes))
        self.buffer[self.position:self.position + len(bytes)] = array.array('b', bytes)
        self.position += len(bytes)
        self.try_emit_message()
        if len(self.buffer) > 128 and self.position < 128:
            self.buffer = array.array('b', self.buffer[:128])

    def try_emit_message(self):
        while self.position >= 3:
            message = self.buffer[0]
            sizeMsb = self.buffer[1]
            sizeLsb = self.buffer[2]
            if (message & 0x80) == 0:
                self.scroll_bad_bytes(1)
                continue
            if (sizeMsb & 0x80) != 0:
                self.scroll_bad_bytes(2)
                continue
            if (sizeLsb & 0x80) != 0:
                self.scroll_bad_bytes(3)
                continue
            messageLen = (sizeMsb << 7) | sizeLsb
            if messageLen > self.position:
                return
            msg = None
            try:
                data = self.buffer[3:messageLen] if messageLen > 3 else []
                self.buffer[:self.position - messageLen] = self.buffer[messageLen:self.position]
                self.position -= messageLen
                if (message & 0x7f) == DgtConstants.DGT_NONE:
                    pass
                elif (message & 0x7f) == DgtConstants.DGT_BOARD_DUMP:
                    msg = BoardDump(data)
                elif (message & 0x7f) == DgtConstants.DGT_BWTIME:
                    if (data[0] & 0x0f) == 0x0a or (data[3] & 0x0f) == 0x0a:
                        self.readyForClockMessage = True
                        msg = ClockAck(data)
                    elif data[0] == 0 and data[1] == 0 and data[2] == 0 and data[3] == 0 and data[4] == 0 and data[5] == 0 and data[6] == 0:
                        pass
                    else:
                        msg = BWTime(data)
                elif (message & 0x7f) == DgtConstants.DGT_FIELD_UPDATE:
                    msg = FieldUpdate(data)
                elif (message & 0x7f) == DgtConstants.DGT_EE_MOVES:
                    msg = EEMoves(data)
                elif (message & 0x7f) == DgtConstants.DGT_BUSADRES:
                    msg = Busadress(data)
                elif (message & 0x7f) == DgtConstants.DGT_SERIALNR:
                    msg = SerialnrMessage(data)
                elif (message & 0x7f) == DgtConstants.DGT_TRADEMARK:
                    msg = TrademarkMessage(data)
                elif (message & 0x7f) == DgtConstants.DGT_VERSION:
                    msg = VersionMessage(data)
                elif (message & 0x7f) == DgtConstants.DGT_BOARD_DUMP_50B:
                    return
                elif (message & 0x7f) == DgtConstants.DGT_BOARD_DUMP_50W:
                    return
                elif (message & 0x7f) == DgtConstants.DGT_LONG_SERIALNR:
                    msg = LongSerialnrMessage(data)
                else:
                    raise DgtProtocolException("Unknown message id %x from board" % (message & 0x7f))
            except Exception as e:
                continue
            if msg is not None:
                self.readCallback(msg)

    def scroll_bad_bytes(self, start):
        good = start
        while good < self.position:
            if (self.buffer[good] & 0x80) != 0:
                break
            good += 1
        self.buffer[:self.position - good] = self.buffer[good:self.position]
        self.position -= good

    def write_byte(self, b):
        self.writeCallback(array.array('b', [b]))

