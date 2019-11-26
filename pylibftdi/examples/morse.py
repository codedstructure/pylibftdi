"""
`morse` - pylibftdi example to generate morse code signals

Requires a bitbang-capable device with appropriate actuator (LED, buzzer etc)
connected to bit 0.
"""

from os import isatty
from time import sleep
from pylibftdi import BitBangDevice

# See https://en.wikipedia.org/wiki/Morse_code
morse_code = """
a.- b-...  c-.-.  d-..  e.  f..-.  g--.  h....  i..  j.--- k-.- l.-..  m--
n-.  o--- p.--.  q--.- r.-.  s...  t- u..- v...- w.-- x-..- y-.-- z--..
1.---- 2..--- 3...-- 4....- 5.....  6-....  7--...  8---..  9----.  0-----
"""

morse_map = {m[0]: m[1:] for m in morse_code.split()}


def output(s, device, wpm=12):
    """
    output given string `s` as a Morse code pattern to given BitBangDevice

    :param s: string to render in morse code
    :param device: open bitbangdevice
    :param wpm: words-per-minute rate. (default 12)
    """
    # Assume 5 letters per word, 13 units (e.g. 5 dots plus space) per letter
    delay = 60 / (5 * 13 * wpm)
    for word in s.split():
        for letter in word:
            morse = morse_map.get(letter)
            if not morse:
                # completely ignore unknown characters
                continue
            for symbol in morse:
                if symbol == '.':
                    device.port = 1
                    sleep(delay)
                    device.port = 0
                else:
                    device.port = 1
                    sleep(3 * delay)
                    device.port = 0
                sleep(delay)  # inter-symbol delay; 1 unit (same as dot)
            # inter-letter delay; 3 units
            sleep(3 * delay)
        # inter-word delay; 7 units
        sleep(7 * delay)


def main(wpm=12):
    """
    :param wpm: words per minute
    """
    while True:
        try:
            s = input('Morse:> ' if isatty(0) else '').lower().strip()
        except EOFError:
            break

        with BitBangDevice() as device:
            output(s, device, wpm=wpm)

    if isatty(0):
        print("Bye!")


if __name__ == '__main__':
    main()
