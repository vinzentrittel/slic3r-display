"""
Slic3r Representation abstract base classes reside here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from os.path import dirname
from pathlib import Path
from sys import stdout
from typing import Any, List, TextIO, Tuple
from json import JSONEncoder, dumps

from stl.mesh import Mesh
from numpy import array
from numpy.linalg import norm

from .markup import ControlPoint, LineMarkup, Markup, PointMarkup
from .types import Float3VectorType

@dataclass
class MrkClass:
    """ Wrapper around list of Markups """
    markups: List[Markup] = field(default_factory=list)


class MrkClassEncoder(JSONEncoder):
    """ Class for providing JSON pretty-printing for MrkClass objects """
    def default(self, o: Any) -> Any:
        """ Return 'obj' as json representation. """
        if isinstance(o, MrkClass):
            obj_dict = asdict(o)
            obj_dict["@schema"] = "https://raw.githubusercontent.com/slicer/slicer/master/Modules/Loadable/Markups/Resources/Schema/markups-schema-v1.0.3.json#"
            return obj_dict
        return super().default(o)


class Slic3rRepresentable(ABC):
    """
    Abstract base class for 3D objects that need representation in 3D Slic3r.

    Implement _update_markups() and Slic3rRepresentable.make_from(list), to instantiate
    a derived class.
    """
    def __init__(self) -> None:
        self.mrk_obj = MrkClass()

    @abstractmethod
    def _update_markups(self) -> None:
        """
        This function is called automatically prior to calls to write and print. Set up your
        MrkClass objects here.
        """

    @staticmethod
    @abstractmethod
    def make_from(point_arrangements: List) -> str:
        """
        Return JSON string from one or more lists of 3D enpoints, that can be interpreted as 3D
        Markup files.

        Keyword arguments:
        point_arrangements - Set of points, to create markups from.
        """

    def write(self, filename: Path) -> None:
        """
        Save 3D Slic3r interpretable markup representation to drive, at path 'filename'.
        
        Keyword arguments:
        filename - System path, where the JSON string will be written at.
        """
        try:
            with open(filename, "w", encoding="utf-8") as file:
                self.print(outfile=file)
        except Exception:
            print(f"Could not write to '{filename}'")

    def print(self, outfile: TextIO=stdout) -> None:
        """
        Write 3D Slic3r interpretable markup representation to stdout (or another file object).

        Keyword arguments:
        outfile - File object, where the JSON string will be printed to (default: stdout)
        """
        self._update_markups()
        print(dumps(self.mrk_obj, cls=MrkClassEncoder, indent=2), file=outfile)

    @classmethod
    def print_from(cls, point_arrangements: List, outfile: TextIO=stdout) -> None:
        """
        Print JSON string from one or more lists of 3D enpoints, that can be interpreted
        as 3D Markup files. The outfile will contain one or more line markups, according
        to point_arrangements parameters lenght.

        Keyword arguments:
        point_arrangements - example:
            point_arrangements=[ [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
                                 [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0]] ]
        outfile - File object, where the JSON string will be printed to (default: stdout)
        """
        print(cls.make_from(point_arrangements), file=outfile)

    @classmethod
    def write_from(cls, point_arrangements: List, filename: Path) -> None:
        """
        Write JSON string from one or more lists of 3D enpoints, that can be interpreted
        as 3D Markup files. The file will contain one or more line markups, according to
        point_arrangements parameters lenght.

        Keyword arguments:
        point_arrangements - example:
            point_arrangements=[ [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
                                 [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0]] ]
        filename - System path, where the JSON string will be written at.
        """
        try:
            with open(filename, "w", encoding="utf-8") as file:
                cls.print_from(point_arrangements, outfile=file)
        except Exception:
            print(f"Could not write to '{filename}'")

class Slic3rPointRepresentable(Slic3rRepresentable):
    """
    Abstract class providing print methods.
    
    Member methods:
    write - Save 3D Slic3r interpretable fiducial markup representation to drive.
    print - Write 3D Slic3r interpretable fiducial markup representation to stdout
            (or another file object).

    Static methods:
    make_from - Returns JSON string of 3D Slic3r interpretable points on the fly.
    print_from - Print JSON string of 3D Slic3r interpretable points on the fly.
    write_from - Write JSON string of 3D Slic3r interpretable points on the fly,
                 to a location on your drive.

    Pure virtual functions (aka override these):
    point_count (property) - Return the number of supplied points by derived class.
    get_point(int) - Return the control point (aka. coordinate) with 'id' as supplied by parameter.
    """
    @property
    @abstractmethod
    def point_count(self) -> int:
        """
        Return the number of supplied control points (aka. coordinates) by derived class.
        ! Implement this in your derived class !
        """

    @abstractmethod
    def get_point(self, id_: int) -> Float3VectorType:
        """
        Return the control pointrs with 'id' as supplied by parameter.
        ! Implement this in your derived class !

        Keyword arguments:
        id - zero based index, specifying the desired control point (aka. coordinate), to be
             returned.
        """

    def _update_markups(self) -> None:
        """
        Create new point markup from the coordinates provided by the derived classes
        virtual functions 'point_count' and 'get_point(int)'.
        """
        markup = PointMarkup()
        for id_ in range(self.point_count):
            markup.add(self.get_point(id_), id_=id_ + 1)
        self.mrk_obj.markups = [markup]

    @staticmethod
    def make_from(point_arrangements: List) -> Slic3rPointRepresentable:
        """
        Return JSON string from one or more 3D control points, that can be interpreted
        as 3D Markup files. The file will contain a fiducial markup. Its number of points
        corresponds to 'point_arrangements' parameter's length.

        Keyword arguments:
        point_arrangements - example:
            point_arrangements=[ [1.0, 0.0, 0.0],
                                 [2.0, 0.0, 0.0],
                                 [3.0, 0.0, 0.0],
                                 [4.0, 0.0, 0.0] ]
        """
        assert isinstance(point_arrangements, Iterable)
        if len(point_arrangements) == 0:
            return ""
        assert all(len(point) == 3 for point in point_arrangements)
        assert all(isinstance(value, float) for point in point_arrangements for value in point)

        markups = [
            PointMarkup(controlPoints=[
                ControlPoint.make_control_point(
                    id_, label=f"P_{id_ + 1}", x=point[0], y=point[1], z=point[2]
                )
                for id_, point in enumerate(point_arrangements)
            ])
        ]
        return dumps(MrkClass(markups), cls=MrkClassEncoder, indent=2)

class Slic3rLineRepresentable(Slic3rRepresentable):
    """
    Abstract class providing print methods.
    
    Member methods:
    write - Save 3D Slic3r interpretable line markup representation to drive.
    print - Write 3D Slic3r interpretable line markup representation to stdout
            (or another file object).

    Static methods:
    make_from - Returns JSON string of 3D Slic3r interpretable line on the fly.
    print_from - Print JSON string of 3D Slic3r interpretable line on the fly.
    write_from - Write JSON string of 3D Slic3r interpretable line on the fly,
                 to a location on your drive.

    Pure virtual functions (aka override these):
    line_count (property) - Return the number of supplied lines by derived class.
    get_line(int) - Return the endpoints for line with 'id' as supplied by parameter.
    """
    @property
    @abstractmethod
    def line_count(self) -> int:
        """
        Return the number of supplied lines by derived class.
        ! Implement this in your derived class !
        """

    @abstractmethod
    def get_line(self, id_: int) -> Tuple[Float3VectorType, Float3VectorType]:
        """
        Return the endpoints for line with 'id' as supplied by parameter.
        ! Implement this in your derived class !

        Result: Two-tuple of lists of 3 float values, i.e.
                ([1.0, 0.0, 0.0], [2.0, 0.0, 0.0],)

        Keyword arguments:
        id - zero based index, specifying the desired line, to be returned.
        """

    def _update_markups(self) -> None:
        """
        Create new line markups from the lines provided by the derived classes
        virtual functions 'line_count' and 'get_line(int)'.
        """
        self.mrk_obj.markups = [LineMarkup() for _ in range(self.line_count)]
        for id_, line in enumerate(self.mrk_obj.markups):
            first_point, second_point = self.get_line(id_)
            line.add(first_point, id_=id_ + 1)
            line.add(second_point, id_=id_ + 1)

    @staticmethod
    def make_from(point_arrangements: List) -> str:
        """
        Return JSON string from one or more lists of 3D enpoints, that can be interpreted
        as 3D Markup files. The file will contain one or more line markups, according to
        point_arrangements parameters lenght.

        Keyword arguments:
        point_arrangements - example:
            point_arrangements=[ [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
                                 [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0]] ]
        """
        assert isinstance(point_arrangements, Iterable)
        if len(point_arrangements) == 0:
            return ""
        assert all(isinstance(line, Iterable) for line in point_arrangements)
        assert all(len(line) == 2 for line in point_arrangements)
        assert all(len(point) == 3 for line in point_arrangements for point in line)
        assert all(
            isinstance(value, float)
            for line in point_arrangements
            for point in line
            for value in point
        )

        markups = [
            LineMarkup(controlPoints=[
                ControlPoint.make_control_point(
                    1, label=f"L_{id_ + 1}", x=line[0][0], y=line[0][1], z=line[0][2]
                ),
                ControlPoint.make_control_point(
                    2, label=f"L_{id_ + 1}", x=line[1][0], y=line[1][1], z=line[1][2]
                ),
            ])
            for id_, line in enumerate(point_arrangements)
        ]
        return dumps(MrkClass(markups), cls=MrkClassEncoder, indent=2)

class Slic3rBoxRepresentable(Slic3rRepresentable):
    """
    Abstract class providing STL write methods.
    
    Member methods:
    write - Write a STL representation of this box.

    Static methods:
    write_from - Write a STL representation of this box on the fly, to a location on your drive.

    Pure virtual functions (aka override these):
    origin (property) - Return the 3D float vector of the subclasses minimal point in all axis
                        directions.
    get_axis(int) - Return an arbitrarily sized axis as 3D float vector.
    """
    UnitCubePath = Path(dirname(__file__), "data", "B.stl")

    @property
    @abstractmethod
    def origin(self) -> Float3VectorType:
        """
        Return the 3D float vector of the subclasses minimal point in all axis directions.
        ! Implement this in your derived class !
        """

    @abstractmethod
    def get_axis(self, id_: int) -> Float3VectorType:
        """
        Return an arbitrarily sized axis as 3D float vector. The 'id'
        parameter determines the axis, to return. 0, 1, 2 for x, y, z axis,
        respectively.
        ! Implement this in your derived class !

        Keyword arguments:
        id - zero based index, specifying the desired axis, to be returned.
        """

    @staticmethod
    def center_to_origin(
        center: Float3VectorType,
        axes: Tuple[Float3VectorType, Float3VectorType, Float3VectorType],
        scale: Float3VectorType=None,
    ) -> Float3VectorType:
        """
        Return a bounding box' origin from a center point and scaled axes.

        Keyword arguments:
        center - mid point of the desired bounding box
        axes - edge vectors of the desired bounding box. Their size is only
               considered, if no 'scale' is passed. Else, normalize axes vectors
               will be used.
        scale - length of each normalized axes. Only use, if the axes lengths
                should be dismissed. Axes length and scale are not multiplied!
        """
        if scale is None:
            return array(center) - array(axes).dot([0.5, 0.5, 0.5])

        transformation_matrix = array(axes)
        transformation_matrix /= norm(transformation_matrix, axis=1)
        return array(center) - transformation_matrix.dot([0.5, 0.5, 0.5] * scale)

    def write(self, filename: Path) -> None:
        """
        Write a STL representation of this box at 'filename'.
        The size, orientation and position is determined by the subclasses
        'origin' property and 'get_axis(int)' method, respectively.

        Keyword arguments:
        filename - System path, where the STL cube will be written at.
        """
        self.mrk_obj = Mesh.from_file(self.UnitCubePath)
        self._save_geometry(
            self.origin,
            axes=[self.get_axis(id) for id in range(3)],
            filename=filename,
            geometry=self.mrk_obj,
        )

    @classmethod
    def _save_geometry(
        cls,
        origin: Float3VectorType,
        axes: Tuple[Float3VectorType, Float3VectorType, Float3VectorType],
        filename: Path,
        geometry: Mesh,
    ) -> None:
        """
        Write a STL representation of an STL Mesh object to 'filename'.
        The size, orientation and position is determined by 'point_arrangements'.

        Keyword arguments:
        origin - 3D float vector of the desired minimal point in all axis directions.
        axes - 3-Tuple of 3D float vector, representing the x, y, z axis, respectively.
               They do not need to be of any certain size.
        filename - System path, where the STL cube will be written at.
        geometry - STL surface mesh of the object to be altered and written.
        """
        assert filename != cls.UnitCubePath
        points = geometry.points.reshape((36, 3,))
        rotation_matrix = array(axes)
        points = points.dot(rotation_matrix)
        geometry.points = points.reshape((12, 9,))

        geometry.translate(origin)
        geometry.save(filename)

    @classmethod
    def write_from(
        cls,
        origin: Float3VectorType,
        axes: Tuple[Float3VectorType, Float3VectorType, Float3VectorType],
        filename: Path,
    ) -> None:
        """
        Write a STL representation of a box at 'filename'.
        The size, orientation and position is determined by 'point_arrangements'.

        Keyword arguments:
        origin - 3D float vector of the desired minimal point in all axis directions.
        axes - 3-Tuple of 3D float vector, representing the x, y, z axis, respectively.
               They do not need to be of any certain size.
        filename - System path, where the STL cube will be written at.
        """
        cls._save_geometry(
            origin, axes, filename, geometry=Mesh.from_file(cls.UnitCubePath),
        )

    def _update_markups(self) -> None:
        raise NotImplementedError

    def print(self, outfile: TextIO=stdout) -> None:
        raise NotImplementedError

    @staticmethod
    def make_from(point_arrangements: List) -> str:
        raise NotImplementedError

    @classmethod
    def print_from(cls, point_arrangements: List, outfile: TextIO=stdout) -> None:
        raise NotImplementedError

if __name__ == "__main__":
    # Usage:
    class MyClass(Slic3rLineRepresentable):
        @property
        def line_count(self) -> int:
            return 2
        def get_line(self, id_: int) -> Tuple[Float3VectorType, Float3VectorType]:
            return [
                ((1.0, 0.0, 0.0,), (2.0, 0.0, 0.0,),),
                ((3.0, 0.0, 0.0,), (4.0, 0.0, 0.0,),),
            ][id_]

    my_obj = MyClass()
    my_obj.print()
    # or
    print(
        Slic3rLineRepresentable.make_from([
            ((1.0, 0.0, 0.0,), (2.0, 0.0, 0.0,),),
            ((3.0, 0.0, 0.0,), (4.0, 0.0, 0.0,),),
        ])
    )
    Slic3rBoxRepresentable.write_from(
        Slic3rBoxRepresentable.center_to_origin(
            center=(0.0, 0.0, 0.0,),
            axes=((1.0, 0.0, 0.0,), (0.0, 1.0, 0.0,), (0.0, 0.0, 1.0,),),
        ),
        axes=((1.0, 0.0, 0.0,), (0.0, 1.0, 0.0,), (0.0, 0.0, 1.0,),),
        filename="just_a_test",
    )
