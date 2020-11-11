#!/usr/bin/env python3
from zorrom.util import add_bool_arg
from zorrom import archs

from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QLinearGradient
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt

import sys
import os


class Window(QMainWindow):
    def __init__(self, arch, rotate=False, rate_c1=0.1, rate_c0=0.02, rate0=0.5, reset_half=False):
        super().__init__()
        self.title = "vizlayout"
        self.verbose = 0
        self.top = 1
        self.left = 1
        self.width = 1920
        self.height = 950
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)
        self.show()
        self.arch = arch
        self.rotate = rotate

        self.mr = archs.get_arch(arch)
        self.ticks = 0
        self.rate_c1 = rate_c1
        self.rate_c0 = rate_c0
        rate0 = rate0
        self.rate = rate0
        self.halfway = False
        self.reset_half = reset_half

        def timer_chain():
            self.timer = QTimer()
            self.timer.timeout.connect(self.tick)
            self.timer.start(100)

        self.timer = QTimer()
        self.timer.timeout.connect(timer_chain)
        # self.timer.start(10000)
        self.timer.start(1)

    def tick(self):
        half = 8 * self.mr.bytes() / 2
        self.ticks += self.rate
        if self.reset_half and self.ticks >= half and not self.halfway:
            self.ticks = half
            self.rate = 0.5
            self.halfway = True
        self.rate += self.rate * self.rate_c1 + self.rate_c0
        # self.rate += self.rate * 0.0001 + 0.00002
        # print('tick %u' % self.ticks)
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        # painter.setPen(QPen(Qt.black,  5, Qt.DotLine))
        painter.setBrush(QBrush(Qt.yellow, Qt.SolidPattern))
        # painter.drawRect(10, 40, 400, 200)

        # self.verbose = True
        x0 = 10
        y0 = 10
        txtw, txth = self.mr.txtwh()
        if self.rotate:
            txtw, txth = txth, txtw
        self.verbose and print("Dimensions: %uw x %uh rom, %u x %u window" %
                               (txtw, txth, self.width, self.height))
        pitchx = (self.width - 2 * x0) // txtw
        pitchy = (self.height - 2 * y0) // txth
        pitchx = pitchy = min(pitchx, pitchy)
        self.verbose and print("Pitch: %u" % pitchx)

        for biti, (off, maski) in enumerate(self.mr.iter_oi()):
            if biti >= self.ticks:
                break
            if off == 0:
                painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))
            elif maski == 0:
                painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))

            col, row = self.mr.oi2cr(off, maski)
            if self.rotate:
                col, row = row, col
            x = x0 + col * pitchx
            y = y0 + row * pitchy
            painter.drawRect(x, y, pitchx, pitchy)
            (self.verbose or 0) and print("0x%04X:0x%02X: %ux %uy" %
                                          (off, 1 << maski, x, y))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert ROM physical layout to binary')
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('--rotate', action='store_true', help='')
    parser.add_argument('--reset-half', action='store_true', help='')
    parser.add_argument('--rate0', type=float, default=0.5, help='Bits per second at t=0')
    parser.add_argument('--rate_c0', type=float, default=0.02, help='Bits per second to add every second')
    parser.add_argument('--rate_c1', type=float, default=0.1, help='Compounding bits per second')
    parser.add_argument('--arch', help='Decoder to use (required)')
    args = parser.parse_args()

    App = QApplication(sys.argv)
    window = Window(args.arch, args.rotate, reset_half=args.reset_half, rate0=args.rate0, rate_c0=args.rate_c0, rate_c1=args.rate_c1)
    sys.exit(App. exec ())
