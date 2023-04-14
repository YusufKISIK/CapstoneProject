import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def visualize_gcode(gcode_file):
    """Visualizes G-code on a 3D plot that can be interactively moved."""
    x, y, z = [], [], []
    with open(gcode_file, 'r') as f:
        for line in f:
            if line.startswith('G1'):
                tokens = line.split()
                x.append(float(tokens[1][1:]))
                y.append(float(tokens[2][1:]))
                z.append(float(tokens[3][1:]))
            if line.startswith('G0'):
                tokens = line.split()
                x.append(float(tokens[0][0]))
                y.append(float(tokens[0][0]))
                z.append(float(tokens[0][0]))
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x, y, z)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.mouse_init()
    plt.show()
