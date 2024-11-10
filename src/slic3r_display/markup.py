# pylint: disable=invalid-name
from __future__ import annotations

from copy import copy
from dataclasses import dataclass, field, Field
from typing import List, Optional

from .settings import (
   DEFAULT_POSITION,
   DEFAULT_ORIENTATION,
   STATUS_DEFINED,
   STATUS_UNDEFINED,
   DEFAULT_COLOR,
   DEFAULT_SELECTED_COLOR,
   DEFAULT_SCALE,
   DEFAULT_THICKNESS,
   DEFAULT_GLYPH_TYPE,
   DEFAULT_PROJECTION_COLOR,
   DEFAULT_SLICE_OPACITY,
   DEFAULT_SNAP_MODE,
   LINE_MARKUP_TYPE,
   POINT_MARKUP_TYPE,
   DEFAULT_COORDINATE_SYSTEM,
   DEFAULT_COORDINATE_UNITS,
   DEFAULT_LABEL_FORMAT,
)
from .types import Float3VectorType, Float9VectorType, MarkupType

def field_copy(l: List) -> Field:
    return field(default_factory=lambda: copy(l))

@dataclass
class ControlPoint:
    id: str
    label: str
    description: str = ""
    associatedNodeID: str = ""
    position: Float3VectorType = field_copy(DEFAULT_POSITION)
    orientation: Float9VectorType = field_copy(DEFAULT_ORIENTATION)
    selected: bool = True
    locked: bool = False
    visibility: bool = True
    positionStatus: str = STATUS_UNDEFINED

    def set_position(self, x: float, y: float, z: float) -> None:
        self.positionStatus = STATUS_DEFINED
        self.position[0] = x
        self.position[1] = y
        self.position[2] = z

    @classmethod
    def make_control_point(cls, id_: int, label: str, x: float, y: float, z: float) -> ControlPoint:
        point = cls(id_, f"{label}-{id_}")
        point.set_position(x, y, z)
        return point

@dataclass
class Display:
    visibility: bool = True
    opacity: float = 1.0
    color: Float3VectorType = field_copy(DEFAULT_COLOR)
    selectedColor: Float3VectorType = field_copy(DEFAULT_SELECTED_COLOR)
    activeColor: Float3VectorType = field_copy(DEFAULT_COLOR)
    propertiesLabelVisibility: bool = True
    pointLabelsVisibility: bool = False
    textScale: float = DEFAULT_SCALE
    glyphType: str = DEFAULT_GLYPH_TYPE
    glyphScale: float = DEFAULT_SCALE
    sliceProjection: bool = False
    sliceProjectionUseFiducialColor: bool = True
    sliceProjectionOutlinedBehindSlicePlane: bool = False
    sliceProjectionColor: Float3VectorType = field_copy(DEFAULT_PROJECTION_COLOR)
    sliceProjectionOpacity: float = DEFAULT_SLICE_OPACITY
    lineThickness: float = DEFAULT_THICKNESS
    lineColorFadingStart: float = 1.0
    lineColorFadingEnd: float = 10.0
    lineColorFadingSaturation: float = 1.0
    lineColorFadingHueOffset: float = 0.0
    handlesInteractive: bool = False
    translationHandleVisibility: bool = True
    rotationHandleVisibility: bool = True
    scaleHandleVisibility: bool = True
    interactionHandleScale: float = DEFAULT_SCALE
    snapMode: str = DEFAULT_SNAP_MODE

@dataclass
class Markup:
    type: MarkupType
    controlPoints: List[ControlPoint] = field(default_factory=list)
    display: Display = Display()
    coordinateSystem: str = DEFAULT_COORDINATE_SYSTEM
    coordinateUnits: str = DEFAULT_COORDINATE_UNITS
    fixedNumberOfControlPoints: bool = False
    labelFormat: str = DEFAULT_LABEL_FORMAT
    lastUsedControlPointNumber: int = 0

    def __getitem__(self, id_: int) -> ControlPoint:
        assert id_ < len(self)
        return self.controlPoints[id_]

    def __setitem__(self, id_: int, point: Float3VectorType) -> None:
        assert id_ < self.capacity and id_ <= len(self)
        if id_ == len(self):
            self.add(point)
        else:
            self.controlPoints[id_].set_position(*point)
        self.lastUsedControlPointNumber = id_

    def __len__(self) -> int:
        return len(self.controlPoints)

    @property
    def capacity(self) -> Optional[int]:
        return None

    def add(self, point: Float3VectorType, id_: int=None) -> None:
        assert self.capacity is None      \
            or len(self) < self.capacity
        self.controlPoints.append(ControlPoint.make_control_point(
            id_=len(self) + 1,
            label=f"L{f'_{id_}' if id_ else ''}",
            x=point[0],
            y=point[1],
            z=point[2],
        ))

class PointMarkup(Markup):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, type=POINT_MARKUP_TYPE, **kwargs)

class LineMarkup(Markup):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, type=LINE_MARKUP_TYPE, **kwargs)

    @property
    def capacity(self) -> Optional[int]:
        return 2
