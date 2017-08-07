import time

from pylibftdi import Device


class MidiDevice(Device):
    def __init__(self, *o, **k):
        Device.__init__(self, *o, **k)
        self.baudrate = 31250


MAJOR_INTERVAL = [2, 2, 1, 2, 2, 2, 1, 2]
MINOR_INTERVAL = [2, 1, 2, 2, 1, 2, 2, 2]
START_NOTE = 48


def volume(beat):
    return 100 if beat % 2 else 127


def scale():
    midi = MidiDevice()

    note = START_NOTE
    for i in range(8):
        midi.write('\x90%c%c' % (chr(note), chr(volume(i))))
        time.sleep(0.25)
        midi.write('\x90%c\x00' % chr(note))
        note += MAJOR_INTERVAL[i]
        time.sleep(0.125)

    time.sleep(0.5)

    for i in range(8):
        note -= MINOR_INTERVAL[7 - i]
        midi.write('\x90%c%c' % (chr(note), chr(volume(i))))
        time.sleep(0.35)
        midi.write('\x90%c\x00' % chr(note))
        time.sleep(0.125)


if __name__ == '__main__':
    scale()
