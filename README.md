# pylsuq

Python implementation of LS-UQ (Uncertainty Quantification) standard developed as part of the OpenSCALING project.

## Installation
```sh
pip install -e path/to/this/project
```

## File I/O
Loading and saving documents can be done through the `load_xml` and `save_xml` functions. The `load_xml` function automatically uses the correct Python class based on the tag name and namespace of the root element.

## XML &ndash; Python object
This implementation is based on a mini-library (included in this repo) intended to simplify the mapping between XML and Python objects. The mini-library is based on Python dataclasses. The following is a simple example of what is possible.
```python
from dataclasses import dataclass, field

from pylsuq import load_xml, save_xml
from pylsuq.domelem import DomElem, xml_attr


@dataclass
class Child(DomElem):
    name: str = field(metadata=xml_attr())
    age: int = field(metadata=xml_attr())


@dataclass
class Parent:
    name: str = field(metadata=xml_attr())
    occupation: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Father(DomElem, Parent):
    pass


@dataclass
class Mother(DomElem, Parent):
    pass


@dataclass
class Pet:
    name: str = field(metadata=xml_attr())


@dataclass
class Dog(DomElem, Pet):
    favorite_food: str = field(default="Bone", metadata=xml_attr(name="favoriteFood"))


@dataclass
class Cat(DomElem, Pet):
    fur_softness: float = field(default=0.5, metadata=xml_attr(name="furSoftness"))


@dataclass
class Family(DomElem, is_document=True):
    father: Father
    mother: Mother
    children: list[Child]
    pet: Dog | Cat | None = None


# Creating and saving a document
family = Family(
        father=Father(name="Bob"),
        mother=Mother(name="Alice", occupation="Software Security Engineer"),
        children=[Child("Charlie", 7), Child("Dora", 11)]
)
print(family)
save_xml("example.xml", family)

# Loading and inspecting a document
family = load_xml("example.xml")
print(len(family.children))  # 2

# Updating document
family.pet = Cat("Ronja", fur_softness=0.999)
save_xml("example.xml", family)
```

Result:
```xml
<Family>
  <Father name="Bob"/>
  <Mother name="Alice" occupation="Software Security Engineer"/>
  <Child name="Charlie" age="7"/>
  <Child name="Dora" age="11"/>
  <Cat name="Ronja" furSoftness="0.999"/>
</Family>
```

There is no ambition to document all the features availabe. Code is documentation :sunglasses:
