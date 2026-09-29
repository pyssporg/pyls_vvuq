# AGENTS.md - pylsuq

## Workflow
- **Installation**: `pip install -e .` (add `.[dev]` for test dependencies)
- **Testing**: Run `pytest` (uses the project's venv). Test suite lives in `tests/` and covers the core XML ↔ dataclass layer (`domelem.py`): `test_deserialization.py` (`from_xml`), `test_serialization.py` (`to_xml`) and `test_io.py` (`load_xml`/`save_xml`). Examples in `examples/` can be used for further manual verification.

## Core Logic: XML ↔ Python
- **`DomElem`**: Base class for any dataclass intended to map to an XML element.
- **`xml_attr()`**: Used in `field(metadata=xml_attr())` to define a field as an XML attribute rather than a child element.
- **Document Registration**: Use `DomElem(is_document=True)` in the class definition to register it as a root document type for `load_xml`.
- **I/O**: `pylsuq.load_xml(path)` and `pylsuq.save_xml(path, obj)` are the primary entry points.

## Type Mapping (DomElem)
The library interprets Python type hints to determine XML structure:
- `list[T]`: Multiple child elements of type `T`.
- `dict[K, V]`: Keyed multiple child elements of type `V`.
- `Optional[T]` or `T | None`: Zero or one child element of type `T`.
- `Union[T, ...]` or `T | U`: One of several possible child types (the first match wins).
- `T` (Single Type): Exactly one child element of type `T`.
- **Attributes**: Only fields marked with `xml_attr()` are mapped to XML attributes; all others are treated as child elements.

## Project Structure
- **Core Logic**: `src/pylsuq/`
- **Examples**: `examples/`
- **Dependencies**: Requires `lxml`.
