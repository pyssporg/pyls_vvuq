from dataclasses import dataclass, field, KW_ONLY
from typing import ClassVar
from itertools import batched, chain
from collections.abc import Iterable, Sequence
import math

from lxml import etree as et

from pylsuq.domelem import DomElem, xml_metadata, xml_attr, register_namespace
from pylsuq.ssc import ATopLevelMetaData, ABaseElement, Units, Dimension, GDimensions, SSC_NS

SSV_NS = "http://ssp-standard.org/SSP1/SystemStructureParameterValues"
register_namespace("ssv", SSV_NS)


def flatten(seq):
    if not isinstance(seq, Iterable):
        return [seq]

    seq = iter(seq)
    head = next(seq)

    while hasattr(head, "__iter__"):
        seq = chain(head, *seq)
        head = next(seq)

    return [head, *seq]


def reshape(seq, shape):
    seq = flatten(seq)

    if len(shape) == 0:
        return seq[0]

    for dim in shape[-1:0:-1]:
        seq = batched(seq, dim)

    return list(seq)


def shape_of(seq):
    shape = []

    while isinstance(seq, Sequence):
        shape.append(len(seq))
        seq = seq[0]

    return tuple(shape)


def is_ssv1_scalar(seq):
    return shape_of(seq) == (1,)


class SSVElem(DomElem):
    NS: ClassVar[str] = SSV_NS


@dataclass
class Real(SSVElem):
    value: list[float] = field(
        metadata=xml_attr(
            serialize=lambda vs: " ".join(str(v) for v in flatten(vs)),
            deserialize=lambda s: [float(v) for v in s.strip().split()],
        )
    )
    unit: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Integer(SSVElem):
    value: list[int] = field(
        metadata=xml_attr(
            serialize=lambda vs: " ".join(str(v) for v in flatten(vs)),
            deserialize=lambda s: [int(v) for v in s.strip().split()],
        )
    )


@dataclass
class Parameter(SSVElem, ABaseElement):
    name: str = field(kw_only=True, metadata=xml_attr())
    value: Real | Integer
    dimensions: list[Dimension] = GDimensions()

    def __post_init__(self):
        if len(self.shape) != 0 or is_ssv1_scalar(self.value.value):
            if self.shape != shape_of(self.value.value):
                self.value.value = reshape(self.value.value, self.shape)
        else:
            self.reshape()

    @property
    def v(self):
        return self.value.value

    @v.setter
    def v(self, value):
        self.value.value = value

    @property
    def shape(self):
        return tuple(dim.size for dim in self.dimensions)

    def reshape(self, shape: tuple[int, ...] | None = None):
        if shape is None:
            self.dimensions = [Dimension(x) for x in shape_of(self.v)]
        else:
            if math.prod(shape) != math.prod(self.shape):
                raise ValueError(f"Cannot reshape from shape {self.shape} to shape {shape}")

            self.dimensions = [Dimension(x) for x in shape]
            self.v = reshape(flatten(self.v), shape)


@dataclass
class Parameters(SSVElem):
    parameters: list[Parameter]

    def __getitem__(self, idx):
        return self.parameters[idx]

    def __setitem__(self, idx, value):
        self.parameters[idx] = value

    def __delitem__(self, idx):
        del self.parameters[idx]

    def __len__(self):
        return len(self.parameters)

    def insert(self, idx, value):
        self.parameters.insert(idx, value)


@dataclass
class ParameterSet(SSVElem, ATopLevelMetaData, ABaseElement,
                   is_document=True,
                   schema="SystemStructureParameterValues.xsd"):
    version: str = field(kw_only=True, default="1.0", metadata=xml_attr())
    name: str = field(kw_only=True, metadata=xml_attr())
    parameters: Parameters
    units: Units | None = None

    def _pre_serialize(self):
        self.auto_version()

    def auto_version(self):
        self.version = "1.0"
        for param in self.parameters:
            if len(param.shape) != 0:
                self.version = "2.0"
                break
