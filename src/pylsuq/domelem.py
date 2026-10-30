from abc import ABC
from collections.abc import Callable
from typing import Union, Any, Optional, ClassVar, Literal, get_args, get_origin
import types
import warnings
from dataclasses import dataclass, field, fields, MISSING, InitVar
from importlib.resources import files as resource_files
from operator import attrgetter
from pathlib import Path
from enum import Enum
from lxml import etree as et

from pylsuq.context import Context
from pylsuq.errors import (
    XmlMappingError,
    mapping_error,
    XmlSchemaValidationWarning,
    schema_error,
    schema_message,
)


METADATA_KEY = "pylsuq"

ValidateMode = Literal["raise", "warn", "off"]
VALIDATE_MODES = ("raise", "warn", "off")


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

def xml_attr_value(value):    
    if isinstance(value,Enum):
        return value.value
    return value

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
        value = elem.get(name)
        if value is None:  # Absent attribute
            if field_.default is not MISSING:
                return field_.default
            if field_.default_factory is not MISSING:
                return field_.default_factory()
            raise XmlMappingError(f"Missing required attribute {name!r}")
        return deserialize(value)


def _read_child(field_, metadata, elem, ns=None):
    if get_origin(field_.type) is list:  # macOccurs > 1
        type_ = get_args(field_.type)[0]
        if is_union(type_):  # heterogeneous list: dispatch per child by tag
            members = {
                member.tag(ns=ns, use_class_ns=metadata.use_class_ns): member
                for member in get_args(type_)
                if member is not type(None)
            }
            return [members[e.tag].from_xml(e) for e in elem if e.tag in members]
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
        child = elem.find(tag)
        if child is None:
            raise XmlMappingError(f"Missing required element <{tag}>")
        return field_.type.from_xml(child)




def _write_attr(obj, field_, metadata, elem):
    value = getattr(obj, field_.name)    
    
    value = xml_attr_value(value)
    
    if not has_default_value(field_, value):
        name = metadata.name or field_.name
        elem.set(name, metadata.serialize(value))


def _write_child(obj, field_, metadata, elem):
    value = getattr(obj, field_.name)
    if get_origin(field_.type) is list:
        type_ = get_args(field_.type)[0]
        if is_union(type_):
            # Members are heterogeneous types: take the namespace from
            # each value rather than the (union) field type.
            elem.extend([
                e.to_xml(ns=type(e).NS if metadata.use_class_ns else obj.NS)
                for e in value
            ])
        else:
            child_ns = type_.NS if metadata.use_class_ns else obj.NS
            elem.extend([e.to_xml(ns=child_ns) for e in value])
    elif get_origin(field_.type) is dict:
        # Keys are redundant: they are derived from the values with
        # metadata.key_fn on deserialization, so only values are written.
        type_ = get_args(field_.type)[1]
        child_ns = type_.NS if metadata.use_class_ns else obj.NS
        elem.extend([e.to_xml(ns=child_ns) for e in value.values()])
    elif is_optional(field_.type):
        if value is not None:
            child_ns = value.NS if metadata.use_class_ns else obj.NS
            elem.append(value.to_xml(ns=child_ns))
    elif is_union(field_.type):
        if value is not None:
            child_ns = value.NS if metadata.use_class_ns else obj.NS
            elem.append(value.to_xml(ns=child_ns))    
    else:
        child_ns = value.NS if metadata.use_class_ns else obj.NS
        elem.append(value.to_xml(ns=child_ns))


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
            metadata = field_.metadata.get(METADATA_KEY, FieldMetadata())

            try:
                if metadata.is_attr:
                    args[field_.name] = _read_attr(field_, metadata, elem)
                else:
                    args[field_.name] = _read_child(field_, metadata, elem, ns)
            except Exception as e:
                raise mapping_error("read", cls, field_, metadata, e) from e

        return cls(**args)

    def to_xml(self, ns: str | None = None) -> et.Element:
        self._pre_serialize()

        elem = et.Element(self.tag(ns=ns), nsmap=NSMAP)

        for field_ in fields(self):
            metadata = field_.metadata.get(METADATA_KEY, FieldMetadata())
            
            try:
                if metadata.is_attr:
                    _write_attr(self, field_, metadata, elem)
                else:
                    _write_child(self, field_, metadata, elem)
            except Exception as e:
                raise mapping_error("write", type(self), field_, metadata, e) from e

        return elem

    @classmethod
    def tag(cls, ns=None, use_class_ns=False):
        if use_class_ns:
            ns = cls.NS
        else:
            ns = ns or cls.NS

        return et.QName(ns, cls.__name__)

    def __init_subclass__(cls, is_document=False, schema: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)

        if schema is not None and not is_document:
            raise TypeError(
                f"{cls.__name__}: schema={schema!r} requires is_document=True"
            )

        if is_document:
            _doctype_registry[cls.tag()] = cls
            if schema is not None:
                _schema_registry[cls] = schema

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
_schema_registry: dict[type, str] = {}
_schema_cache: dict[str, et.XMLSchema] = {}


def _schema_path(name: str) -> str:
    """Filesystem path of the bundled XSD entry point `name`."""
    return str(resource_files("pylsuq").joinpath("schema", name))


def _get_schema(name: str) -> et.XMLSchema:
    """The compiled schema for entry point `name`, cached across calls.

    lxml resolves xs:import and xs:include through the relative
    schemaLocation hints in the entry file, so one compiled XMLSchema per
    entry point covers the whole multi-file grammar.
    """
    if name not in _schema_cache:
        _schema_cache[name] = et.XMLSchema(et.parse(_schema_path(name)))
    return _schema_cache[name]


def _check_validate_mode(validate: ValidateMode):
    if validate not in VALIDATE_MODES:
        raise ValueError(
            f"validate must be one of {', '.join(map(repr, VALIDATE_MODES))}, "
            f"got {validate!r}"
        )


def _validate_document(elem, cls: type, where: str, validate: ValidateMode):
    """XSD-validate a document (Element or tree) of document class `cls`.

    Checks `elem` against the schema registered for `cls`, if any:
    schema violations are warned about ("warn") or raised as
    XmlSchemaValidationError ("raise"). The mode must already have been
    confirmed with _check_validate_mode.
    """
    if validate == "off":
        return

    schema_name = _schema_registry.get(cls)
    if schema_name is None:  # No schema registered: nothing to validate against
        return

    schema = _get_schema(schema_name)
    if schema.validate(elem):
        return

    if validate == "raise":
        raise schema_error(schema_name, schema.error_log, where)
    warnings.warn(
        schema_message(schema_name, schema.error_log, where),
        XmlSchemaValidationWarning,
        stacklevel=3,
    )


def load_xml(path: str | Path, validate: ValidateMode = "off"):
    """Parse the XML document at `path` into its registered document class.

    validate: "off" (default, no validation), "warn" (warn on schema
    violations) or "raise" (raise XmlSchemaValidationError). Checked
    before deserialization, so schema problems are reported even when
    the document could not be mapped either.
    """
    _check_validate_mode(validate)
    tree = et.parse(path)
    root = tree.getroot()

    cls = _doctype_registry[root.tag]
    _validate_document(tree, cls, str(path), validate)

    obj = cls.from_xml(root)
    obj._ctx["path"] = path

    return obj


def save_xml(path: str | Path, elem, pretty_print=True, validate: ValidateMode = "warn"):
    """Serialize `elem` to `path`, then XSD-validate the written document.

    The file is always written first, so a document that violates its
    schema can still be inspected.

    validate: "warn" (default, warn on schema violations), "raise" (raise
    XmlSchemaValidationError) or "off" (no validation).
    """
    _check_validate_mode(validate)
    xml_elem = elem.to_xml()
    et.cleanup_namespaces(xml_elem)
    with open(path, "w") as f:
        f.write(et.tostring(xml_elem, encoding=str, pretty_print=pretty_print))

    # Re-parse the written file: violations then point at real line/column
    # numbers of the document on disk.
    _validate_document(et.parse(path), type(elem), str(path), validate)
