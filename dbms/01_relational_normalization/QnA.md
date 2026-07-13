# Q&A — Relational Model & Normalization Theory

---

## 🟢 Easy

**Q1. Define Superkey, Candidate Key, Primary Key, and Foreign Key.**

- **Superkey**: Any set of attributes that uniquely identifies a row in a table. It can contain extra, redundant attributes.
- **Candidate Key**: A minimal superkey. It contains no redundant attributes (if you remove any attribute, it ceases to be a superkey).
- **Primary Key**: The specific candidate key chosen by the database designer to identify tuples. It cannot contain NULL values.
- **Foreign Key**: A column or group of columns that references the primary key of another table, establishing a link between the two and enforcing referential integrity.

---

**Q2. What is a weak entity set? Give a real-world example.**

A **weak entity set** is an entity set that does not possess a primary key of its own. It relies on an owner (strong) entity set via an identifying relationship to be uniquely identified.
- It contains a **partial key** (or discriminator) that distinguishes entities under the same owner.
- **Example**: `Dependent(Name, Age, Relationship)` associated with `Employee(Emp_ID, Name, Salary)`. The `Dependent` cannot be uniquely identified by their name alone (multiple employees could have a dependent named "John"). It is identified by the combination of `Emp_ID` (from the employee) and the dependent's `Name` (partial key).

---

**Q3. State Armstrong's Axioms for functional dependencies.**

Armstrong's Axioms are three sound and complete rules used to infer all FDs:
1. **Reflexivity**: If $Y \subseteq X$, then $X \rightarrow Y$.
2. **Augmentation**: If $X \rightarrow Y$, then $XZ \rightarrow YZ$ for any $Z$.
3. **Transitivity**: If $X \rightarrow Y$ and $Y \rightarrow Z$, then $X \rightarrow Z$.

---

**Q4. What is the difference between a prime and a non-prime attribute?**

- **Prime Attribute**: An attribute that is a member of *at least one* candidate key of the relation.
- **Non-prime Attribute**: An attribute that is not a part of *any* candidate key.

For example, if the candidate keys of $R(A, B, C, D)$ are $\{AB\}$ and $\{AC\}$, then $A$, $B$, and $C$ are prime attributes, and $D$ is a non-prime attribute.

---

## 🟡 Medium

**Q5. Explain the three database anomalies that occur in unnormalized schemas.**

1. **Insertion Anomaly**: Inability to insert information without introducing a dummy placeholder. E.g., if a table stores employee and department info, and the primary key is `Emp_ID`, we cannot add a new department until we hire at least one employee for it.
2. **Update Anomaly**: Redundant data leads to inconsistency during updates. If `Dept_Name` is repeated for 100 employees, changing the department name requires updating all 100 rows. Missing one row leads to an inconsistent state.
3. **Deletion Anomaly**: Unintentional loss of data. If the last employee in a department is deleted, the entire record of the department's existence is erased.

---

**Q6. Compare 3NF and BCNF. Why is BCNF considered stronger?**

A relation is in **3NF** if, for every non-trivial functional dependency $X \rightarrow A$:
- Either $X$ is a superkey,
- Or $A$ is a prime attribute.

A relation is in **BCNF** if, for every non-trivial functional dependency $X \rightarrow A$:
- $X$ must be a superkey.

**Why BCNF is stronger**: BCNF removes the second option of 3NF. It does not allow non-trivial dependencies where the left side is not a superkey, even if the right side is a prime attribute. BCNF guarantees that all redundancy determined by functional dependencies is completely eliminated, whereas 3NF allows minor redundancies.

---

**Q7. Is it always possible to decompose a relation into BCNF that is both lossless and dependency-preserving?**

**No**. While it is always possible to achieve a **lossless-join** decomposition into BCNF, it is **not always possible** to make it dependency-preserving. 

**Example**: $R(A, B, C)$ with $FD = \{AB \rightarrow C, C \rightarrow A\}$.
- Candidate keys: $AB$ and $BC$.
- $C \rightarrow A$ violates BCNF because $C$ is not a superkey (its closure is $CA$, which does not contain $B$).
- If we decompose $R$ to satisfy BCNF: $R_1(C, A)$ and $R_2(C, B)$.
- The dependency $AB \rightarrow C$ is **lost** because its attributes are split across $R_1$ and $R_2$.
- Thus, we cannot achieve a BCNF decomposition that is both lossless and dependency-preserving. If we must preserve this dependency, we must settle for **3NF**.

---

## 🔴 Hard

**Q8. Consider a relation $R(A, B, C, D, E, G)$ with the following set of functional dependencies $F$:**
$$F = \{AB \rightarrow C, \ C \rightarrow A, \ BC \rightarrow D, \ ACD \rightarrow B, \ D \rightarrow EG\}$$
**Find all the candidate keys of $R$.**

**Step 1: Partition attributes based on their positions in the FDs.**
- Left side only (L-type): none. (Every attribute appears on the right side of at least one FD).
- Right side only (R-type): $E, G$ (they only appear on the right side of $D \rightarrow EG$).
- Both sides (LR-type): $A, B, C, D$.

**Step 2: Identify essential attributes.**
Attributes that are L-type plus attributes not present in FDs *must* be in every candidate key. Here, there are no L-type attributes. However, let's analyze which attributes cannot be determined by others:
- $E$ and $G$ can be determined by $D$.
- $D$ is determined by $BC$.
- $C$ is determined by $AB$.
- $B$ is determined by $ACD$.
- $A$ is determined by $C$.
Let's find the closure of various combinations of LR-type attributes $\{A, B, C, D\}$.

**Step 3: Test candidate key candidates.**
Let's try combination $BC$:
$$(BC)^+ = \{B, C\}$$
- Using $C \rightarrow A$, we get $A$: $(BC)^+ = \{A, B, C\}$
- Using $AB \rightarrow C$ (already have $C$).
- Using $BC \rightarrow D$, we get $D$: $(BC)^+ = \{A, B, C, D\}$
- Using $D \rightarrow EG$, we get $E, G$: $(BC)^+ = \{A, B, C, D, E, G\} = R$.
Since $(BC)^+ = R$ and no proper subset of $\{B, C\}$ is a superkey (check: $B^+ = \{B\}$, $C^+ = \{A, C\}$), **$BC$ is a Candidate Key**.

Let's try another combination. Since $C \rightarrow A$, let's check $AB$:
$$(AB)^+ = \{A, B\}$$
- Using $AB \rightarrow C$, we get $C$: $(AB)^+ = \{A, B, C\}$
- Using $BC \rightarrow D$ (since we have $B, C$), we get $D$: $(AB)^+ = \{A, B, C, D\}$
- Using $D \rightarrow EG$, we get $E, G$: $(AB)^+ = \{A, B, C, D, E, G\} = R$.
Thus, **$AB$ is a Candidate Key**.

Let's try combination $CD$:
$$(CD)^+ = \{C, D\}$$
- Using $C \rightarrow A$, we get $A$: $(CD)^+ = \{A, C, D\}$
- Using $ACD \rightarrow B$, we get $B$: $(CD)^+ = \{A, B, C, D\}$
- Using $D \rightarrow EG$, we get $E, G$: $(CD)^+ = \{A, B, C, D, E, G\} = R$.
Thus, **$CD$ is a Candidate Key**.

Are there any other candidate keys? Let's check $AC$:
$$(AC)^+ = \{A, C\}$$ (No $B$, cannot determine others).

Let's check $BD$:
$$(BD)^+ = \{B, D\}$$
- Using $D \rightarrow EG$, we get $E, G$: $(BD)^+ = \{B, D, E, G\}$ (Cannot determine $A$ or $C$).

Let's check $AD$:
$$(AD)^+ = \{A, D\}$$ (Cannot determine $B$ or $C$).

**Summary of Candidate Keys**: $\{AB, BC, CD\}$.

---

**Q9. Consider the relation schema $R(A, B, C, D, E)$ with the functional dependencies:**
$$F = \{A \rightarrow B, \ BC \rightarrow D, \ D \rightarrow A\}$$
**Identify the highest normal form of $R$.**

**Step 1: Find the candidate keys.**
- Left side only: $C, E$ (they never appear on the right side of any FD).
- Right side only: none.
- Both sides: $A, B, D$.

Since $C$ and $E$ must be in every candidate key, let's compute the closure of $CE$:
$$(CE)^+ = \{C, E\}$$ (not $R$).

Let's add the LR attributes one by one:
$$(ACE)^+ = \{A, C, E\}$$
- $A \rightarrow B \implies (ACE)^+ = \{A, B, C, E\}$
- $BC \rightarrow D \implies (ACE)^+ = \{A, B, C, D, E\} = R$.
So **$ACE$ is a Candidate Key**.

Let's check $DCE$:
$$(DCE)^+ = \{D, C, E\}$$
- $D \rightarrow A \implies (DCE)^+ = \{A, C, D, E\}$
- $A \rightarrow B \implies (DCE)^+ = \{A, B, C, D, E\} = R$.
So **$DCE$ is a Candidate Key**.

Let's check $BCE$:
$$(BCE)^+ = \{B, C, E\}$$ (Cannot determine others because $B$ and $C$ alone do not lead to $A$ or $D$).

**Candidate Keys**: $\{ACE, DCE\}$.
- **Prime attributes**: $\{A, C, D, E\}$
- **Non-prime attributes**: $\{B\}$

**Step 2: Test 1NF.**
- Assumed to be in 1NF (atomic attributes).

**Step 3: Test 2NF.**
- A relation is in 2NF if there are no partial dependencies on any candidate key for any **non-prime** attribute.
- The only non-prime attribute is $B$.
- Let's check FDs pointing to $B$: $A \rightarrow B$.
- Is $A$ a proper subset of a candidate key? Yes, $A$ is a proper subset of $ACE$.
- Therefore, $A \rightarrow B$ is a **partial dependency** (a part of candidate key determines a non-prime attribute).
- Hence, the relation is **NOT in 2NF**.

**Conclusion**: The highest normal form of the relation is **1NF**.

---

**Q10. Test if the decomposition of $R(A, B, C, D, E)$ with $F = \{A \rightarrow C, \ B \rightarrow D, \ C \rightarrow E\}$ into $R_1(A, B)$, $R_2(A, C)$, $R_3(B, D, E)$ is lossless or lossy using the Chase Algorithm (Matrix Method).**

**Step 1: Construct the initial matrix.**
Rows represent the decomposed tables $R_1, R_2, R_3$. Columns represent attributes $A, B, C, D, E$.

| Schema | A | B | C | D | E |
|---|---|---|---|---|---|
| $R_1(A, B)$ | $a_1$ | $a_2$ | $b_{13}$ | $b_{14}$ | $b_{15}$ |
| $R_2(A, C)$ | $a_1$ | $b_{22}$ | $a_3$ | $b_{24}$ | $b_{25}$ |
| $R_3(B, D, E)$ | $b_{31}$ | $a_2$ | $b_{33}$ | $a_4$ | $a_5$ |

**Step 2: Apply FD $A \rightarrow C$.**
- Check rows matching in the $A$ column: Row 1 and Row 2 both have $a_1$ in column $A$.
- Equate their values in the $C$ column ($b_{13}$ and $a_3$). Replace $b_{13}$ with $a_3$.

Updated matrix:

| Schema | A | B | C | D | E |
|---|---|---|---|---|---|
| $R_1(A, B)$ | $a_1$ | $a_2$ | **$a_3$** | $b_{14}$ | $b_{15}$ |
| $R_2(A, C)$ | $a_1$ | $b_{22}$ | $a_3$ | $b_{24}$ | $b_{25}$ |
| $R_3(B, D, E)$ | $b_{31}$ | $a_2$ | $b_{33}$ | $a_4$ | $a_5$ |

**Step 3: Apply FD $B \rightarrow D$.**
- Check rows matching in $B$: Row 1 and Row 3 both have $a_2$ in column $B$.
- Equate their values in the $D$ column ($b_{14}$ and $a_4$). Replace $b_{14}$ with $a_4$.

Updated matrix:

| Schema | A | B | C | D | E |
|---|---|---|---|---|---|
| $R_1(A, B)$ | $a_1$ | $a_2$ | $a_3$ | **$a_4$** | $b_{15}$ |
| $R_2(A, C)$ | $a_1$ | $b_{22}$ | $a_3$ | $b_{24}$ | $b_{25}$ |
| $R_3(B, D, E)$ | $b_{31}$ | $a_2$ | $b_{33}$ | $a_4$ | $a_5$ |

**Step 4: Apply FD $C \rightarrow E$.**
- Check rows matching in $C$: Row 1 and Row 2 both have $a_3$ in column $C$.
- Equate their values in $E$ ($b_{15}$ and $b_{25}$). They are both $b$-values, let's keep them equal (say $b_{15}$).
- Wait, does $R_3$ match? No, $R_3$ has $b_{33}$ in column $C$.

Wait, let's check if we missed any updates.
Let's check if we can apply $B \rightarrow D$ again or others. No changes.
Let's check if the matrix contains any row containing all $a$-values:
- Row 1: $a_1, a_2, a_3, a_4, b_{15}$ (not all $a$)
- Row 2: $a_1, b_{22}, a_3, b_{24}, b_{25}$ (not all $a$)
- Row 3: $b_{31}, a_2, b_{33}, a_4, a_5$ (not all $a$)

Thus, the decomposition is **lossy**.

**How to make it lossless?**
If we change $R_3(B, D, E)$ to $R_3(B, D)$ and add $R_4(C, E)$, let's see. Or if we had a direct connection between $B$ and $E$.
Since no row ended up with all $a$-values, we cannot reconstruct the original tuples without creating spurious data.
