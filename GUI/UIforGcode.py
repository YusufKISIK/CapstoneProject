from gcody import *


def visualize_gcode(gcode_file):
    GcodeVis = read(gcode_file)
    GcodeVis.cbar_view()
    #GcodeVis.slide_view()


