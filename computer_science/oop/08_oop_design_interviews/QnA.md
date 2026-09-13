# QnA: OOP Design Interviews

Test your knowledge of Object-Oriented Design and interview patterns.

## 🟢 Easy

**1. What is the difference between aggregation and composition? Give a UML example of each.**
- **Aggregation:** A "HAS-A" relationship where the child can exist independently of the parent. 
  - *Example:* A Library has Books. If the library is destroyed, the books still exist. 
  - *UML Notation:* Hollow diamond (`Library ◇→ Book`).
- **Composition:** A stronger "OWNS-A" relationship where the child cannot exist without the parent. 
  - *Example:* A House has Rooms. If the house is demolished, the rooms cease to exist.
  - *UML Notation:* Filled diamond (`House ◆→ Room`).

**2. Walk me through your process when asked an OOP design question in an interview. What do you do in the first 2 minutes?**
- In the first 2-3 minutes, I use the "Clarify" step of the 5-step framework. I **do not** start writing code or drawing classes. I ask questions to narrow the scope of the problem.
- I ask about:
  1. Scale (is it local or distributed?)
  2. Actors (who uses this system?)
  3. Key workflows (what are the top 2 use cases?)
  4. Constraints (are there specific rules, like borrowing limits?)

## 🟡 Medium

**3. Design a Parking Lot — identify the core classes, their relationships (IS-A / HAS-A), and at least one design pattern.**
- **Core Classes:** `ParkingLot`, `ParkingFloor`, `ParkingSpot`, `Vehicle`, `Ticket`.
- **Relationships:**
  - `ParkingLot` ◆→ `ParkingFloor` (Composition)
  - `ParkingFloor` ◆→ `ParkingSpot` (Composition)
  - `Vehicle` ⎵→ `Car`, `Truck`, `Motorcycle` (IS-A / Inheritance)
  - `ParkingSpot` ⎵→ `CompactSpot`, `LargeSpot` (IS-A / Inheritance)
- **Design Pattern:** The **Strategy Pattern** is ideal for rate calculation (`ParkingRateStrategy`), allowing the system to switch between hourly, daily, or dynamic pricing models without modifying the core `ParkingLot` class.

**4. How would you model the relationship between Library and BookItem in UML? Is it aggregation or composition? Why?**
- It is **Aggregation** (`Library ◇→ BookItem`).
- **Why:** The physical copies of a book (`BookItem`) have an independent lifecycle from the `Library`. If a specific library branch closes, the books are not destroyed; they can be transferred to another branch or donated. They exist outside the context of that specific library.

## 🔴 Hard

**5. Full design: ATM System — show all classes, relationships, the State pattern with state transitions, and walk through a complete withdrawal scenario.**
- *(Note: Ensure you can diagram this on a whiteboard. See the README for the full code skeleton.)*
- **Classes:** `ATM`, `ATMState` (Interface), `IdleState`, `HasCardState`, `AuthenticationState`, `DispensingState`.
- **Relationships:** `ATM` HAS-A `ATMState`. The concrete states implement (`⇢`) the `ATMState` interface.
- **Scenario:** User approaches ATM (`IdleState`). Inserts card → transitions to `HasCardState`. User enters PIN; system validates it → transitions to `AuthenticationState`. User selects withdraw $50; system checks balance, signals dispenser → transitions to `DispensingState`, ejects card, returns to `IdleState`.

**6. Full design: Hotel Management System. Requirements: rooms (Single/Double/Suite), guests can book, check in, check out, generate bill with room charges + services. Identify all classes, relationships, patterns used, and walk through a booking scenario.**
- **Core Classes:** `Hotel`, `Room`, `RoomBooking`, `Guest`, `Bill`, `ServiceCharge`.
- **Relationships:**
  - `Room` ⎵→ `SingleRoom`, `DoubleRoom`, `Suite` (Inheritance).
  - `Hotel` ◆→ `Room` (Composition).
  - `RoomBooking` ──────> `Guest` and `Room` (Association).
- **Patterns:**
  - **Decorator Pattern:** For calculating the final `Bill`. Start with the base room charge, and wrap it with decorators for `RoomService`, `SpaCharge`, `LateCheckoutFee`, etc.
- **Scenario Walkthrough:** Guest searches for available `DoubleRoom`. System creates a `RoomBooking` linking `Guest` and `Room` with status `PENDING`. Guest checks in; status changes to `ACTIVE`. During stay, guest orders food; `ServiceCharge` objects are linked to the `RoomBooking`. At checkout, the system uses the Decorator pattern to aggregate base costs and service charges, generates a `Bill`, processes payment, and frees the `Room`.
