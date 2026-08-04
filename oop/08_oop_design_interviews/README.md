# Module 8: Object-Oriented Design Interviews - The Capstone

Welcome to the capstone module of our Object-Oriented Programming (OOP) curriculum. In this module, we transition from theory to practice. Object-Oriented Design (OOD) rounds in interviews for Software Development Engineer (SDE) roles are infamous for their ambiguity. The goal of this module is to equip you with a structured process for dissecting these open-ended problems, designing robust systems, and communicating your thought process effectively.

We will cover the Object-Oriented Analysis and Design (OOAD) process, basic UML notation, a battle-tested 5-step interview framework, and three comprehensive design walkthroughs: a Parking Lot, a Library Management System, and an ATM System.

---

## 1. OOAD Process (Object-Oriented Analysis & Design)

Object-Oriented Analysis and Design (OOAD) is a structured method for analyzing, designing, and implementing software systems using object-oriented concepts. It bridges the gap between raw requirements and executable code.

### Step 1: Gather Requirements (Functional + Non-Functional)
Before designing anything, you must understand what the system is supposed to do.
- **Functional Requirements:** What features must the system support? (e.g., "Users can reserve a book.")
- **Non-Functional Requirements:** Constraints on the system. (e.g., "The system should handle 10,000 concurrent users," or "Must be highly available.")

### Step 2: Identify Nouns → Candidate Classes
Read through the requirements and highlight the nouns. These often become your core classes or entities.
- *Example:* "A **user** can park their **car** in a **spot** and receive a **ticket**."
- *Candidate Classes:* User, Car, Spot, Ticket.

### Step 3: Identify Verbs → Methods and Responsibilities
Highlight the verbs in the requirements. These indicate behaviors or operations that your classes need to perform.
- *Example:* "A user can **park** their car in a spot and **receive** a ticket."
- *Methods:* `parkVehicle()`, `issueTicket()`. Assign these responsibilities to the appropriate classes (e.g., a `ParkingLot` might handle `parkVehicle()`).

### Step 4: Define Relationships (IS-A, HAS-A, USES-A)
Determine how the classes interact with one another.
- **IS-A (Inheritance):** A Car IS-A Vehicle.
- **HAS-A (Aggregation/Composition):** A Library HAS-A Book.
- **USES-A (Dependency):** A ParkingRateCalculator USES-A Ticket.

### Step 5: Apply Design Patterns Where They Naturally Fit
Do not force design patterns, but recognize when they solve a specific problem gracefully.
- Need a single instance of a configuration manager? Use **Singleton**.
- Need to calculate prices differently based on rules? Use **Strategy**.
- Need to notify users when an item is back in stock? Use **Observer**.

### Step 6: Validate with a Scenario Walkthrough
Take a core use case (e.g., "User checks out a book") and trace it through your proposed classes and methods. Ensure that all necessary data is available and state transitions occur correctly.

---

## 2. UML Class Diagram Notation

Unified Modeling Language (UML) provides a standard way to visualize system design. While you don't need to draw perfect UML in an interview, knowing the standard notations helps convey your ideas clearly.

### Core Elements
- **Classes:** Represented as a box, typically divided into three compartments:
  1. Class Name
  2. Attributes (Fields)
  3. Methods (Operations)

### Relationships

| Relationship Type | Symbol / Notation | Meaning | Example |
| :--- | :--- | :--- | :--- |
| **Association** | `A → B` (Solid line, open arrow) | A uses B (weak relationship). | `Driver` → `Car` |
| **Aggregation** | `A ◇→ B` (Hollow diamond) | A HAS-A B. B can exist independently of A. | `Library` ◇→ `Book` |
| **Composition** | `A ◆→ B` (Filled diamond) | A OWNS B. B cannot exist without A. | `House` ◆→ `Room` |
| **Inheritance** | `A ⎵→ B` (Solid line, open arrowhead) | A IS-A B (extends). | `Car` ⎵→ `Vehicle` |
| **Realization** | `A ⇢ B` (Dashed line, open arrowhead) | A implements interface B. | `ArrayList` ⇢ `List` |

### ASCII Art Representation

```text
Inheritance:        Car ──────▷ Vehicle
Realization:        HourlyRate - - - - ▷ ParkingRate
Aggregation:        Library ◇────── Book
Composition:        House ◆────── Room
Association:        Driver ──────> Car
```

### Aggregation vs Composition: A Deeper Dive
Understanding the difference between aggregation and composition is crucial for accurate modeling.

- **Aggregation ("HAS-A", independent lifecycle):** A Library has Books. If the Library is destroyed (closes down), the Books still exist and can be moved to another library. The relationship is weak.
- **Composition ("OWNS-A", dependent lifecycle):** A House has Rooms. If the House is destroyed, the Rooms are also destroyed. A Room cannot exist without the House. The relationship is strong.

---

## 3. 5-Step Interview Framework

When faced with an open-ended design question, stick to this 5-step framework to stay organized and demonstrate structured thinking.

### Step 1: Clarify (2-3 minutes)
Never start drawing immediately. Ask questions to narrow the scope.
- **Scale:** Is this for a single building or a global chain?
- **Actors:** Who interacts with the system? (e.g., Admin, Customer, System).
- **Workflows:** What are the top 2-3 most important use cases?
- **Constraints:** Are there specific business rules? (e.g., "Can a user reserve multiple items?")

### Step 2: Identify Core Entities
Based on the clarification, list out the top 5-8 primary classes. Keep it simple. Don't worry about relationships yet, just get the nouns on the board.

### Step 3: Define Relationships (Draw the Diagram)
Begin connecting the entities. Draw out the IS-A and HAS-A relationships. Create class hierarchies where appropriate (e.g., Abstract `Vehicle` class extended by `Car` and `Motorcycle`).

### Step 4: Add Design Patterns
Look at your design and see if any standard problems exist that can be solved with patterns. Mention these out loud to your interviewer. "I'm going to use the Strategy pattern for the pricing module so we can easily add holiday pricing later."

### Step 5: Walk Through a Scenario
Pick the most complex or central use case and trace it end-to-end. "Let's trace what happens when a user checks out a book..." This helps find bugs in your design and proves to the interviewer that the system works.

---

## 4. Full Design Walkthrough 1: Parking Lot System

### Requirements Clarification
- **Scope:** A multi-floor parking lot.
- **Vehicle Types:** Compact, Large (SUV/Truck), Motorcycle.
- **Operations:** Entry (get ticket, assign spot), Exit (calculate fee, free spot).
- **Pricing:** Calculated based on vehicle type and time spent.

### Candidate Classes
- `ParkingLot`, `ParkingFloor`, `ParkingSpot`, `Vehicle`, `Ticket`, `EntrancePanel`, `ExitPanel`

### UML Relationships (ASCII)
```text
ParkingLot ◆────── ParkingFloor (Composition: Floors exist only in the Lot)
ParkingFloor ◆────── ParkingSpot (Composition)
ParkingSpot ──────> Vehicle (Association: Spot holds a Vehicle temporarily)
Ticket ──────> Vehicle (Association)
Ticket ──────> ParkingSpot (Association)

Vehicle ◂────── Car (Inheritance)
Vehicle ◂────── Truck (Inheritance)
Vehicle ◂────── Motorcycle (Inheritance)

ParkingSpot ◂────── CompactSpot (Inheritance)
ParkingSpot ◂────── LargeSpot (Inheritance)
ParkingSpot ◂────── MotorcycleSpot (Inheritance)
```

### Code Implementation (Java)

```java
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

// Enum for Vehicle Types
enum VehicleType { MOTORCYCLE, COMPACT, LARGE }
enum SpotType { MOTORCYCLE, COMPACT, LARGE }
enum TicketStatus { ACTIVE, PAID, LOST }

// Strategy Pattern for Rate Calculation
interface ParkingRateStrategy {
    double calculateRate(Ticket ticket);
}

class HourlyRateStrategy implements ParkingRateStrategy {
    public double calculateRate(Ticket ticket) {
        // Mock calculation
        return 10.0;
    }
}

// Core Entities
abstract class Vehicle {
    private String licensePlate;
    private VehicleType type;

    public Vehicle(String licensePlate, VehicleType type) {
        this.licensePlate = licensePlate;
        this.type = type;
    }
    public VehicleType getType() { return type; }
}

class Car extends Vehicle {
    public Car(String licensePlate) { super(licensePlate, VehicleType.COMPACT); }
}

abstract class ParkingSpot {
    private String id;
    private boolean isFree;
    private Vehicle vehicle;
    private SpotType type;

    public ParkingSpot(String id, SpotType type) {
        this.id = id;
        this.type = type;
        this.isFree = true;
    }

    public boolean isFree() { return isFree; }
    public SpotType getType() { return type; }
    
    public void assignVehicle(Vehicle vehicle) {
        this.vehicle = vehicle;
        isFree = false;
    }

    public void removeVehicle() {
        this.vehicle = null;
        isFree = true;
    }
}

class CompactSpot extends ParkingSpot {
    public CompactSpot(String id) { super(id, SpotType.COMPACT); }
}

class Ticket {
    private String ticketId;
    private LocalDateTime entryTime;
    private LocalDateTime exitTime;
    private Vehicle vehicle;
    private ParkingSpot assignedSpot;
    private double fee;
    private TicketStatus status;

    public Ticket(Vehicle vehicle, ParkingSpot spot) {
        this.ticketId = "TKT-" + System.currentTimeMillis();
        this.entryTime = LocalDateTime.now();
        this.vehicle = vehicle;
        this.assignedSpot = spot;
        this.status = TicketStatus.ACTIVE;
    }
    
    // Getters and setters...
    public ParkingSpot getAssignedSpot() { return assignedSpot; }
}

class ParkingFloor {
    private String floorId;
    private Map<SpotType, List<ParkingSpot>> spots;

    public ParkingSpot findAvailableSpot(VehicleType type) {
        // Logic to find a spot based on vehicle type
        // E.g., Compact vehicle can fit in Compact or Large spots
        return null; // Mock return
    }
}

// Singleton Pattern for ParkingLot
class ParkingLot {
    private static ParkingLot instance;
    private List<ParkingFloor> floors;
    private ParkingRateStrategy rateStrategy;

    private ParkingLot() {
        // init
    }

    public static synchronized ParkingLot getInstance() {
        if (instance == null) {
            instance = new ParkingLot();
        }
        return instance;
    }

    public Ticket processEntry(Vehicle vehicle) {
        for (ParkingFloor floor : floors) {
            ParkingSpot spot = floor.findAvailableSpot(vehicle.getType());
            if (spot != null) {
                spot.assignVehicle(vehicle);
                return new Ticket(vehicle, spot);
            }
        }
        throw new RuntimeException("Lot is full");
    }

    public double processExit(Ticket ticket) {
        ticket.getAssignedSpot().removeVehicle();
        double fee = rateStrategy.calculateRate(ticket);
        return fee;
    }
}
```

### Scenario Walkthrough
1. **Car enters:** Driver arrives at `EntrancePanel`. System identifies it's a `Car` (VehicleType.COMPACT).
2. **Assign spot:** `ParkingLot` iterates through `ParkingFloor`s to `findAvailableSpot`. A `CompactSpot` is found.
3. **Issue ticket:** `spot.assignVehicle()` is called. A new `Ticket` is created with the current time, vehicle, and spot reference, and given to the user.
4. **Calculate fee & Exit:** User arrives at `ExitPanel`. `ParkingLot.processExit(ticket)` is called. The `ParkingSpot` is freed. The `ParkingRateStrategy` calculates the fee. The user pays, and the gate opens.

---

## 5. Full Design Walkthrough 2: Library Management System

### Requirements Clarification
- **Scope:** Single library branch management.
- **Actors:** Member (borrows books), Librarian (manages inventory), System (fines/notifications).
- **Core Operations:** Search (title, author, ISBN), Reserve, Checkout, Return, Fine calculation.
- **Constraints:** A single book title can have multiple physical copies (BookItems). Members have borrowing limits.

### Candidate Classes
- `Library`, `Book`, `BookItem`, `Member`, `Librarian`, `BookLending`, `Reservation`, `Fine`, `Search` (interface).

### Design Patterns Utilized
- **Strategy Pattern:** For the `Search` interface (search by Title, Author, or ISBN).
- **Observer Pattern:** When a book becomes available, `Reservation` notifies the waiting `Member`.
- **Factory Pattern:** For generating `Fine` receipts.

### Code Implementation (Java)

```java
import java.util.Date;
import java.util.List;
import java.util.ArrayList;

enum BookFormat { HARDCOVER, PAPERBACK, AUDIO_BOOK, EBOOK }
enum BookStatus { AVAILABLE, RESERVED, LOANED, LOST }
enum ReservationStatus { WAITING, PENDING, COMPLETED, CANCELED }

// Person hierarchy
abstract class Person {
    private String name;
    private String email;
    private String phone;
}

class Member extends Person {
    private String memberId;
    private Date dateOfMembership;
    private int totalBooksCheckedOut;
    
    // Observer pattern update method
    public void notify(String message) {
        System.out.println("Notification for " + memberId + ": " + message);
    }
}

class Librarian extends Person {
    public void addBookItem(BookItem item) { /* ... */ }
    public void blockMember(Member member) { /* ... */ }
}

// Book vs BookItem distinction is crucial
abstract class Book {
    private String ISBN;
    private String title;
    private String subject;
    private String publisher;
    private String language;
    private int numberOfPages;
    private List<String> authors;
}

class BookItem extends Book {
    private String barcode;
    private boolean isReferenceOnly;
    private double price;
    private BookFormat format;
    private BookStatus status;
    private Date dateOfPurchase;
    private Date publicationDate;
}

class BookReservation {
    private Date creationDate;
    private ReservationStatus status;
    private String bookItemBarcode;
    private String memberId;

    public void updateStatus(ReservationStatus status) { this.status = status; }
}

class BookLending {
    private Date creationDate;
    private Date dueDate;
    private Date returnDate;
    private String bookItemBarcode;
    private String memberId;
}

// Strategy Pattern for Search
interface Search {
    List<Book> searchByTitle(String title);
    List<Book> searchByAuthor(String author);
    List<Book> searchBySubject(String subject);
}

class Catalog implements Search {
    private Map<String, List<Book>> bookTitles;
    private Map<String, List<Book>> bookAuthors;
    
    public List<Book> searchByTitle(String title) {
        return bookTitles.get(title);
    }
    // ... implement other searches
}

class Fine {
    private Date creationDate;
    private double bookItemBarcode;
    private String memberId;
    
    public static void collectFine(String memberId, long daysLate) {
        // calculate fine based on days
    }
}
```

### Scenario Walkthrough
1. **Search:** `Member` uses `Catalog.searchByTitle()`. Returns a list of `Book`s.
2. **Reserve:** `Member` selects a book. If all `BookItem`s have `BookStatus.LOANED`, a `BookReservation` is created with `WAITING` status.
3. **Return:** Another member returns the book. The system updates the `BookItem` to `AVAILABLE`.
4. **Notify:** The system checks `BookReservation`s. It finds the waiting member and uses the Observer pattern (`member.notify()`) to send an alert.
5. **Checkout:** The notified member checks out the book. A `BookLending` record is created, and the `BookItem` status becomes `LOANED`.

---

## 6. Full Design Walkthrough 3: ATM System (State Pattern)

### Requirements Clarification
- **Scope:** Standard cash dispensing ATM.
- **Operations:** Insert card, enter PIN, check balance, withdraw cash, eject card.
- **Key Pattern:** The **State Pattern** is the canonical solution for an ATM because the machine's behavior changes entirely based on its current state (e.g., you cannot withdraw cash if you haven't inserted a card).

### States and Transitions
- `IdleState` → Insert Card → `HasCardState`
- `HasCardState` → Enter PIN → `AuthenticationState`
- `AuthenticationState` → Select Transaction → `DispensingState` (if withdraw)
- *Any State* → Eject Card → `IdleState`

### Code Implementation (State Pattern in Java)

```java
// State Interface
interface ATMState {
    void insertCard();
    void ejectCard();
    void enterPIN(int pin);
    void requestCash(int amount);
}

// Context Class
class ATM {
    private ATMState idleState;
    private ATMState hasCardState;
    private ATMState authState;
    private ATMState dispensingState;
    
    private ATMState currentState;
    private int cashInventory;

    public ATM(int initialCash) {
        idleState = new IdleState(this);
        hasCardState = new HasCardState(this);
        // init others...
        
        cashInventory = initialCash;
        currentState = idleState; // Initial State
    }

    public void setState(ATMState state) { this.currentState = state; }
    
    // Getters for states
    public ATMState getHasCardState() { return hasCardState; }
    public ATMState getAuthState() { return authState; }
    public ATMState getIdleState() { return idleState; }
    
    // Delegate actions to the current state
    public void insertCard() { currentState.insertCard(); }
    public void ejectCard() { currentState.ejectCard(); }
    public void enterPIN(int pin) { currentState.enterPIN(pin); }
    public void requestCash(int amount) { currentState.requestCash(amount); }
    
    public void dispenseCash(int amount) { cashInventory -= amount; }
}

// Concrete States
class IdleState implements ATMState {
    private ATM atm;
    public IdleState(ATM atm) { this.atm = atm; }

    public void insertCard() {
        System.out.println("Card inserted.");
        atm.setState(atm.getHasCardState());
    }
    public void ejectCard() { System.out.println("No card to eject."); }
    public void enterPIN(int pin) { System.out.println("Insert card first."); }
    public void requestCash(int amount) { System.out.println("Insert card first."); }
}

class HasCardState implements ATMState {
    private ATM atm;
    public HasCardState(ATM atm) { this.atm = atm; }

    public void insertCard() { System.out.println("Card already inserted."); }
    public void ejectCard() {
        System.out.println("Card ejected.");
        atm.setState(atm.getIdleState());
    }
    public void enterPIN(int pin) {
        if (pin == 1234) { // Mock validation
            System.out.println("PIN validated.");
            atm.setState(atm.getAuthState());
        } else {
            System.out.println("Invalid PIN. Card ejected.");
            atm.setState(atm.getIdleState());
        }
    }
    public void requestCash(int amount) { System.out.println("Enter PIN first."); }
}

// Additional states (AuthenticationState, DispensingState) follow similar logic.
```

### Scenario Walkthrough
1. **User inserts card:** System is in `IdleState`. `insertCard()` transitions system to `HasCardState`.
2. **User enters wrong PIN:** System is in `HasCardState`. `enterPIN(9999)` fails. `HasCardState` transitions system back to `IdleState` and ejects card.
3. **User re-inserts and enters right PIN:** System transitions to `HasCardState`, then `enterPIN(1234)` succeeds. System transitions to `AuthenticationState`.
4. **User withdraws $100:** `requestCash(100)` is called. `AuthenticationState` verifies balance, deducts funds via Bank API, and transitions to `DispensingState`. Hardware dispenses cash. System resets to `IdleState`.

This encapsulates all the logic gracefully—preventing a user from asking for cash before authenticating simply by managing which state object is currently active.
