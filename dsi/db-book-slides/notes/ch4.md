# Chapter 4: Intermediate SQL

*Database System Concepts, 7th Ed.*
*© Silberschatz, Korth and Sudarshan*

---

## 1. Join Expressions

Join operations take two relations and return another relation as a result. A join operation is essentially a Cartesian product that requires tuples in the two relations to match under some condition. It also specifies the attributes that are present in the result.

Join operations are typically used as subquery expressions in the `from` clause.

**Types of Joins:**
- **Natural Join**
- **Inner Join**
- **Outer Join**

### Natural Join
Natural join matches tuples with the same values for all common attributes, and retains only one copy of each common column.

*Example:* List the names of instructors along with the course ID of the courses they taught.
```sql
select name, course_id
from student natural join takes;
```

![Student Relation](../images/ch4_slides/slide_006.png)
![Takes Relation](../images/ch4_slides/slide_007.png)
![student natural join takes](../images/ch4_slides/slide_008.png)

**Multiple Relations:**
The `from` clause can combine multiple relations using natural join:
```sql
select A1, A2, … An
from r1 natural join r2 natural join .. natural join rn
where P;
```

**Danger in Natural Join:**
Beware of unrelated attributes with the same name which get equated incorrectly.

*Example:* List the names of students along with the titles of courses they have taken.
- **Incorrect:** `from student natural join takes natural join course;` (Omits pairs where the student takes a course in a department other than their own).
- **Correct:** 
  ```sql
  select name, title
  from student natural join takes, course
  where takes.course_id = course.course_id;
  ```

### Outer Join
An extension of the join operation that avoids loss of information. It computes the join and then adds tuples from one relation that do not match tuples in the other relation to the result, using `null` values for missing information.

**Forms of Outer Join:**
- **Left Outer Join** (`⟕`)
- **Right Outer Join** (`⟖`)
- **Full Outer Join** (`⟗`)

![Outer Join Examples](../images/ch4_slides/slide_011.png)
![Left Outer Join](../images/ch4_slides/slide_012.png)
![Right Outer Join](../images/ch4_slides/slide_013.png)
![Full Outer Join](../images/ch4_slides/slide_014.png)

### Joined Types and Conditions
- **Join Condition:** Defines which tuples in the two relations match, and what attributes are present in the result. Examples: `using (course_id)`, `on course.course_id = prereq.course_id`.
- **Join Type:** Defines how tuples in each relation that do not match any tuple in the other relation are treated. Examples: `inner join`, `left outer join`, `right outer join`, `full outer join`.

---

## 2. Views

In some cases, it is not desirable for all users to see the entire logical model (all the actual relations stored in the database). A view provides a mechanism to hide certain data from specific users. Any relation that is not part of the conceptual model but is made visible to a user as a "virtual relation" is called a view.

### View Definition
A view is defined using the `create view` statement:
```sql
create view v as <query expression>
```
Once defined, the view name `v` can be used to refer to the virtual relation it generates. A view definition does not create a new relation; rather, it saves an expression that is substituted into queries when the view is used.

*Example:*
```sql
create view faculty as
select ID, name, dept_name
from instructor;
```

### Views Defined Using Other Views
One view may be used in the expression defining another view. 
- A view `v1` **depends directly** on `v2` if `v2` is used in the expression defining `v1`.
- A view `v1` **depends** on `v2` if there is a path of dependencies from `v1` to `v2`.
- A view is **recursive** if it depends on itself.

### View Expansion
To define the meaning of views defined in terms of other views, view expansion repeats the replacement of any view relation with its defining expression until no view relations are present. As long as definitions are not recursive, this loop will terminate.

### Materialized Views
Certain database systems allow view relations to be physically stored. A physical copy is created when the view is defined.
- If relations used in the query are updated, the materialized view result becomes out of date.
- The view must be maintained by updating it whenever the underlying relations are updated.

### Update of a View
Updates on views must be translated to updates on the underlying instructor relation. Some updates cannot be translated uniquely, and some cannot be translated at all.

Most SQL implementations allow updates only on **simple views**:
- The `from` clause has only one database relation.
- The `select` clause contains only attribute names (no expressions, aggregates, or `distinct`).
- Any attribute not listed in the `select` clause can be set to `null`.
- The query does not have a `group by` or `having` clause.

---

## 3. Transactions

A transaction consists of a sequence of query and/or update statements and is a "unit" of work. The SQL standard specifies that a transaction begins implicitly when an SQL statement is executed.

The transaction must end with one of the following statements:
- `commit work`: The updates performed by the transaction become permanent in the database.
- `rollback work`: All the updates performed by the SQL statements in the transaction are undone.

**Properties:**
- **Atomic transaction:** Either fully executed or rolled back as if it never occurred.
- **Isolation:** Isolated from concurrent transactions.

---

## 4. Integrity Constraints

Integrity constraints guard against accidental damage to the database by ensuring that authorized changes do not result in a loss of data consistency.

### Constraints on a Single Relation
- `not null`
- `primary key`
- `unique (A1, A2, …, Am)`: States that the attributes form a candidate key. Candidate keys are permitted to be `null` (unlike primary keys).
- `check (P)`: Specifies a predicate `P` that must be satisfied by every tuple in a relation. (e.g., `check (semester in ('Fall', 'Winter', 'Spring', 'Summer'))`)

### Referential Integrity
Ensures that a value that appears in one relation for a given set of attributes also appears for a certain set of attributes in another relation.

Specified as part of the SQL `create table` statement:
```sql
foreign key (dept_name) references department
```
By default, it references the primary-key attributes of the referenced table, but a list of attributes can be specified explicitly.

**Cascading Actions:**
When a referential-integrity constraint is violated, the normal procedure is to reject the action. An alternative is to cascade the action (or use `set null` / `set default`):
```sql
foreign key (dept_name) references department
    on delete cascade
    on update cascade
```

### Integrity Constraint Violation During Transactions
When inserting tuples that reference each other, constraint checking can be problematic. Solutions:
- Insert referenced tuples first.
- Set foreign keys to `null` initially and update them later.
- Defer constraint checking.

### Complex Check Conditions
The predicate in the `check` clause can be an arbitrary predicate that includes a subquery. The condition must be checked when a tuple is inserted/modified, and also when the referenced relation changes.

### Assertions
An assertion is a predicate expressing a condition that we wish the database always to satisfy.
```sql
create assertion <assertion-name> check (<predicate>);
```

---

## 5. SQL Data Types and Schemas

### Built-in Data Types
- `date`: Contains a 4-digit year, month, and date (e.g., `date '2005-7-27'`).
- `time`: Time of day in hours, minutes, and seconds (e.g., `time '09:00:30.75'`).
- `timestamp`: Date plus time of day.
- `interval`: Period of time (e.g., `interval '1' day`). Intervals can be added to or subtracted from date/time/timestamp values.

### Large-Object Types
Used to store large objects like photos, videos, and CAD files.
- `blob`: Binary large object (uninterpreted binary data).
- `clob`: Character large object (large collection of character data).
When queried, a pointer is returned rather than the large object itself.

### User-Defined Types and Domains
- **User-Defined Types:** `create type Dollars as numeric (12,2) final`
- **Domains (SQL-92):** `create domain person_name char(20) not null`. Domains are similar to types but can have constraints (like `not null` or `check`) specified on them.

---

## 6. Index Definition in SQL

Many queries reference only a small proportion of the records in a table. An index is a data structure that allows the database system to efficiently find tuples with a specified value for an attribute, without scanning all tuples.

```sql
create index <name> on <relation-name> (attribute);
```
*Example:* `create index studentID_index on student(ID)`

---

## 7. Authorization

We may assign a user several forms of authorizations (privileges) on parts of the database (relations or views):
- **Read:** Allows reading, but not modification.
- **Insert:** Allows insertion of new data, but not modification of existing data.
- **Update:** Allows modification, but not deletion.
- **Delete:** Allows deletion of data.

**Authorization to Modify Schema:**
- **Index:** Creation and deletion of indices.
- **Resources:** Creation of new relations.
- **Alteration:** Addition or deletion of attributes.
- **Drop:** Deletion of relations.

### Authorization Specification in SQL
The `grant` statement is used to confer authorization:
```sql
grant <privilege list> on <relation or view> to <user list>
```
The `<user list>` can be a user-id, `public` (all valid users), or a role.
*Note:* Granting a privilege on a view does not imply granting privileges on the underlying relations. The grantor must already hold the privilege (or be the DBA).

The `revoke` statement is used to revoke authorization:
```sql
revoke <privilege list> on <relation or view> from <user list>
```
If the `<privilege list>` is `all`, all privileges are revoked. All privileges that depend on the revoked privilege are also revoked.

**Privileges in SQL:**
`select`, `insert`, `update`, `delete`, `all privileges`.

### Roles
A role distinguishes among various users regarding what they can access/update.
- Create a role: `create role <name>`
- Assign users/roles to a role: `grant <role> to <users>`
- Grant privileges to roles: `grant select on takes to instructor`
- Roles can be granted to other roles, creating a chain (e.g., `teaching_assistant` -> `instructor` -> `dean`).

### Authorization on Views
If a user is granted access to a view but does not have permissions on the underlying relations, they can still query the view (provided the view's creator had the necessary permissions).

### Other Authorization Features
- **references privilege:** Required to create a foreign key (e.g., `grant reference (dept_name) on department to Mariano`).
- **transfer of privileges:** `with grant option` allows the grantee to pass the privilege to others. Revoking can be specified as `cascade` or `restrict`.