from typing import Any
from collections.abc import MutableMapping


class Context(MutableMapping):
    parent: "Context | None"
    mapping: dict[str, Any]

    def __init__(self, parent=None, mapping=None):
        self.parent = parent
        self.mapping = mapping if mapping is not None else {}

    def __getitem__(self, key):
        cur = self
        while cur is not None:
            if key in cur.mapping:
                return cur.mapping[key]

            cur = cur.parent

        raise KeyError(f"Key {key!r} not found in Context or any ancestor")

    def __setitem__(self, key, value):
        self.mapping[key] = value

    def __delitem__(self, key):
        del self.mapping[key]

    def __len__(self):
        keys = set()
        cur = self
        while cur is not None:
            keys |= cur.mapping.keys()

            cur = cur.parent

        return len(keys)

    def __iter__(self):
        keys = set()
        cur = self
        while cur is not None:
            keys |= cur.mapping.keys()

            cur = cur.parent

        return iter(keys)

    def __repr__(self):
        return f"Context(parent={self.parent!r}, {self.mapping!r})"
