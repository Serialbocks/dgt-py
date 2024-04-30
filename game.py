class Game:
    def __init__(self, moves, result):
        self.moves = moves  # Assuming moves is already an immutable list
        self.result = result

    def uci(self):
        ply = 0
        builder = []
        for m in self.moves:
            if ply % 2 == 0:
                builder.append(f"{1 + ply // 2}. {m.move.uci()}")
            else:
                builder.append(f" {m.move.uci()}\n")
            ply += 1
        self.append_result(builder)
        builder.append('\n')
        return ''.join(builder)

    def pgn(self, include_clock):
        ply = 0
        sb = []
        for m in self.moves:
            if ply % 2 == 0:
                sb.append(f"{1 + ply // 2}. {m.san}")
                if include_clock and m.clock_info is not None:
                    sb.append(f" {{[%clk {m.clock_info.left_time_string()}]}}")
            else:
                sb.append(f" {m.san}")
                if include_clock and m.clock_info is not None:
                    sb.append(f" {{[%clk {m.clock_info.right_time_string()}]}}")
                sb.append('\n')
            ply += 1
        self.append_result(sb)
        sb.append('\n')
        return ''.join(sb)

    def append_result(self, sb):
        sb.append(f" {self.result.result_string() if self.result else '*'}")
