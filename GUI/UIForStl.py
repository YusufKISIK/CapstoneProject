import sys
from os.path import exists

import vtk
import vtkmodules
from PyQt6.QtCore import QSettings, QSize, QPoint, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMainWindow, QApplication, QFrame, QVBoxLayout, QFileDialog, QMessageBox
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from copy import deepcopy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import StlToGcode.Gcode
import StlToGcode.StlSlicer

import UIforGcode as GcodeScreen


class MainWindow(QMainWindow):
    vtkmodules.qt.QVTKRWIBase = "QGLWidget"
    reader = vtk.vtkSTLReader()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.setAcceptDrops(True)
        self.initUI()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            link = event.mimeData().urls()[0]
            # load dropped STL
            self.loadSTL(link.toLocalFile())
        else:
            event.ignore()

    def closeEvent(self, event):
        # Write window size and position to config file
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        super().closeEvent(event)

    # GUI definition
    def initUI(self):

        self.setWindowTitle('Capstone Project By Yusuf IŞIK')
        # read window size and position from config file
        # actions definition
        openFile = QAction(QIcon('../icons/open-24.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open STL File')
        openFile.triggered.connect(self.showSTLFileDialog)

        ConvertStlToGcode = QAction(QIcon('../icons/convert.png'), 'Convert Stl To Gcode', self)
        ConvertStlToGcode.setShortcut('Ctrl+C')
        ConvertStlToGcode.setStatusTip('Convert Stl To Gcode')
        ConvertStlToGcode.triggered.connect(self.showStlConvertdialog)

        exitAction = QAction(QIcon('../icons/close-window-24.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        aboutAction = QAction(QIcon('../icons/info-24.png'), 'About', self)
        aboutAction.setStatusTip('About Capstone Project')
        aboutAction.triggered.connect(self.aboutInfo)

        # display menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        fileMenu = menubar.addMenu('&Convertor')
        fileMenu.addAction(ConvertStlToGcode)
        fileMenu = menubar.addMenu('&Help')
        fileMenu.addAction(aboutAction)

        # display toolbar
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(openFile)
        toolbar.addSeparator()
        toolbar.addAction(ConvertStlToGcode)
        toolbar.addSeparator()
        toolbar.addAction(aboutAction)
        toolbar.addSeparator()
        toolbar.addAction(exitAction)

        # display STL main window
        self.frame = QFrame()
        self.vl = QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)



        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.Initialize()
        self.iren.Start()

        # load default STL
        if len(sys.argv) > 1:
            filename = sys.argv[1]
        else:
            filename = "../simpleStlFiles/3mmBox.stl"
        file_exists = exists(filename)
        if file_exists:
            self.loadSTL(filename)

        # set main window
        # Load window size and position from settings
        self.settings = QSettings('Capstone Project', 'MainWindow')
        # Initial window size/pos last saved. Use default values for first time
        self.resize(self.settings.value("size", QSize(1080, 720)))
        self.move(self.settings.value("pos", QPoint(200, 200)))


        self.show()

    def slice_STL_file(self, filename):

        self.reader.SetFileName(filename)
        print(filename)
        parsed, auxdata = StlToGcode.StlSlicer.parse_stl(filename)

        if filename:
            print("Output of parsed STL:")
            print(parsed)
            print("\nAuxiliary metadata:")
            print(auxdata)
            print("STL mesh ingestion done.\n")

        params = deepcopy(StlToGcode.StlSlicer.DEFAULT_PARAMETERS)
        sliced = StlToGcode.StlSlicer.slice_model(parsed, auxdata, params, verbose=False)
        print(sliced)
        print("Slicing done.\n")

        outpath = filename.replace(".stl", ".gcode")
        print("Outputting to: {}".format(outpath))
        StlToGcode.Gcode.export(sliced, outpath)
        GcodeScreen.visualize_gcode(outpath)

    # load STL file
    def loadSTL(self, filename):
        # Create source
        self.reader.SetFileName(filename)

        transform = vtk.vtkTransform()
        transformFilter = vtk.vtkTransformPolyDataFilter()
        transformFilter.SetTransform(transform)
        transformFilter.SetInputConnection(self.reader.GetOutputPort())
        transformFilter.Update()

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.reader.GetOutputPort())

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.ren.AddActor(actor)
        self.ren.ResetCamera()
        self.vtkWidget.repaint()



    # display STL file selection dialog
    def showSTLFileDialog(self):
        filename = QFileDialog.getOpenFileName(self)
        if filename[0] != "":
            f = open(filename[0], 'r')
            with f:
                self.loadSTL(str(filename[0]))

    def showStlConvertdialog(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', '', 'STL (*.stl)')
        if filename[0] != "":
            f = open(filename[0], 'r')
            with f:
                self.slice_STL_file(str(filename[0]))

    def aboutInfo(self):
        QMessageBox.about(self, "About",
                          "<h3>Capstone Project By Yusuf IŞIK</h3>"
                          "Copyright &#169;Yusuf IŞIK")
    def resetCamera(self):
        self.ren.ResetCamera()
        self.vtkWidget.repaint()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.setWindowIcon(QIcon('../icons/main.png'))
    window.setWindowIcon(QIcon('../icons/main.png'))
    sys.exit(app.exec())


