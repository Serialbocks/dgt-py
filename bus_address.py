class DgtProtocolException(Exception):
    pass

class Busadress:
    def __init__(self, data):
        if len(data) != 2:
            raise DgtProtocolException("Busadress expects exactly two bytes of data")
        self.address = (data[0] << 7) | data[1]
