from gcody import *

file = 'C:/Users/uzayi/Desktop/Ödev/CapstoneProject/simpleStlFiles/cube.gcode'
GcodeVis = read(file)
GcodeVis.slide_view()

def visualize_gcode(gcode_file):
    GcodeVis = read(gcode_file)
    GcodeVis.cbar_view()
    #GcodeVis.slide_view()


