# Module 5: Python Performance and Internals

## 1. CPython VM Architecture & Bytecode Execution

To write high-performance Python,
one must understand how the reference implementation,
CPython, executes code.
CPython is not a machine-code compiler;
it is an interpreter that runs atop a virtual machine.
The execution of a Python script involves
several distinct phases that transform
human-readable source code into bytecode,
which is then evaluated by the
CPython Virtual Machine.

### 1.1 The Compilation Pipeline

When you run a Python script,
the interpreter performs the following pipeline:

```text
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|   Source Code     | ---> |   Parse Tree /    | ---> |  Abstract Syntax  |
|   (.py files)     |      |   CST             |      |  Tree (AST)       |
|                   |      |                   |      |                   |
+-------------------+      +-------------------+      +-------------------+
                                                              |
                                                              v
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  Hardware / CPU   | <--- |  Evaluation Loop  | <--- |   Code Object     |
|  Execution        |      |  (ceval.c)        |      |   (PyCodeObject)  |
|                   |      |                   |      |                   |
+-------------------+      +-------------------+      +-------------------+
```

1.  **Lexing and Parsing:**
The source code is read and converted
into a token stream,
which is then parsed into a
Concrete Syntax Tree (CST) using
Python's PEG (Parsing Expression Grammar) parser
(introduced in Python 3.9).
The PEG parser avoids the limitations
of the older LL(1) parser and
generates the syntax tree more intuitively.

2.  **AST Generation:**
The CST is transformed into an
Abstract Syntax Tree (AST),
stripping away syntactic sugar and formatting
to represent the logical structure of the code.
The AST allows static analysis tools
to verify code correctness and forms
the basis for subsequent compilation.

3.  **CFG and Bytecode Generation:**
The compiler traverses the AST to build
a Control Flow Graph (CFG) and finally emits
CPython bytecode.
The CFG models the logical branches and
loops in the program,
enabling basic optimizations like
dead code elimination before the
bytecode is generated.

4.  **Evaluation:**
The bytecode is wrapped in a `PyCodeObject`
and executed by the CPython VM's evaluation loop.
This code object contains the bytecodes,
the constants used, the local variables,
and the names of the globals accessed.

### 1.2 The Evaluation Loop and Frame Objects

The heart of CPython is `ceval.c`,
which contains the main evaluation loop.
Historically, this was a massive `switch`
statement that dispatched execution based
on the current bytecode instruction.
In more recent versions,
CPython has evolved to include computed gotos
for faster dispatch on some platforms,
drastically reducing branch prediction penalties.

Every time a function is called,
CPython creates a **Frame Object** (`PyFrameObject`).
Frames encapsulate the state of a function call,
including local variables,
the instruction pointer,
and the value stack.
This mechanism provides the isolation required
for recursive function calls and local state management.

```text
+-------------------------------------------------+
| PyFrameObject                                   |
+-------------------------------------------------+
| f_back      : Pointer to previous frame         |
| f_code      : Pointer to PyCodeObject           |
| f_builtins  : Dictionary of builtin objects     |
| f_globals   : Dictionary of global variables    |
| f_locals    : Dictionary of local variables     |
| f_lasti     : Last instruction executed         |
| f_valuestack: Array for intermediate values     |
+-------------------------------------------------+
```

Frame objects are inherently linked,
creating the call stack that you observe
in tracebacks.
Because frame objects are allocated on the heap
rather than the native C stack,
Python can inspect and modify them dynamically
(e.g., via the `sys._getframe()` function),
though this incurs allocation overhead.

### 1.3 Detailed Opcode Walkthrough with `dis`

The `dis` module is an essential tool
for performance tuning.
It allows you to inspect the bytecode
generated for any Python function,
revealing why certain operations are
slower than others.

Let us dissect a more complex function
to understand the specific opcodes at play:

```python
import dis

def calculate_discount(price, discount_rate):
    if price > 100:
        return price - (price * discount_rate)
    return price

print("Disassembly of calculate_discount:")
dis.dis(calculate_discount)
```

The output reveals a series of instructions.
Let's break down each opcode observed
in this execution path:

1.  **`LOAD_FAST`**:
This instruction is used to load
local variables (`price`, `discount_rate`).
It accesses the variable from an array
attached to the frame object using an index.
Because it is a simple array lookup in C,
it is extremely fast - much faster
than a dictionary lookup.

2.  **`LOAD_GLOBAL`**:
If the function called a global function
like `print()`, you would see this opcode.
It must look up the name in the module's
globals dictionary, and if not found,
in the builtins dictionary.
This double dictionary lookup is comparatively slow,
which is why local variable access is preferred
in hot loops.

3.  **`COMPARE_OP`**:
Used for the `price > 100` comparison.
It pulls the top two items from the value stack,
performs the rich comparison operation specified
(e.g., greater than), and pushes the
boolean result back onto the stack.

4.  **`POP_JUMP_IF_FALSE`**:
Often seen following `COMPARE_OP`,
this instruction modifies the instruction pointer
to jump to the `return price` block if the
condition was false.
This is how Python implements control flow
for `if` statements.

5.  **`BINARY_OP`**:
For the subtraction and multiplication,
CPython uses `BINARY_OP`.
In earlier versions, this was `BINARY_MULTIPLY`
or `BINARY_SUBTRACT`.
It pops the top two values, applies the operator
(by looking up the `__mul__` or `__sub__`
dunder methods on the objects),
and pushes the result.

6.  **`PRECALL` and `CALL`**:
When calling a function,
Python 3.11+ uses `PRECALL` to set up
the call frame, followed by `CALL` to
actually invoke the function.
`CALL` handles the argument passing,
pushes the new frame onto the execution stack,
and resumes evaluation inside the called function.

7.  **`RETURN_VALUE`**:
Pops the top item from the stack and
returns it to the calling frame,
ending the execution of the current frame
and destroying it (or returning it
to a free list).

Understanding these instructions allows
developers to write code that leverages
faster execution paths,
such as caching global lookups in local
variables within intensive loops.

---

## 2. Advanced Optimizations: PEP 659 and 3.13 JIT

Recent versions of Python have focused
heavily on performance, under the umbrella
of the "Faster CPython" project
(often associated with the Shannon Plan).

### 2.1 Specializing Adaptive Interpreter

Introduced in Python 3.11,
PEP 659 implements a Specializing Adaptive
Interpreter.
Instead of treating every bytecode instruction
statically, the interpreter monitors the types
of objects passing through instructions.
If an instruction sees the same types repeatedly
(e.g., adding two floats),
it "adapts" the generic bytecode into a
specialized, faster version.
This process is known as bytecode quickening
and inline caching.

State Machine of an Instruction:
```text
+--------------+      Threshold      +--------------+
|              |      Reached        |              |
|  Unadaptive  | ------------------> |   Adaptive   |
|  Instruction |                     |   Instruction|
|              | <------------------ |              |
+--------------+      Deoptimize     +--------------+
                             |
                      Success|Type Match
                             v
                      +--------------+
                      |              |
                      |  Specialized |
                      |  Instruction |
                      |              |
                      +--------------+
```

When an instruction like `LOAD_ATTR` executes,
it initially operates as an unadaptive instruction.
After a certain threshold of executions,
it transforms into an adaptive instruction,
which profiles the types it encounters.
If the types are consistent
(e.g., it always accesses the same attribute
on instances of a specific class),
it specializes into an instruction like
`LOAD_ATTR_INSTANCE_VALUE`. 

Specialized opcodes bypass the generic,
slow dispatch logic.
For example:

- **`LOAD_ATTR_INSTANCE_VALUE`**:
Bypasses the dictionary lookup for instance
attributes by caching the memory offset
of the attribute directly in the bytecode cache.

- **`BINARY_OP_ADD_INT`**:
Bypasses the generic `__add__` lookup
and directly performs a C-level integer addition,
provided both operands are integers.

- **`BINARY_OP_ADD_FLOAT`**:
Similar to the integer version,
this directly utilizes the CPU's floating-point
unit for addition, drastically reducing the
overhead of boxed arithmetic.

If the types change later
(e.g., passing a string to a function that
previously only saw integers),
the instruction gracefully falls back
(deoptimizes) to the generic instruction.
This adaptive behavior provides significant
speedups for idiomatic Python code without
requiring static typing.

### 2.2 Python 3.13 JIT (Copy-and-Patch)

Python 3.13 introduces an experimental
Just-In-Time (JIT) compiler based on a
"Copy-and-Patch" architecture.
Unlike tracing JITs (like PyPy)
or method JITs (like early Java),
the Copy-and-Patch JIT works by directly
stitching together pre-compiled machine code
snippets (templates) corresponding to
bytecode instructions.

1.  **Templates:**
During CPython's build process,
the C compiler generates binary templates
for each bytecode instruction.
These templates are heavily optimized
by the C compiler (like LLVM or GCC).

2.  **Copy:**
At runtime, the JIT copies these binary
templates into executable memory.

3.  **Patch:**
It patches the templates with runtime-specific
values (like memory addresses, constants,
or branch offsets).

```text
+----------------+       +------------------+
| Bytecode Array | ----> | JIT Compiler     | 
| [LOAD_FAST,    |       | (Copies machine  | 
|  BINARY_ADD]   |       |  code templates) | 
+----------------+       +------------------+
                                 |
                                 v
                         +-------------------+
                         | Executable Memory |
                         | [Machine Code 1,  |
                         |  Machine Code 2]  |
                         +-------------------+
```

This approach provides a significant speedup
with very low compilation overhead,
making it ideal for Python's dynamic nature.
By utilizing the copy-and-patch methodology,
CPython avoids the complex and heavy
infrastructure required by traditional
tracing JITs, allowing it to remain
relatively simple and maintainable while
still extracting substantial performance gains
on hot code paths.

---

## 3. Profiling, Benchmarking, and Memory Management

Before optimizing, you must measure.
Blind optimization often leads to unreadable
code with zero performance benefit.

### 3.1 Vectorized Numerical Processing Benchmarks

To understand the impact of various optimization
techniques, let's benchmark a common numerical
operation: squaring a large array of numbers.
We will compare pure Python loops,
list comprehensions, NumPy SIMD,
and Numba JIT.

```python
import timeit
import numpy as np
from numba import jit

# Setup code
setup_code = """
import numpy as np
from numba import jit
data = list(range(1000000))
data_np = np.arange(1000000, dtype=np.int32)

def pure_loop(arr):
    res = []
    for x in arr:
        res.append(x * x)
    return res

def list_comp(arr):
    return [x * x for x in arr]

def numpy_simd(arr):
    return arr * arr

@jit(nopython=True)
def numba_jit(arr):
    res = np.empty_like(arr)
    for i in range(arr.shape[0]):
        res[i] = arr[i] * arr[i]
    return res

# Warm up numba
numba_jit(data_np)
"""

# Benchmarking
print("Pure Loop:", timeit.timeit("pure_loop(data)", setup=setup_code, number=10))
print("List Comp:", timeit.timeit("list_comp(data)", setup=setup_code, number=10))
print("NumPy SIMD:", timeit.timeit("numpy_simd(data_np)", setup=setup_code, number=10))
print("Numba JIT:", timeit.timeit("numba_jit(data_np)", setup=setup_code, number=10))
```

The results highlight the massive disparity:

- **Pure loops** are the slowest due to the
overhead of the `append` method,
dynamic typing, and boxing/unboxing
of integers.

- **List comprehensions** are significantly
faster than loops because the `append`
operation is implemented in C and
optimized internally.

- **NumPy SIMD** operates on contiguous
memory blocks using vectorized CPU instructions,
bypassing the Python evaluation loop entirely.

- **Numba JIT** compiles the Python function
down to optimized LLVM machine code,
often matching or exceeding NumPy by
fusing loops and avoiding intermediate
array allocations.

### 3.2 Deterministic Profiling with `cProfile`

`cProfile` is a deterministic profiler;
it hooks into every function call,
return, and exception.
It is highly accurate regarding *call counts*
but introduces significant overhead,
which can distort the timing of small functions.

```python
import cProfile
import pstats

def expensive_computation():
    total = 0
    for i in range(10000):
        total += sum([x for x in range(100)])
    return total

profiler = cProfile.Profile()
profiler.enable()
expensive_computation()
profiler.disable()

stats = pstats.Stats(profiler).sort_stats('cumtime')
stats.print_stats(10)
```

### 3.3 Sampling Profiling with `py-spy`

For production environments,
deterministic profiling is too slow.
`py-spy` is a sampling profiler.
It reads the memory of the Python process
from the outside (often using eBPF or
OS-level memory APIs) without modifying
or pausing the interpreter.

```bash
# Record a flamegraph of a running Python process
py-spy record -o profile.svg --pid 12345

# Top-like view for Python
py-spy top --pid 12345
```
Because it samples the call stack at a fixed
interval (e.g., 100 times a second),
it has virtually zero overhead.
The resulting flame graphs provide a visual
hierarchy of CPU time spent in various functions,
making it trivial to identify hot spots
in production applications without degrading
performance.

### 3.4 Memory Profiling: `tracemalloc` and `memray`

Memory leaks and excessive allocations
kill performance due to GC pressure
and CPU cache thrashing.
Tracking down memory leaks in Python
can be challenging due to reference
counting and the garbage collector.

`tracemalloc` is built into the standard
library and tracks Python memory allocations
down to the specific line of code:

```python
import tracemalloc

# Start tracing memory allocations
tracemalloc.start()

# Simulate a memory leak
def simulate_leak():
    leak_list = []
    for _ in range(100000):
        leak_list.append("This is a leaked string" * 10)
    return leak_list

leaked_data = simulate_leak()

# Take a snapshot of memory usage
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 memory-consuming lines ]")
for stat in top_stats[:10]:
    print(stat)
```

`tracemalloc` allows you to compare snapshots
over time to isolate precisely where memory
is growing unbounded.

For a more comprehensive view,
`memray` (by Bloomberg) is a powerful
memory profiler that tracks both Python
allocations and native C allocations
(such as those from NumPy or C extensions).
It intercepts calls to `malloc`, `free`,
and related functions.

```bash
# Run a script with memray
python -m memray run my_script.py

# Generate a flame graph of memory allocations
python -m memray flamegraph memray-my_script.py.XXXXX.bin
```
The flame graph produced by `memray`
visually represents the memory hierarchy,
instantly revealing which functions are
responsible for the largest memory
footprints and peak memory usage.

---

## 4. High-Performance Native Extensions with Rust

When algorithmic optimization and vectorization
are not enough, rewriting critical sections
in a systems language is the next step.
Rust, via the `PyO3` framework and `maturin`
build system, has become the preferred choice
for this due to its memory safety guarantees,
zero-cost abstractions, and excellent
developer ergonomics.

### 4.1 PyO3 + Maturin Walkthrough

We will create a complete Rust extension
to compute the Mandelbrot set,
demonstrating the integration between
Python and Rust.

**Step 1: `pyproject.toml`**
This file configures the build system
to use `maturin`, which handles the
compilation of the Rust code into a
Python extension module.

```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "fast_mandelbrot"
version = "0.1.0"
description = "High-performance Mandelbrot computation in Rust"
requires-python = ">=3.8"
```

**Step 2: `Cargo.toml`**
This file configures the Rust project
and its dependencies, specifically enabling
the `extension-module` feature for `pyo3`.

```toml
[package]
name = "fast_mandelbrot"
version = "0.1.0"
edition = "2021"

[lib]
name = "fast_mandelbrot"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20.0", features = ["extension-module"] }
```

**Step 3: `src/lib.rs`**
This file contains the actual Rust implementation
and the PyO3 bindings that expose the
function to Python.

```rust
use pyo3::prelude::*;

/// Computes the number of iterations before the sequence escapes.
#[pyfunction]
fn compute_mandelbrot(c_re: f64, c_im: f64, max_iter: u32) -> u32 {
    let mut z_re = c_re;
    let mut z_im = c_im;
    
    for i in 0..max_iter {
        // If the magnitude squared exceeds 4, the sequence has escaped.
        if z_re * z_re + z_im * z_im > 4.0 {
            return i;
        }
        
        let new_re = z_re * z_re - z_im * z_im + c_re;
        let new_im = 2.0 * z_re * z_im + c_im;
        
        z_re = new_re;
        z_im = new_im;
    }
    
    max_iter
}

/// A Python module implemented in Rust.
#[pymodule]
fn fast_mandelbrot(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_mandelbrot, m)?)?;
    Ok(())
}
```

**Step 4: Building and Benchmarking**
To build the extension in release mode,
you execute:
```bash
maturin develop --release
```
This compiles the Rust code and installs
the resulting `.so` or `.pyd` module
into the current virtual environment.

Now, we can benchmark it against a pure
Python implementation:

```python
import timeit
from fast_mandelbrot import compute_mandelbrot

def py_mandelbrot(c_re, c_im, max_iter):
    z_re = c_re
    z_im = c_im
    for i in range(max_iter):
        if z_re * z_re + z_im * z_im > 4.0:
            return i
        new_re = z_re * z_re - z_im * z_im + c_re
        new_im = 2.0 * z_re * z_im + c_im
        z_re = new_re
        z_im = new_im
    return max_iter

# Benchmarking
print("Rust time:", timeit.timeit("compute_mandelbrot(-0.7, 0.27015, 1000)", globals=globals(), number=10000))
print("Python time:", timeit.timeit("py_mandelbrot(-0.7, 0.27015, 1000)", globals=globals(), number=10000))
```
The Rust extension operates purely on unboxed
native floating-point numbers without any
CPython VM overhead during the loop.
The results generally show a 50x to 100x
performance improvement over the pure
Python version.

### 4.5 Data Structures and Memory Layout

Choosing the right data structure is critical.
Python's `list` is a dynamic array of pointers
to `PyObject` structs.
It is excellent for random access but
terrible for prepending data.

```text
Memory Layout of a Python List:
+---------------+
| PyListObject  |
+---------------+       +-------+-------+-------+
| ob_refcnt     |       | PyObj | PyObj | PyObj |
| ob_type       |       | Ptr   | Ptr   | Ptr   |
| ob_size       | ----> +-------+-------+-------+
| allocated     |         |       |       |
| ob_item (ptr) |         v       v       v
+---------------+       [Obj]   [Obj]   [Obj]
```

When you insert an item at the beginning
of a list (using `list.insert(0, item)`),
CPython must shift every single pointer
in the array one position to the right,
resulting in an O(n) operation.
If you perform this repeatedly,
the algorithmic complexity devolves to O(n^2).

To optimize queue operations (FIFO),
use `collections.deque`,
which is implemented as a doubly-linked
list of blocks (usually containing 64 items per block).
This structure provides O(1) appends
and pops from both ends,
guaranteeing fast execution regardless
of the queue size.

### 4.6 Detailed Analysis of Memory Leaks in Python
Memory leaks in Python typically stem
from the application's design,
as the garbage collector (GC) is usually
very reliable.
However, Python uses reference counting
as its primary memory management technique,
supplemented by a cyclic garbage collector.

Reference counting means every object tracks
how many references point to it.
When the count reaches zero,
the object is immediately deallocated.
This is deterministic and fast.
The problem arises with cyclic references,
where Object A points to Object B,
and Object B points back to Object A.
Their reference counts will never reach zero
purely through scope exit.
The cyclic GC is responsible for detecting
and cleaning up these isolated cycles.

If an application continually appends objects
to a global list or dictionary and never
removes them, this is a logical memory leak.
A common scenario is using decorators or
caching mechanisms (like memoization)
without bounds or eviction policies.
For instance, using a naive dictionary
to cache function results will grow unbounded
if the input domain is large.
The `functools.lru_cache` mitigates this
by providing a Least Recently Used eviction policy,
ensuring the cache size remains within
a fixed limit.

Another source of memory leaks is unclosed resources.
While Python attempts to clean up unclosed files
or network sockets when the object is destroyed,
relying on the GC for resource management is risky.
Using context managers (`with` statements)
guarantees that resources are deterministically
released exactly when they are no longer needed,
preventing file descriptor exhaustion
and associated memory pressure.

Furthermore, C extensions can leak memory
if they allocate memory via `malloc`
but fail to `free` it,
or if they improperly increment a Python
object's reference count (`Py_INCREF`)
without a corresponding decrement (`Py_DECREF`).
The `memray` profiler discussed earlier
is indispensable for tracking down these
native-level leaks, as Python's built-in
`tracemalloc` cannot see memory allocated
directly by C extensions.

### 4.7 Concurrency and the Global Interpreter Lock (GIL)
No discussion of Python performance is complete
without addressing the Global Interpreter Lock (GIL).
The GIL is a mutex that protects access
to Python objects, preventing multiple threads
from executing Python bytecodes at once.
This lock is necessary because CPython's
memory management (reference counting)
is not thread-safe.
Without the GIL, concurrent modifications
to an object's reference count could lead
to race conditions, double frees,
or memory corruption.

Because of the GIL, multithreading in Python
does not provide a performance benefit
for CPU-bound tasks.
If you spawn 4 threads to perform heavy
mathematical computations,
they will still execute sequentially,
and the overhead of acquiring and releasing
the GIL will actually make the multithreaded
version slower than a single-threaded one.

However, the GIL is released during I/O operations.
When a thread is waiting for a network response,
reading from a file,
or waiting for a database query to return,
it drops the GIL.
This allows other Python threads to run.
Therefore, multithreading is highly effective
for I/O-bound workloads,
such as web scraping, network servers,
or concurrent API requests.

For CPU-bound tasks,
the solution is multiprocessing.
The `multiprocessing` module bypasses the GIL
by creating entirely separate Python processes,
each with its own memory space and its own GIL.
These processes can execute in parallel
across multiple CPU cores,
achieving true parallelization.
The trade-off is that inter-process
communication (IPC) is significantly slower
and more complex than sharing memory
between threads,
and the memory footprint of the application
multiplies with each new process.

Recent developments in the Python ecosystem,
such as PEP 703 (Making the Global Interpreter
Lock Optional in CPython),
aim to provide a GIL-free build of Python,
potentially unlocking true multithreading
for CPU-bound workloads in the future.

### 4.8 Zero-Copy Data Structures
When dealing with large datasets,
the cost of copying memory can become
a severe bottleneck.
Zero-copy operations allow multiple variables
or functions to access the same underlying
memory buffer without duplicating the data.
Python provides the `memoryview` object
and the broader Buffer Protocol to facilitate this.

A `memoryview` allows Python code to access
the internal data of an object that supports
the buffer protocol (like `bytes` or `bytearray`)
without copying.

```python
data = b"A large sequence of bytes..."
# Creating a memoryview does not copy the data
view = memoryview(data)

# Slicing the view creates a new view,
# still pointing to the original memory
slice_view = view[2:10]

print(slice_view.tobytes())
```

This technique is extensively used in
high-performance networking code,
cryptographic hashing,
and data serialization
(like in Apache Arrow or Pandas).
By avoiding unnecessary allocations and copies,
applications can process massive streams
of data with a minimal memory footprint
and vastly improved throughput.
The buffer protocol also acts as the glue
that allows libraries like NumPy
to share memory directly with C or Rust
extensions without conversion overhead.

---
*End of Module 5 README.md*
