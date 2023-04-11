import tkinter as tk
from tkinter import filedialog
from vpython import *

import click
from copy import deepcopy
import StlToGcode.Gcode
import StlToGcode.StlSlicer

# create the VPython scene
scene = canvas()

# define the function to load the G-code file
def load_Gcode_file():
    # open a file dialog box to select a file
    file_path = filedialog.askopenfilename()
    if file_path:
        # parse the G-code file
        code = StlToGcode.Gcode.parse_gcode(file_path)
        # create a 3D model of the G-code in VPython
        for i in range(len(code) - 1):
            #cylinder(pos=code[i], axis=code[i+1]-code[i], color=color.red)
            arrow(pos=code[i], axis=code[i + 1] - code[i], color=color.red)

def load_STL_file():
    file_path = filedialog.askopenfilename()

    print("Loading STL: '{}'\n".format(file_path))
    parsed, auxdata = StlToGcode.StlSlicer.parse_stl(file_path)

    if file_path:
        print("Output of parsed STL:")
        print(parsed)
        print("\nAuxiliary metadata:")
        print(auxdata)
        print("STL mesh ingestion done.\n")

    params = deepcopy(StlToGcode.StlSlicer.DEFAULT_PARAMETERS)
    sliced = StlToGcode.StlSlicer.slice_model(parsed, auxdata, params, verbose=False)
    print(sliced)
    print("Slicing done.\n")

    outpath = file_path.replace(".stl", ".gcode")
    print("Outputting to: {}".format(outpath))
    StlToGcode.Gcode.export(sliced, outpath)

    code = StlToGcode.Gcode.parse_gcode(outpath)
    # create a 3D model of the G-code in VPython
    for i in range(len(code) - 1):
        # cylinder(pos=code[i], axis=code[i+1]-code[i], color=color.red)
        pyramid(pos=code[i], axis=code[i + 1] - code[i], color=color.red)

root = tk.Tk()
root.title('G-code Viewer')
root.geometry('250x200')

load_Stl_button = tk.Button(root, text='Load STL file', command=load_STL_file)
load_Stl_button.pack(pady=20)

# run the GUI main loop
root.mainloop()