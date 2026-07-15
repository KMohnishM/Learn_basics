# Module 1: Relational Model & Normalization Theory

---

## 1. Entity-Relationship (ER) Model

The Entity-Relationship (ER) model is a high-level conceptual data model used to design database schemas. It describes data as entities, relationships, and attributes.

### Entities and Entity Sets
- **Entity**: A distinguishable object or concept in the real world (e.g., a specific employee, a physical computer).
- **Entity Set**: A collection of similar entities (e.g., the set of all employees). Represented as a rectangle in ER diagrams.
- **Strong Entity Set**: Has a primary key that uniquely identifies each entity without relying on other entity sets.
- **Weak Entity Set**: Cannot be uniquely identified by its own attributes alone. It depends on an **identifying strong entity set** (owner) via an **identifying relationship** (represented by a double diamond).
  - A weak entity set has a **partial key** (or **discriminator**), which is a set of attributes that uniquely distinguishes weak entities associated with the same owner entity.
  - Represented as a double rectangle; the partial key is underlined with a dashed line.

### Attributes
Attributes are properties of an entity or relationship. Represented as ovals.
1. **Simple / Atomic**: Cannot be divided into subparts (e.g., `Age`, `Salary`).
2. **Composite**: Can be split into subparts (e.g., `Name` divided into `First_Name` and `Last_Name`).
3. **Single-Valued**: Contains exactly one value for a given entity instance (e.g., `Date_of_Birth`).
4. **Multi-Valued**: Can contain multiple values for a single entity (e.g., `Phone_Numbers`, `Degrees`). Represented as a double oval.
5. **Derived**: Computed from other attributes (e.g., `Age` derived from `Date_of_Birth` and current date). Represented as a dashed oval.
6. **Key Attribute**: Uniquely identifies an entity in the entity set. Underlined in the diagram.

### Relationships and Constraints
- **Relationship Set**: A mathematical relation among $n \ge 2$ entity sets. Represented as a diamond.
- **Cardinality Ratios** (Binary Relationships):
  - **One-to-One (1:1)**: An entity in A is associated with at most one entity in B, and vice versa (e.g., Employee $\leftrightarrow$ Office).
  - **One-to-Many (1:N)**: An entity in A is associated with any number of entities in B, but B is associated with at most one in A (e.g., Department $\rightarrow$ Employees).
  - **Many-to-Many (N:M)**: Any number of entities in A are associated with any number in B, and vice versa (e.g., Students $\leftrightarrow$ Courses).
- **Participation Constraints**:
  - **Total Participation (Double Line)**: Every entity in the set must participate in at least one relationship in the relationship set (e.g., every `Account` must belong to a `Customer`).
  - **Partial Participation (Single Line)**: Some entities in the set may not participate in the relationship (e.g., not every `Employee` manages a `Department`).

---

## 2. Relational Model Concepts

The relational model represents data as a collection of relations (tables).

- **Relation Schema ($R$)**: The logical design of a table, denoting the relation name and its attributes: $R(A_1, A_2, \dots, A_n)$.
- **Relation Instance ($r(R)$)**: The actual table containing a set of tuples (rows) at a specific point in time. No duplicate tuples are allowed in a mathematical relation.
- **Tuple ($t$)**: A row in a relation, representing a single record.
- **Domain ($D$)**: The set of permitted atomic values for an attribute (e.g., domain of `Age` is positive integers).
- **Null Value**: A special value indicating that the value is either unknown or does not exist.

### Keys in the Relational Model
- **Superkey ($K$)**: A set of one or more attributes whose values uniquely identify a tuple in a relation instance. If $t_1 \ne t_2$, then $t_1[K] \ne t_2[K]$.
- **Candidate Key ($CK$)**: A minimal superkey. A superkey is a candidate key if no proper subset of it is also a superkey (no redundant attributes).
- **Primary Key ($PK$)**: The candidate key chosen by the database designer to uniquely identify tuples in the relation.
- **Foreign Key ($FK$)**: An attribute (or set of attributes) in a relation $R_1$ that references the primary key of another relation $R_2$. It enforces **referential integrity** — every value in the foreign key column must either exist in the referenced primary key column or be NULL.

---

## 3. Functional Dependencies (FDs)

A functional dependency is a constraint between two sets of attributes in a relation.

### Definition
Let $R$ be a relation schema, and $\alpha, \beta \subseteq R$. The functional dependency:
$$\alpha \rightarrow \beta$$
(read as "$\alpha$ functionally determines $\beta$") holds on $R$ if, in every legal relation instance $r(R)$, for any two tuples $t_1$ and $t_2$ in $r$:
$$\text{If } t_1[\alpha] = t_2[\alpha], \text{ then } t_1[\beta] = t_2[\beta]$$

- If two rows have the same value for the columns in $\alpha$, they must have the same value for the columns in $\beta$.
- **Trivial FD**: $\alpha \rightarrow \beta$ is trivial if $\beta \subseteq \alpha$ (e.g., $A, B \rightarrow A$).
- **Non-trivial FD**: $\alpha \rightarrow \beta$ where $\beta \not\subseteq \alpha$.

### Armstrong's Axioms
A set of rules used to infer all functional dependencies logically implied by a given set $F$:
1. **Reflexivity**: If $\beta \subseteq \alpha$, then $\alpha \rightarrow \beta$.
2. **Augmentation**: If $\alpha \rightarrow \beta$, then $\gamma\alpha \rightarrow \gamma\beta$ for any attribute set $\gamma$.
3. **Transitivity**: If $\alpha \rightarrow \beta$ and $\beta \rightarrow \gamma$, then $\alpha \rightarrow \gamma$.

### Secondary Rules (Derived from Axioms)
- **Union**: If $\alpha \rightarrow \beta$ and $\alpha \rightarrow \gamma$, then $\alpha \rightarrow \beta\gamma$.
- **Decomposition**: If $\alpha \rightarrow \beta\gamma$, then $\alpha \rightarrow \beta$ and $\alpha \rightarrow \gamma$.
- **Pseudotransitivity**: If $\alpha \rightarrow \beta$ and $\gamma\beta \rightarrow \delta$, then $\alpha\gamma \rightarrow \delta$.

---

## 4. Attribute Closure & Finding Candidate Keys

### Attribute Closure Algorithm
The attribute closure of a set of attributes $\alpha$ under a set of functional dependencies $F$, denoted as $\alpha^+$, is the set of all attributes functionally determined by $\alpha$.

```
Algorithm Attribute_Closure(α, F):
  Result := α;
  repeat
    for each functional dependency β → γ in F do:
      if β ⊆ Result then:
        Result := Result ∪ γ;
  until (Result does not change)
  return Result;
```

### Finding All Candidate Keys of a Relation
To find all candidate keys for a relation $R$ with FD set $F$:
1. **Identify essential attributes**:
   - **L-type**: Attributes appearing only on the Left side of FDs, or not appearing at all. These *must* be part of every candidate key.
   - **R-type**: Attributes appearing only on the Right side of FDs. These *cannot* be part of any candidate key.
   - **LR-type**: Attributes appearing on both sides. These may or may not be part of the key.
2. **Start with the core**: Let $X$ be the set of all L-type attributes.
3. **Compute the closure**: Find $X^+$.
   - If $X^+ = R$, then $X$ is the unique candidate key.
   - If $X^+ \ne R$, then systematically add combinations of LR-type attributes to $X$ and compute their closures until you find minimal sets that determine $R$.

---

## 5. Normalization Theory

Normalization is the process of organizing attributes in a relation to minimize data redundancy and eliminate update anomalies.

### Database Anomalies (Without Normalization)
Consider an unnormalized schema `Emp_Dept(Emp_ID, Name, Dept_Name, Dept_Manager)`:
- **Redundancy**: Department manager names are duplicated for every employee in that department.
- **Insertion Anomaly**: Cannot insert a new department if it doesn't have any employees assigned yet (since `Emp_ID` is the primary key and cannot be NULL).
- **Update Anomaly**: If a department manager changes, we must update the manager in multiple rows. If we miss one, the database becomes inconsistent.
- **Deletion Anomaly**: If the last employee in a department is deleted, the department information (and its manager) is lost entirely.

### Normal Forms (1NF, 2NF, 3NF, BCNF)

Let **Prime Attribute** be any attribute that is a member of any candidate key of $R$.
Let **Non-prime Attribute** be any attribute that is not part of any candidate key.

#### First Normal Form (1NF)
A relation is in 1NF if and only if the domain of each attribute contains only **atomic (indivisible) values**, and the value of any attribute in a tuple is a single value from the domain.
- No multi-valued attributes (e.g., an array or comma-separated list of values in a single cell).
- No composite attributes.

#### Second Normal Form (2NF)
A relation is in 2NF if:
1. It is in 1NF.
2. No **non-prime attribute** is **partially dependent** on any candidate key.
   - A dependency $\alpha \rightarrow A$ is a partial dependency if $A$ is non-prime and $\alpha$ is a proper subset of a candidate key.
   - In short: Non-prime attributes must depend on the *whole* key, not a *part* of the key.

#### Third Normal Form (3NF)
A relation is in 3NF if:
1. It is in 2NF.
2. No non-prime attribute is **transitively dependent** on any candidate key.
   - A dependency $\alpha \rightarrow \beta$ is transitive if $\alpha \rightarrow \gamma$ and $\gamma \rightarrow \beta$ (where $\gamma$ is not a superkey).
   - Formally, for every non-trivial functional dependency $\alpha \rightarrow \beta$:
     - Either $\alpha$ is a **superkey** of $R$,
     - Or each attribute in $\beta - \alpha$ is a **prime attribute** of $R$.

#### Boyce-Codd Normal Form (BCNF)
A relation is in BCNF (a stronger version of 3NF) if for every non-trivial functional dependency $\alpha \rightarrow \beta$:
- $\alpha$ must be a **superkey** of $R$.

*Note*: The difference between 3NF and BCNF is that 3NF allows the right-hand side ($\beta$) to be prime when the left-hand side ($\alpha$) is not a superkey. BCNF strictly forbids this.

---

## 6. Decomposition Properties

When a relation $R$ is decomposed into $R_1, R_2, \dots, R_k$, the decomposition must satisfy two critical properties:

### 1. Lossless-Join Decomposition
A decomposition of $R$ into $R_1$ and $R_2$ is **lossless-join** if and only if:
$$r(R) = \pi_{R_1}(r(R)) \bowtie \pi_{R_2}(r(R))$$
If we reconstruct the relation by joining the sub-relations, we must get the exact original tuples — no extra "spurious" tuples.

**Theorem (Binary Case)**:
A decomposition of $R$ into $R_1$ and $R_2$ is lossless-join if the common attributes are a candidate key of at least one of the relations:
$$(R_1 \cap R_2) \rightarrow R_1 \quad \text{or} \quad (R_1 \cap R_2) \rightarrow R_2$$

#### The Matrix Method (Chase Algorithm)
For decomposing into $n$ relations, construct a table with columns representing attributes of $R$ and rows representing decomposed schemas.
1. Fill cell $(i, j)$ with $a_j$ if attribute $A_j$ is in schema $R_i$. Otherwise, fill it with $b_{ij}$.
2. Interate through functional dependencies in $F$. If $\alpha \rightarrow \beta$ holds:
   - For all rows that match in their $\alpha$ columns, equate their $\beta$ columns (replace $b$-values with $a$-values if present).
3. If any row becomes all $a_j$ values ($a_1, a_2, \dots, a_m$), the decomposition is **lossless**. Otherwise, it is **lossy**.

### 2. Dependency Preservation
A decomposition of $R$ into $R_1, R_2, \dots, R_k$ is dependency-preserving if the union of the closures of the dependencies of each sub-relation is equivalent to the closure of $F$:
$$(F_1 \cup F_2 \cup \dots \cup F_k)^+ = F^+$$
Where $F_i$ is the projection of $F$ onto $R_i$ (all FDs in $F^+$ containing only attributes of $R_i$).

**Testing Algorithm**:
To test if a functional dependency $\alpha \rightarrow \beta$ is preserved:
```
Result := α;
repeat
  for each sub-relation R_i do:
    t := (Result ∩ R_i)⁺ ∩ R_i;
    Result := Result ∪ t;
until (Result does not change)

If β ⊆ Result, then the dependency α → β is preserved.
```
If all dependencies in $F$ are preserved, the decomposition is dependency-preserving.

---

## 7. Multi-valued Dependencies (MVDs) & 4NF

### Multi-valued Dependency (MVD)
An MVD $X \twoheadrightarrow Y$ holds on $R$ if, for any legal relation instance, the presence of tuples $(x, y_1, z_1)$ and $(x, y_2, z_2)$ implies the presence of $(x, y_1, z_2)$ and $(x, y_2, z_1)$. (The $Y$-values from both tuples swap with both $Z$-values.)
- The value of $X$ determines a *set* of values for $Y$, and this set is completely independent of the attributes in $Z = R - (X \cup Y)$.
- Represented with a double-headed arrow: $X \twoheadrightarrow Y$.
- **Trivial MVD**: $X \twoheadrightarrow Y$ is trivial if $Y \subseteq X$ or $X \cup Y = R$.

### Fourth Normal Form (4NF)
A relation schema $R$ is in 4NF with respect to a set of functional and multi-valued dependencies $D$ if, for all non-trivial multi-valued dependencies $X \twoheadrightarrow Y$ in $D^+$:
- $X$ is a **superkey** of $R$.

*Note*: Every relation in 4NF is also in BCNF.
