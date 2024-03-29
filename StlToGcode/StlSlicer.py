import math
import numpy as np
import GUI.UIForStl as UIForStl

DEFAULT_PARAMETERS = {
    "layer_height": 0.2,
    "nozzle_diameter": 0.1,
    "resolution": 0.5
}

infillsParam = 0.5
scaleValue = 1.0


class Triangle:
    def __init__(self, side):
        self.side = side
        self.h = math.sqrt(3) / 2 * side
        self.v1 = (0.0, 0.0)
        self.v2 = (side, 0.0)
        self.v3 = (side / 2, self.h)
        # self.center = (side/2, self.h/3)


def slice_model(parsed_stl, auxdata, params, verbose=True):
    off_x, off_y, off_z = -1.0 * auxdata["x_min"] * scaleValue, -1.0 * auxdata["y_min"] * scaleValue, -1.0 * auxdata["z_min"] * scaleValue
    if verbose:
        print("Offsets: {:+0.2f}x\t{:+0.2f}y\t{:+0.2f}z".format(off_x, off_y, off_z))
    # Sort the facets by minimum z-coordinate while applying offsets.
    parsed_stl.sort(key=lambda facet: min([vertex[2] for vertex in facet["vertices"]]))
    facets = [{"normal": d["normal"],
               "vertices": (
                   ((scaleValue * d["vertices"][0][0] + off_x), (scaleValue * d["vertices"][0][1] + off_y),
                    (scaleValue * d["vertices"][0][2] + off_z)),
                   ((scaleValue * d["vertices"][1][0] + off_x), (scaleValue * d["vertices"][1][1] + off_y),
                    (scaleValue * d["vertices"][1][2] + off_z)),
                   ((scaleValue * d["vertices"][2][0] + off_x), (scaleValue * d["vertices"][2][1] + off_y),
                    (scaleValue * d["vertices"][2][2] + off_z))
               )}
              for d in parsed_stl]
    perimeters = generate_perimeters(facets, auxdata, params)
    infill = generate_infill_and_supports(auxdata, params)
    sliced = perimeters + infill
    sliced.sort(key=lambda x: x[0][2])
    print(list.count(sliced, 0))
    return sliced


def generate_perimeters(facets, auxdata, params):
    def my_round(x, base):
        return round(base * round(float(x) / base), 1)

    perimeters = []
    z_max = my_round((auxdata["z_max"] - auxdata["z_min"]) * scaleValue, params["layer_height"])
    for z_ind in np.arange(0, z_max + params["layer_height"], params["layer_height"]):
        for facet in facets:
            min_z = min([vertex[2] for vertex in facet["vertices"]])
            max_z = max([vertex[2] for vertex in facet["vertices"]])

            # Skip this iteration if facet is all above the current z-index.
            if min_z >= z_ind + params["layer_height"]:
                continue
            # SKip this iteration if facet is all below the current z-index.
            elif max_z < z_ind:
                continue
            # Otherwise, calculate the intersection of this facet
            else:
                perimeters += intersect(facet, z_ind, params)
    return perimeters


def generate_infill_and_supports(auxdata, params):
    if infillsParam == 0:
        return []

    max_x = ((auxdata["x_max"] * scaleValue) - (auxdata["x_min"] * scaleValue))
    max_y = ((auxdata["y_max"] * scaleValue) - (auxdata["y_min"] * scaleValue))
    max_z = ((auxdata["z_max"] * scaleValue) - (auxdata["z_min"] * scaleValue))
    unit = math.sqrt(max_x * max_y  * scaleValue) * (1.00000001 - infillsParam) / (2 * math.sqrt(2))

    horiz = []
    t = Triangle(unit)
    for x_off in np.arange(0, max_x + unit * 3, unit * 3):
        horiz += [((t.v1[0] + x_off, t.v1[1]), (t.v2[0] + x_off, t.v2[1])),
                  ((t.v1[0] + x_off, t.v1[1]), (t.v3[0] + x_off, t.v3[1])),
                  ((t.v2[0] + x_off, t.v2[1]), (t.v3[0] + x_off, t.v3[1]))]

    vert = []
    for y_off in np.arange(0, max_y + unit * math.sqrt(2), unit * math.sqrt(2)):
        raw_tessellation = [((x1, y1 + y_off), (x2, y2 + y_off)) for ((x1, y1), (x2, y2)) in horiz]

        strict_in = [seg for seg in raw_tessellation if
                     0 <= seg[0][0] <= max_x and 0 <= seg[1][0] <= max_x and
                     0 <= seg[0][1] <= max_y and 0 <= seg[1][1] <= max_y]
        almost_in = [seg for seg in raw_tessellation if seg not in strict_in and
                     ((0 <= seg[0][0] <= max_x and 0 <= seg[0][1] <= max_y) or
                      (0 <= seg[1][0] <= max_x and 0 <= seg[1][1] <= max_y))]

        for ((x1, y1), (x2, y2)) in almost_in:
            x1, x2 = min(max(0, x1), max_x), min(max(0, x2), max_x)
            y1, y2 = min(max(0, y1), max_y), min(max(0, y2), max_y)
            vert.append(((x1, y1), (x2, y2)))

        vert += strict_in

    infill = []
    for z_off in np.arange(0, max_z, params["layer_height"]):
        infill += [((x1 * scaleValue, y1 * scaleValue, z_off * scaleValue), (x2 * scaleValue, y2 * scaleValue, z_off * scaleValue)) for ((x1, y1), (x2, y2)) in vert]

    return infill


def intersect(facet, z_ind, params):
    segments = []
    points_abv_layer = [vtx for vtx in facet["vertices"] if vtx[2] > z_ind + params["layer_height"]]
    points_blw_layer = [vtx for vtx in facet["vertices"] if vtx[2] < z_ind + params["layer_height"]]
    points_mid_layer = [vtx for vtx in facet["vertices"] if z_ind <= vtx[2] <= z_ind + params["layer_height"]]

    if 1.0 - params["nozzle_diameter"] / 10.00 <= abs(facet["normal"][2]) \
            <= 1.0 + params["nozzle_diameter"] / 10.00:
        vertices = [vtx for vtx in facet["vertices"]]
        x_min = min(list(map(lambda x: x[0], vertices)))
        x_max = max(list(map(lambda x: x[0], vertices)))
        y_min = min(list(map(lambda y: y[1], vertices)))
        y_max = max(list(map(lambda y: y[1], vertices)))

        if True or (z_ind / params["layer_height"]) % 2 == 0:
            lefts = [vtx for vtx in vertices if vtx[0] == x_min]
            rights = [vtx for vtx in vertices if vtx[0] == x_max]
            centers = [vtx for vtx in vertices if vtx not in lefts and vtx not in rights]

            def fill_case_1(left1, left2, right):
                xl1, yl1 = left1[0], left1[1]
                xl2, yl2 = left2[0], left2[1]
                xr, yr = right[0], right[1]

                for x_ind in np.arange(xl1, xr, params["layer_height"]):
                    t1 = (x_ind - xl1) / (xr - xl1)
                    t2 = (x_ind - xl2) / (xr - xl2)
                    segments.append((
                        (x_ind * scaleValue, (yr - yl1) * t1 + yl1 * scaleValue, z_ind * scaleValue),
                        (x_ind * scaleValue, (yr - yl2) * t2 + yl2 * scaleValue, z_ind * scaleValue),
                    ))

            def fill_case_2(left, right1, right2):
                xl, yl = left[0], left[1]
                xr1, yr1 = right1[0], right1[1]
                xr2, yr2 = right2[0], right2[1]

                for x_ind in np.arange(xl, xr1, params["layer_height"]):
                    t1 = (x_ind - xl) / (xr1 - xl)
                    t2 = (x_ind - xl) / (xr2 - xl)
                    segments.append((
                        (x_ind * scaleValue, (yr1 - yl) * t1 + yl * scaleValue, z_ind * scaleValue),
                        (x_ind * scaleValue, (yr2 - yl) * t2 + yl * scaleValue, z_ind * scaleValue),
                    ))

            if len(lefts) == 2:
                fill_case_1(lefts[0], lefts[1], rights[0])

            elif len(rights) == 2:
                fill_case_2(lefts[0], rights[0], rights[1])

            else:
                x_mid = centers[0][0]
                t = (x_mid - lefts[0][0]) / (rights[0][0] - lefts[0][0])
                y_mid = (rights[0][1] - lefts[0][1]) * t + lefts[0][1]
                midpoint = (x_mid, y_mid, z_ind)
                fill_case_2(lefts[0], centers[0], midpoint)
                fill_case_1(centers[0], midpoint, rights[0])
        else:
            for y_ind in np.arange(y_min, y_max + params["layer_height"], params["layer_height"]):
                pass

    else:
        if len(points_mid_layer) == 2:
            x1, y1, z1 = points_mid_layer[0][0], points_mid_layer[0][1], z_ind
            x2, y2, z2 = points_mid_layer[1][0], points_mid_layer[1][1], z_ind
            segments.append(((x1 * scaleValue, y1 * scaleValue, z1 * scaleValue), (x2 * scaleValue, y2 * scaleValue, z2 * scaleValue)))

        elif len(points_mid_layer) == 0:
            if len(points_blw_layer) == 2:
                px, py, pz = points_abv_layer[0][0], points_abv_layer[0][1], points_abv_layer[0][2]
                x1, y1, z1 = points_blw_layer[0][0], points_blw_layer[0][1], points_blw_layer[0][2]
                x2, y2, z2 = points_blw_layer[1][0], points_blw_layer[1][1], points_blw_layer[1][2]

            else:
                px, py, pz = points_blw_layer[0][0], points_blw_layer[0][1], points_blw_layer[0][2]
                x1, y1, z1 = points_abv_layer[0][0], points_abv_layer[0][1], points_abv_layer[0][2]
                x2, y2, z2 = points_abv_layer[1][0], points_abv_layer[1][1], points_abv_layer[1][2]

            t1 = (z_ind - pz) / (z1 - pz)
            t2 = (z_ind - pz) / (z2 - pz)

            segments.append((
                ((x1 - px) * t1 + px * scaleValue, (y1 - py) * t1 + py * scaleValue, z_ind * scaleValue),
                ((x2 - px) * t2 + px * scaleValue, (y2 - py) * t2 + py * scaleValue, z_ind * scaleValue),
            ))
    return segments


def parse_stl(stlpath):
    parsed = []
    auxdata = {
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
        "z_min": None,
        "z_max": None,
    }

    with open(stlpath, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()

            # First line of the ASCII file definition
            if line == "solid ASCII":
                continue

            # Add a new facet to the object.
            elif line.startswith("facet normal"):
                parsed.append({
                    "normal": tuple(map(float, line.split()[2:]))
                })

            # Add a point to the previously appended facet.
            elif line.startswith("vertex"):
                if "vertices" not in parsed[-1]:
                    parsed[-1]["vertices"] = []

                parsed[-1]["vertices"].append(tuple(map(float, line.split()[1:])))

                # Update auxiliary metadata parameters.
                x, y, z = parsed[-1]["vertices"][-1]

                if auxdata["x_min"] is None or x < auxdata["x_min"]:
                    auxdata["x_min"] = x
                if auxdata["x_max"] is None or x > auxdata["x_max"]:
                    auxdata["x_max"] = x

                if auxdata["y_min"] is None or y < auxdata["y_min"]:
                    auxdata["y_min"] = y
                if auxdata["y_max"] is None or y > auxdata["y_max"]:
                    auxdata["y_max"] = y

                if auxdata["z_min"] is None or z < auxdata["z_min"]:
                    auxdata["z_min"] = z
                if auxdata["z_max"] is None or z > auxdata["z_max"]:
                    auxdata["z_max"] = z

    return parsed, auxdata
