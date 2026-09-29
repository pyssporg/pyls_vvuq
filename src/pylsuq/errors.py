"""Diagnostic error types for the XML <-> dataclass mapping layer.

This module centralizes error reporting for pylsuq.domelem, so that the
serialization/deserialization mechanics can stay free of error-handling
clutter. Mapping code raises plain exceptions; the from_xml/to_xml field
loops catch them and re-raise XmlMappingError with the class and field
where the problem actually resides.
"""
from typing import get_args, get_origin


class XmlMappingError(Exception):
    """Raised when a DomElem dataclass field cannot be mapped to or from
    XML.

    The message identifies the class and member where the problem
    occurred; the original exception is preserved in __cause__. For
    nested elements the inner XmlMappingError becomes the cause, so the
    full message traces the path from the failing class down to the
    root cause.
    """


def describe_field(cls: type, field_, is_attr: bool) -> str:
    """Human-readable location of a dataclass field.

    Example: "Family.pet (child element)"
    """
    kind = "attribute" if is_attr else "child element"
    return f"{cls.__name__}.{field_.name} ({kind})"


def mapping_error(direction: str, cls: type, field_, metadata, err: Exception) -> "XmlMappingError":
    """Build an XmlMappingError locating the failure at cls.field_,
    appending a hint for common declaration mistakes when detected.
    """
    msg = f"Could not {direction} {describe_field(cls, field_, metadata.is_attr)}: {err}"
    hint = field_hint(field_, metadata)
    if hint:
        msg += f"\n  hint: {hint}"
    return XmlMappingError(msg)


def field_hint(field_, metadata) -> str:
    """A likely cause of a mapping failure, or "" when nothing applicable.

    Kept apart from the mapping code on purpose: hints are best-effort
    heuristics for frequent declaration mistakes, not logic.
    """
    if metadata.is_attr:
        if metadata.deserialize is not None or metadata.serialize is not str:
            return ("the custom serialize/deserialize callable in the "
                    "field metadata raised this error")
        return ""

    if get_origin(field_.type) is dict:
        return "dict fields can only be deserialized so far; serialization is not implemented"

    type_ = _declared_child_type(field_)
    if isinstance(type_, type) and not hasattr(type_, "from_xml"):
        return (f"{type_.__name__!r} is not a DomElem subclass; make it "
                "inherit DomElem or map the field to an XML attribute "
                "with metadata=xml_attr()")
    return ""


def _declared_child_type(field_):
    """Unwrap list/dict/Optional/Union to the declared child class."""
    origin = get_origin(field_.type)
    if origin is list:
        return get_args(field_.type)[0]
    if origin is dict:
        return get_args(field_.type)[1]
    for arg in get_args(field_.type):
        if arg is not type(None):
            return arg
    return field_.type
