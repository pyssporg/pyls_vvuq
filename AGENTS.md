# AGENTS.md - pylsuq

## Workflow
- **Installation**: `pip install -e .` (add `.[dev]` for test dependencies)
- **Testing**: Run `pytest` (uses the project's venv). Test suite lives in `tests/` and covers the core XML ↔ dataclass layer (`domelem.py`): `test_deserialization.py` (`from_xml`), `test_serialization.py` (`to_xml`) and `test_io.py` (`load_xml`/`save_xml`). Examples in `examples/` can be used for further manual verification.

## Core Logic: XML ↔ Python
- **`DomElem`**: Base class for any dataclass intended to map to an XML element.
- **`xml_attr()`**: Used in `field(metadata=xml_attr())` to define a field as an XML attribute rather than a child element.
- **Document Registration**: Use `DomElem(is_document=True)` in the class definition to register it as a root document type for `load_xml`.
- **I/O**: `pylsuq.load_xml(path)` and `pylsuq.save_xml(path, obj)` are the primary entry points.

## Error Diagnostics
- Mapping problems raise `pylsuq.errors.XmlMappingError`, which names the class and field where the issue is (also exported as `pylsuq.XmlMappingError`).
- `pylsuq.errors.mapping_error()`/`field_hint()` append best-effort hints for common declaration mistakes (non-`DomElem` child types, missing `xml_attr()`, failing custom callables).
- Error handling is deliberately separated from the mapping mechanics: `from_xml`/`to_xml` wrap per-field failures with class/member context, while `_read_*`/`_write_*` helpers raise plain exceptions. Keep this separation when extending the layer.

## Type Mapping (DomElem)
The library interprets Python type hints to determine XML structure:
- `list[T]`: Multiple child elements of type `T`.
- `dict[K, V]`: Keyed multiple child elements of type `V`. Keys are never written to XML — they are re-derived from the values with `key_fn` on deserialization.
- `Optional[T]` or `T | None`: Zero or one child element of type `T`.
- `Union[T, ...]` or `T | U`: One of several possible child types (the first match wins).
- `T` (Single Type): Exactly one child element of type `T`.
- **Attributes**: Only fields marked with `xml_attr()` are mapped to XML attributes; all others are treated as child elements.

## Project Structure
- **Core Logic**: `src/pylsuq/`
- **Examples**: `examples/`
- **Dependencies**: Requires `lxml`.
