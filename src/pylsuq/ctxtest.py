from dataclasses import dataclass, field, KW_ONLY

from lxml import etree as et

from domelem import DomElem, xml_attr


@dataclass
class Inner(DomElem):
    alternate: str = field(metadata=xml_attr())
    use_base: bool = field(metadata=xml_attr(deserialize=lambda s: s == "True"))

    def result(self):
        if self.use_base:
            return self._ctx["base"]
        else:
            return self.alternate


@dataclass
class Outer(DomElem):
    base: str = field(metadata=xml_attr())
    inner: Inner

    def __post_init__(self):
        super().__post_init__()
        self._ctx["base"] = self.base


def main():
    ex1 = r"""
<Outer base="base-value">
    <Inner alternate="alt-value" use_base="True" />
</Outer>
"""

    elem = et.fromstring(ex1)
    outer = Outer.from_xml(elem)
    print(outer.inner.result())

    inner = Inner(alternate="alt-value2", use_base=True)
    outer2 = Outer(base="base-value2", inner=inner)

    print(inner.result())


if __name__ == "__main__":
    main()
