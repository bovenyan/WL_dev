import sys
import tty
import termios


class pressKey:
    def __call__(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def press():
    inkey = pressKey()
    status = 0
    while(1):
        k = inkey()
        if k == '':
            continue
        if (ord(k) == 113):
            return 5   # 'p' for taking picture
        if (ord(k) == 3 or ord(k) == 4):
            return 0   # Ctrl+C  Ctrl+D  for exit
        if (ord(k) == 27):
            if status == 1:
                return 0   # ESC  for exit
            status = 1
            continue
        if (ord(k) == 91 and status == 1):  # moving
            status = 2
            continue
        if (ord(k) == 65 and status == 2):  # move up
            return 1
        if (ord(k) == 66 and status == 2):  # move down
            return 2
        if (ord(k) == 68 and status == 2):  # move left
            return 3
        if (ord(k) == 67 and status == 2):  # move right
            return 4
        status = 0
