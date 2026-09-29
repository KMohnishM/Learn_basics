# Module 1: Advanced Core - Cheatsheet

## Python Dunder Methods Quick Reference

| Category | Method | Description | Trigger |
|---|---|---|---|
| **Lifecycle** | `__new__(cls, ...)` | Allocates memory for a new object instance. | `MyClass()` |
| | `__init__(self, ...)` | Initializes attributes of a newly created object. | Post-`__new__` automatic call |
| | `__del__(self)` | Finalizer, called when refcount drops to 0. | `del obj` or GC |
| **Attributes** | `__getattr__(self, name)` | Fallback invoked if attribute is missing. | `obj.missing` |
| | `__getattribute__(self, name)`| Unconditional interceptor for all attr access. | `obj.any_attr` |
| | `__setattr__(self, name, val)`| Intercepts all attribute assignments. | `obj.x = 1` |
| **Sequences** | `__getitem__(self, key)` | Handles indexing and slicing. | `obj[2]`, `obj[1:5]` |
| | `__len__(self)` | Returns sequence length. | `len(obj)` |
| | `__contains__(self, item)` | Handles membership testing. | `item in obj` |
| **Context** | `__enter__(self)` | Setup logic for context manager. | `with obj:` |
| | `__exit__(self, exc_typ, ...)`| Cleanup. Return `True` to suppress exceptions.| Exiting `with` block |
| **Callable** | `__call__(self, ...)` | Allows instance to be executed as a function. | `obj()` |

---

## Memory Allocation & Garbage Collection Triggers

```text
[ PYMALLOC ARENA (256 KB) ]
   |
   +-- [ POOL (4 KB) - Size Class: 16 bytes ]
   |      +-- Block (16b) -> Active (e.g. small str)
   |      +-- Block (16b) -> FREE
   |
   +-- [ POOL (4 KB) - Size Class: 32 bytes ]
          +-- Block (32b) -> Active

==================================================

[ REFERENCE COUNTING (O(1) Deallocation) ]
   obj = [1, 2, 3]    # ob_refcnt = 1
   ref = obj          # ob_refcnt = 2
   del ref            # ob_refcnt = 1
   del obj            # ob_refcnt = 0 -> IMMEDIATE DEALLOCATION

[ GENERATIONAL GC (For Cyclic References) ]
   Generation 0 (Young) -> Threshold: ~700 allocations > deallocations
           |
      (Survivors)
           v
   Generation 1 (Intermediate) -> Threshold: ~10 Gen0 sweeps
           |
      (Survivors)
           v
   Generation 2 (Long-Lived) -> Threshold: ~10 Gen1 sweeps
```

---

## Custom Context Manager & Decorator Boilerplate

### Context Manager (Class Based)
```python
class ManagedResource:
    def __enter__(self):
        print("Acquiring Resource")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Releasing Resource")
        if exc_type is not None:
            print(f"Handling {exc_type}")
            return True # Suppress Exception
```

### Parameterized Decorator
```python
import functools

def advanced_decorator(param1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # PRE-EXECUTION LOGIC
            result = func(*args, **kwargs)
            # POST-EXECUTION LOGIC
            return result
        return wrapper
    return decorator
```

---

## Generator `send()` / `yield from` Communication Flow

```text
[ MAIN ROUTINE ]                      [ DELEGATOR (`yield from`) ]        [ SUB-GENERATOR ]
       |                                           |                                |
       | --- gen.send(None) (Start) -------------> |                                |
       |                                           | --- forwards .send(None) ----> | (Execution starts)
       |                                           |                                | yield 1
       | <---------------------------------------- | <----------------------------- |
       |                                           |                                |
       | --- gen.send("DATA") -------------------> |                                |
       |                                           | --- forwards "DATA" ---------> | val = yield
       |                                           |                                | yield val + 1
       | <---------------------------------------- | <----------------------------- |
       |                                           |                                |
       | --- gen.throw(ValueError) --------------> |                                |
       |                                           | --- forwards .throw() -------> | (Raises inside sub)
       |                                           |                                | (handles, raises StopIteration)
       | <--- (yield from returns result) -------- | <--- (StopIteration(result)) - |
```
