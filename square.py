class Square:
    A1 = 0
    C1 = 2
    D1 = 3
    F1 = 5
    G1 = 6
    H1 = 7
    A8 = 56
    H8 = 63

    @staticmethod
    def square(file, rank):
        return file ^ (rank << 3)

    @staticmethod
    def file(square):
        return square & 7

    @staticmethod
    def rank(square):
        return square >> 3

    @staticmethod
    def mirror(square):
        return square ^ 0x38

    @staticmethod
    def combine(a, b):
        return Square.square(Square.file(a), Square.rank(b))

    @staticmethod
    def distance(a, b):
        return max(abs(Square.file(a) - Square.file(b)),
                   abs(Square.rank(a) - Square.rank(b)))


