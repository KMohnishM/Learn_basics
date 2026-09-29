# Module 1: Advanced Core

## 1. The Python Data Model & Special Methods (Dunders)

At the heart of Python's power is its unified data model. Every piece of data in Python is an object, meaning it is backed by a C struct (`PyObject`) that guarantees specific behaviors. Understanding how Python interacts with this object through special methods (dunders) is the key to writing idiomatic, powerful, and scalable code.

### Everything is an Object
Beneath the Python syntax, every variable maps to a memory address holding a `PyObject`. This fundamental C structure contains two critical fields:
- `ob_refcnt`: The reference count for memory management.
- `ob_type`: A pointer to the object's type object (which dictates its behavior).

When you call `id(obj)`, you are essentially reading the memory address of the `PyObject`. When you call `type(obj)`, CPython follows the `ob_type` pointer.

### Object Lifecycle & Initialization

The process of bringing a Python object to life is a two-step process controlled by `__new__` and `__init__`.

#### `__new__(cls, *args, **kwargs)`
`__new__` is the actual memory allocator. It is a static method responsible for creating and returning the empty instance of a class. It is rarely overridden in day-to-day programming but is strictly required when:
- Creating Singletons.
- Subclassing immutable types like `tuple` or `str` (where state must be set before instantiation).
- Developing metaclasses.

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("Allocating memory for Singleton")
            cls._instance = super().__new__(cls)
        return cls._instance
```

#### `__init__(self, *args, **kwargs)`
Once `__new__` returns the object, CPython automatically passes it to `__init__`. This is merely an initializer; it mutates the state of the existing object. It must return `None`.

#### `__del__(self)`
The finalizer, `__del__`, is called when the object's reference count drops to zero. Relying on `__del__` for critical cleanup (like closing files) is an anti-pattern. Its exact timing is non-deterministic (especially in cyclic garbage collection), and if it raises an exception, the exception is ignored and printed to stderr.

### Emulating Callable Objects
You can make instances of your custom classes behave like standard functions by overriding `__call__`. This is extremely useful for creating stateful functions or replacing complex closures.

```python
class ExponentialBackoff:
    def __init__(self, base_delay):
        self.base_delay = base_delay
        self.attempts = 0

    def __call__(self):
        delay = self.base_delay * (2 ** self.attempts)
        self.attempts += 1
        return delay

backoff = ExponentialBackoff(1.0)
print(backoff()) # 1.0
print(backoff()) # 2.0
```

### Attribute Access Hooks

Python intercepts dot notation (`obj.attr`) using powerful dunder methods.

#### `__getattr__(self, name)`
This is a fallback method. It is invoked *only* if `name` is not found in the object's instance dictionary, its class dictionary, or its MRO base classes. It is perfect for dynamic APIs.

#### `__getattribute__(self, name)`
This is an unconditional interceptor. It fires for *every single* attribute lookup. Implementing it requires extreme caution.

```python
class SecureBox:
    def __init__(self, secret):
        self._secret = secret
        self.is_locked = True

    def __getattribute__(self, name):
        if name == '_secret':
            is_locked = super().__getattribute__('is_locked')
            if is_locked:
                raise PermissionError("Box is locked")
        # Must use super() to prevent infinite RecursionError
        return super().__getattribute__(name)
```

#### `__setattr__` and `__delattr__`
These intercept assignment (`obj.attr = val`) and deletion (`del obj.attr`). Just like `__getattribute__`, overriding them requires using `super()` or assigning directly to `self.__dict__` to avoid infinite recursion.

### Emulating Sequence and Mapping Types

Classes can emulate lists, tuples, or dictionaries by implementing the sequence protocol.
- `__len__`: Triggers for `len(obj)`.
- `__getitem__`: Triggers for `obj[key]` and slicing `obj[1:5]`.
- `__setitem__`: Triggers for `obj[key] = val`.
- `__delitem__`: Triggers for `del obj[key]`.
- `__contains__`: Triggers for `val in obj`.

When slicing (`obj[1:5:2]`), Python passes a `slice` object into `__getitem__`.

```python
class Vector:
    def __init__(self, components):
        self._components = list(components)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Vector(self._components[index])
        return self._components[index]
```

### Memory Optimization with `__slots__`

By default, Python instances store attributes in a dynamic dictionary (`__dict__`). This hash map uses significant memory per object (often over 100 bytes even when empty).

If you are creating millions of instances of a data class, this overhead is catastrophic. By defining `__slots__`, you instruct CPython to suppress `__dict__` and `__weakref__` creation. Instead, the requested attributes are stored in a highly packed, fixed-size C array directly on the `PyObject` struct.

```python
class PointMemoryHeavy:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class PointMemoryLight:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y
```
*Note on Inheritance*: If a subclass inherits from `PointMemoryLight`, it will generate a `__dict__` unless it also explicitly declares `__slots__ = ()` or adds new slots.

---

## 2. CPython Memory Management & Garbage Collection

CPython abstracts away explicit memory management, but high-performance systems engineers must understand the exact mechanisms to prevent memory leaks and GC-induced latency spikes.

### Memory Architecture

CPython relies on the operating system for large memory blocks, but handles small allocations itself to prevent fragmentation.
- **PyMalloc**: The small object allocator. It handles all allocations <= 512 bytes. It requests large `Arenas` (256 KB) from the OS, divides them into 4 KB `Pools`, and further divides those into fixed-size `Blocks` (e.g., 16-byte blocks, 32-byte blocks).
- **Raw Allocator**: For objects > 512 bytes, Python bypasses PyMalloc and uses the standard OS `malloc`/`free`.

### Reference Counting

The absolute foundation of CPython memory management is deterministic reference counting.
Every time an object is referenced (assigned to a variable, passed to a function, put in a list), CPython increments `ob_refcnt` via `Py_INCREF`. When a reference is dropped, it decrements via `Py_DECREF`.

When `ob_refcnt == 0`, memory is deallocated instantly. This guarantees $O(1)$ constant-time cleanup without halting execution.

### The Reference Cycle Problem

Reference counting has one fatal flaw: cycles.
```python
a = []
b = []
a.append(b)
b.append(a)
del a
del b
```
Even after deleting the global references, the lists hold references to each other. Their reference counts drop to 1, never hitting 0. This is a memory leak.

### Cyclic Garbage Collector (Generational GC)

To catch reference cycles, CPython runs a background Generational GC. It exclusively tracks container objects (lists, dicts, instances).

The GC uses a Tri-Color Marking algorithm (simplified in CPython). It temporarily subtracts all internal reference counts between tracked objects. If an object's count reaches 0 during this test, it is completely isolated from the main program and is destroyed.

To avoid performance degradation, the GC segregates objects into three generations:
- **Generation 0**: Young objects. Swept frequently.
- **Generation 1**: Swept occasionally.
- **Generation 2**: Long-lived objects. Swept rarely.

*Tuning*: In massive backend services (e.g., Instagram's Django servers), developers often call `gc.disable()` to entirely turn off the generational GC on worker processes, saving up to 10% CPU overhead and preventing Copy-on-Write memory page fragmentation during `fork()`.

### Weak References

To build caches without causing memory leaks, use the `weakref` module. A weak reference points to an object without incrementing its `ob_refcnt`.

```python
import weakref

class HugeData:
    pass

data = HugeData()
cache = weakref.WeakValueDictionary()
cache['session_1'] = data

del data # Reference count drops to 0. It is deleted.
# cache['session_1'] automatically evaporates!
```

---

## 3. Iterators, Generators, and Coroutine Foundations

### Iteration Protocol
The Python iteration protocol revolves around two interfaces.
1. **Iterable**: Implements `__iter__()`, which returns an Iterator.
2. **Iterator**: Implements `__iter__()` (returning self) and `__next__()` (returning a value, or raising `StopIteration`).

### Generators & Yield Mechanics

Generators are functions that contain the `yield` keyword. Calling them does not execute the function; it returns a Generator Object. Execution suspends at the `yield` statement, saving the entire local stack frame (variables, instruction pointer) in memory.

This allows O(1) memory processing of O(N) data streams, like iterating over a 100GB log file.

### Advanced Generator Communication

Generators are not just data producers; they are coroutines capable of bidirectional communication.

- `generator.send(value)`: Resumes execution and injects `value` as the result of the `yield` expression.
- `generator.throw(Exception)`: Forces an exception to be raised inside the generator at the current `yield` point.
- `generator.close()`: Raises `GeneratorExit`, gracefully terminating it.

```python
def moving_average():
    total, count = 0.0, 0
    average = None
    while True:
        term = yield average
        if term is None:
            break
        total += term
        count += 1
        average = total / count

ma = moving_average()
next(ma)            # Prime the generator
print(ma.send(10))  # 10.0
print(ma.send(20))  # 15.0
```

### Sub-generator Delegation (`yield from`)

`yield from iterable` delegates execution to a sub-generator. It establishes a transparent, bidirectional tunnel. Any `.send()` or `.throw()` called on the delegator is piped directly to the sub-generator. When the sub-generator raises `StopIteration(value)`, `yield from` evaluates to that `value`.

---

## 4. Scopes, Closures, and Advanced Decorators

### Variable Scopes & the LEGB Rule
Python resolves variable lookups strictly in the LEGB order:
1. **Local**: Variables in the current function body.
2. **Enclosing**: Variables in statically nested functions.
3. **Global**: Module-level variables.
4. **Built-in**: The `builtins` module (`len`, `print`).

By default, assignment binds a name to the Local scope.
- Use `global var_name` to force assignment to the module scope.
- Use `nonlocal var_name` to force assignment to an enclosing closure scope.

### Closures

When a nested inner function references an Enclosing variable, Python compiles a Closure. Instead of storing the variable on the stack, it creates a heap-allocated Cell object. Both the outer function and the inner function's `__closure__` attribute hold references to this Cell, allowing shared, mutable state long after the outer function returns.

### Decorators Architecture

Decorators are syntactic sugar for wrapping functions.

#### Parameterized Decorators
A decorator taking arguments requires a 3-level function nest: the factory, the decorator, and the wrapper.

```python
import functools

def require_auth(role):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.role != role:
                raise PermissionError("Access Denied")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_auth("admin")
def delete_database():
    pass
```

Using `@functools.wraps` is absolutely essential. It copies the `__name__`, `__doc__`, `__annotations__`, and sets `__wrapped__`, preserving introspection and debugging capabilities.

---

## 5. Context Managers & ExitStack

### Context Management Protocol
The `with` statement guarantees deterministic resource cleanup via two methods:
- `__enter__(self)`: Acquires the resource, optionally returning it for the `as` variable.
- `__exit__(self, exc_type, exc_val, exc_tb)`: Releases the resource.

If `__exit__` returns `True`, any exception raised in the block is suppressed. If it returns `False` or `None`, the exception propagates.

### The Decorator Approach
You can avoid writing a full class by using `contextlib.contextmanager`.

```python
from contextlib import contextmanager

@contextmanager
def timer():
    import time
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        print(f"Elapsed: {end - start:.4f}s")
```

### Dynamic Resource Management with ExitStack

When the number of context managers is not known ahead of time, standard `with` statements fail. `contextlib.ExitStack` provides a programmatic stack that safely unwinds all registered managers even if exceptions occur halfway through allocation.

```python
from contextlib import ExitStack

def process_multiple_files(file_paths):
    with ExitStack() as stack:
        files = [stack.enter_context(open(f, 'r')) for f in file_paths]
        # All files are guaranteed to close safely
```

---

## 6. Detailed PyObject C Structure and Memory Layout

The underlying magic of Python objects relies heavily on the `PyObject` C structure. In the CPython implementation, memory layout is predictable and vital for system integrators or performance engineers who may write C extensions.

### PyObject Layout Breakdown

When you allocate an object in Python, you are actually allocating a C structure. The most fundamental struct is `PyObject`.

```c
typedef struct _object {
    _PyObject_HEAD_EXTRA
    Py_ssize_t ob_refcnt;
    struct _typeobject *ob_type;
} PyObject;
```

Let us dissect these components:
- `_PyObject_HEAD_EXTRA`: This is a macro used for debugging builds. In standard builds, it expands to nothing. In debug builds, it provides doubly linked list pointers to track all active objects, which is extremely useful for hunting down memory leaks from the C level.
- `ob_refcnt`: As discussed earlier, this is a signed integer (`Py_ssize_t`) keeping track of how many references point to this object. If it falls to zero, the object is immediately queued for deallocation. Because it is a signed integer, dropping below zero usually indicates a catastrophic reference counting bug in a C extension.
- `ob_type`: A pointer to a `_typeobject`. This points to the class of the object (e.g., the `int` type object, the `str` type object). The type object itself contains all the function pointers (slots) that dictate how the object behaves, like how to add it to another object or how to calculate its length.

### PyVarObject for Variable Length Structures

For objects that have a variable length, such as lists, strings, or tuples, Python uses an extended structure called `PyVarObject`:

```c
typedef struct {
    PyObject ob_base;
    Py_ssize_t ob_size; /* Number of items in variable part */
} PyVarObject;
```
Here, `ob_base` is the standard `PyObject` structure (providing reference count and type). The `ob_size` field stores the number of items. This explains why `len(my_list)` is an $O(1)$ constant time operation: it merely reads the `ob_size` field directly from memory.

---

## 7. Complete Custom Sequence and Mapping Implementation

To fully integrate custom objects into Python's ecosystem, implementing the Sequence and Mapping protocols completely is highly recommended. It allows custom data structures to behave exactly like built-in lists or dictionaries.

### A Complete Sequence: Custom List

Below is a robust implementation of a custom sequence that handles slicing, negative indices, item assignment, and deletion.

```python
class MySequence:
    def __init__(self, initial_data=None):
        self._data = list(initial_data) if initial_data else []
        
    def __len__(self):
        return len(self._data)
        
    def _validate_index(self, index):
        if isinstance(index, slice):
            return
        if not isinstance(index, int):
            raise TypeError("Indices must be integers or slices")
        if index < -len(self._data) or index >= len(self._data):
            raise IndexError("Sequence index out of range")
            
    def __getitem__(self, index):
        self._validate_index(index)
        if isinstance(index, slice):
            return MySequence(self._data[index])
        return self._data[index]
        
    def __setitem__(self, index, value):
        self._validate_index(index)
        if isinstance(index, slice):
            if not hasattr(value, '__iter__'):
                raise TypeError("Can only assign an iterable to a slice")
            self._data[index] = list(value)
        else:
            self._data[index] = value
            
    def __delitem__(self, index):
        self._validate_index(index)
        del self._data[index]
        
    def __repr__(self):
        return f"MySequence({self._data})"
        
    def append(self, value):
        self._data.append(value)
```

### A Complete Mapping: Custom Dictionary

A mapping behaves like a dictionary. To do this comprehensively, we must implement dunder methods that handle key lookups, modifications, and length. We can inherit from `collections.abc.MutableMapping` to automatically get methods like `.update()` and `.get()` for free, provided we implement a few core dunders.

```python
from collections.abc import MutableMapping

class CustomMapping(MutableMapping):
    def __init__(self, *args, **kwargs):
        self._store = dict()
        self.update(dict(*args, **kwargs))
        
    def __getitem__(self, key):
        return self._store[key]
        
    def __setitem__(self, key, value):
        # We can add custom behavior here, like logging
        print(f"Setting {key} to {value}")
        self._store[key] = value
        
    def __delitem__(self, key):
        print(f"Deleting {key}")
        del self._store[key]
        
    def __iter__(self):
        return iter(self._store)
        
    def __len__(self):
        return len(self._store)
        
    def __repr__(self):
        return f"CustomMapping({self._store})"
```

---

## 8. Deep Dive into Generational GC and the Tri-Color Algorithm

Python's Generational Garbage Collector (GC) steps in where reference counting fails. Its primary job is detecting and breaking cyclic references.

### Tri-Color Marking Algorithm Concept

While Python's actual C implementation uses a specialized algorithm, it fundamentally mirrors Tri-Color Marking concepts:
1. **White**: Objects that are candidates for garbage collection.
2. **Grey**: Objects that are known to be alive (reachable), but their references have not been fully scanned yet.
3. **Black**: Objects that are alive, and all objects they reference have also been scanned.

The GC starts by assuming all tracked container objects are unreachable (White). It identifies Root objects (like global variables and active stack frames), marks them Grey, and begins traversing their references. Any object reached is marked Grey, then Black once fully explored. Anything left White at the end is unreachable and is destroyed.

### Debugging Reference Cycles with `gc` Module

Python provides the `gc` module to introspect and manage the garbage collector manually.

```python
import gc

# Force a full collection of all generations
collected_count = gc.collect()
print(f"Objects collected: {collected_count}")

# Let's create a cycle and debug it
class Node:
    def __init__(self, name):
        self.name = name
        self.next = None

node_a = Node("A")
node_b = Node("B")
node_a.next = node_b
node_b.next = node_a

# Find what node_a refers to:
referents = gc.get_referents(node_a)
print("Referents of A:", [type(obj) for obj in referents])
# This will show A's internal __dict__, which contains the 'next' reference to B.

# Find what refers to node_a:
referrers = gc.get_referrers(node_a)
print("Referrers to A count:", len(referrers))
# This will show the global dictionary (where node_a variable lives)
# and the __dict__ of node_b.

# Clean up explicitly to break cycle for this example
node_a.next = None
node_b.next = None
```
By utilizing `gc.get_referrers()`, you can often track down exactly what object is keeping another object alive, which is invaluable for fixing memory leaks in long-running processes.

---

## 9. Advanced Generator Delegation with `yield from`

The `yield from` statement, introduced in Python 3.3, revolutionized generator composition. It does far more than just yield items from a sub-iterator; it creates a transparent, two-way communication channel between the caller and the sub-generator.

### Transparent Exception Forwarding

When you use `yield from`, the delegating generator automatically passes exceptions down to the sub-generator if `throw()` is called.

```python
def sub_generator():
    try:
        yield 1
        yield 2
    except ValueError:
        yield "Caught ValueError in sub_generator"
    yield 3

def delegating_generator():
    yield "Start"
    yield from sub_generator()
    yield "End"

gen = delegating_generator()
print(next(gen))      # Start
print(next(gen))      # 1
print(gen.throw(ValueError)) # Caught ValueError in sub_generator
print(next(gen))      # 3
print(next(gen))      # End
```

### Capturing Return Values

A generator can return a value when it finishes, raising `StopIteration(value)`. When using `yield from`, this return value is beautifully captured.

```python
def accumulate_data():
    total = 0
    while True:
        value = yield
        if value is None:
            break
        total += value
    return total  # Becomes the value of the yield from expression

def main_processor():
    print("Starting accumulator...")
    result = yield from accumulate_data()
    print(f"Accumulator finished with total: {result}")
    yield "Done"

processor = main_processor()
next(processor) # Prime it
processor.send(10)
processor.send(20)
processor.send(30)
try:
    processor.send(None) # Tell accumulator to finish
except StopIteration:
    pass
# Output will print: Accumulator finished with total: 60
```

---

## 10. Complete ExitStack Practical Example

Managing multiple dynamic resources safely can be painful. If you need to open an unknown number of files, or connect to multiple sockets, `ExitStack` handles the teardown seamlessly, even if a failure occurs halfway through allocation.

### Managing Sockets and Files

```python
import socket
from contextlib import ExitStack
import os
import tempfile

def connect_to_services_and_log(addresses):
    # addresses is a list of (host, port) tuples
    active_sockets = []
    
    with ExitStack() as stack:
        # 1. Manage a temporary file for logging
        log_file = stack.enter_context(
            tempfile.NamedTemporaryFile(mode='w+', delete=False)
        )
        log_file.write("Starting connections...\n")
        
        # 2. Dynamically allocate sockets
        for host, port in addresses:
            try:
                # Create a socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Ensure it gets closed no matter what
                stack.enter_context(sock)
                
                # Attempt connection
                sock.connect((host, port))
                active_sockets.append(sock)
                log_file.write(f"Connected to {host}:{port}\n")
            except OSError as e:
                log_file.write(f"Failed to connect to {host}:{port} - {e}\n")
                # Even if we fail here and raise, ExitStack will close all previously 
                # opened sockets and the log file automatically!
                raise
                
        # 3. Use the resources safely
        for sock in active_sockets:
            sock.sendall(b"PING")
            
        log_file.write("Finished operations successfully.\n")
        
    # At this indentation level, the ExitStack context is closed.
    # ALL sockets are guaranteed to be closed.
    # The temp log file is guaranteed to be closed.
    print(f"Operation complete. Log saved to {log_file.name}")
```
This pattern prevents resource leakage in highly concurrent or complex initialization setups, ensuring strict cleanup regardless of network timeouts or file system errors.

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>
