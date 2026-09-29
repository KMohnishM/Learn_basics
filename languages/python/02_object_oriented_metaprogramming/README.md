# Module 2: Object-Oriented Metaprogramming

## 1. Multiple Inheritance & C3 Linearization (MRO)

Python natively supports multiple inheritance, allowing a class to derive from more than one base class. While this enables powerful mixin-based architectures, it introduces ambiguity known as the "Diamond Problem": if both parent classes define the same method, which one should the child inherit?

### Method Resolution Order (MRO)
Python solves this ambiguity using a strict algorithm called Method Resolution Order (MRO). You can inspect the MRO of any class at runtime using `cls.__mro__` or `cls.mro()`. The MRO guarantees a linear, predictable sequence in which Python searches for attributes and methods.

### The C3 Linearization Algorithm
Python 2.3 introduced the C3 Linearization algorithm to compute the MRO. It strictly enforces two constraints:
1. Children precede their parents.
2. If a class inherits from multiple parents, they are checked in the order specified in the base class tuple.

The mathematical formula for C3 is:
`L(C) = [C] + merge(L(B1), L(B2), ..., L(Bn), [B1, B2, ..., Bn])`

**Step-by-step example:**
Consider a diamond hierarchy:
```python
class Base: pass
class A(Base): pass
class B(Base): pass
class Child(A, B): pass
```
1. `L(Base) = [Base]`
2. `L(A) = [A, Base]`
3. `L(B) = [B, Base]`
4. `L(Child) = [Child] + merge([A, Base], [B, Base], [A, B])`

The `merge` operation looks for a "Good Head" (a class that is the first element of a list and does NOT appear in the tail of any other list).
- Inspect `A` (head of `[A, Base]`): It doesn't appear in the tails. Good head! Extract it.
- `merge([Base], [B, Base], [B])`
- Inspect `Base`: Appears in the tail of `[B, Base]`. Bad head! Skip.
- Inspect `B` (head of `[B, Base]`): Good head! Extract it.
- `merge([Base], [Base], [])`
- Extract `Base`.
Final MRO: `[Child, A, B, Base, object]`

If the inheritance graph is mathematically impossible to linearize without violating the constraints, Python raises a `TypeError: Cannot create a consistent method resolution order (MRO)`.

### The Mechanics of `super()`
`super()` is arguably the most misunderstood function in Python. It does **not** mean "call the parent class". It means **"call the next class in the runtime MRO chain"**.

This distinction is vital for cooperative multiple inheritance.
```python
class Base:
    def process(self):
        print("Base")

class Logger(Base):
    def process(self):
        print("Logging...")
        super().process()

class Validator(Base):
    def process(self):
        print("Validating...")
        super().process()

class Application(Logger, Validator):
    pass
```
If you call `Application().process()`, the flow goes:
`Application -> Logger -> Validator -> Base`.
When `Logger.process` calls `super().process()`, it jumps laterally to `Validator`, not vertically to `Base`. To prevent runtime crashes during lateral jumps, cooperative methods must accept and forward `*args, **kwargs`.

---

## 2. The Descriptor Protocol Deep Dive

Descriptors are the engine behind most of Python's class-level magic, including properties, methods, static methods, and class methods. A descriptor is any object that manages attribute access by implementing the descriptor protocol methods.

### Protocol Methods
- `__get__(self, instance, owner=None)`: Called when the attribute is accessed (`obj.attr`).
- `__set__(self, instance, value)`: Called during assignment (`obj.attr = val`).
- `__delete__(self, instance)`: Called during deletion (`del obj.attr`).
- `__set_name__(self, owner, name)`: (Python 3.6+) Automatically captures the variable name assigned to the descriptor in the class body.

### Data Descriptors vs Non-Data Descriptors
The critical distinction lies in which methods are implemented:
- **Data Descriptor**: Implements `__set__` or `__delete__`. Data descriptors take absolute precedence over the instance's dictionary. You cannot shadow them by modifying `instance.__dict__`. (`@property` is a data descriptor).
- **Non-Data Descriptor**: Implements only `__get__`. The instance dictionary takes precedence over non-data descriptors. (Methods are non-data descriptors).

### Attribute Lookup Hierarchy
When you evaluate `obj.x`, Python follows this strict precedence:
1. Data descriptor on the class/MRO.
2. `x` inside `obj.__dict__`.
3. Non-data descriptor on the class/MRO.
4. `x` inside `type(obj).__dict__`.
5. The `__getattr__` hook.

### Building a Validation Descriptor
Descriptors allow you to write reusable attribute-level logic.

```python
class RangeField:
    def __init__(self, min_val, max_val):
        self.min = min_val
        self.max = max_val

    def __set_name__(self, owner, name):
        self.private_name = '_' + name

    def __get__(self, instance, owner):
        if instance is None: return self
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if not (self.min <= value <= self.max):
            raise ValueError(f"Value must be between {self.min} and {self.max}")
        setattr(instance, self.private_name, value)

class Sensor:
    temperature = RangeField(-50, 150)
```
When `sensor.temperature = 200` is executed, the descriptor intercepts the assignment and validates it before storage.

---

## 3. Metaclasses & Class Creation Mechanics

Just as instances are created by classes, classes themselves are instances of a higher-order factory called a metaclass. By default, the metaclass of all Python classes is `type`.

### Dynamic Class Generation
You can bypass the `class` keyword entirely using the 3-argument signature of `type()`:
`type(name_string, bases_tuple, namespace_dict)`

```python
MyDynamicClass = type("MyDynamicClass", (object,), {"x": 10, "say_hello": lambda self: "Hello"})
```

### The Class Creation Lifecycle
When Python evaluates a `class` block, it orchestrates a 5-step process controlled by the metaclass:
1. **Metaclass Determination**: Python figures out which metaclass to use.
2. **Namespace Preparation**: `metaclass.__prepare__(name, bases)` returns the dictionary used as the local namespace during the execution of the class body. (Historically used to return `OrderedDict`).
3. **Execution**: The class body is executed, populating the namespace.
4. **Allocation**: `metaclass.__new__(mcs, name, bases, namespace)` allocates the actual class object in memory.
5. **Initialization**: `metaclass.__init__(cls, name, bases, namespace)` configures the newly constructed class.

### Building an ORM Metaclass
Metaclasses are excellent for declarative programming, like parsing a schema before the class even finishes compiling.

```python
class ModelMeta(type):
    def __new__(mcs, name, bases, namespace):
        fields = {k: v for k, v in namespace.items() if isinstance(v, RangeField)}
        namespace['_fields'] = fields
        namespace['table_name'] = name.lower() + "s"
        return super().__new__(mcs, name, bases, namespace)

class Model(metaclass=ModelMeta):
    pass
    # Subclasses will automatically have _fields and table_name populated.
```

### Modern Alternative: `__init_subclass__`
Python 3.6 introduced `__init_subclass__(cls, **kwargs)`, a class method that triggers when a class is subclassed. It replaces 80% of metaclass use-cases (like plugin registration or simple attribute injection) without the complexity and risk of metaclass conflicts in multiple inheritance scenarios.

---

## 4. Abstract Base Classes (ABCs) & Structural Typing

Python's dynamic nature allows "duck typing" (if it walks and quacks like a duck, it's a duck). However, complex systems require stricter contracts.

### Nominal Typing with ABCs
The `abc` module provides Abstract Base Classes to enforce interface contracts.

```python
from abc import ABC, abstractmethod

class DataStore(ABC):
    @abstractmethod
    def save(self, payload):
        pass
```
By inheriting from `DataStore` (which uses `ABCMeta` under the hood), a subclass cannot be instantiated unless it overrides the `save` method. This fail-fast mechanism prevents passing incomplete objects into critical workflows.

### Virtual Subclasses
You can register a completely unrelated class as a subclass of an ABC without changing its inheritance graph.

```python
class ThirdPartyStore:
    def save(self, payload): pass

DataStore.register(ThirdPartyStore)
print(isinstance(ThirdPartyStore(), DataStore))  # True!
```
This bypasses inheritance while satisfying `isinstance()` type checks.

### Structural Subtyping with Protocols (PEP 544)
Modern Python type hinting introduced `typing.Protocol` to enable true static duck typing.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Savable(Protocol):
    def save(self, payload: dict) -> bool:
        ...

class FileStore:
    def save(self, payload: dict) -> bool:
        return True

# No inheritance needed! Mypy will accept FileStore as a Savable.
# The runtime_checkable decorator allows isinstance checks:
isinstance(FileStore(), Savable) # True
```
Protocols heavily decouple codebases. A library can define a Protocol, and user code can satisfy it implicitly, strictly verified by static analyzers like Mypy.

---

## 5. C3 Linearization Complete Worked Example

To truly understand how Python resolves complex inheritance architectures, let's manually calculate a 5-level multiple inheritance diamond using the C3 Linearization algorithm.

Consider the following class hierarchy:

```python
class O: pass
class F(O): pass
class E(O): pass
class D(O): pass
class C(D, F): pass
class B(D, E): pass
class A(B, C): pass
```

According to C3, the linearization $L(Class)$ is computed as:
$L(C) = [C] + merge(L(B_1), ..., L(B_n), [B_1, ..., B_n])$

Let's compute from the base classes upwards:

1. **Base Classes:**
   $L(O) = [O]$
   $L(F) = [F, O]$
   $L(E) = [E, O]$
   $L(D) = [D, O]$

2. **Level 3 (C and B):**
   $L(C) = [C] + merge(L(D), L(F), [D, F])$
   $L(C) = [C] + merge([D, O], [F, O], [D, F])$
   - Examine `D`: It is the head of the first list. Does it appear in the tail of any other list? No. (The tails are `[O]`, `[O]`, `[F]`). Good head.
   - Extract `D`:
   $L(C) = [C, D] + merge([O], [F, O], [F])$
   - Examine `O`: It appears in the tail of `[F, O]`. Bad head.
   - Examine `F`: It is the head of the second list. Does it appear in the tail? No. Good head.
   - Extract `F`:
   $L(C) = [C, D, F] + merge([O], [O], [])$
   - Extract `O`.
   **Result:** $L(C) = [C, D, F, O]$

   $L(B) = [B] + merge(L(D), L(E), [D, E])$
   $L(B) = [B] + merge([D, O], [E, O], [D, E])$
   - Extract `D` (Good head).
   - Extract `E` (Good head).
   - Extract `O`.
   **Result:** $L(B) = [B, D, E, O]$

3. **Level 4 (A):**
   $L(A) = [A] + merge(L(B), L(C), [B, C])$
   $L(A) = [A] + merge([B, D, E, O], [C, D, F, O], [B, C])$
   - Examine `B`: Good head.
   - Extract `B`:
   $L(A) = [A, B] + merge([D, E, O], [C, D, F, O], [C])$
   - Examine `D`: Appears in the tail of `[C, D, F, O]`. Bad head. Move to next list.
   - Examine `C`: Good head.
   - Extract `C`:
   $L(A) = [A, B, C] + merge([D, E, O], [D, F, O], [])$
   - Examine `D`: Good head.
   - Extract `D`:
   $L(A) = [A, B, C, D] + merge([E, O], [F, O], [])$
   - Extract `E`, then extract `F`, then extract `O`.
   
   **Final MRO for A:** `[A, B, C, D, E, F, O]`

---

## 6. Complete Typed Validation Descriptor Library

Building robust data models requires validation. Python's descriptor protocol allows us to create a typed validation framework comparable to what powers Django or Pydantic internally.

```python
import re
from datetime import datetime

class BaseField:
    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = '_' + name

    def __get__(self, instance, owner):
        if instance is None: return self
        return getattr(instance, self.private_name, None)

    def __set__(self, instance, value):
        self.validate(value)
        setattr(instance, self.private_name, value)

    def validate(self, value):
        # Override in subclasses
        pass

class IntegerField(BaseField):
    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value):
        if not isinstance(value, int):
            raise TypeError(f"Expected int, got {type(value).__name__}")
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"Value must be >= {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"Value must be <= {self.max_val}")

class StringField(BaseField):
    def __init__(self, regex=None, max_length=None):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length

    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError("Expected string")
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"Length exceeds max length of {self.max_length}")
        if self.regex and not self.regex.match(value):
            raise ValueError(f"Value does not match pattern {self.regex.pattern}")

class DateTimeField(BaseField):
    def validate(self, value):
        if not isinstance(value, datetime):
            raise TypeError("Expected datetime object")

# Usage Example
class User:
    age = IntegerField(min_val=18, max_val=120)
    username = StringField(regex=r'^[a-zA-Z0-9_]+$', max_length=30)
    created_at = DateTimeField()
```

---

## 7. Full ActiveRecord-Style Mini-ORM Implementation

Metaclasses excel at registering components automatically. We can build a minimal Object-Relational Mapper (ORM) that parses descriptor fields at class creation time, dynamically mapping them to a database architecture.

```python
class ModelMeta(type):
    def __new__(mcs, name, bases, namespace):
        # Prevent processing the base Model class itself
        if name == 'Model':
            return super().__new__(mcs, name, bases, namespace)
            
        fields = {}
        for key, val in namespace.items():
            if isinstance(val, BaseField):
                fields[key] = val
                
        # Inject metadata into the class
        namespace['_fields'] = fields
        namespace['_table_name'] = name.lower() + "s"
        
        cls = super().__new__(mcs, name, bases, namespace)
        return cls

class Model(metaclass=ModelMeta):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self._fields:
                raise AttributeError(f"Invalid field: {key}")
            setattr(self, key, value)
            
    def to_dict(self):
        return {key: getattr(self, key) for key in self._fields}
        
    def save(self):
        # Simulate a database INSERT or UPDATE
        columns = ", ".join(self._fields.keys())
        values = ", ".join(repr(getattr(self, k)) for k in self._fields.keys())
        query = f"INSERT INTO {self._table_name} ({columns}) VALUES ({values});"
        print(f"Executing Query: {query}")
        
    @classmethod
    def filter(cls, **kwargs):
        # Simulate a database SELECT
        conditions = " AND ".join(f"{k} = {repr(v)}" for k, v in kwargs.items())
        query = f"SELECT * FROM {cls._table_name} WHERE {conditions};"
        print(f"Executing Query: {query}")
        return []

# Utilizing the ORM
class Employee(Model):
    id = IntegerField(min_val=1)
    name = StringField(max_length=100)

emp = Employee(id=101, name="John Doe")
emp.save()
# Executing Query: INSERT INTO employees (id, name) VALUES (101, 'John Doe');
Employee.filter(name="John Doe")
# Executing Query: SELECT * FROM employees WHERE name = 'John Doe';
```

---

## 8. Complete Plugin Registration System with `__init_subclass__`

Historically, metaclasses were used to build plugin registries. Python 3.6+ provides `__init_subclass__`, which accomplishes the same goal in a much simpler and less conflict-prone manner.

```python
class PluginBase:
    # The registry dictionary living on the base class
    registry = {}

    def __init_subclass__(cls, plugin_name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        # Enforce a contract: subclasses must provide a descriptive docstring
        if not cls.__doc__:
            raise ValueError(f"Plugin {cls.__name__} must have a docstring")
            
        # Use the provided name or default to the class name
        name = plugin_name or cls.__name__.lower()
        cls.registry[name] = cls
        
    def execute(self):
        raise NotImplementedError

# Creating Plugins
class ImagePlugin(PluginBase, plugin_name="image_processor"):
    """Processes image files like PNG and JPEG."""
    def execute(self):
        print("Processing image data...")

class AudioPlugin(PluginBase):
    """Processes audio files like MP3 and WAV."""
    def execute(self):
        print("Processing audio data...")

# The registry is automatically populated during class creation
print(PluginBase.registry.keys())
# dict_keys(['image_processor', 'audioplugin'])
```
This pattern is vastly superior to Metaclasses for this specific use case because it perfectly respects cooperative inheritance and avoids the dreaded `TypeError: metaclass conflict`.

---

## 9. Dynamic Protocol Implementation with Custom `__subclasshook__`

While `typing.Protocol` is the standard for static structural subtyping, you can implement runtime structural subtyping manually using Abstract Base Classes and the `__subclasshook__` method. This allows `issubclass()` and `isinstance()` to return True if an object structurally matches the requirements, regardless of inheritance.

```python
from abc import ABC, abstractmethod

class Serializable(ABC):
    @abstractmethod
    def serialize(self):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Serializable:
            # Check if the target class or any of its MRO bases has a 'serialize' method
            if any("serialize" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented

class NetworkPayload:
    def serialize(self):
        return '{"data": "payload"}'

# Test the structural typing
payload = NetworkPayload()

# These return True even though NetworkPayload does NOT inherit from Serializable!
print(issubclass(NetworkPayload, Serializable)) # True
print(isinstance(payload, Serializable))        # True
```
This is the fundamental mechanism that powers `@runtime_checkable` in the `typing` module under the hood, allowing true Pythonic duck typing at runtime while maintaining strict interface contracts.

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>