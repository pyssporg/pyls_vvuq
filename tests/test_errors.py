"""Tests for error diagnostics in DomElem.to_xml and DomElem.from_xml.

Errors caused by dataclass declaration mistakes or malformed XML should
surface as XmlMappingError messages that point to the class and member
where the problem actually is, with the root cause preserved in
__cause__ and (for nested elements) in the chained message.
"""
from dataclasses import dataclass, field

import pytest
from lxml import etree as et

from pylsuq.domelem import DomElem, xml_attr
from pylsuq.errors import XmlMappingError


def parse(xml_string):
    return et.fromstring(xml_string.strip().encode())


@dataclass
class Child(DomElem):
    name: str = field(metadata=xml_attr())
    age: int = field(metadata=xml_attr())


@dataclass
class Parent(DomElem):
    child: Child


class TestDeserializationDiagnostics:
    def test_missing_required_child_names_class_and_field(self):
        with pytest.raises(
            XmlMappingError, match=r"Parent\.child.*Missing required element <Child>"
        ):
            Parent.from_xml(parse('<Parent/>'))

    def test_bad_attr_value_names_class_and_field(self):
        with pytest.raises(XmlMappingError, match=r"Child\.age"):
            Child.from_xml(parse('<Child name="c" age="notanint"/>'))

    def test_nested_error_traces_path_down_to_root_cause(self):
        xml = '<Parent><Child name="c" age="notanint"/></Parent>'
        with pytest.raises(XmlMappingError) as excinfo:
            Parent.from_xml(parse(xml))

        message = str(excinfo.value)
        # The location in the parent and the location in the child are
        # both present in the chained message.
        assert "Parent.child" in message
        assert "Child.age" in message

    def test_original_error_is_preserved_as_cause(self):
        with pytest.raises(XmlMappingError) as excinfo:
            Child.from_xml(parse('<Child name="c" age="notanint"/>'))
        assert isinstance(excinfo.value.__cause__, ValueError)

    def test_child_field_not_declared_as_domelem(self):
        # Declaration mistake: a plain type used as a child element
        # (missing metadata=xml_attr()).
        @dataclass
        class BadDecl(DomElem):
            name: str

        with pytest.raises(XmlMappingError, match=r"BadDecl\.name"):
            BadDecl.from_xml(parse('<BadDecl/>'))

    def test_non_domelem_child_hint_suggests_xml_attr(self):
        @dataclass
        class BadDecl(DomElem):
            name: str

        with pytest.raises(
            XmlMappingError, match=r"hint:.*not a DomElem subclass.*xml_attr"
        ):
            BadDecl.from_xml(parse('<BadDecl/>'))

    def test_missing_required_attribute_is_named(self):
        with pytest.raises(
            XmlMappingError, match=r"Child\.name.*Missing required attribute 'name'"
        ):
            Child.from_xml(parse('<Child/>'))

    def test_custom_deserializer_failure_gets_hint(self):
        @dataclass
        class BadDeserializer(DomElem):
            coordinates: list = field(
                metadata=xml_attr(deserialize=lambda s: s.nonexistent_method())
            )

        with pytest.raises(XmlMappingError, match=r"hint:.*custom"):
            BadDeserializer.from_xml(parse('<BadDeserializer coordinates="1 2"/>'))


class TestSerializationDiagnostics:
    def test_non_domelem_child_names_class_and_field(self):
        @dataclass
        class PlainChild:
            x: str

        @dataclass
        class BrokenParent(DomElem):
            child: PlainChild

        obj = BrokenParent(child=PlainChild(x="y"))
        with pytest.raises(XmlMappingError, match=r"BrokenParent\.child"):
            obj.to_xml()

    def test_failing_serializer_names_class_and_field(self):
        @dataclass
        class BadSerializer(DomElem):
            value: str = field(metadata=xml_attr(serialize=lambda v: 1 / 0))

        with pytest.raises(XmlMappingError, match=r"BadSerializer\.value"):
            BadSerializer(value="x").to_xml()

    def test_failing_serializer_gets_custom_callable_hint(self):
        @dataclass
        class BadSerializer(DomElem):
            value: str = field(metadata=xml_attr(serialize=lambda v: 1 / 0))

        with pytest.raises(XmlMappingError, match=r"hint:.*custom"):
            BadSerializer(value="x").to_xml()

    def test_dict_field_serialization_gets_hint(self):
        @dataclass
        class DictHolder(DomElem):
            children: dict[str, Child] = field(default_factory=dict)

        obj = DictHolder(children={"c": Child("c", 1)})
        with pytest.raises(XmlMappingError, match=r"hint:.*dict fields"):
            obj.to_xml()

    def test_original_error_is_preserved_as_cause(self):
        @dataclass
        class PlainChild:
            x: str

        @dataclass
        class BrokenParent(DomElem):
            child: PlainChild

        obj = BrokenParent(child=PlainChild(x="y"))
        with pytest.raises(XmlMappingError) as excinfo:
            obj.to_xml()
        assert isinstance(excinfo.value.__cause__, AttributeError)

    def test_nested_error_traces_path_down_to_root_cause(self):
        @dataclass
        class PlainChild:
            x: str

        @dataclass
        class GrandChild(DomElem):
            child: PlainChild

        @dataclass
        class TopParent(DomElem):
            child: GrandChild

        obj = TopParent(child=GrandChild(child=PlainChild(x="y")))
        with pytest.raises(XmlMappingError) as excinfo:
            obj.to_xml()

        message = str(excinfo.value)
        assert "TopParent.child" in message
        assert "GrandChild.child" in message
