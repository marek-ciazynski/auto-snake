from __future__ import annotations
from typing import Tuple
from enum import Enum
import os

ESC = '\033'
CSI = f'{ESC}['


# TODO remove
def esc_code(seq):
    print(CSI + seq)


def get_term_size() -> Tuple[int, int]:
    stty_size = os.popen('stty size', 'r').read().split()
    return tuple(map(int, stty_size))[::-1]


# TODO move to Control class
def set_cursor_position(x, y):
    esc_code(f'{y};{x}H')


# TODO rename?
class Control(Enum):
    clear = '2J'
    hide_cursor = '?25l'
    show_cursor = '?25h'

    @staticmethod
    def esc_code(seq):
        print(CSI + seq)

    def __call__(self):
        self.esc_code(self.value)


class Color(Enum):
    Reset = '0m'
    Bold = '1m'
    Dim = '2m'

    @staticmethod
    def color_seq(color: Color):
        return CSI + color.value

    def text(self, content: str):
        return self.color_seq(self) + content + self.color_seq(self.Reset)
