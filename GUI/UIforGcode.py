import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import requests
from gcody import *

g = gcode()

#file = 'C:/Users/uzayi/Desktop/Ödev/CapstoneProject/simpleStlFiles/3mmBox.gcode'


def visualize_gcode(gcode_file):
    GcodeVis = read(gcode_file)
    GcodeVis.cbar_view()  # This method takes ~60 seconds to work.


