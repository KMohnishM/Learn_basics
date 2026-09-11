# QnA: Relational Normalization

## 1. What is the difference between a superkey, candidate key, and primary key? Give a concrete example of a relation with 3 distinct candidate keys.
A superkey is any set of attributes that uniquely identifies a tuple in a relation. It may contain redundant attributes.
A candidate key is a minimal superkey; it uniquely identifies a tuple, but no proper subset of its attributes is a superkey.
A primary key is the specific candidate key chosen by the database designer to act as the principal means of identifying tuples.
While a relation can have multiple candidate keys, it can only have one primary key.
For example, consider a relation `Employee(EmployeeID, SSN, Email, Name, Department)`.
Assuming that EmployeeID, SSN, and Email are all guaranteed to be unique for every employee, we have three distinct candidate keys:
1. {EmployeeID}
2. {SSN}
3. {Email}
Any of these could serve as the primary key. If we choose EmployeeID as the primary key, then SSN and Email remain candidate keys (often implemented as UNIQUE constraints).
A superkey could be {EmployeeID, Name} or {SSN, Department}, as they both contain a candidate key and thus uniquely identify a row.

## 2. What does functional dependency X -> Y mean formally? Give 5 real-world FDs from a university schema.
Formally, a functional dependency X -> Y on a relation schema R implies that for any two tuples t1 and t2 in any valid relation instance r(R), if t1[X] = t2[X], then it must be true that t1[Y] = t2[Y].
In other words, the values of the attribute set X uniquely determine the values of the attribute set Y.
Here are 5 real-world functional dependencies from a university schema:
1. `StudentID -> Name, DateOfBirth, Major` (A student ID uniquely identifies the student's personal details and their major).
2. `CourseCode -> CourseName, Credits, Department` (A course code like 'CS101' uniquely identifies its name and credit hours).
3. `InstructorID -> InstructorName, Office, Salary` (An instructor ID uniquely determines the instructor's details).
4. `DepartmentName -> Building, Budget, HeadOfDepartment` (A department name uniquely determines its physical location and financial budget).
5. `StudentID, CourseCode, Semester -> Grade` (The combination of a student, the specific course, and the semester they took it uniquely determines the final grade they received).
These FDs are essential for determining the normal form of the relations in the database schema.

## 3. State Armstrong's Axioms formally. Then prove that the Union rule (if X->Y and X->Z then X->YZ) is derivable from the three axioms.
Armstrong's Axioms are a set of sound and complete rules used to infer all functional dependencies on a relational database.
1. Axiom of Reflexivity: If Y is a subset of X, then X -> Y.
2. Axiom of Augmentation: If X -> Y, then XZ -> YZ for any set of attributes Z.
3. Axiom of Transitivity: If X -> Y and Y -> Z, then X -> Z.
To prove the Union rule (If X -> Y and X -> Z, then X -> YZ):
Given:
(1) X -> Y
(2) X -> Z
Proof:
(3) X -> XY (Apply Augmentation to (1) by adding X to both sides: XX -> XY, which simplifies to X -> XY)
(4) XY -> YZ (Apply Augmentation to (2) by adding Y to both sides)
(5) X -> YZ (Apply Transitivity to (3) and (4))
Thus, the Union rule is successfully derived from Armstrong's Axioms alone, proving that if a set of attributes determines two other sets individually, it determines them jointly.

## 4. What is the closure of an attribute set X+ under a set of FDs? Walk through computing {StudentID}+.
The closure of an attribute set X, denoted as X+, is the set of all attributes that are functionally determined by X under a given set of functional dependencies (FDs) F.
It is computed using an iterative algorithm that starts with X+ = X, and repeatedly adds the right side of any FD whose left side is currently a subset of X+, until X+ stops changing.
Given FDs:
1. StudentID -> Name, Major
2. Major -> Department, Dean
3. Department -> Building
Let's compute {StudentID}+:
Step 1: Initialize the closure with the attribute set itself.
{StudentID}+ = {StudentID}
Step 2: Check FD 1 (StudentID -> Name, Major). The left side {StudentID} is in the closure. Add the right side.
{StudentID}+ = {StudentID, Name, Major}
Step 3: Check FD 2 (Major -> Department, Dean). The left side {Major} is a subset of the closure. Add the right side.
{StudentID}+ = {StudentID, Name, Major, Department, Dean}
Step 4: Check FD 3 (Department -> Building). The left side {Department} is in the closure. Add the right side.
{StudentID}+ = {StudentID, Name, Major, Department, Dean, Building}
No more FDs can add new attributes. The final closure {StudentID}+ contains all the listed attributes.

## 5. Explain 1NF, 2NF, and 3NF using a single running example.
Consider an unnormalized table: `OrderItems(OrderID, Date, CustomerName, ItemID, ItemName, Qty, Price)`.
1NF requires that all attributes contain atomic values (no repeating groups). Assume our table satisfies this, but its primary key is {OrderID, ItemID}.
2NF requires 1NF AND that no non-prime attribute is partially dependent on any candidate key.
In our table, `Date` and `CustomerName` depend only on `OrderID`, not the full key {OrderID, ItemID}. `ItemName` and `Price` depend only on `ItemID`.
To achieve 2NF, we decompose into:
- `Orders(OrderID, Date, CustomerName)`
- `Items(ItemID, ItemName, Price)`
- `OrderDetails(OrderID, ItemID, Qty)` (Qty depends on the full key).
3NF requires 2NF AND that no non-prime attribute is transitively dependent on the primary key.
Suppose in our `Orders` table, `CustomerName` determines `CustomerAddress` (not shown, but let's assume `Orders(OrderID, Date, CustomerID, CustomerName, CustomerAddress)`).
`OrderID -> CustomerID -> CustomerName, CustomerAddress`. The non-prime attributes depend on `CustomerID`, which is not a candidate key.
To achieve 3NF, we decompose `Orders` into:
- `Orders(OrderID, Date, CustomerID)`
- `Customers(CustomerID, CustomerName, CustomerAddress)`
This eliminates the transitive dependency and brings the schema into 3NF.

## 6. What is the difference between 3NF and BCNF? Use the CourseAdvisor example.
3NF strictly prohibits transitive dependencies of non-prime attributes on primary keys. However, it allows a prime attribute to depend on a non-prime attribute.
BCNF (Boyce-Codd Normal Form) is a stronger version of 3NF. It requires that for EVERY non-trivial functional dependency X -> Y, X must be a superkey. BCNF does not make exceptions for prime attributes.
Example: `CourseAdvisor(Student, Course, Advisor)`
FDs:
1. {Student, Course} -> Advisor (Each student has one advisor per course).
2. Advisor -> Course (Each advisor advises for exactly one specific course).
Candidate keys: {Student, Course} and {Student, Advisor}.
This relation is in 3NF because there are no non-prime attributes (all attributes are part of some candidate key).
However, it violates BCNF because of the FD `Advisor -> Course`. `Advisor` is a determinant but NOT a superkey.
If we decompose to achieve BCNF: `R1(Advisor, Course)` and `R2(Student, Advisor)`.
While in BCNF, this decomposition loses the dependency `{Student, Course} -> Advisor`. We can no longer easily enforce the rule that a student cannot have multiple advisors for the same course without joining the tables.

## 7. What is lossless-join decomposition? State the test for a two-relation decomposition.
A decomposition of relation R into R1 and R2 is a lossless-join decomposition if, for all valid instances of R, joining R1 and R2 via a natural join perfectly reconstructs the original relation R without generating any spurious (extra, incorrect) tuples.
The test for a lossless-join decomposition into R1 and R2 is that the intersection of their attributes must be a superkey for at least one of the decomposed relations.
Formally, either:
(R1 INTERSECT R2) -> R1  OR  (R1 INTERSECT R2) -> R2
Example: Given R(A, B, C) and FD B -> C. We decompose into R1(A, B) and R2(B, C).
Let's apply the test:
The intersection of R1 and R2 is {B} (since R1 INTERSECT R2 = {A, B} INTERSECT {B, C} = {B}).
We check if {B} is a superkey for R1 or R2.
In R2(B, C), the FD B -> C applies. Since B determines all other attributes in R2, {B} is a superkey for R2.
Because (R1 INTERSECT R2) -> R2 is true, the decomposition is lossless. We can safely decompose and later join on B without data corruption.

## 8. What is dependency-preserving decomposition? Give an example where choosing 3NF over BCNF is correct.
A dependency-preserving decomposition ensures that all functional dependencies present in the original relation can still be enforced by checking the individual decomposed relations, without needing to join them back together.
Formally, if F is the set of FDs, a decomposition is dependency-preserving if the union of the closures of the FDs on the individual decomposed relations is equal to the closure of F (F+).
Example where 3NF is preferred over BCNF:
Consider `CourseAdvisor(Student, Course, Advisor)` with FDs: {Student, Course} -> Advisor and Advisor -> Course.
As shown earlier, decomposing to BCNF yields `R1(Advisor, Course)` and `R2(Student, Advisor)`.
This BCNF decomposition is NOT dependency-preserving because the FD `{Student, Course} -> Advisor` cannot be enforced in either R1 or R2 alone. If a transaction attempts to insert a new advisor for an existing student-course pair, the system would have to join R1 and R2 to check the constraint, which is highly inefficient.
In this scenario, a database engineer would deliberately choose to leave the relation in 3NF (un-decomposed) to preserve the dependency and ensure efficient constraint checking, accepting the slight redundancy of the `Advisor -> Course` anomaly.

## 9. What is a canonical cover? Define extraneous attributes and redundant FDs.
A canonical cover (or minimal cover) for a set of functional dependencies F is a simplified set of FDs Fc that is logically equivalent to F (i.e., Fc+ = F+), but contains no redundancies.
An attribute is extraneous in an FD if removing it from the left or right side does not change the closure of the FD set.
An FD is redundant if removing the entire FD from the set does not change the closure of the FD set.
Given F = {A->BC, B->C, A->B, AB->C}. Let's find the canonical cover.
Step 1: Simplify right sides (singleton right sides):
F' = {A->B, A->C, B->C, A->B, AB->C}
Step 2: Remove redundant FDs:
A->B is repeated, keep one: {A->B, A->C, B->C, AB->C}.
Check A->C: A->B and B->C imply A->C (transitivity). So A->C is redundant. Remove it.
Current set: {A->B, B->C, AB->C}.
Step 3: Remove extraneous attributes from left sides:
In AB->C, is A or B extraneous?
Compute {A}+ under {A->B, B->C}. {A}+ = {A, B, C}. Since A already determines C, adding B is unnecessary. B is extraneous in AB->C.
The FD becomes A->C.
But wait, we already found A->C is redundant because of A->B and B->C. So AB->C is entirely redundant.
Final Canonical Cover Fc: {A->B, B->C}.

## 10. What are multi-valued dependencies (MVDs) and 4NF? Give the PersonHobbyLanguage example.
A multi-valued dependency (MVD) X ->-> Y occurs when, for a single value of X, there exists a set of values for Y, and this set of Y values is completely independent of the values of other attributes in the relation.
Fourth Normal Form (4NF) requires that a relation is in BCNF, and for every non-trivial MVD X ->-> Y, X must be a superkey.
Example: `PersonInfo(PersonName, Hobby, Language)`
Assume a person can have multiple hobbies and speak multiple languages, and these two sets are completely independent.
Sample data for 'Alice':
(Alice, Tennis, English)
(Alice, Tennis, French)
(Alice, Reading, English)
(Alice, Reading, French)
There is an MVD `PersonName ->-> Hobby` and `PersonName ->-> Language`. If Alice adds a new hobby 'Coding', we must add two new rows (Coding, English) and (Coding, French) to maintain the Cartesian product, causing severe update anomalies.
To achieve 4NF, we decompose the relation to separate the independent multi-valued facts:
- `PersonHobbies(PersonName, Hobby)`
- `PersonLanguages(PersonName, Language)`
This decomposition eliminates the MVD anomaly and normalizes the data.

## 11. What is denormalization? Give 3 concrete production scenarios where denormalization is the correct decision.
Denormalization is the deliberate process of adding redundancy back into a normalized database schema to improve read performance. It involves combining tables or storing derived data to avoid expensive JOIN operations during querying.
While it violates normalization rules, it is a valid engineering trade-off for read-heavy systems.
Three concrete production scenarios:
1. Materialized Views for Analytics: In a data warehouse, a fully normalized star schema might require joining 10 tables to generate a daily sales report. Denormalizing into a flat "wide table" allows lightning-fast aggregations.
2. Caching User Profiles: A system might frequently display a user's name, avatar, and total post count. Instead of joining `Users` and `Posts` with a `COUNT()` on every page load, the `post_count` can be stored directly on the `Users` table.
3. Order History Snapshots: When an e-commerce order is placed, the product's current name and price should be copied into the `OrderLineItems` table. If the product name changes later, the historical order invoice must reflect the original name. This is deliberate redundancy for historical accuracy.
Consistency Mechanisms: Denormalization requires mechanisms to keep the redundant data in sync. This is typically achieved using database triggers, background asynchronous workers (e.g., updating post counts via a message queue), or materialized view refreshes.

## 12. What is referential integrity? Explain ON DELETE CASCADE, ON DELETE RESTRICT, ON DELETE SET NULL.
Referential integrity is a database constraint ensuring that relationships between tables remain consistent. It guarantees that a foreign key value always points to an existing, valid primary key value in the referenced table.
When a referenced row is deleted, the database can react in several ways:
1. `ON DELETE CASCADE`: Automatically deletes all child rows that reference the deleted parent row.
   Correct usage: Deleting a `User` should cascade to delete their `UserPreferences`.
   Danger: Accidentally deleting a `Company` could cascade and wipe out thousands of `Employees` and `Orders` silently.
2. `ON DELETE RESTRICT` (or NO ACTION): Prevents the deletion of the parent row if any child rows still reference it, throwing an error.
   Correct usage: Deleting a `ProductCategory` should be restricted if there are still `Products` assigned to it, preventing orphaned products.
   Danger: Can make cleanup difficult if there are deep hierarchies of referenced data that must be deleted manually in exact order.
3. `ON DELETE SET NULL`: Sets the foreign key column in the child rows to NULL when the parent row is deleted.
   Correct usage: If an `Employee` is deleted, their `ManagedBy` foreign key on subordinate employees can be set to NULL until a new manager is assigned.
   Danger: Requires the foreign key column to be nullable. If the business logic expects a valid reference, application code might crash with NullPointerExceptions.

## 13. What is the difference between a natural key and a surrogate key? Compare UUID vs BIGSERIAL.
A natural key is a primary key formed of attributes that already exist in the real world and have business meaning (e.g., SSN, Email, ISBN).
A surrogate key is an artificially generated identifier with no intrinsic business meaning, created purely for database identification purposes (e.g., an auto-incrementing integer or a UUID).
Comparison in PostgreSQL (UUID vs BIGSERIAL):
1. Storage Size: `BIGSERIAL` (8-byte integer) is highly compact. `UUID` requires 16 bytes. This affects both table size and index size.
2. Index Performance: `BIGSERIAL` values are sequentially inserted. B-Tree indexes handle sequential inserts perfectly with minimal fragmentation. Standard v4 UUIDs are random, causing massive B-Tree index fragmentation and page splits, severely degrading insert performance on large tables.
3. Readability: `BIGSERIAL` values (1, 2, 3...) are easy for humans to read, remember, and communicate in support tickets. UUIDs (e.g., 550e8400-e29b-41d4-a716-446655440000) are unreadable.
4. Distributed Generation: This is where UUID shines. UUIDs can be generated by application servers independently without a central coordinator (database sequence), completely eliminating round-trips for ID generation and enabling seamless database sharding or active-active replication. `BIGSERIAL` forces a single point of truth for generation.

## 14. What are insertion anomalies, deletion anomalies, and update anomalies?
Anomalies are severe data integrity issues that occur in poorly normalized tables when performing standard CRUD operations.
Consider an unnormalized table: `EmployeeDept(EmpID, EmpName, DeptName, DeptLocation)`.
1. Insertion Anomaly: Inability to insert certain facts into the database because other facts are missing.
   Example: Suppose we want to create a new department 'Research' in 'Building C', but we haven't hired any employees for it yet. Because EmpID is likely the primary key (or part of it), we cannot insert this department into the table without a dummy employee, violating entity integrity.
2. Deletion Anomaly: Unintended loss of data due to the deletion of other data.
   Example: If the only employee in the 'Marketing' department quits, and we delete their row `DELETE FROM EmployeeDept WHERE EmpID = 105;`, we completely lose the fact that the 'Marketing' department is located in 'Building A'.
3. Update Anomaly: Data inconsistency resulting from data redundancy when updating a value.
   Example: If the 'Sales' department moves to 'Building B', we must execute:
   ```sql
   UPDATE EmployeeDept SET DeptLocation = 'Building B' WHERE DeptName = 'Sales';
   ```
   If the system crashes halfway through updating multiple rows, some Sales employees will be listed in the old building and some in the new one, destroying data consistency.

## 15. What is 5NF (Project-Join Normal Form)? Give a real-world example.
Fifth Normal Form (5NF), or Project-Join Normal Form (PJNF), deals with cases where a relation can be decomposed into three or more smaller relations, but cannot be decomposed into just two without data loss. It eliminates join dependencies that are not implied by candidate keys.
A table is in 5NF if every non-trivial join dependency is implied by the superkeys of the table.
Real-world example: `SupplierPartProject(Supplier, Part, Project)`
Suppose the rule is: If a Supplier provides a Part, and the Supplier supplies to a Project, and the Project uses that Part, then the Supplier MUST supply that Part to that Project.
This creates a cyclic dependency.
Data:
(Smith, Nut, ProjectA)
(Smith, Bolt, ProjectB)
(Jones, Nut, ProjectA)
If we decompose this into only two tables (e.g., Supplier-Part and Supplier-Project), and join them back, we get spurious tuples (e.g., implying Smith supplies Bolts to ProjectA, which isn't true).
To satisfy 5NF, we must decompose into three relations:
- R1(Supplier, Part)
- R2(Part, Project)
- R3(Supplier, Project)
Only by joining all three of these relations together can we losslessly reconstruct the original `SupplierPartProject` table without generating false data based on the business rules.
