# Module 4 Q&A: Polymorphism

**🟢 Easy:**

**1. What is the difference between overloading and overriding? Give one example of each.**
- **Overloading** happens at compile-time when multiple functions have the same name but different parameters within the same scope. (e.g., `void print(int)` vs `void print(double)`).
- **Overriding** happens at runtime when a derived class replaces the implementation of a base class's virtual method. (e.g., `Animal::speak()` is overridden by `Dog::speak()`).

**2. What makes a function virtual in C++? What about in Java (what is the default)?**
- In C++, a function becomes virtual only if explicitly declared with the `virtual` keyword in the base class.
- In Java, all non-static, non-final, non-private methods are virtual by default (opt-out dynamic dispatch).

**3. What is object slicing in C++? Why doesn't it happen in Java?**
- **Object Slicing** in C++ occurs when a derived object is assigned to a base class variable by value (e.g., `Base b = derived_obj;`). The derived-specific fields and virtual pointer are "sliced off", leaving only the base object.
- It doesn't happen in Java because Java variables do not hold objects by value; they hold references to objects on the heap. Assigning a reference just copies the pointer, leaving the heap object untouched.

**🟡 Medium:**

**4. Explain the vTable and vPtr mechanism in C++. How many vTables exist for a 3-class hierarchy (A → B → C where B overrides foo and C overrides bar)?**
- A **vTable** is a per-class array of function pointers. A **vPtr** is a hidden pointer inside every object instance pointing to its class's vTable.
- In a hierarchy of `A → B → C`, there are exactly **three vTables** created by the compiler (one for A, one for B, and one for C), regardless of how many methods are overridden.

**5. Why MUST a polymorphic base class destructor be virtual in C++? Show the exact undefined behavior when it's missing.**
- If a base destructor is not virtual, deleting a derived object via a base pointer uses static binding. Only `~Base()` is called.
- **Undefined Behavior:** `Base* p = new Derived(); delete p;` will fail to call `~Derived()`. Any heap memory, file handles, or network sockets allocated by `Derived` are permanently leaked.

**6. What does `@Override` do in Java? What happens if you omit it and accidentally write the wrong method signature?**
- `@Override` is an annotation that tells the compiler to strictly verify that the method actually overrides a base method.
- If omitted and the signature is slightly wrong (e.g., `void print(int)` instead of `void print()`), the code compiles successfully but treats it as an overloaded method. The dynamic dispatch fails, causing the base method to be called at runtime, leading to silent logical bugs.

**🔴 Hard:**

**7. Given this C++ class:**
```cpp
class Animal {
    int age;          // 4 bytes
public:
    virtual void speak();  // adds vPtr
    virtual ~Animal();
};
class Dog : public Animal {
    double weight;    // 8 bytes
    char name[8];    // 8 bytes
};
```
**Calculate the exact `sizeof(Animal)` and `sizeof(Dog)` on a 64-bit system (explain padding and vPtr placement).**
- **`sizeof(Animal)`:** The compiler injects an 8-byte vPtr at the beginning of the object. Then comes `int age` (4 bytes). Total is 12 bytes, but due to 8-byte alignment requirements on 64-bit systems, 4 bytes of padding are added at the end. Total = **16 bytes**.
- **`sizeof(Dog)`:** Inherits the 16 bytes of `Animal`. `double weight` (8 bytes) starts at offset 16. `char name[8]` (8 bytes) follows at offset 24. Total = 16 + 8 + 8 = **32 bytes**.

**8. Trace what happens at runtime when this code executes:**
```cpp
Animal* a = new Dog();
a->speak();
delete a;
```
**Step through: (1) what does `new Dog()` do to the vPtr? (2) how does `a->speak()` resolve to `Dog::speak`? (3) what does `delete a` do with a virtual destructor?**
1. `new Dog()` allocates memory on the heap. First, the `Animal` constructor runs, setting the vPtr to `vTable_Animal`. Then, the `Dog` constructor runs, updating the vPtr to point to `vTable_Dog`.
2. `a->speak()`: The CPU dereferences `a`, reads the vPtr, follows it to `vTable_Dog`, looks up the index for `speak()`, and invokes the function pointer found there (`Dog::speak`).
3. `delete a`: Because `~Animal()` is virtual, the CPU looks up the destructor index in `vTable_Dog`. It dynamically dispatches to `~Dog()`. After `~Dog()` finishes executing, it automatically statically invokes `~Animal()` to destroy the base portion. Finally, the heap memory is freed.
