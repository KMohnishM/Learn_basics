# Python Curriculum

## Overview
Python is a high-level, dynamic, multi-paradigm programming language that has become the de facto standard across distributed systems, artificial intelligence, machine learning, backend services, and high-performance computing. Its design philosophy emphasizes code readability, but beneath the surface lies an exceptionally flexible runtime environment. 

This curriculum is designed for systems engineers seeking to move beyond syntax and master the CPython interpreter, object-oriented metaprogramming, and advanced concurrency models. By understanding the underlying C structures, memory management algorithms, and the global interpreter lock, engineers can write high-performance Python code capable of scaling across distributed architectures.

## Module Map

| Module | Core Topics | Learning Objectives |
|---|---|---|
| 01_advanced_core | Data Model, Memory Management, GC, Iterators, Generators, Closures, Context Managers | Master the Python data model, reference counting, cyclic garbage collection, and advanced generator communication. |
| 02_object_oriented_metaprogramming | MRO, C3 Linearization, Descriptor Protocol, Metaclasses, ABCs, Protocols | Understand cooperative multiple inheritance, build data descriptors, and leverage metaclasses for framework design. |
| 03_type_systems | Static Typing, Mypy, Pydantic, Structural Subtyping, Generics | Implement strict static analysis and runtime data validation using modern Python type hinting. |
| 04_concurrency | Asyncio, Multiprocessing, Threading, GIL Mechanics | Architect scalable asynchronous systems and parallel processing pipelines while navigating the Global Interpreter Lock. |
| 05_cpython_internals | C API, PyObject, Cevel.c, Opcodes, Bytecode Analysis | Analyze Python bytecode and write C extensions to bypass performance bottlenecks. |
| 06_modern_packaging | Poetry, Build Systems, Wheels, CI/CD, Rust Extensions (PyO3) | Package applications hermetically and integrate Rust for safe, zero-cost abstractions. |

## The Python Mastery Roadmap

The journey to Python mastery follows a strict progression from runtime mechanics to structural architecture and finally systems-level optimization:

1. **Advanced Core**: Establish a rigorous understanding of what happens when a Python object is allocated, referenced, and destroyed.
2. **Metaprogramming**: Move from defining objects to defining the rules that create objects.
3. **Type Systems & Pydantic**: Impose strict boundaries on dynamic structures.
4. **Concurrency & Asyncio**: Escape the single-threaded paradigm for I/O and CPU bound workloads.
5. **CPython Internals & Performance**: Inspect the virtual machine executing the code.
6. **Modern Packaging & Tooling**: Ship the code predictably and extend it with lower-level languages.

## Prerequisites

- Proficiency in basic Python syntax (functions, loops, basic classes).
- Understanding of standard data structures (lists, dictionaries, sets).
- Familiarity with a Unix-like command line environment.
- Basic knowledge of memory concepts (pointers, heap vs. stack) is recommended but not strictly required.

## Study Path

Begin with `01_advanced_core`. Read the `README.md` thoroughly, study the memory diagrams, and execute the provided code examples in a Python 3.11+ REPL. Afterward, attempt to answer the questions in `QnA.md` from memory before checking the detailed answers. Finally, use `CHEATSHEET.md` as a daily reference while working on production systems. Proceed to subsequent modules only when you can confidently explain the internal mechanics of the concepts covered.
