"""Tests for the UncertaintyQuantification root document (lsuq.py).

Pins the document registration (is_document=True) and the attribute
mapping of the root element per schema/UncertaintyQuantification.xsd:
name, info, requiredAssumptionsRefs, stmdRef and srmdRef are XML
attributes, not child elements.
"""
from lxml import etree as et

from pylsuq import UncertaintyQuantification, load_xml, save_xml
from pylsuq.lsuq import (
    UQ_NAMESPACE,
    ActivitySettings,
    CredibilityAssessment,
    ProcessContext,
    TypedOperationalDomain,
    TypedOperationalDomainKind,
)


class TestUncertaintyQuantificationDocument:
    def test_registered_as_document_root(self, tmp_path):
        path = tmp_path / "uq.xml"
        save_xml(path, UncertaintyQuantification(name="experiment"))
        assert isinstance(load_xml(path), UncertaintyQuantification)

    def test_schema_attributes_written_on_root_element(self, tmp_path):
        path = tmp_path / "uq.xml"
        save_xml(path, UncertaintyQuantification(name="experiment", info="i"))
        root = et.parse(path).getroot()
        assert root.get("name") == "experiment"
        assert root.get("info") == "i"
        assert root.find("info") is None

    def test_round_trip_attributes(self, tmp_path):
        obj = UncertaintyQuantification(
            name="experiment",
            info="basic check",
            requiredAssumptionsRefs="RA1 RA2",
            stmdRef="file:///stmd",
            srmdRef="file:///srmd",
            version="1.0",
        )
        path = tmp_path / "uq.xml"
        save_xml(path, obj)
        assert load_xml(path) == obj

    def test_inherited_toplevel_metadata_written_as_root_attributes(self, tmp_path):
        path = tmp_path / "uq.xml"
        save_xml(path, UncertaintyQuantification(name="experiment", author="Ada"))
        root = et.parse(path).getroot()
        assert root.get("author") == "Ada"
        # The attribute group is flattened: no ATopLevelMetaData child element
        assert not root.findall(
            "{http://ssp-standard.org/SSP1/SystemStructureCommon}ATopLevelMetaData"
        )

    def test_inherited_toplevel_metadata_round_trip(self, tmp_path):
        obj = UncertaintyQuantification(
            name="experiment", author="Ada", file_version="0.1"
        )
        path = tmp_path / "uq.xml"
        save_xml(path, obj)
        assert load_xml(path) == obj


class TestDomainMetadataAttributes:
    def test_typed_operational_domain_round_trip(self):
        obj = TypedOperationalDomain(
            id="OD1",
            kind=TypedOperationalDomainKind.OPERATIONAL_DESIGN_DOMAIN,
            name="domain",
            geometryKind="hyper-rectangle",
            parentRef="OD0",
            srmdRef="file:///srmd",
            credibility_assessment=CredibilityAssessment(
                level="L2", purpose="demo", standard="STD-1"
            ),
            process_context=ProcessContext(
                process="development", phase="P2", glueParticleRef="GP7"
            ),
        )
        elem = obj.to_xml()
        for attr in ("name", "geometryKind", "parentRef", "srmdRef"):
            assert elem.get(attr) is not None
            assert elem.find(attr) is None
        ca = elem.find(f"{{{UQ_NAMESPACE}}}CredibilityAssessment")
        assert (ca.get("level"), ca.get("purpose"), ca.get("standard")) == (
            "L2", "demo", "STD-1",
        )
        pc = elem.find(f"{{{UQ_NAMESPACE}}}ProcessContext")
        assert (pc.get("process"), pc.get("phase"), pc.get("glueParticleRef")) == (
            "development", "P2", "GP7",
        )
        assert TypedOperationalDomain.from_xml(elem) == obj

    def test_activity_settings_round_trip(self):
        obj = ActivitySettings(method="Monte Carlo")
        elem = obj.to_xml()
        assert elem.get("method") == "Monte Carlo"
        assert elem.find("method") is None
        assert ActivitySettings.from_xml(elem) == obj
