from pathlib import Path
from re import search
from typing import List

from .core import (
    Slic3rCurveRepresentable,
    Slic3rRepresentable,
    Slic3rLineRepresentable,
    Slic3rPointRepresentable,
)
from .settings import LINE_MARKUP_TYPE, POINT_MARKUP_TYPE, CURVE_MARKUP_TYPE
from .types import Float3VectorType

def convert(representable: Slic3rRepresentable) -> Slic3rPointRepresentable:
    result = _PointImplementation()
    for markup in representable.mrk_obj.markups:
        for point in markup:
            result.points.append(point)
    return result

def convert_file(filename: Path) -> Slic3rPointRepresentable:
    if _PointImplementation.contains_points(filename):
        representable = _PointImplementation()
    elif _LineImplementation.contains_lines(filename):
        representable = _LineImplementation()
    elif _CurveImplementation.contains_curves(filename):
        representable = _CurveImplementation()
    else:
        raise NotImplementedError

    representable.read(filename)
    return convert(representable)

class _PointImplementation(Slic3rPointRepresentable):
    def __init__(self) -> None:
        super().__init__()
        self.points: Float3VectorType = []

    def get_point(self, id_: int) -> Float3VectorType:
        assert 0 <= id_ < len(self.points)
        return self.points[id_]

    @property
    def point_count(self) -> int:
        return len(self.points)

    @staticmethod
    def contains_points(filename: Path):
        with open(filename, "r", encoding="utf-8") as file:
            return search(
                f'"type": "{POINT_MARKUP_TYPE}",', "\n".join(file.readlines())
            ) is not None

class _LineImplementation(Slic3rLineRepresentable):
    def __init__(self) -> None:
        super().__init__()
        self.lines: Float3VectorType = []

    def get_line(self, id_: int) -> List[Float3VectorType]:
        assert 0 <= id_ < len(self.lines)
        return self.lines[id_]

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
        self.curves: Float3VectorType = []

    def get_curve(self, id_: int) -> List[Float3VectorType]:
        assert 0 <= id_ < len(self.curves)
        return self.curves[id_]

    @property
    def curve_count(self) -> int:
        return len(self.curves)

    @staticmethod
    def contains_curves(filename: Path):
        with open(filename, "r", encoding="utf-8") as file:
            return search(
                f'"type": "{CURVE_MARKUP_TYPE}",', "\n".join(file.readlines())
            ) is not None

if __name__ == "__main__":
    convert_file(Path("src/slic3r_display/data/OC.mrk.json")).print()
