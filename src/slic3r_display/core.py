"""
Slic3r Representation abstract base classes reside here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, is_dataclass
from sys import stdout
from typing import List, Optional, TextIO, Tuple
from json import JSONEncoder, dumps

from .markup import ControlPoint, LineMarkup, Markup

@dataclass
class MrkClass:
    """ Wrapper around list of Markups """
    markups: List[Markup] = field(default_factory=list)


class MrkClassEncoder(JSONEncoder):
    """ Class for providing JSON pretty-printing for MrkClass objects """
    def default(self, obj: Any) -> Any:
        """ Return 'obj' as json representation. """
        if isinstance(obj, MrkClass):
            obj_dict = asdict(obj)
            obj_dict["@schema"] = "https://raw.githubusercontent.com/slicer/slicer/master/Modules/Loadable/Markups/Resources/Schema/markups-schema-v1.0.3.json#"
            return obj_dict
        return super().default(obj)


class Slic3rLineRepresentable(ABC):
    """
    Abstract class providing print methods.
    
    Member methods:
    write - Save 3D Slic3r interpretable line markup representation to drive.
    print - Write 3D Slic3r interpretable line markup representation to stdout (or another file object).

    Pure virtual functions (aka override these):
    line_count (property) - Return the number of supplied lines by derived class.
    get_line(int) - Return the endpoints for line with 'id' as supplied by parameter.
    """
    def __init__(self) -> None:
        self.mrk_obj = MrkClass()
    
    @property
    @abstractmethod
    def line_count(self) -> int:
        """
        Return the number of supplied lines by derived class.
        ! Implement this in your derived class !
        """
        ...

    @abstractmethod
    def get_line(self, id: int) -> Tuple[Float3VectorType, Float3VectorType]:
        """
        Return the endpoints for line with 'id' as supplied by parameter.

        Result: Two-tuple of lists of 3 float values, i.e.
                ([1.0, 0.0, 0.0], [2.0, 0.0, 0.0],)

        Keyword arguments:
        id - zero based index, specifying the desired line, to be returned.
        """
        ...

    def _update_markups(self) -> None:
        """
        Create new line markups from the lines provided by the derived classes
        virtual functions 'line_count' and 'get_line(int)'.
        """
        self.mrk_obj.markups = [LineMarkup() for _ in range(self.line_count)]
        for id, line in enumerate(self.mrk_obj.markups):
            first_point, second_point = self.get_line(id)
            line.add(first_point, id=id + 1)
            line.add(second_point, id=id + 1)

    def write(self, filename: Path) -> None:
        """
        Save 3D Slic3r interpretable line markup representation to drive, at path 'filename'.
        
        Keyword arguments:
        filename - System path, where the JSON string will be written at.
        """
        try:
            with open(filename, "w") as file:
                self.print(outfile=file)
        except Exception as err:
            print(f"Could not write to '{filename}'")

    def print(self, outfile: TextIO=stdout) -> None:
        """
        Write 3D Slic3r interpretable line markup representation to stdout (or another file object).

        Keyword arguments:
        outfile - File object, where the JSON string will be printed to (default: stdout)
        """
        self._update_markups()
        print(dumps(self.mrk_obj, cls=MrkClassEncoder, indent=2), file=outfile)

    @staticmethod
    def make_from(point_arrangements: List) -> str:
        """
        Return JSON string from one or more lists of 3D enpoints, that can be interpreted as 3D Markup files.
        The file will contain one or more line markups, according to point_arrangements parameters lenght.

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
                ControlPoint.make_control_point(1, label=f"L_{id + 1}", x=line[0][0], y=line[0][1], z=line[0][2]),
                ControlPoint.make_control_point(2, label=f"L_{id + 1}", x=line[1][0], y=line[1][1], z=line[1][2]),
            ])
            for id, line in enumerate(point_arrangements)
        ]
        return dumps(MrkClass(markups), cls=MrkClassEncoder, indent=2)

    @classmethod
    def print_from(cls, point_arrangements: List, outfile: TextIO=stdout) -> None:
        """
        Print JSON string from one or more lists of 3D enpoints, that can be interpreted as 3D Markup files.
        The outfile will contain one or more line markups, according to point_arrangements parameters lenght.

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
        Write JSON string from one or more lists of 3D enpoints, that can be interpreted as 3D Markup files.
        The file will contain one or more line markups, according to point_arrangements parameters lenght.

        Keyword arguments:
        point_arrangements - example:
            point_arrangements=[ [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
                                 [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0]] ]
        filename - System path, where the JSON string will be written at.
        """
        try:
            with open(filename, "w") as file:
                cls.print_from(point_arrangements, outfile=file)
        except Exception as err:
            print(f"Could not write to '{filename}'")

if __name__ == "__main__":
    """
    Usage:
    """
    class MyClass(Slic3rLineRepresentable):
        @property
        def line_count(self) -> int:
            return 2
        def get_line(self, id: int) -> Tuple[Float3VectorType, Float3VectorType]:
            return [
                ((1.0, 0.0, 0.0,), (2.0, 0.0, 0.0,),),
                ((3.0, 0.0, 0.0,), (4.0, 0.0, 0.0,),),
            ][id]
    
    my_obj = MyClass()
    my_obj.print()
    # or
    print(
        Slic3rLineRepresentable.make_from([
            ((1.0, 0.0, 0.0,), (2.0, 0.0, 0.0,),),
            ((3.0, 0.0, 0.0,), (4.0, 0.0, 0.0,),),
        ])
    )
