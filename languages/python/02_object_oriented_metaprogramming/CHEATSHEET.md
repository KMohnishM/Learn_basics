# Module 2: Object-Oriented Metaprogramming - Cheatsheet

## C3 Linearization Merge Rules & MRO Lookup Flow

**Formula:** `L(C) = [C] + merge(L(B1), L(B2), ..., L(Bn), [B1, B2, ..., Bn])`

**Merge Process:**
1. Look at the **head** (first element) of the first list.
2. Is it a **Good Head**? (A class is a good head if it does NOT appear in the **tail** of any other list).
3. If YES: Extract it, add it to the final MRO, and remove it from all lists in the merge.
4. If NO: Move to the head of the next list and check again.
5. Repeat until all lists are empty. If no good head can be found and lists are not empty, raise `TypeError`.

**Example:**
```python
class O: pass
class A(O): pass
class B(O): pass
class C(O): pass
class K1(A, B, C): pass
class K2(B, A): pass # Notice flipped A, B order
# class Z(K1, K2): pass -> Raises TypeError: MRO conflict!
```

---

## Descriptor Protocol Lookup Priority Hierarchy

When evaluating `instance.attribute`, Python resolves the lookup strictly in this order:

1. **Data Descriptors** (on class/MRO)
   *(Implements `__set__` or `__delete__`)*
   *(Overrides instance dictionary entirely)*
2. **Instance Dictionary**
   *(Found in `instance.__dict__`)*
3. **Non-Data Descriptors** (on class/MRO)
   *(Implements only `__get__`)*
   *(Methods, `@classmethod`, `@staticmethod` fall here)*
4. **Class Dictionary / MRO Base Classes**
   *(Found in `type(instance).__dict__`)*
5. **Fallback `__getattr__`**
   *(If defined on the class)*
6. **Error**
   *(Raises `AttributeError`)*

---

## Metaclass vs `__init_subclass__` Syntax

### Modern Approach (`__init_subclass__`)
Best for simple class registry, modifying subclass properties, or dependency injection.
```python
class PluginBase:
    registry = []
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("Base"):
            cls.registry.append(cls)
```

### Heavy Metaprogramming Approach (`metaclass`)
Best for modifying class creation logic, parsing descriptors before class execution, or injecting custom `__prepare__` namespaces.
```python
class RegistryMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if not name.startswith("Base"):
            cls.registry.append(cls)
        return cls

class PluginBase(metaclass=RegistryMeta):
    registry = []
```

---

## Protocol & ABC Declaration Boilerplate

### Abstract Base Class (Nominal Subtyping)
Requires explicit inheritance. Fails at instantiation if incomplete.
```python
import abc

class Repository(abc.ABC):
    @abc.abstractmethod
    def save(self, data: dict) -> bool:
        pass

# Fails if save() is not implemented
class PostgresRepo(Repository): 
    def save(self, data: dict) -> bool:
        return True
```

### Protocol (Structural Subtyping / Static Duck Typing)
Requires NO inheritance. Mypy checks structure automatically.
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str:
        ...

class Button:
    # No inheritance needed!
    def render(self) -> str:
        return "<button></button>"

def draw(element: Renderable):
    print(element.render())

# Runtime check works due to @runtime_checkable
assert isinstance(Button(), Renderable) 
```
