from pathlib import Path
from re import search
from typing import List

from .core import (
    Slic3rCurveRepresentable,
    Slic3rRepresentable,
    Slic3rLineRepresentable,
    Slic3rPointRepresentable,
)
from .markup import ControlPoint
from .settings import (
    LINE_MARKUP_TYPE,
    POINT_MARKUP_TYPE,
    CLOSED_CURVE_MARKUP_TYPE,
    CURVE_MARKUP_TYPE,
)
from .types import Float3VectorType

def convert(representable: Slic3rRepresentable) -> Slic3rPointRepresentable:
    """
    Convert any instance of an implementation of Slic3rRepresentable into a dummy
    Slic3rPointRepresentable implementation's instance.

    Keyword arguments:
    representable - an instance of an inheriting class of any Slic3rRepresentable.
    """
    result = _PointImplementation()
    for markup in representable.mrk_obj.markups:
        for point in markup:
            result.points.append(point.position)
    return result

def concatenate(*representables: Slic3rRepresentable) -> Slic3rPointRepresentable:
    """
    Return a single instance of a dummy Slic3rPointRepresentable implementation, containing
    points of any number of Slic3rRepresentables.

    Keyword arguments:
    representables - argument list containing one or more instances of an inheriting class of any
                     Slic3rRepresentable. All instances must be of the same type.
    """
    assert len(representables) > 0
    assert all(type(r) is type(representables[0]) for r in representables)

    result = _PointImplementation()
    for representable in representables:
        representable._update_markups()
        for markup in representable.mrk_obj.markups:
            for point in markup:
                result.points.append(point.position)
    return result

def convert_file(filename: Path, swap_coordinate_system: bool=False) -> Slic3rPointRepresentable:
    """
    Convert a 3D Slic3r .mrk.json markups file ino a dummy Slic3rPointRepresentable instance.

    Keyword arguments:
    filename - path to an existing .mrk.json file as created by 3D Slic3r.
    """
    if _PointImplementation.contains_points(filename):
        representable = _PointImplementation()
    elif _LineImplementation.contains_lines(filename):
        representable = _LineImplementation()
    elif _CurveImplementation.contains_curves(filename):
        representable = _CurveImplementation()
    else:
        raise NotImplementedError

    representable.read(filename)
    for markup in representable.mrk_obj.markups:
        if isinstance(representable, _LineImplementation):
            representable.lines.append([p.position for p in markup])
        elif isinstance(representable, _CurveImplementation):
            representable.curves.append([p.position for p in markup])
        else:
            for point in markup:
                representable.points.append(point.position)

    if swap_coordinate_system:
        print(representable.curves)
        representable.swap_coordinate_system()
        print(representable.curves)
    return convert(representable)

def concatenate_files(*filenames: Path, swap_coordinate_system: bool=False) -> Slic3rPointRepresentable:
    """
    Return a single instance of a dummy Slic3rPointRepresentable implementation, containing
    points of any number of Slic3rRepresentables, read from disc.

    Keyword arguments:
    representables - argument list containing one or more filenames to existing .mrk.json files
                     of the same type as created by 3D Slic3r.
    """
    if not swap_coordinate_system:
        return concatenate(*[convert_file(filename) for filename in filenames])

    representables = []
    for filename in filenames:
        representable = convert_file(filename)
        representable.swap_coordinate_system()
        representables.append(representable)
    return concatenate(*representables)

class _PointImplementation(Slic3rPointRepresentable):
    def __init__(self) -> None:
        super().__init__()
        self.points: Float3VectorType = []

    def get_point(self, id_: int) -> Float3VectorType:
        assert 0 <= id_ < len(self.points)
        return self.points[id_]

    def swap_coordinate_system(self) -> None:
        self.points = [self.swap_coordinate_system_for(p) for p in self.points]

    @property
    def point_count(self) -> int:
        return len(self.points)

    @staticmethod
    def contains_points(filename: Path):
        with open(filename, "r", encoding="utf-8") as file:
            return search(
                f'"type": "{POINT_MARKUP_TYPE}",', "\n".join(file.readlines())
            ) is not None

    @staticmethod
    def swap_coordinate_system_for(point: ControlPoint) -> ControlPoint:
        position = point.position
        position[:] = -position[0], -position[1], position[2]
        return point

class _LineImplementation(Slic3rLineRepresentable):
    def __init__(self) -> None:
        super().__init__()
        self.lines: List[Float3VectorType] = []

    def get_line(self, id_: int) -> List[Float3VectorType]:
        assert 0 <= id_ < len(self.lines)
        return self.lines[id_]

    def swap_coordinate_system(self) -> None:
        for line in self.lines:
            line[:] = [_PointImplementation.swap_coordinate_system_for(p) for p in line]

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @staticmethod
    def contains_lines(filename: Path):
        with open(filename, "r", encoding="utf-8") as file:
            return search(f'"type": "{LINE_MARKUP_TYPE}",', "\n".join(file.readlines())) is not None

class _CurveImplementation(Slic3rCurveRepresentable):
    def __init__(self) -> None:
        super().__init__()
        self.curves: List[Float3VectorType] = []

    def get_curve(self, id_: int) -> List[Float3VectorType]:
        assert 0 <= id_ < len(self.curves)
        return self.curves[id_]

    @property
    def curve_count(self) -> int:
        return len(self.curves)

    def swap_coordinate_system(self) -> None:
        for curve in self.curves:
            curve[:] = [_PointImplementation.swap_coordinate_system_for(p) for p in curve]

    @staticmethod
    def contains_curves(filename: Path):
        with open(filename, "r", encoding="utf-8") as file:
            return search(
                f'"type": "{CURVE_MARKUP_TYPE}|{CLOSED_CURVE_MARKUP_TYPE}",',
                "\n".join(file.readlines()),
            ) is not None

if __name__ == "__main__":
    convert_file(Path("src/slic3r_display/data/OC.mrk.json")).print()
