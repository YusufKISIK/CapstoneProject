import sys
import os.path
from PyQt6.QtCore import Qt, QFile
from PyQt6.QtGui import QSurfaceFormat, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QOpenGLWidget
from stl import mesh
from numpy import cos, sin, pi


class GcodeViewer(QMainWindow):
    def _init_(self):
        super()._init_()

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Gcode Viewer")

        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)

        self.show()


class GLWidget(QOpenGLWidget):
    def _init_(self, parent):
        super()._init_(parent)

        self.setMinimumSize(800, 600)

        # Set OpenGL version and format
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(fmt)

        # Load Gcode file
        path = "C:/Users/uzayi/Desktop/Ödev/CapstoneProject/simpleStlFiles/cube.stl"
        self.mesh = self.load_gcode(path)

        # Set background color
        self.setBackgroundColor(QColor(70, 70, 70))

    def initializeGL(self):
        # Set OpenGL options
        self.gl = self.context().versionFunctions()
        self.gl.glEnable(self.gl.GL_DEPTH_TEST)
        self.gl.glClearColor(self.bg_color.red() / 255.0, self.bg_color.green() / 255.0, self.bg_color.blue() / 255.0,
                             1.0)

    def paintGL(self):
        # Clear screen
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)

        # Set up camera and lights
        self.gl.glMatrixMode(self.gl.GL_MODELVIEW)
        self.gl.glLoadIdentity()
        self.gl.glTranslatef(0, 0, -10)
        self.gl.glRotatef(30, 1, 0, 0)
        self.gl.glRotatef(self.time * 30, 0, 1, 0)

        # Draw Gcode file
        self.gl.glColor3f(1, 1, 1)
        self.mesh.draw()

    def resizeGL(self, width, height):
        # Set viewport
        self.gl.glViewport(0, 0, width, height)

        # Set orthographic projection
        self.gl.glMatrixMode(self.gl.GL_PROJECTION)
        self.gl.glLoadIdentity()
        aspect_ratio = width / height
        self.gl.glOrtho(-5 * aspect_ratio, 5 * aspect_ratio, -5, 5, 0.1, 50)

    def setBackgroundColor(self, color):
        self.bg_color = color

    def load_gcode(self, filename):
        # Load Gcode file using "pyramid-stl"
        mesh_gcode = mesh.Mesh.from_file(filename)

        # Scale and center Gcode mesh
        mesh_gcode = self.scale_mesh(mesh_gcode)
        mesh_gcode = self.center_mesh(mesh_gcode)

        return mesh_gcode

    def scale_mesh(self, mesh):
        # Scale mesh by 2
        mesh.x *= 2.0
        mesh.y *= 2.0
        mesh.z *= 2.0

        return mesh

    def center_mesh(self, mesh):
        # Center mesh around (0, 0, 0)
        cx, cy, cz = mesh.center
        mesh.x -= cx
        mesh.y -= cy
        mesh.z -= cz

        return mesh


if __name__ == '_main_':
    app = QApplication(sys.argv)
    mainWin = GcodeViewer()
    sys.exit(app.exec())