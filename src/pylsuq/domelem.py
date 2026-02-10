from abc import ABC
from collections.abc import Callable
from typing import Union, Any, Optional, ClassVar, get_args, get_origin
import types
from dataclasses import dataclass, field, fields, MISSING, InitVar
from operator import attrgetter

from lxml import etree as et

from pylsuq.context import Context


METADATA_KEY = "pylsuq"


@dataclass
class FieldMetadata:
    is_attr: bool = False
    name: str | None = None
    serialize: Callable[[Any], str] = str
    deserialize: Callable[[str], Any] | None = None
    use_class_ns: bool = False
    key_fn: Callable[[Any], str] = attrgetter("name")


def xml_metadata(**kwargs):
    return {METADATA_KEY: FieldMetadata(**kwargs)}


def xml_attr(**kwargs):
    return xml_metadata(is_attr=True, **kwargs)


NSMAP = {}


def register_namespace(nickname, namespace):
    et.register_namespace(nickname, namespace)
    NSMAP[nickname] = namespace

# TODO: element groups


def is_optional(type_):
    """An optional is either Optional[T], Union[T, None] or T | None."""
    origin = get_origin(type_)
    args = get_args(type_)

    if origin in {Union, types.UnionType}:
        return len(args) == 2 and args[1] is types.NoneType

    return origin is Optional


def is_union(type_):
    """A union is a union with at least two non-None types as options."""
    origin = get_origin(type_)
    args = get_args(type_)

    if origin in {Union, types.UnionType}:
        return sum(1 for x in args if x is not types.NoneType) >= 2


def has_default_value(field_, value):
    if field_.default is MISSING and field_.default_factory is MISSING:
        return False

    if field_.default is not MISSING:
        return value == field_.default
    else:
        return value == field_.default_factory()


def _read_attr(field_, metadata, elem):
    name = metadata.name or field_.name
    deserialize = metadata.deserialize
    if is_optional(field_.type):
        value = elem.get(name)
        deserialize = deserialize or get_args(field_.type)[0]
        return deserialize(value) if value is not None else None
    else:
        deserialize = deserialize or field_.type
        return deserialize(elem.get(name))


def _read_child(field_, metadata, elem, ns=None):
    if get_origin(field_.type) is list:  # macOccurs > 1
        type_ = get_args(field_.type)[0]
        tag = type_.tag(ns=ns, use_class_ns=metadata.use_class_ns)
        return [type_.from_xml(e) for e in elem.findall(tag)]
    elif get_origin(field_.type) is dict:  # keyed maxOccurs > 1
        type_ = get_args(field_.type)[1]
        tag = type_.tag(ns=ns, use_class_ns=metadata.use_class_ns)
        children = (type_.from_xml(e) for e in elem.findall(tag))
        return {metadata.key_fn(child): child for child in children}
    elif is_optional(field_.type):  # minOccurs == 0, maxOccurs == 1
        type_ = get_args(field_.type)[0]
        tag = type_.tag(ns=ns, use_class_ns=metadata.use_class_ns)
        child = elem.find(tag)
        return type_.from_xml(child) if child is not None else None
    elif is_union(field_.type):
        for type_ in get_args(field_.type):
            if type_ is type(None):
                continue
            child = elem.find(type_.tag(ns=ns, use_class_ns=metadata.use_class_ns))
            if child is not None:
                return type_.from_xml(child)
        else:  # No union member is present
            return None
    else:
        tag = field_.type.tag(ns=ns, use_class_ns=metadata.use_class_ns)
        return field_.type.from_xml(elem.find(tag))


class DomElem:
    NS: ClassVar[str | None] = None
    # _ctx: InitVar[ChainMap]
    # ChainMap för rekursive kontext

    def __post_init__(self):
        self._ensure_ctx_init()

    @classmethod
    def from_xml(cls: type, elem: et.Element, ns: str | None = None):
        args = {}

        for field_ in fields(cls):
            if METADATA_KEY in field_.metadata:
                metadata = field_.metadata[METADATA_KEY]
            else:
                metadata = FieldMetadata()

            if metadata.is_attr:
                args[field_.name] = _read_attr(field_, metadata, elem)
            else:
                args[field_.name] = _read_child(field_, metadata, elem, ns)

        return cls(**args)

    def to_xml(self, ns: str | None = None) -> et.Element:
        self._pre_serialize()

        elem = et.Element(self.tag(ns=ns), nsmap=NSMAP)

        for field_ in fields(self):
            if METADATA_KEY in field_.metadata:
                metadata = field_.metadata[METADATA_KEY]
            else:
                metadata = FieldMetadata()

            value = getattr(self, field_.name)

            if metadata.is_attr:
                name = metadata.name or field_.name
                if not has_default_value(field_, value):
                    elem.set(name, metadata.serialize(value))
            else:
                if get_origin(field_.type) is list:
                    type_ = get_args(field_.type)[0]
                    child_ns = type_.NS if metadata.use_class_ns else self.NS
                    elem.extend([e.to_xml(ns=child_ns) for e in value])
                elif is_optional(field_.type):
                    if value is not None:
                        child_ns = value.NS if metadata.use_class_ns else self.NS
                        elem.append(value.to_xml(ns=child_ns))
                elif is_union(field_.type):
                    if value is not None:
                        child_ns = value.NS if metadata.use_class_ns else self.NS
                        elem.append(value.to_xml(ns=child_ns))
                else:
                    value = getattr(self, field_.name)
                    child_ns = value.NS if metadata.use_class_ns else self.NS
                    elem.append(value.to_xml(ns=child_ns))

        return elem

    @classmethod
    def tag(cls, ns=None, use_class_ns=False):
        if use_class_ns:
            ns = cls.NS
        else:
            ns = ns or cls.NS

        return et.QName(ns, cls.__name__)

    def __init_subclass__(cls, is_document=False, **kwargs):
        super().__init_subclass__(**kwargs)

        if is_document:
            _doctype_registry[cls.tag()] = cls

    def _ensure_ctx_init(self):
        if not hasattr(self, "_ctx") or self._ctx is None:
            self._ctx = Context()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if isinstance(value, DomElem):
            self._ensure_ctx_init()
            value._ctx.parent = self._ctx

    def _pre_serialize(self):
        pass  # Do nothing pre serialize by default


_doctype_registry = {}


def load_xml(path):
    tree = et.parse(path)

    root = tree.getroot()

    obj = _doctype_registry[root.tag].from_xml(root)
    obj._ctx["path"] = path

    return obj


def save_xml(path, elem, pretty_print=True):
    xml_elem = elem.to_xml()
    et.cleanup_namespaces(xml_elem)
    with open(path, "w") as f:
        f.write(et.tostring(xml_elem, encoding=str, pretty_print=True))
