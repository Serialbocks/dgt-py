from abc import ABC, abstractmethod

from dgt_constants import DgtConstants

class DgtClockMessage(ABC):
    @abstractmethod
    def get_message_data(self):
        """
        Get the data payload bytes of the clock message.

        :return: The data bytes to send to the clock. Must be non-null.
        """
        pass

    @abstractmethod
    def get_message_id(self):
        """
        Get the identifier of the message sent to the clock.

        :return: The message ID
        """
        pass

    def to_bytes(self):
        """
        Convert the message to the correct byte stream to send to the board.

        :return: The bytes to send to the board
        """
        data = self.get_message_data()

        bytes_ = bytearray(len(data) + 5)

        bytes_[0] = DgtConstants.DGT_CLOCK_MESSAGE
        bytes_[1] = len(data) + 3
        bytes_[2] = DgtConstants.DGT_CMD_CLOCK_START_MESSAGE
        bytes_[3] = self.get_message_id()

        bytes_[len(data) + 4] = DgtConstants.DGT_CMD_CLOCK_END_MESSAGE

        bytes_[4:len(data) + 4] = data

        return bytes(bytes_)


