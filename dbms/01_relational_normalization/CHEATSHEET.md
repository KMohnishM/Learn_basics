# Cheat Sheet — Relational Model & Normalization

## Keys & Closures

### Attribute Closure Algorithm
```
X⁺ = X
repeat
  for each FD (A → B) in F:
    if A ⊆ X⁺:
      X⁺ = X⁺ ∪ B
until X⁺ does not change
```

### Candidate Key Identification Rules
Partition relation attributes based on their positions in the FD set $F$:

| Attribute Type | Position in FDs | Key Status |
|----------------|-----------------|------------|
| **L-type** | Left side only, or not in FDs | **MUST** be in every Candidate Key |
| **R-type** | Right side only | **CANNOT** be in any Candidate Key |
| **LR-type** | Both sides | **MAY** be in Candidate Key |

**Steps:**
1. Let $X$ = Union of all L-type attributes.
2. Compute $X^+$. If $X^+ = R$, then $X$ is the unique Candidate Key.
3. If $X^+ \ne R$, append combinations of LR-type attributes to $X$ and test their closures.

---

## Normal Forms Summary

Let $X \rightarrow A$ be any non-trivial functional dependency.
- **Prime attribute**: Part of *any* candidate key.
- **Non-prime attribute**: Not part of *any* candidate key.

| Normal Form | Rule / Constraint | Violations |
|-------------|-------------------|------------|
| **1NF** | Attributes must contain only atomic values. No sets or tables as values. | Multi-valued or composite attributes. |
| **2NF** | In 1NF + No **partial dependency** of non-prime attributes on a candidate key. | $Proper\_Subset\_of\_CK \rightarrow Non-prime$ |
| **3NF** | In 2NF + For every $X \rightarrow A$, either $X$ is a **Superkey** or $A$ is **Prime**. | $Non-superkey \rightarrow Non-prime$ |
| **BCNF** | For every $X \rightarrow A$, $X$ must be a **Superkey**. | $Non-superkey \rightarrow Prime$ |
| **4NF** | For every non-trivial MVD $X \twoheadrightarrow Y$, $X$ must be a **Superkey**. | Multi-valued dependencies determined by non-keys. |

---

## Decomposition Properties

Let relation $R$ be decomposed into $R_1, R_2, \dots, R_k$.

### 1. Lossless-Join Decomposition (Binary Case)
The decomposition of $R$ into $R_1$ and $R_2$ is lossless-join if:
$$(R_1 \cap R_2) \rightarrow R_1 \quad \text{or} \quad (R_1 \cap R_2) \rightarrow R_2$$
*(The common attributes must form a superkey of at least one of the relations).*

### 2. Dependency Preservation
A decomposition is dependency-preserving if the union of FDs of all sub-relations is equivalent to $F$:
$$(F_1 \cup F_2 \cup \dots \cup F_k)^+ = F^+$$

**Testing a specific dependency $X \rightarrow Y$:**
1. Initialize $Result = X$.
2. For each sub-relation $R_i$:
   - $t = (Result \cap R_i)^+ \cap R_i$
   - $Result = Result \cup t$
3. Repeat step 2 until $Result$ does not change.
4. If $Y \subseteq Result$, the dependency is **preserved**.

---

## Canonical Cover (Minimal Cover) — $F_c$

A **Canonical Cover** $F_c$ is a minimal, equivalent set of FDs (no redundant FDs, no redundant attributes on LHS). Required for the **3NF Synthesis Algorithm**.

**Steps to find $F_c$:**
1. **Remove extraneous attributes** from the LHS of every FD (test if $A$ is extraneous in $AB \rightarrow C$: remove $A$, check if $B^+ \ni C$ already — if yes, $A$ is extraneous).
2. **Remove redundant FDs**: For each $X \rightarrow Y$ in $F$, check if $Y$ is derivable from $F - \{X \rightarrow Y\}$. If yes, remove it.
3. Repeat until $F_c$ is stable.

**3NF Synthesis Algorithm:**
1. Compute the canonical cover $F_c$.
2. For each FD $X \rightarrow Y$ in $F_c$, create relation schema $R_i(XY)$.
3. If no schema contains a candidate key of $R$, add a new schema with the candidate key attributes.
4. Remove any schema $R_i$ whose attributes are a subset of another schema $R_j$.



```
                [ Atomic Attributes? ]
                          │
                  No ─────┴───── Yes
                 (1NF)          (Go to 2NF check)
                                  │
                  ┌───────────────┴───────────────┐
         [ Partial Dependency? ]       [ No Partial Dependency? ]
                  │                               │
                 1NF                             2NF
                                        (Go to 3NF check)
                                          │
                  ┌───────────────────────┴───────────────────────┐
       [ Transitive Dependency? ]       [ No Transitive Dependency? ]
                  │                               │
                 2NF                             3NF
                                        (Go to BCNF check)
                                          │
                  ┌───────────────────────┴───────────────────────┐
       [ Non-trivial X → A where ]      [ Every non-trivial X → A has ]
       [ X is NOT a Superkey ]          [ X as a Superkey ]
                  │                               │
                 3NF                             BCNF
```
