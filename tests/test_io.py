"""Tests for file I/O: pylsuq.load_xml and pylsuq.save_xml.

Covers document registration (is_document=True), reading, writing,
path handling and full round-trips.
"""
from dataclasses import dataclass, field

import pytest
from lxml import etree as et

from pylsuq.domelem import DomElem, xml_attr, load_xml, save_xml


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
class Child(DomElem):
    name: str = field(metadata=xml_attr())
    age: int = field(metadata=xml_attr())


@dataclass
class Family(DomElem, is_document=True):
    surname: str = field(metadata=xml_attr())
    children: list[Child] = field(default_factory=list)
    pet: Dog | Cat | None = None


@pytest.fixture
def family():
    return Family(
        surname="Doe",
        children=[Child("Charlie", 7), Child("Dora", 11)],
        pet=Cat("Ronja", fur_softness=0.999),
    )


class TestSaveXml:
    def test_writes_file(self, tmp_path, family):
        path = tmp_path / "family.xml"
        save_xml(path, family)
        assert path.exists()
        assert "<Family" in path.read_text()

    def test_written_xml_is_parseable(self, tmp_path, family):
        path = tmp_path / "family.xml"
        save_xml(path, family)
        root = et.parse(path).getroot()
        assert root.tag == "Family"
        assert root.get("surname") == "Doe"
        assert len(root.findall("Child")) == 2

    def test_accepts_str_path(self, tmp_path, family):
        path = str(tmp_path / "family.xml")
        save_xml(path, family)
        assert (tmp_path / "family.xml").exists()


class TestLoadXml:
    def test_loads_registered_document(self, tmp_path):
        path = tmp_path / "family.xml"
        path.write_text(
            '<Family surname="Doe"><Child name="Charlie" age="7"/></Family>'
        )
        obj = load_xml(path)
        assert isinstance(obj, Family)
        assert obj.surname == "Doe"
        assert obj.children == [Child("Charlie", 7)]

    def test_accepts_str_and_path(self, tmp_path):
        content = '<Family surname="Doe"/>'
        (tmp_path / "family.xml").write_text(content)
        from_str = load_xml(str(tmp_path / "family.xml"))
        from_path = load_xml(tmp_path / "family.xml")
        assert from_str == from_path

    def test_path_is_stored_in_context(self, tmp_path):
        path = tmp_path / "family.xml"
        path.write_text('<Family surname="Doe"/>')
        obj = load_xml(path)
        assert obj._ctx["path"] == path

    def test_unregistered_root_tag_raises_key_error(self, tmp_path):
        path = tmp_path / "unknown.xml"
        path.write_text('<UnregisteredDocument/>')
        with pytest.raises(KeyError):
            load_xml(path)


class TestRoundTrip:
    def test_save_then_load_gives_equal_object(self, tmp_path, family):
        path = tmp_path / "family.xml"
        save_xml(path, family)
        assert load_xml(path) == family

    def test_modify_then_resave(self, tmp_path, family):
        path = tmp_path / "family.xml"
        save_xml(path, family)

        loaded = load_xml(path)
        loaded.pet = Dog("Rex", favorite_food="Steak")
        loaded.children.append(Child("Eve", 1))
        save_xml(path, loaded)

        reloaded = load_xml(path)
        assert reloaded.pet == Dog("Rex", favorite_food="Steak")
        assert len(reloaded.children) == 3
