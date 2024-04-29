class DgtProtocolException(Exception):
    def __init__(self, msg, e=None):
        super().__init__(msg)
        if e is not None:
            super().__init__(msg, e)
