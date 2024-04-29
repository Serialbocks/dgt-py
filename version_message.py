class DgtProtocolException(Exception):
    pass

class VersionMessage:
    def __init__(self, data):
        if len(data) != 2:
            raise DgtProtocolException("Version message expects exactly two bytes of data")
        self.major = data[0]
        self.minor = data[1]
