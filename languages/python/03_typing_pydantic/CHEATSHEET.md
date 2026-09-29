# CHEATSHEET: Advanced Typing & Pydantic V2

## 1. Quick Syntax Reference (Python 3.10 - 3.12+)

| Feature | Pre-3.10 / Legacy | Modern Python (3.10 - 3.12+) | Use Case |
| :--- | :--- | :--- | :--- |
| **Union Types** | `Union[int, str]` | `int \| str` | Declaring variable can be one of multiple types. |
| **Optional** | `Optional[str]` | `str \| None` | Variable can be type or None. |
| **Type Alias** | `Vector = List[float]` | `type Vector = list[float]` (3.12) | Defining clean, reusable names for complex types. |
| **Generic Alias** | `T = TypeVar('T')`<br>`Map = Dict[str, T]` | `type Map[T] = dict[str, T]` (3.12) | Type aliases that accept type parameters. |
| **Collections** | `Dict`, `List`, `Set` | `dict`, `list`, `set` | Use built-in lowercase collections for typing. |

---

## 2. Pydantic V1 vs V2 Equivalents

| Concept | Pydantic V1 | Pydantic V2 | Notes |
| :--- | :--- | :--- | :--- |
| **Base Model** | `from pydantic import BaseModel` | `from pydantic import BaseModel` | Same base, entirely new Rust engine underneath. |
| **Field Validation**| `@validator('name')` | `@field_validator('name')` | Must be a `@classmethod` in V2. |
| **Root Validation** | `@root_validator` | `@model_validator(mode='after')` | Use `mode='before'` for raw dict manipulation. |
| **Dict Export** | `model.dict()` | `model.model_dump()` | All core methods prefixed with `model_` to avoid namespace collisions. |
| **JSON Export** | `model.json()` | `model.model_dump_json()` | Faster JSON serialization powered by `pydantic-core`. |
| **Settings** | `from pydantic import BaseSettings` | `from pydantic_settings import BaseSettings` | Moved to standalone package `pydantic-settings`. |
| **Custom Schema** | `__modify_schema__` | `__get_pydantic_core_schema__` | Generates Rust-compatible CoreSchema directly. |

---

## 3. Pydantic Architecture (ASCII Diagram)

```text
+-------------------------------------------------------------+
|                     Python Application                      |
|  user = User(id=1, name="Alice", email="alice@test.com")    |
+------------------------------|------------------------------+
                               | Instantiation triggers validation
+------------------------------v------------------------------+
|                        pydantic (V2)                        |
|  (Builds Python API, decorators, and routing structures)    |
+------------------------------|------------------------------+
                               | Compiles model to CoreSchema
+------------------------------v------------------------------+
|                    pydantic-core (Rust)                     |
|  +-------------------------------------------------------+  |
|  | State Machine Validator:                              |  |
|  | 1. Type Coercion (e.g., str -> int)                   |  |
|  | 2. Constraint Checks (gt, lt, min_length)             |  |
|  | 3. Rust-speed JSON parsing                            |  |
|  +-------------------------------------------------------+  |
+------------------------------|------------------------------+
                               | Returns Validated Data or Errors
+------------------------------v------------------------------+
|            Python Objects / Validation Exception            |
+-------------------------------------------------------------+
```

---

## 4. Variance Cheatsheet

| Variance Type | Definition | Syntax Example | When to use |
| :--- | :--- | :--- | :--- |
| **Invariance** | Strict matching required. `List[Dog] != List[Animal]` | `T = TypeVar('T')` | Mutable collections (e.g., lists, dicts). |
| **Covariance** | Subtype can replace supertype. `Seq[Dog] <= Seq[Animal]` | `T = TypeVar('T', covariant=True)` | Read-only collections, return types. |
| **Contravariance**| Supertype can replace subtype. `Call[Animal] <= Call[Dog]`| `T = TypeVar('T', contravariant=True)`| Input arguments, callable parameters, consumers. |

---

## 5. Useful Typing Imports

```python
from typing import (
    Any, Callable, Literal, Protocol, TypeVar, Generic, ParamSpec, 
    TypeAlias, TypedDict, runtime_checkable, Annotated, Self
)
# Python 3.10+ / typing_extensions
from typing import TypeGuard, TypeIs, Unpack
```
