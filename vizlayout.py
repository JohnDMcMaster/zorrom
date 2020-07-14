from zorrom.util import add_bool_arg
from zorrom import archs

from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QLinearGradient
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt

import sys


class Window(QMainWindow):
    def __init__(self, arch):
        super().__init__()
        self.title = "PyQt5 Drawing Tutorial"
        self.verbose = 0
        self.top = 1
        self.left = 1
        self.width = 1920
        self.height = 900
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)
        self.show()
        self.arch = arch

        self.mr = archs.get_arch(arch)
        self.ticks = 0
        self.rate = 1
        self.halfway = False

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
        self.ticks += int(self.rate)
        if self.ticks >= half and not self.halfway:
            self.ticks = half
            self.rate = 0.5
            self.halfway = True
        self.rate += self.rate * 0.1 + 0.02
        # print('tick %u' % self.ticks)
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        # painter.setPen(QPen(Qt.black,  5, Qt.DotLine))
        painter.setBrush(QBrush(Qt.yellow, Qt.SolidPattern))
        # painter.drawRect(10, 40, 400, 200)

        x0 = 10
        y0 = 10
        txtw, txth = self.mr.txtwh()
        self.verbose and print("Dimensions: %uw x %uh" % (txtw, txth))
        pitchx = (self.width - 2 * x0) // txtw
        pitchy = (self.height - 2 * y0) // txth
        pitchx = pitchy = min(pitchx, pitchy)
        self.verbose and print("Pitch: %u" % pitchx)

        for biti, (off, maski) in enumerate(self.mr.iter_oi()):
            if biti >= self.ticks:
                break
            if maski == 0:
                painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))

            col, row = self.mr.oi2cr(off, maski)
            x = x0 + col * pitchx
            y = y0 + row * pitchy
            painter.drawRect(x, y, pitchx, pitchy)
            self.verbose and print("0x%04X:0x%02X: %ux %uy" %
                                   (off, 1 << maski, x, y))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert ROM physical layout to binary')
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('--arch', help='Decoder to use (required)')
    args = parser.parse_args()

    App = QApplication(sys.argv)
    window = Window(args.arch)
    sys.exit(App. exec ())
