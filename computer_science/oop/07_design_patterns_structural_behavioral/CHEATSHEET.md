# Structural & Behavioral Patterns Cheatsheet

## The 8 Patterns at a Glance

| Pattern | Category | Intent | 1-Line Use Case |
|---------|----------|--------|-----------------|
| **Adapter** | Structural | Convert interfaces | Make incompatible systems (e.g., legacy code) talk to each other. |
| **Decorator** | Structural | Add behavior dynamically | Add features to an object without subclassing (e.g., I/O stream wrappers). |
| **Facade** | Structural | Simplify complexity | Provide a single entry point to a complex subsystem of classes. |
| **Proxy** | Structural | Control access | Delay expensive object creation (lazy load) or check permissions. |
| **Observer** | Behavioral | 1-to-N notification | Notify UI components when backend data changes (Pub/Sub). |
| **Strategy** | Behavioral | Interchange algorithms | Swap out logic (e.g., sorting algorithms, payment types) at runtime. |
| **Command** | Behavioral | Encapsulate requests | Implement undo/redo functionality or job queueing. |
| **Iterator** | Behavioral | Sequential access | Traverse a custom data structure without exposing its internals. |

---

## Behavioral Pattern Comparison

When to use which behavioral pattern?

| Pattern | Focus | Key Benefit | Example |
|---------|-------|-------------|---------|
| **Observer** | State change notification | Loose coupling between the publisher and subscribers. | Event listeners, MVC model updates. |
| **Strategy** | Swappable algorithms | Eliminates massive `if/else` logic; Open/Closed principle. | Payment processing, Sorting selection. |
| **Command** | Objectifying a request | Allows queuing, logging, and undo/redo operations. | Text editor undo stack, Task queues. |

---

## Structural Pattern Decision Guide

Use this flow to decide which structural pattern you need:

| If you want to... | Use this pattern | Insight |
|-------------------|------------------|---------|
| Make existing, incompatible interfaces work together | **Adapter** | Converts Interface A to Interface B. |
| Provide a simple interface for a complex backend | **Facade** | Hides complexity behind a unified wrapper. |
| Add new behavior to an object dynamically | **Decorator** | Wraps the object and implements the *same* interface. |
| Control access to or delay creation of an object | **Proxy** | Acts as a stand-in that implements the *same* interface. |

---

## Observer: Push vs. Pull Models

- **Push Model:** The Subject sends all the necessary data along with the notification (e.g., `update(String symbol, double price)`). Better when Observers always need the same specific data.
- **Pull Model:** The Subject just sends a notification that it changed (e.g., `update()`). The Observer then queries the Subject to get the data it cares about (e.g., `subject.getPrice()`). Better when Observers might need different subsets of data from the Subject.
