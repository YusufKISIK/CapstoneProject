import math
from vpython import vector
import GUI.UIForStl as UIstl

total_move_count = 0


# define the function to parse a G-code file
def parse_gcode(filename):
    x = 0
    y = 0
    z = 0
    code = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('G1'):
                params = line.split(' ')
                for param in params:
                    if param.startswith('X'):
                        x = float(param[1:])
                    elif param.startswith('Y'):
                        y = float(param[1:])
                    elif param.startswith('Z'):
                        z = float(param[1:])
                code.append(vector(x, y, z))
    return code


def export(sliced, outpath, offset=0, g92number=0):
    global total_move_count
    f = open(outpath, "w")
    e_off = 0
    print("G0 F4320.0 X20.0 Y20.0 Z0.0", file=f)
    for (x1, y1, z1), (x2, y2, z2) in sliced:
        if e_off > 100:
            e_off = 0
            print("G92 E0", file=f)
            g92number += 1
        e_dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        offset += 1
        print("G1 X{:0.5f} Y{:0.5f} Z{:0.5f}".format(x1, y1, z1), file=f)
        print("G1 X{:0.5f} Y{:0.5f} E{:0.5f}".format(x2, y2, e_off + e_dist), file=f)
        e_off += e_dist
    total_move_count = len(sliced) + offset + g92number
    UIstl.count = float(total_move_count)
    MoveCount = total_move_count
    print(MoveCount)
    return MoveCount


def Movement():
    return total_move_count
