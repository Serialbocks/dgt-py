import datetime

class EEMoves:
    EE_POWERUP = 0x6a
    EE_EOF = 0x6b
    EE_FOURROWS = 0x6c
    EE_EMPTYBOARD = 0x6d
    EE_DOWNLOADED = 0x6e
    EE_BEGINPOS = 0x6f
    EE_BEGINPOS_ROT = 0x7a
    EE_START_TAG = 0x7b
    EE_WATCHDOG_ACTION = 0x7c
    EE_FUTURE_1 = 0x7d
    EE_FUTURE_2 = 0x7e
    EE_NOP = 0x7f
    EE_NOP2 = 0x00

    def __init__(self, data):
        events = []
        i = 0
        while i < len(data):
            value = data[i]
            if (0x6a <= value <= 0x6f) or (0x7a <= value <= 0x7f) or value == 0x00:
                events.append(self.SimpleEvent(value))
                i += 1
            elif 0x40 <= value <= 0x5f:
                if i + 1 >= len(data):
                    break
                events.append(self.FieldEvent(value & 0x0f, data[i+1]))
                i += 2
            elif (0x60 <= value <= 0x69) or (0x70 <= value <= 0x79):
                if i + 2 >= len(data):
                    break
                events.append(self.ClockEvent((value & 0x10) == 0x10, value & 0x0f, data[i+1], data[i+2]))
                i += 3
            else:
                i += 1

        self.events = events

    def visitEvents(self, visitor):
        for e in self.events:
            if isinstance(e, self.SimpleEvent):
                simpleEvent = e
                if simpleEvent.type == self.EE_POWERUP:
                    visitor.powerup()
                elif simpleEvent.type == self.EE_EOF:
                    visitor.eof()
                elif simpleEvent.type == self.EE_FOURROWS:
                    visitor.fourRows()
                elif simpleEvent.type == self.EE_EMPTYBOARD:
                    visitor.emptyBoard()
                elif simpleEvent.type == self.EE_DOWNLOADED:
                    visitor.downloaded()
                elif simpleEvent.type == self.EE_BEGINPOS:
                    visitor.initialPosition(False)
                elif simpleEvent.type == self.EE_BEGINPOS_ROT:
                    visitor.initialPosition(True)
                elif simpleEvent.type == self.EE_START_TAG:
                    visitor.startTag()
                elif simpleEvent.type == self.EE_WATCHDOG_ACTION:
                    visitor.watchdogAction()
                elif simpleEvent.type == self.EE_NOP or simpleEvent.type == self.EE_NOP2:
                    pass
                elif simpleEvent.type == self.EE_FUTURE_1:
                    visitor.future1()
                elif simpleEvent.type == self.EE_FUTURE_2:
                    visitor.future2()
                else:
                    raise Exception(f"Unknown simple event code 0x{simpleEvent.type:x}")
            elif isinstance(e, self.ClockEvent):
                clockEvent = e
                visitor.clockUpdate(clockEvent)
            elif isinstance(e, self.FieldEvent):
                fieldEvent = e
                visitor.fieldUpdate(fieldEvent)
            else:
                raise Exception(f"Unknown event class {e.__class__.__name__}")

    class SimpleEvent:
        def __init__(self, type):
            self.type = type

    class FieldEvent:
        def __init__(self, piece, field):
            self.square = field
            self.role = piece

    class ClockEvent:
        def __init__(self, isLeft, hours, minutes, seconds):
            self.isLeft = isLeft
            self.time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

    class Visitor:
        def fieldUpdate(self, event):
            pass

        def clockUpdate(self, event):
            pass

        def powerup(self):
            pass

        def eof(self):
            pass

        def fourRows(self):
            pass

        def emptyBoard(self):
            pass

        def downloaded(self):
            pass

        def initialPosition(self, rotated):
            pass

        def startTag(self):
            pass

        def watchdogAction(self):
            pass

        def future1(self):
            pass

        def future2(self):
            pass
