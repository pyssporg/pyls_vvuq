"""Tests for dataclass -> XML serialization (DomElem.to_xml).

Each test class targets one branch of the serialization logic in
pylsuq.domelem (DomElem.to_xml), so failures isolate the specific
mapping kind: attributes, optionals, unions, lists, single children
and namespaces.
"""
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Union

import pytest
from lxml import etree as et

from pylsuq.domelem import DomElem, xml_attr, xml_metadata
from pylsuq.errors import XmlMappingError


# ---------------------------------------------------------------------------
# Attributes
# ---------------------------------------------------------------------------

@dataclass
class AttrLeaf(DomElem):
    name: str = field(metadata=xml_attr())
    age: int = field(metadata=xml_attr())


class TestSimpleAttributes:
    def test_writes_attributes_as_strings(self):
        elem = AttrLeaf(name="Bob", age=7).to_xml()
        assert elem.get("name") == "Bob"
        assert elem.get("age") == "7"


@dataclass
class OptionalAttrLeaf(DomElem):
    name: str = field(metadata=xml_attr())
    nickname: str | None = field(default=None, metadata=xml_attr())


class TestOptionalAttributes:
    def test_none_attr_is_omitted(self):
        elem = OptionalAttrLeaf(name="A").to_xml()
        assert "nickname" not in elem.attrib

    def test_set_attr_is_written(self):
        elem = OptionalAttrLeaf(name="A", nickname="Al").to_xml()
        assert elem.get("nickname") == "Al"


@dataclass
class DefaultAttrLeaf(DomElem):
    name: str = field(metadata=xml_attr())
    sound: str = field(default="Woof", metadata=xml_attr())


class TestDefaultValueAttributes:
    def test_attr_equal_to_default_is_omitted(self):
        elem = DefaultAttrLeaf(name="Rex").to_xml()
        assert "sound" not in elem.attrib

    def test_attr_different_from_default_is_written(self):
        elem = DefaultAttrLeaf(name="Rex", sound="Bark").to_xml()
        assert elem.get("sound") == "Bark"


@dataclass
class CustomSerLeaf(DomElem):
    coordinates: list[float] = field(
        metadata=xml_attr(serialize=lambda cs: " ".join(str(c) for c in cs))
    )


class TestCustomAttributeSerializer:
    def test_custom_serialize_callable_is_used(self):
        elem = CustomSerLeaf(coordinates=[0.0, 0.8]).to_xml()
        assert elem.get("coordinates") == "0.0 0.8"


@dataclass
class RenamedAttrLeaf(DomElem):
    fur_softness: float = field(metadata=xml_attr(name="furSoftness"))


class TestRenamedAttribute:
    def test_attr_name_override_is_used(self):
        elem = RenamedAttrLeaf(fur_softness=0.999).to_xml()
        assert elem.get("furSoftness") == "0.999"
        assert "fur_softness" not in elem.attrib


# ---------------------------------------------------------------------------
# Child elements
# ---------------------------------------------------------------------------

@dataclass
class Child(DomElem):
    name: str = field(metadata=xml_attr())


@dataclass
class SingleChildParent(DomElem):
    child: Child


class TestSingleChild:
    def test_writes_single_child(self):
        elem = SingleChildParent(child=Child("c1")).to_xml()
        children = elem.findall("Child")
        assert len(children) == 1
        assert children[0].get("name") == "c1"


@dataclass
class ListParent(DomElem):
    children: list[Child] = field(default_factory=list)


class TestListChildren:
    def test_writes_one_element_per_item(self):
        obj = ListParent(children=[Child("a"), Child("b")])
        elem = obj.to_xml()
        assert [c.get("name") for c in elem.findall("Child")] == ["a", "b"]

    def test_empty_list_writes_no_elements(self):
        elem = ListParent().to_xml()
        assert elem.findall("Child") == []


@dataclass
class DictParent(DomElem):
    children: dict[str, Child] = field(default_factory=dict)


class TestDictChildren:
    @pytest.mark.xfail(reason="to_xml has no branch for dict fields")
    def test_dict_children_serialize(self):
        obj = DictParent(children={"a": Child("a")})
        elem = obj.to_xml()
        assert [c.get("name") for c in elem.findall("Child")] == ["a"]


@dataclass
class OptionalChildParent(DomElem):
    child: Optional[Child] = None


class TestOptionalChild:
    def test_none_child_is_omitted(self):
        elem = OptionalChildParent().to_xml()
        assert elem.findall("Child") == []

    def test_set_child_is_written(self):
        elem = OptionalChildParent(child=Child("x")).to_xml()
        assert len(elem.findall("Child")) == 1


# ---------------------------------------------------------------------------
# Unions
# ---------------------------------------------------------------------------

@dataclass
class PetBase:
    name: str = field(metadata=xml_attr())


@dataclass
class Dog(DomElem, PetBase):
    favorite_food: str = field(default="Bone", metadata=xml_attr(name="favoriteFood"))


@dataclass
class Cat(DomElem, PetBase):
    fur_softness: float = field(default=0.5, metadata=xml_attr(name="furSoftness"))


@dataclass
class UnionParent(DomElem):
    pet: Union[Dog, Cat]


class TestUnionChild:
    def test_first_union_member_serializes_with_its_tag(self):
        elem = UnionParent(pet=Dog(name="Rex")).to_xml()
        assert len(elem.findall("Dog")) == 1
        assert elem.findall("Cat") == []

    def test_second_union_member_serializes_with_its_tag(self):
        elem = UnionParent(pet=Cat(name="Ronja", fur_softness=0.7)).to_xml()
        assert len(elem.findall("Cat")) == 1
        assert elem.findall("Dog") == []


# ---------------------------------------------------------------------------
# Namespaces and tag()
# ---------------------------------------------------------------------------

NS_A = "http://example.com/ns-a"
NS_B = "http://example.com/ns-b"


@dataclass
class NsChild(DomElem):
    NS: ClassVar[str | None] = NS_A
    name: str = field(metadata=xml_attr())


@dataclass
class NsParent(DomElem):
    NS: ClassVar[str | None] = NS_A
    child: NsChild


class TestNamespaces:
    def test_root_element_uses_class_namespace(self):
        elem = NsChild(name="x").to_xml()
        assert elem.tag == f"{{{NS_A}}}NsChild"

    def test_children_use_parent_namespace_by_default(self):
        elem = NsParent(child=NsChild("x")).to_xml(ns=NS_A)
        assert elem[0].tag == f"{{{NS_A}}}NsChild"


@dataclass
class ForeignChild(DomElem):
    NS: ClassVar[str | None] = NS_B
    name: str = field(metadata=xml_attr())


@dataclass
class MixedNsParent(DomElem):
    NS: ClassVar[str | None] = NS_A
    child: ForeignChild = field(metadata=xml_metadata(use_class_ns=True))


class TestUseClassNs:
    def test_child_written_with_its_own_namespace(self):
        elem = MixedNsParent(child=ForeignChild("x")).to_xml(ns=NS_A)
        assert elem[0].tag == f"{{{NS_B}}}ForeignChild"


class TestTag:
    def test_tag_without_namespace(self):
        assert Child.tag() == "Child"

    def test_tag_with_explicit_namespace(self):
        assert Child.tag(ns=NS_A) == f"{{{NS_A}}}Child"

    def test_tag_uses_class_ns_by_default(self):
        assert NsChild.tag() == f"{{{NS_A}}}NsChild"

    def test_explicit_ns_overrides_class_ns(self):
        assert NsChild.tag(ns=NS_B) == f"{{{NS_B}}}NsChild"

    def test_use_class_ns_ignores_explicit_ns(self):
        assert ForeignChild.tag(ns=NS_A, use_class_ns=True) == f"{{{NS_B}}}ForeignChild"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@dataclass
class PlainChild:
    x: str


@dataclass
class BrokenParent(DomElem):
    child: PlainChild


class TestNonDomElemChild:
    def test_missing_to_xml_raises_mapping_error(self):
        obj = BrokenParent(child=PlainChild(x="y"))
        with pytest.raises(XmlMappingError, match=r"BrokenParent\.child"):
            obj.to_xml()
