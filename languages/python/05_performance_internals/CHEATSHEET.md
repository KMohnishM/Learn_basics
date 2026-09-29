# Python Performance and Internals Cheatsheet

## 1. CPython Bytecode Opcodes (Common)

| Opcode Name | Description | Example Trigger | Complexity |
| :--- | :--- | :--- | :--- |
| `LOAD_FAST` | Loads a local variable from the frame's fast array. | `x = 5; print(x)` | O(1) (Array Index) |
| `LOAD_GLOBAL` | Loads a global variable from the global namespace dictionary. | `import math; math.pi` | O(1) to O(N) (Hash Lookup) |
| `STORE_FAST` | Stores a value into a local variable. | `def f(): x = 1` | O(1) |
| `BINARY_OP` | Performs a binary operation (add, sub, mult, etc.). | `a + b` | Depends on magic methods |
| `CALL` | Calls a callable object with arguments. | `my_func()` | Overhead of new frame creation |
| `UNPACK_SEQUENCE` | Unpacks an iterable into distinct variables. | `a, b = (1, 2)` | O(N) where N is sequence length|
| `FOR_ITER` | Calls `__next__()` on an iterator. | `for i in range(10):` | O(1) per step |
| `JUMP_FORWARD` | Unconditionally jumps forward in the bytecode. | `if False: pass` | O(1) |
| `POP_JUMP_IF_FALSE`| Pops top of stack, jumps if it is false. | `if x < 10:` | O(1) |

## 2. Profiling Tools Matrix

| Tool | Type | Overhead | Best Use Case | Output Format |
| :--- | :--- | :--- | :--- | :--- |
| `timeit` | Micro-benchmark | N/A | Benchmarking small snippets / pure algorithms. | Console Output |
| `cProfile` | Deterministic CPU | High | Local development, algorithmic optimization. | `.prof` / `pstats` text |
| `line_profiler` | Line-by-line CPU | Very High | Identifying exact slow lines in a known bottleneck function. | Annotated Source Text |
| `py-spy` | Sampling CPU | Very Low | Production environments, live systems. | Flame Graphs (`.svg`), Top UI |
| `tracemalloc` | Python Memory | Medium | Finding pure Python memory leaks and allocation hotspots. | Console / Code references |
| `memray` | Full Memory Tracker| High | Finding leaks in Python and C extensions (NumPy, PyO3). | Flame Graphs (`.html`) |

## 3. Profiling Snippets

### py-spy
```bash
# Generate a flame graph for a specific PID
py-spy record -o profile.svg --pid 12345

# View live execution like the `top` command
py-spy top --pid 12345

# Dump current call stack for all threads
py-spy dump --pid 12345
```

### tracemalloc
```python
import tracemalloc

# Start tracking
tracemalloc.start()

# ... Run application code ...

# Take a snapshot and show top 5 memory hogs
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:5]:
    print(stat)
```

## 4. Data Structure Time Complexity

| Structure | Operation | Average Case | Worst Case | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `list` | Append / Pop Last | O(1) | O(N) | Underlying C array needs reallocation occasionally. |
| `list` | Insert / Pop First | O(N) | O(N) | Must shift all subsequent elements in memory. |
| `list` | Random Access | O(1) | O(1) | Direct pointer arithmetic via `ob_item`. |
| `collections.deque` | Append / Pop (Left/Right) | O(1) | O(1) | Implemented as a doubly-linked list of blocks. |
| `collections.deque` | Random Access | O(N) | O(N) | Must traverse linked list to find index. |
| `set` | Add / Remove / Lookup | O(1) | O(N) | Hash table. Worst case occurs with hash collisions. |
| `dict` | Get / Set / Delete | O(1) | O(N) | Hash table. Python 3.6+ maintains insertion order. |
