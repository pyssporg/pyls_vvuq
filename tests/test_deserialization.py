"""Tests for XML -> dataclass deserialization (DomElem.from_xml).

Each test class targets one branch of the deserialization logic in
pylsuq.domelem (_read_attr / _read_child), so failures isolate the
specific mapping kind: attributes, optionals, unions, lists, dicts,
single children and namespaces.
"""
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Union

from lxml import etree as et

from pylsuq.domelem import DomElem, xml_attr, xml_metadata


def parse(xml_string):
    return et.fromstring(xml_string.strip().encode())


# ---------------------------------------------------------------------------
# Attributes
# ---------------------------------------------------------------------------

@dataclass
class AttrLeaf(DomElem):
    name: str = field(metadata=xml_attr())
    age: int = field(metadata=xml_attr())


class TestSimpleAttributes:
    def test_reads_string_and_coerces_int(self):
        elem = parse('<AttrLeaf name="Bob" age="7"/>')
        obj = AttrLeaf.from_xml(elem)
        assert obj.name == "Bob"
        assert obj.age == 7
        assert isinstance(obj.age, int)


@dataclass
class OptionalAttrLeaf(DomElem):
    name: str = field(metadata=xml_attr())
    nickname: str | None = field(default=None, metadata=xml_attr())
    score: Optional[float] = field(default=None, metadata=xml_attr())


class TestOptionalAttributes:
    def test_optional_attr_present(self):
        elem = parse('<OptionalAttrLeaf name="A" nickname="Al" score="1.5"/>')
        obj = OptionalAttrLeaf.from_xml(elem)
        assert obj.nickname == "Al"
        assert obj.score == 1.5

    def test_optional_attr_absent_gives_none(self):
        elem = parse('<OptionalAttrLeaf name="A"/>')
        obj = OptionalAttrLeaf.from_xml(elem)
        assert obj.nickname is None
        assert obj.score is None


@dataclass
class CustomDeserLeaf(DomElem):
    coordinates: list[float] = field(
        metadata=xml_attr(deserialize=lambda s: [float(c) for c in s.split()])
    )


class TestCustomAttributeDeserializer:
    def test_custom_deserialize_callable_is_used(self):
        elem = parse('<CustomDeserLeaf coordinates="0 0.8 2.5"/>')
        obj = CustomDeserLeaf.from_xml(elem)
        assert obj.coordinates == [0.0, 0.8, 2.5]


@dataclass
class DefaultAttrLeaf(DomElem):
    name: str = field(metadata=xml_attr())
    sound: str = field(default="Woof", metadata=xml_attr())
    aliases: list = field(default_factory=list, metadata=xml_attr(
        deserialize=lambda s: s.split() if s else []
    ))


class TestDefaultValueAttributes:
    """An absent attribute with a dataclass default corresponds to an XSD
    attribute default: deserialization should yield the default value."""

    def test_absent_attr_uses_field_default(self):
        elem = parse('<DefaultAttrLeaf name="Rex"/>')
        obj = DefaultAttrLeaf.from_xml(elem)
        assert obj.sound == "Woof"

    def test_absent_attr_uses_field_default_factory(self):
        elem = parse('<DefaultAttrLeaf name="Rex"/>')
        obj = DefaultAttrLeaf.from_xml(elem)
        assert obj.aliases == []

    def test_present_attr_overrides_default(self):
        elem = parse('<DefaultAttrLeaf name="Rex" sound="Bark" aliases="rex rover"/>')
        obj = DefaultAttrLeaf.from_xml(elem)
        assert obj.sound == "Bark"
        assert obj.aliases == ["rex", "rover"]


@dataclass
class RenamedAttrLeaf(DomElem):
    fur_softness: float = field(metadata=xml_attr(name="furSoftness"))


class TestRenamedAttribute:
    def test_attr_name_override_is_used(self):
        elem = parse('<RenamedAttrLeaf furSoftness="0.999"/>')
        obj = RenamedAttrLeaf.from_xml(elem)
        assert obj.fur_softness == 0.999


class TestInheritedAttributes:
    @dataclass
    class PersonBase:
        name: str = field(metadata=xml_attr())
        occupation: str | None = field(default=None, metadata=xml_attr())

    @dataclass
    class Parent(DomElem, PersonBase):
        pass

    def test_fields_inherited_from_plain_base_class(self):
        elem = parse('<Parent name="Alice" occupation="Engineer"/>')
        obj = self.Parent.from_xml(elem)
        assert obj.name == "Alice"
        assert obj.occupation == "Engineer"


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
    def test_reads_single_child(self):
        elem = parse('<SingleChildParent><Child name="c1"/></SingleChildParent>')
        obj = SingleChildParent.from_xml(elem)
        assert obj.child == Child(name="c1")


@dataclass
class ListParent(DomElem):
    children: list[Child] = field(default_factory=list)


class TestListChildren:
    def test_reads_multiple_children(self):
        elem = parse(
            '<ListParent>'
            '<Child name="a"/><Child name="b"/><Child name="c"/>'
            '</ListParent>'
        )
        obj = ListParent.from_xml(elem)
        assert obj.children == [Child("a"), Child("b"), Child("c")]

    def test_no_children_gives_empty_list(self):
        elem = parse('<ListParent/>')
        obj = ListParent.from_xml(elem)
        assert obj.children == []


@dataclass
class DictParent(DomElem):
    children: dict[str, Child] = field(default_factory=dict)


class TestDictChildren:
    def test_children_keyed_by_key_fn(self):
        elem = parse(
            '<DictParent><Child name="a"/><Child name="b"/></DictParent>'
        )
        obj = DictParent.from_xml(elem)
        assert obj.children == {"a": Child("a"), "b": Child("b")}

    def test_no_children_gives_empty_dict(self):
        elem = parse('<DictParent/>')
        obj = DictParent.from_xml(elem)
        assert obj.children == {}


@dataclass
class OptionalChildParent(DomElem):
    child: Optional[Child] = None


class TestOptionalChild:
    def test_optional_child_present(self):
        elem = parse('<OptionalChildParent><Child name="x"/></OptionalChildParent>')
        obj = OptionalChildParent.from_xml(elem)
        assert obj.child == Child("x")

    def test_optional_child_absent_gives_none(self):
        elem = parse('<OptionalChildParent/>')
        obj = OptionalChildParent.from_xml(elem)
        assert obj.child is None


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


@dataclass
class OptionalUnionParent(DomElem):
    pet: Dog | Cat | None = None


class TestUnionChild:
    def test_first_union_member_matches(self):
        elem = parse('<UnionParent><Dog name="Rex" favoriteFood="Steak"/></UnionParent>')
        obj = UnionParent.from_xml(elem)
        assert obj.pet == Dog(name="Rex", favorite_food="Steak")

    def test_second_union_member_matches(self):
        elem = parse('<UnionParent><Cat name="Ronja" furSoftness="0.7"/></UnionParent>')
        obj = UnionParent.from_xml(elem)
        assert obj.pet == Cat(name="Ronja", fur_softness=0.7)

    def test_no_member_present_gives_none(self):
        elem = parse('<UnionParent/>')
        obj = UnionParent.from_xml(elem)
        assert obj.pet is None

    def test_optional_union_none_member_is_skipped(self):
        elem = parse('<OptionalUnionParent><Dog name="Rex"/></OptionalUnionParent>')
        obj = OptionalUnionParent.from_xml(elem)
        assert obj.pet == Dog(name="Rex")


# ---------------------------------------------------------------------------
# Namespaces
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
    def test_reads_namespaced_children(self):
        elem = parse(
            f'<NsParent xmlns="{NS_A}"><NsChild name="x"/></NsParent>'
        )
        obj = NsParent.from_xml(elem, ns=NS_A)
        assert obj.child == NsChild("x")

    def test_child_class_ns_used_as_fallback(self):
        # Even without an explicit ns argument, the child's own NS is used.
        elem = parse(
            f'<NsParent xmlns="{NS_A}"><NsChild name="x"/></NsParent>'
        )
        obj = NsParent.from_xml(elem)
        assert obj.child == NsChild("x")


@dataclass
class ForeignChild(DomElem):
    NS: ClassVar[str | None] = NS_B
    name: str = field(metadata=xml_attr())


@dataclass
class MixedNsParent(DomElem):
    NS: ClassVar[str | None] = NS_A
    child: ForeignChild = field(metadata=xml_metadata(use_class_ns=True))


class TestUseClassNs:
    def test_child_read_with_its_own_namespace(self):
        elem = parse(
            f'<MixedNsParent xmlns="{NS_A}" xmlns:b="{NS_B}">'
            f'<b:ForeignChild name="x"/>'
            f'</MixedNsParent>'
        )
        obj = MixedNsParent.from_xml(elem, ns=NS_A)
        assert obj.child == ForeignChild("x")
