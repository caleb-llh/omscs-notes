# Chapter 3: Introduction to SQL

**Source:** *Database System Concepts, 7th Ed.* by Silberschatz, Korth, and Sudarshan.

## 1. Overview and History
- **History:** SQL was originally developed by IBM as the "Sequel" language as part of the System R project at the IBM San Jose Research Laboratory. It was later renamed to Structured Query Language (SQL).
- **Standards:** ANSI and ISO have published multiple standards over the years, including SQL-86, SQL-89, SQL-92, SQL:1999 (Y2K compliant), and SQL:2003. Commercial systems generally offer most SQL-92 features along with varying proprietary extensions from later standards.
- **SQL Parts:** 
  - **DML (Data Manipulation Language):** Provides the ability to query information, and to insert, delete, and modify tuples in the database.
  - **DDL (Data Definition Language):** Includes commands for specifying schemas and integrity constraints.
  - **View Definition:** Commands for defining views.
  - **Transaction Control:** Commands specifying the beginning and ending of transactions.
  - **Embedded and Dynamic SQL:** Defines how SQL statements can be embedded within general-purpose programming languages.
  - **Authorization:** Includes commands for specifying access rights to relations and views.

## 2. SQL Data Definition (DDL)
The SQL data-definition language (DDL) allows the specification of information about relations, including schemas, attribute types, integrity constraints, indices, security/authorization, and physical storage structures on disk.

### Domain Types
- `char(n)`: Fixed-length character string, with user-specified length `n`.
- `varchar(n)`: Variable-length character string, with user-specified maximum length `n`.
- `int`: Integer (machine-dependent).
- `smallint`: Small integer (machine-dependent subset of the integer domain).
- `numeric(p, d)`: Fixed-point number with user-specified precision `p` digits, and `d` digits to the right of the decimal point (e.g., `numeric(3,1)` stores 44.5 exactly).
- `real`, `double precision`: Floating-point and double-precision numbers (machine-dependent).
- `float(n)`: Floating-point number with user-specified precision of at least `n` digits.

### Creating Tables
Relations are defined using the `create table` command.
```sql
create table instructor (
    ID char(5),
    name varchar(20) not null,
    dept_name varchar(20),
    salary numeric(8,2),
    primary key (ID),
    foreign key (dept_name) references department
);
```

### Integrity Constraints
SQL prevents updates that violate integrity constraints.
- `primary key (A1, ..., An)`
- `foreign key (Am, ..., An) references r`
- `not null`

### Table Updates
- **Insert:** `insert into instructor values ('10211', 'Smith', 'Biology', 66000);`
- **Delete:** `delete from student;` (Removes all tuples from the relation)
- **Drop Table:** `drop table r;` (Removes the table structure entirely)
- **Alter Table:** 
  - Add attribute: `alter table r add A D;` (Existing tuples are assigned `null` for the new attribute `A` of domain `D`).
  - Drop attribute: `alter table r drop A;` (Not supported by all databases).

## 3. Basic Query Structure
A typical SQL query consists of three main clauses: `select`, `from`, and `where`. The result of an SQL query is a relation.
```sql
select A1, A2, ..., An
from r1, r2, ..., rm
where P
```

### The `select` Clause
- Corresponds to the projection operation of the relational algebra. Lists the desired attributes.
- **Case Insensitivity:** SQL names are case-insensitive (e.g., `Name` ≡ `NAME` ≡ `name`).
- **Duplicates:** SQL allows duplicates by default. Use the `distinct` keyword to force elimination of duplicates (e.g., `select distinct dept_name`), and `all` to explicitly retain them.
- **Asterisk:** `select *` denotes "all attributes".
- **Literals & Arithmetic:** You can select literal strings (e.g., `select '437' as FOO`) or perform arithmetic expressions (`+`, `-`, `*`, `/`) on attributes (e.g., `select ID, name, salary/12 as monthly_salary`).

### The `where` Clause
- Corresponds to the selection predicate of the relational algebra. Specifies conditions that the result must satisfy.
- Allows logical connectives: `and`, `or`, and `not`.
- Comparison operators: `<`, `<=`, `>`, `>=`, `=`, and `<>`.
- Supports the `between` comparison operator (e.g., `where salary between 90000 and 100000`).
- Supports tuple comparison: `where (instructor.ID, dept_name) = (teaches.ID, 'Biology')`.

### The `from` Clause
- Corresponds to the Cartesian product operation. Lists the relations involved.
- For common attributes across joined tables, rename using the relation name (e.g., `instructor.ID`).

### The Rename Operation
- Use the `as` clause to rename relations and attributes: `old-name as new-name`.
- Example: `from instructor as T, instructor as S`. The keyword `as` is optional (`instructor T`).

![Self Join Example](../images/ch3_slides/slide_021.png)

### String Operations
- The `like` operator uses patterns for string matching:
  - `%` matches any substring.
  - `_` matches any single character.
- Example: `where name like '%dar%'`.
- Escape characters can be defined: `like '100 \%' escape '\'`.
- Patterns are case-sensitive.
- SQL also supports string concatenation (using `||`), case conversion, string length extraction, etc.

### Ordering Tuples
- Use `order by` to sort the display of tuples.
- Specify `desc` for descending order or `asc` for ascending order (default).
- Can sort on multiple attributes: `order by dept_name, name`.

## 4. Set Operations
SQL supports standard set operations. Each operation automatically eliminates duplicates by default.
- `union`
- `intersect`
- `except`
To retain all duplicates, append the `all` keyword: `union all`, `intersect all`, `except all`.

## 5. Null Values
- `null` signifies an unknown value or that a value does not exist.
- The result of any arithmetic expression involving `null` is `null`.
- Use predicates `is null` and `is not null` to check for null values.
- Comparisons involving `null` (other than the `is null` predicates) evaluate to **unknown** (e.g., `5 < null` or `null = null` evaluates to unknown).
- **Three-Valued Logic (True, False, Unknown):**
  - `and`: (true and unknown) = unknown; (false and unknown) = false; (unknown and unknown) = unknown.
  - `or`: (unknown or true) = true; (unknown or false) = unknown; (unknown or unknown) = unknown.
  - The result of a `where` clause predicate is treated as `false` if it evaluates to `unknown`.

## 6. Aggregate Functions
These functions operate on the multiset of values of a column and return a single value:
- `avg`: Average value
- `min`: Minimum value
- `max`: Maximum value
- `sum`: Sum of values
- `count`: Number of values (e.g., `count(*)` or `count(distinct ID)`)

### Grouping and Having
- **`group by`:** Used to group rows. Attributes in the `select` clause that are *not* inside aggregate functions must appear in the `group by` list.
- **`having`:** Applies predicates to groups *after* they are formed (whereas the `where` clause applies predicates to tuples *before* forming groups).
```sql
select dept_name, avg(salary) as avg_salary
from instructor
group by dept_name
having avg(salary) > 42000;
```

## 7. Nested Subqueries
A subquery is a `select-from-where` expression nested within another query.

### Set Membership (`in` / `not in`)
Tests whether a value matches any value in a set returned by a subquery.
```sql
select distinct name
from instructor
where name not in ('Mozart', 'Einstein');
```

![Set Membership](../images/ch3_slides/slide_036.png)

### Set Comparison (`some` / `all`)
- `> some`: Evaluates to true if the condition holds for at least one element in the set (`= some` is equivalent to `in`).
- `> all`: Evaluates to true if the condition holds for all elements in the set (`<> all` is equivalent to `not in`).

![Set Comparison](../images/ch3_slides/slide_039.png)

### Test for Empty Relations (`exists` / `not exists`)
- The `exists` construct returns `true` if the argument subquery is nonempty.
- Commonly used with **correlated subqueries**, where the inner query references a correlation name (variable) from the outer query.

### Test for Absence of Duplicate Tuples (`unique`)
- The `unique` construct evaluates to `true` if a given subquery contains no duplicates.

### Subqueries in the `from` Clause
SQL allows subquery expressions to be used in the `from` clause, essentially creating a temporary relation to be queried against.
```sql
select dept_name, avg_salary
from (select dept_name, avg(salary) as avg_salary
      from instructor
      group by dept_name)
where avg_salary > 42000;
```

![Subqueries in the From Clause](../images/ch3_slides/slide_048.png)

### The `with` Clause
Provides a way of defining a temporary relation whose definition is available only to the query in which the `with` clause occurs. Useful for simplifying complex queries.
```sql
with max_budget(value) as (
    select max(budget) from department
)
select department.name
from department, max_budget
where department.budget = max_budget.value;
```

### Scalar Subqueries
A subquery that returns a single value, and is used wherever a single value is expected. Throws a runtime error if it returns more than one tuple.

## 8. Modification of the Database

### Deletion
Deletes tuples from a relation.
```sql
delete from instructor
where salary < (select avg(salary) from instructor);
```
*(Note: When evaluating this, SQL computes the average first and identifies all tuples to delete, then executes the deletions without iteratively recomputing the average).*

### Insertion
Adds new tuples to a relation.
```sql
insert into course (course_id, title, dept_name, credits)
values ('CS-437', 'Database Systems', 'Comp. Sci.', 4);
```
Can also insert the results of a query (`insert into ... select ...`). The `select` statement is fully evaluated before any results are inserted.

### Updates
Updates values in existing tuples.
```sql
update instructor
set salary = salary * 1.05
where salary < 70000;
```
**Case Statement for Conditional Updates:**
Allows for conditional updating in a single pass where order of execution would otherwise cause logical errors.
```sql
update instructor
set salary = case
    when salary <= 100000 then salary * 1.05
    else salary * 1.03
end;
```
Scalar subqueries can also be used inside `update` statements to recompute values based on other tables.