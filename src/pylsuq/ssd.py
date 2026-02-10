from dataclasses import dataclass, field, KW_ONLY
from typing import ClassVar

from lxml import etree as et

from pylsuq.domelem import DomElem, xml_metadata, xml_attr, register_namespace
from pylsuq.ssc import ATopLevelMetaData, ABaseElement, Units, Dimension, GDimensions, SSC_NS

SSD_NS = "http://ssp-standard.org/SSP1/SystemStructureDescription"
register_namespace("ssd", SSD_NS)
