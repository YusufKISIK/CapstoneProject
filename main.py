import sys

import StlToGcode.Gcode
import StlToGcode.StlSlicer
import GUI.UIForStl as Screen

from PyQt6.QtWidgets import  QApplication
from PyQt6.QtGui import QIcon



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Screen.MainWindow()
    app.setWindowIcon(QIcon('../icons/main.png'))
    window.setWindowIcon(QIcon('../icons/main.png'))
    sys.exit(app.exec())