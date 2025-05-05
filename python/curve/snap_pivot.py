import maya.cmds as cmds
import math


def get_bounding_box():
    node = cmds.ls(sl=True)
    boundingbox = cmds.exactWorldBoundingBox(node)
    return boundingbox


def get_points(curve):
    points = cmds.ls(f"{curve}.cv[*]", fl=True)

    return points


def get_point_positions(points):
    pos_dict = {}
    point_positions = []
    for point in points:
        pos = cmds.xform(point, q=True, t=True, ws=True)
        point_positions.append(pos)

        pos_dict[point] = pos
    
    return pos_dict


def classify_faces(vertices, tolerance=1e-6):
    def close(a, b):
        return abs(a - b) <= tolerance

    # 軸ごとの最大・最小を取得
    max_y = max(v[1] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_x = min(v[0] for v in vertices)
    max_z = max(v[2] for v in vertices)
    min_z = min(v[2] for v in vertices)

    faces = {
        "top": [v for v in vertices if close(v[1], max_y)],
        "bottom": [v for v in vertices if close(v[1], min_y)],
        "right": [v for v in vertices if close(v[0], max_x)],
        "left": [v for v in vertices if close(v[0], min_x)],
        "front": [v for v in vertices if close(v[2], max_z)],
        "back": [v for v in vertices if close(v[2], min_z)],
    }

    return faces


def cross(u, v):
    return [
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    ]


def normalize(v):
    length = math.sqrt(sum(x**2 for x in v))
    return [x / length for x in v] if length > 0 else [0, 0, 0]


def compute_normal(p0, p1, p2):
    u = [p1[i] - p0[i] for i in range(3)]
    v = [p2[i] - p0[i] for i in range(3)]
    normal = cross(u, v)
    return normalize(normal)


def deduplicate(vertices, precision=6):
    seen = set()
    result = []
    for v in vertices:
        # 少数誤差対策：丸めてからタプル化
        key = tuple(round(coord, precision) for coord in v)
        if key not in seen:
            seen.add(key)
            result.append(v)
    return result


def get_cube_normal(cube_faces):
    up_vector = compute_normal(*cube_faces["top"][:3])
    side_vector = compute_normal(*cube_faces["right"][:3])
    front_vector = compute_normal(*cube_faces["front"][:3])

    return up_vector, side_vector, front_vector


def main():
    points = get_points("curveShape2")
    print(points)
    point_positions = get_point_positions(points)
    print(point_positions)

    faces = classify_faces(point_positions.values())
    for face in faces:
        faces[face] = deduplicate(faces[face])
    print(faces)

    up_vector, side_vector, front_vector = get_cube_normal(faces)
    vectors = [up_vector, side_vector, front_vector]
    print(vectors)