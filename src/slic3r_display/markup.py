from __future__ import annotations

from copy import copy
from dataclasses import dataclass, field

from .settings import *
from .types import Float3VectorType, Float9VectorType

field_copy = lambda list: field(default_factory=lambda: copy(list))

@dataclass
class ControlPoint:
    id: str
    label: str
    description: str = ""
    associatedNodeID: str = ""
    position: Float3VectorType = field_copy(DefaultPosition)
    orientation: Float9VectorType = field_copy(DefaultOrientation)
    selected: bool = True
    locked: bool = False
    visibility: bool = True
    positionStatus: str = StatusUndefined

    def set_position(self, x: float, y: float, z: float) -> None:
        self.positionStatus = StatusDefined
        self.position[0] = x
        self.position[1] = y
        self.position[2] = z

    @classmethod
    def make_control_point(cls, id: int, label: str, x: float, y: float, z: float) -> ControlPoint:
        point = cls(id, f"{label}-{id}")
        point.set_position(x, y, z)
        return point

@dataclass
class Display:
    visibility: bool = True
    opacity: float = 1.0
    color: Float3VectorType = field_copy(DefaultColor)
    selectedColor: Float3VectorType = field_copy(DefaultSelectedColor)
    activeColor: FloatVectorType = field_copy(DefaultColor)
    propertiesLabelVisibility: bool = True
    pointLabelsVisibility: bool = False
    textScale: float = DefaultScale
    glyphType: str = DefaultGlyphType
    glyphScale: float = DefaultScale
    sliceProjection: bool = False
    sliceProjectionUseFiducialColor: bool = True
    sliceProjectionOutlinedBehindSlicePlane: bool = False
    sliceProjectionColor: FloatVectorType = field_copy(DefaultProjectionColor)
    sliceProjectionOpacity: float = DefaultSliceOpacity
    lineThickness: float = DefaultThickness
    lineColorFadingStart: float = 1.0
    lineColorFadingEnd: float = 10.0
    lineColorFadingSaturation: float = 1.0
    lineColorFadingHueOffset: float = 0.0
    handlesInteractive: bool = False
    translationHandleVisibility: bool = True
    rotationHandleVisibility: bool = True
    scaleHandleVisibility: bool = True
    interactionHandleScale: float = DefaultScale
    snapMode: str = DefaultSnapMode

@dataclass
class Markup:
    type: MarkupType
    controlPoints: List[ControlPoint] = field(default_factory=list)
    display: Display = Display()
    coordinateSystem: str = DefaultCoordinateSystem
    coordinateUnits: str = DefaultCoordinateUnits
    fixedNumberOfControlPoints: bool = False
    labelFormat: str = DefaultLabelFormat
    lastUsedControlPointNumber: int = 0

    def __getitem__(self, id: int) -> ControlPoint:
        assert id < len(self)
        return self.controlPoints[id]

    def __setitem__(self, id: int, point: Float3VectorType) -> None:
        assert id < self.capacity() and id <= len(self)
        if id == len(self):
            self.add(point)
        else:
            self.controlPoints[id].set_position(*point)
        self.lastUsedControlPointNumber = id

    def __len__(self) -> int:
        return len(self.controlPoints)

    def capacity(self) -> Optional[int]:
        return None

    def add(self, point: Float3VectorType, id: int=None) -> None:
        assert len(self) < self.capacity()
        self.controlPoints.append(ControlPoint.make_control_point(
            id=len(self) + 1,
            label=f"L{f'_{id}' if id else ''}",
            x=point[0],
            y=point[1],
            z=point[2],
        ))

class LineMarkup(Markup):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, type=LineMarkupType, **kwargs)

    def capacity(self) -> Optional[int]:
        return 2

