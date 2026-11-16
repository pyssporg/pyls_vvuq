"""XSD schema validation of saved and loaded documents.

Document classes register their entry-point XSD via
``is_document=True, schema="..."``; lxml resolves the relative
xs:import/xs:include hints in src/pylsuq/schema/ from there.
``save_xml`` validates with the mode "warn" by default (write, then warn),
``load_xml`` with "off"; "raise" turns violations into
XmlSchemaValidationError in both cases. The file is always written before
validation so an invalid document can still be inspected.
"""
import warnings
from contextlib import contextmanager
from dataclasses import dataclass, field

import pytest
from lxml import etree as et

from pylsuq.domelem import (
    DomElem,
    _get_schema,
    _schema_registry,
    load_xml,
    save_xml,
    xml_attr,
)
from pylsuq.errors import XmlSchemaValidationError, XmlSchemaValidationWarning
from pylsuq.lsuq import UncertaintyQuantification
from pylsuq.ssv import Parameter, ParameterSet, Parameters, Real


@contextmanager
def caught_warnings():
    """Recorded warning list, for asserting that nothing is warned."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        yield caught


# A parseable UQ document that violates the schema (unknown attribute) but
# still deserializes, since the mapper ignores unknown attributes.
INVALID_UQ_XML = """\
<uq:UncertaintyQuantification xmlns:uq="http://openscaling.org/UQ1/UncertaintyQuantification"
  name="experiment" bogusAttribute="oops"/>
"""


def make_uq(**kwargs):
    return UncertaintyQuantification(name="experiment", **kwargs)


def make_broken_uq(extra_attr="bogusAttribute"):
    """A UQ document whose serialization carries a schema-forbidden
    attribute. Invalidity is guaranteed independent of the serializer's
    own behaviour."""
    doc = make_uq()
    to_xml = doc.to_xml

    def broken(ns=None):
        elem = to_xml(ns=ns)
        elem.set(extra_attr, "oops")
        return elem

    doc.to_xml = broken
    return doc


def schema_warnings(caught):
    return [w for w in caught if issubclass(w.category, XmlSchemaValidationWarning)]


class TestSchemaRegistration:
    def test_document_classes_register_their_schema(self):
        assert _schema_registry[UncertaintyQuantification] == "UncertaintyQuantification.xsd"
        assert _schema_registry[ParameterSet] == "SystemStructureParameterValues.xsd"

    def test_schemas_compile_once_and_cache(self):
        first = _get_schema("UncertaintyQuantification.xsd")
        assert first is _get_schema("UncertaintyQuantification.xsd")
        assert first is not _get_schema("SystemStructureParameterValues.xsd")

    def test_schema_kwarg_requires_is_document(self):
        with pytest.raises(TypeError):

            @dataclass
            class Rogue(DomElem, schema="UncertaintyQuantification.xsd"):
                text: str = field(metadata=xml_attr())


class TestDocumentClassesWithoutSchema:
    def test_unregistered_document_skips_validation(self, tmp_path):
        @dataclass
        class Note(DomElem, is_document=True):
            text: str = field(metadata=xml_attr())

        path = tmp_path / "note.xml"
        save_xml(path, Note(text="hello"), validate="raise")
        assert path.exists()


class TestSaveValidation:
    def test_valid_documents_warn_on_nothing(self, tmp_path):
        ps = ParameterSet(
            name="ps",
            parameters=Parameters(
                [Parameter(name="p", value=Real(value=[1.0, 2.0], unit="kg"))]
            ),
        )
        for doc, name in ((make_uq(), "uq.xml"), (ps, "psv.xml")):
            with caught_warnings() as caught:
                save_xml(tmp_path / name, doc, validate="warn")
            assert schema_warnings(caught) == []

    def test_valid_documents_pass_raise_mode(self, tmp_path):
        save_xml(tmp_path / "uq.xml", make_uq(), validate="raise")

    def test_scalar_parameterset_writes_version_and_validates(self, tmp_path):
        # Regression: version="1.0" must be written even though "1.0" is the
        # auto_version() default, the SSV schema requires the attribute.
        ps = ParameterSet(
            name="ps",
            parameters=Parameters([Parameter(name="p", value=Real(value=[1.0]))]),
        )
        path = tmp_path / "psv.xml"
        save_xml(path, ps, validate="raise")
        assert ps.version == "1.0"
        assert et.parse(path).getroot().get("version") == "1.0"

    def test_invalid_document_warns_and_still_writes(self, tmp_path):
        path = tmp_path / "uq.xml"
        with pytest.warns(XmlSchemaValidationWarning, match="bogusAttribute"):
            save_xml(path, make_broken_uq())  # "warn" is the default
        assert path.exists()
        assert "bogusAttribute" in path.read_text()

    def test_invalid_document_raise_writes_then_raises(self, tmp_path):
        path = tmp_path / "uq.xml"
        with pytest.raises(XmlSchemaValidationError) as excinfo:
            save_xml(path, make_broken_uq(), validate="raise")
        # The invalid document is on disk for inspection ...
        assert path.exists()
        # ... and the error locates the violation.
        msg = str(excinfo.value)
        assert "does not validate against schema UncertaintyQuantification.xsd" in msg
        assert "bogusAttribute" in msg
        assert any("bogusAttribute" in v for v in excinfo.value.violations)

    def test_invalid_document_ignored_in_off_mode(self, tmp_path):
        with caught_warnings() as caught:
            save_xml(tmp_path / "uq.xml", make_broken_uq(), validate="off")
        assert schema_warnings(caught) == []


class TestLoadValidation:
    @pytest.fixture
    def invalid_path(self, tmp_path):
        path = tmp_path / "invalid.xml"
        path.write_text(INVALID_UQ_XML)
        return path

    def test_off_is_default_and_ignores_violations(self, invalid_path):
        with caught_warnings() as caught:
            obj = load_xml(invalid_path)
        assert schema_warnings(caught) == []
        assert isinstance(obj, UncertaintyQuantification)

    def test_warn_reports_violations_and_still_loads(self, invalid_path):
        with pytest.warns(XmlSchemaValidationWarning, match="bogusAttribute"):
            obj = load_xml(invalid_path, validate="warn")
        assert isinstance(obj, UncertaintyQuantification)

    def test_raise_reports_violations(self, invalid_path):
        with pytest.raises(XmlSchemaValidationError) as excinfo:
            load_xml(invalid_path, validate="raise")
        violations = excinfo.value.violations
        assert len(violations) == 1
        # Violations carry the element path into the parsed document.
        assert violations[0].startswith("/uq:UncertaintyQuantification")

    def test_valid_document_passes_raise_mode(self, tmp_path):
        path = tmp_path / "uq.xml"
        save_xml(path, make_uq())
        assert isinstance(load_xml(path, validate="raise"), UncertaintyQuantification)


class TestValidateModes:
    @pytest.mark.parametrize("args", [("save",), ("load",)])
    def test_unknown_mode_rejected_before_io(self, tmp_path, args):
        # No file exists at this path: the mode must be rejected before any
        # serialization or parsing happens.
        path = tmp_path / "does-not-exist.xml"
        with pytest.raises(ValueError, match="validate must be one of"):
            if args[0] == "save":
                save_xml(path, make_uq(), validate="strict")
            else:
                load_xml(path, validate="strict")