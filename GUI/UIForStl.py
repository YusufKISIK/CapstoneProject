import sys
from os.path import exists
import numpy as np
import vtk
import vtkmodules
from PyQt6.QtCore import QSettings, QSize, QPoint, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMainWindow, QApplication, QFrame, QVBoxLayout, QFileDialog, QMessageBox, QLineEdit, \
    QStatusBar, QToolBar, QButtonGroup, QGroupBox, QCheckBox, QHBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from copy import deepcopy
import StlToGcode.Gcode as Gcode
import StlToGcode.StlSlicer as StlSlicer
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

        refreshAction = QAction(QIcon('../icons/refresh.png'), 'About', self)
        refreshAction.setStatusTip('Refresh Time Data')
        refreshAction.triggered.connect(self.showSelectedTimeData)

        self.textboxScale = QLineEdit(self)
        self.textboxScale.setReadOnly(True)

        self.textboxInfill = QLineEdit(self)
        self.textboxInfill.setReadOnly(True)

        self.textboxTimeData = QLineEdit(self)
        self.textboxTimeData.setReadOnly(True)

        # Create the checkboxes
        self.cb1 = QCheckBox("0.5", self)
        self.cb2 = QCheckBox("1", self)
        self.cb3 = QCheckBox("2", self)
        self.cb4 = QCheckBox("3", self)
        self.cbinfil1 = QCheckBox("0.3", self)
        self.cbinfil2 = QCheckBox("0.5", self)
        self.cbinfil3 = QCheckBox("0.7", self)

        # Add the checkboxes to a group so that only one can be selected at a time
        self.cb_group = QButtonGroup(self)
        self.cb_group.addButton(self.cb1)
        self.cb_group.addButton(self.cb2)
        self.cb_group.addButton(self.cb3)
        self.cb_group.addButton(self.cb4)
        self.cb_group.setExclusive(True)
        self.cb_group.buttonClicked.connect(self.showSelectedValue)

        self.cbinfill_group = QButtonGroup(self)
        self.cbinfill_group.addButton(self.cbinfil1)
        self.cbinfill_group.addButton(self.cbinfil2)
        self.cbinfill_group.addButton(self.cbinfil3)
        self.cbinfill_group.setExclusive(True)
        self.cbinfill_group.buttonClicked.connect(self.showSelectedInfillValue)

        self.cbtime_group = QButtonGroup(self)
        self.cbtime_group.buttonClicked.connect(self.showSelectedTimeData)

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
        fileMenu.addSeparator()

        # display toolbar
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(openFile)
        toolbar.addSeparator()
        toolbar.addAction(ConvertStlToGcode)
        toolbar.addSeparator()
        toolbar.addAction(aboutAction)
        toolbar.addSeparator()
        toolbar.addAction(exitAction)
        toolbar.addSeparator()
        # Create a toolbar and add the checkboxes to it
        toolbar = self.addToolBar('Scale')
        toolbar.addWidget(self.cb1)
        toolbar.addWidget(self.cb2)
        toolbar.addWidget(self.cb3)
        toolbar.addWidget(self.cb4)
        toolbar.addSeparator()
        toolbar.addWidget(self.textboxScale)
        toolbar.addSeparator()
        toolbar.addWidget(self.cbinfil1)
        toolbar.addWidget(self.cbinfil2)
        toolbar.addWidget(self.cbinfil3)
        toolbar.addSeparator()
        toolbar.addWidget(self.textboxInfill)
        toolbar.addSeparator()
        toolbar.addAction(refreshAction)
        toolbar.addWidget(self.textboxTimeData)

        # create toolbar and add actions
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # display statusbar
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
        parsed, auxdata = StlSlicer.parse_stl(filename)

        if filename:
            print("Output of parsed STL:")
            print(parsed)
            print("\nAuxiliary metadata:")
            print(auxdata)
            print("STL mesh ingestion done.\n")

        params = deepcopy(StlSlicer.DEFAULT_PARAMETERS)
        sliced = StlSlicer.slice_model(parsed, auxdata, params, verbose=False)
        print(sliced)
        print("Slicing done.\n")

        outpath = filename.replace(".stl", ".gcode")
        print("Outputting to: {}".format(outpath))
        Gcode.export(sliced, outpath)
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
        filename = QFileDialog.getOpenFileName(self, 'Open file', '', 'STL (*.stl)')
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

    def showSelectedValue(self, checkbox):
        if checkbox.isChecked():
            self.textboxScale.setText(
                "* with " + checkbox.text() + " mm x " + checkbox.text() + " mm x " + checkbox.text() + " mm")
        else:
            self.textboxScale.clear()
        StlSlicer.scaleValue = float(checkbox.text())

    def showSelectedInfillValue(self, checkbox):
        if checkbox.isChecked():
            self.textboxInfill.setText("Infill Rate = " + checkbox.text())
        else:
            self.textboxInfill.clear()
        StlSlicer.infillsParam = float(checkbox.text())

    def showSelectedTimeData(self):
        self.textboxTimeData.setText("Total Move = " + str(Gcode.MoveCount))
        print("Total Move = " + str(Gcode.MoveCount))

    def resetCamera(self):
        self.ren.ResetCamera()
        self.vtkWidget.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.setWindowIcon(QIcon('../icons/main.png'))
    window.setWindowIcon(QIcon('../icons/main.png'))
    sys.exit(app.exec())
