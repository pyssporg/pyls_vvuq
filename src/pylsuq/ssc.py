from dataclasses import dataclass, field, KW_ONLY
from datetime import datetime
from collections.abc import MutableSequence
from typing import ClassVar

from lxml import etree as et

from pylsuq.domelem import DomElem, xml_metadata, xml_attr, register_namespace

SSC_NS = "http://ssp-standard.org/SSP1/SystemStructureCommon"
register_namespace("ssc", SSC_NS)


@dataclass
class ATopLevelMetaData:
    _: KW_ONLY
    author: str | None = field(default=None, metadata=xml_attr())
    file_version: str | None = field(default=None, metadata=xml_attr(name="fileversion"))
    copyright: str | None = field(default=None, metadata=xml_attr())
    license: str | None = field(default=None, metadata=xml_attr())
    generation_tool: str | None = field(default=None, metadata=xml_attr(name="generationTool"))
    generation_datetime: datetime | None = field(
        default=None,
        metadata=xml_attr(
            name="generationTimeAndDate",
            deserialize=datetime.fromisoformat,
            serialize=datetime.isoformat,
        ),
    )

    def __post_init__(self):
        if self.generation_tool is None:
            self.generation_tool = "pylsuq"

        if self.generation_datetime is None:
            self.generation_datetime = datetime.now().replace(microsecond=0)


@dataclass
class ABaseElement:
    _: KW_ONLY
    id: str | None = field(default=None, metadata=xml_attr())
    description: str | None = field(default=None, metadata=xml_attr())


@dataclass
class BaseUnit(DomElem):
    kg: int = field(default=0, metadata=xml_attr())
    m: int = field(default=0, metadata=xml_attr())
    s: int = field(default=0, metadata=xml_attr())
    A: int = field(default=0, metadata=xml_attr())
    K: int = field(default=0, metadata=xml_attr())
    mol: int = field(default=0, metadata=xml_attr())
    cd: int = field(default=0, metadata=xml_attr())
    rad: int = field(default=0, metadata=xml_attr())
    factor: float = field(default=1, metadata=xml_attr())
    offset: float = field(default=0, metadata=xml_attr())


@dataclass
class Unit(DomElem, ABaseElement):
    name: str = field(kw_only=True, metadata=xml_attr())
    base: BaseUnit


@dataclass
class Units(DomElem):
    NS: ClassVar[str] = SSC_NS
    units: dict[str, Unit]

    def __getitem__(self, name):
        return self.units[name]

    def __delitem__(self, name):
        del self.units[name]

    def __len__(self):
        return len(self.units)

    def add_unit(self, unit):
        self.units[unit.name] = unit

    def __iter__(self):
        return self.units.values()


@dataclass
class Dimension(DomElem):
    NS: ClassVar[str] = SSC_NS
    size: int | None = field(default=None, metadata=xml_attr())
    size_connector: str | None = field(default=None, metadata=xml_attr())


def GDimensions():
    return field(default_factory=list, metadata=xml_metadata(use_class_ns=True))
