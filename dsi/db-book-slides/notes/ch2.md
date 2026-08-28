# Chapter 2: Intro to Relational Model

## Structure of Relational Databases

- **Relation**: A table consisting of **attributes** (columns) and **tuples** (rows).
- **Attributes**: The set of allowed values for each attribute is called the **domain** of the attribute.
  - Attribute values are (normally) required to be atomic; that is, indivisible.
  - The special value **null** is a member of every domain. It indicates that the value is "unknown".
  - The null value causes complications in the definition of many operations.
- **Relations are Unordered**: Order of tuples is irrelevant (tuples may be stored in an arbitrary order).

## Database Schema and Instance

- **Database schema**: The logical structure of the database.
- **Database instance**: A snapshot of the data in the database at a given instant in time.
- **Example**:
  - Schema: `instructor (ID, name, dept_name, salary)`
  - Instance: The actual data rows at a given moment.

![Example of a Instructor Relation](../images/ch2_slides/slide_003.png)
![Schema Diagram for University Database](../images/ch2_slides/slide_008.png)

## Keys

- Let $K \subseteq R$
- **Superkey**: $K$ is a superkey of $R$ if values for $K$ are sufficient to identify a unique tuple of each possible relation $r(R)$.
  - Example: `{ID}` and `{ID, name}` are both superkeys of `instructor`.
- **Candidate key**: Superkey $K$ is a candidate key if $K$ is minimal.
  - Example: `{ID}` is a candidate key for `instructor`.
- **Primary key**: One of the candidate keys is selected to be the primary key.
- **Foreign key constraint**: Value in one relation must appear in another.
  - **Referencing relation**: The relation containing the foreign key.
  - **Referenced relation**: The relation being referred to.
  - Example: `dept_name` in `instructor` is a foreign key from `instructor` referencing `department`.

## Relational Query Languages

- Languages can be procedural versus non-procedural (or declarative).
- **"Pure" languages**:
  - Relational algebra
  - Tuple relational calculus
  - Domain relational calculus
- The above 3 pure languages are equivalent in computing power.

## The Relational Algebra

- An algebraic language consisting of a set of operations that take one or two relations as input and produce a new relation as their result.
- **Six basic operators**:
  - select: $\sigma$
  - project: $\Pi$
  - union: $\cup$
  - set difference: $-$
  - Cartesian product: $\times$
  - rename: $\rho$

### Select Operation ($\sigma$)
- The select operation selects tuples that satisfy a given predicate.
- **Notation**: $\sigma_p(r)$, where $p$ is the selection predicate.
- **Example**: Select those tuples of the `instructor` relation where the instructor is in the "Physics" department.
  - Query: $\sigma_{\text{dept\_name}=\text{"Physics"}}(\text{instructor})$
- We allow comparisons using $=, \neq, >, \geq, <, \leq$ in the selection predicate.
- We can combine several predicates into a larger predicate by using connectives: $\land$ (and), $\lor$ (or), $\lnot$ (not).
  - Example: Find the instructors in Physics with a salary greater than 90,000.
    - $\sigma_{\text{dept\_name}=\text{"Physics"} \land \text{salary} > 90000}(\text{instructor})$
- The select predicate may include comparisons between two attributes.
  - Example: Find all departments whose name is the same as their building name.
    - $\sigma_{\text{dept\_name}=\text{building}}(\text{department})$

### Project Operation ($\Pi$)
- A unary operation that returns its argument relation, with certain attributes left out.
- **Notation**: $\Pi_{A_1, A_2, \dots, A_k}(r)$ where $A_1, A_2, \dots, A_k$ are attribute names and $r$ is a relation name.
- The result is defined as the relation of $k$ columns obtained by erasing the columns that are not listed.
- Duplicate rows are removed from the result, since relations are sets.
- **Example**: Eliminate the `dept_name` attribute of `instructor`.
  - Query: $\Pi_{\text{ID, name, salary}}(\text{instructor})$

![Project Operation Example](../images/ch2_slides/slide_013.png)

### Composition of Relational Operations
- The result of a relational-algebra operation is a relation, and therefore relational-algebra operations can be composed together into a relational-algebra expression.
- **Example**: Find the names of all instructors in the Physics department.
  - $\Pi_{\text{name}}(\sigma_{\text{dept\_name}=\text{"Physics"}}(\text{instructor}))$
- Instead of giving the name of a relation as the argument of the projection operation, we give an expression that evaluates to a relation.

### Cartesian-Product Operation ($\times$)
- Allows us to combine information from any two relations.
- **Notation**: $r \times s$
- **Example**: The Cartesian product of the relations `instructor` and `teaches` is written as: `instructor` $\times$ `teaches`
- We construct a tuple of the result out of each possible pair of tuples: one from the `instructor` relation and one from the `teaches` relation.
- Since the instructor ID appears in both relations, we distinguish between these attributes by attaching the name of the relation from which the attribute originally came.
  - `instructor.ID`
  - `teaches.ID`

![The instructor X teaches table](../images/ch2_slides/slide_017.png)

### Join Operation ($\bowtie$)
- The join operation allows us to combine a select operation and a Cartesian-Product operation into a single operation.
- Consider relations $r(R)$ and $s(S)$. Let $\theta$ be a predicate on attributes in the schema $R \cup S$. The join operation $r \bowtie_\theta s$ is defined as follows:
  - $r \bowtie_\theta s = \sigma_\theta(r \times s)$
- **Example**:
  - $\sigma_{\text{instructor.ID} = \text{teaches.ID}}(\text{instructor} \times \text{teaches})$
  - Can equivalently be written as: $\text{instructor} \bowtie_{\text{instructor.ID} = \text{teaches.ID}} \text{teaches}$

### Union Operation ($\cup$)
- Allows us to combine two relations.
- **Notation**: $r \cup s$
- For $r \cup s$ to be valid:
  1. $r, s$ must have the same arity (same number of attributes).
  2. The attribute domains must be compatible (example: 2nd column of $r$ deals with the same type of values as does the 2nd column of $s$).
- **Example**: Find all courses taught in the Fall 2017 semester, or in the Spring 2018 semester, or in both.
  - $\Pi_{\text{course\_id}}(\sigma_{\text{semester}=\text{"Fall"} \land \text{year}=2017}(\text{section})) \cup \Pi_{\text{course\_id}}(\sigma_{\text{semester}=\text{"Spring"} \land \text{year}=2018}(\text{section}))$

![section table](../images/ch2_slides/slide_021.png)

### Set-Intersection Operation ($\cap$)
- Allows us to find tuples that are in both the input relations.
- **Notation**: $r \cap s$
- **Assume**:
  - $r, s$ have the same arity.
  - Attributes of $r$ and $s$ are compatible.
- **Example**: Find the set of all courses taught in both the Fall 2017 and the Spring 2018 semesters.
  - $\Pi_{\text{course\_id}}(\sigma_{\text{semester}=\text{"Fall"} \land \text{year}=2017}(\text{section})) \cap \Pi_{\text{course\_id}}(\sigma_{\text{semester}=\text{"Spring"} \land \text{year}=2018}(\text{section}))$

### Set Difference Operation ($-$)
- Allows us to find tuples that are in one relation but are not in another.
- **Notation**: $r - s$
- Set differences must be taken between compatible relations.
  - $r$ and $s$ must have the same arity.
  - Attribute domains of $r$ and $s$ must be compatible.
- **Example**: Find all courses taught in the Fall 2017 semester, but not in the Spring 2018 semester.
  - $\Pi_{\text{course\_id}}(\sigma_{\text{semester}=\text{"Fall"} \land \text{year}=2017}(\text{section})) - \Pi_{\text{course\_id}}(\sigma_{\text{semester}=\text{"Spring"} \land \text{year}=2018}(\text{section}))$

### The Assignment Operation ($\leftarrow$)
- It is convenient at times to write a relational-algebra expression by assigning parts of it to temporary relation variables.
- **Notation**: $\leftarrow$ (works like assignment in a programming language).
- **Example**: Find all instructors in the "Physics" and "Music" departments.
  - $\text{Physics} \leftarrow \sigma_{\text{dept\_name}=\text{"Physics"}}(\text{instructor})$
  - $\text{Music} \leftarrow \sigma_{\text{dept\_name}=\text{"Music"}}(\text{instructor})$
  - $\text{Physics} \cup \text{Music}$
- With the assignment operation, a query can be written as a sequential program consisting of a series of assignments followed by an expression whose value is displayed as the result of the query.

### The Rename Operation ($\rho$)
- The results of relational-algebra expressions do not have a name that we can use to refer to them. The rename operator, $\rho$, is provided for that purpose.
- **Expression**: $\rho_x(E)$
  - Returns the result of expression $E$ under the name $x$.
- **Another form**: $\rho_{x(A_1, A_2, \dots, A_n)}(E)$

### Aggregate Functions ($\gamma$)
- These functions operate on the multiset (set with duplicates) of values of a column of a relation, and return a value.
- **Functions**:
  - `avg`: average value
  - `min`: minimum value
  - `max`: maximum value
  - `sum`: sum of values
  - `count`: number of values
- **Examples**:
  - Find the average salary of instructors: $\gamma_{\text{avg}(\text{salary})}(\text{instructor})$
  - Find the total number of courses in 2018: $\gamma_{\text{count}(\text{course\_id})}(\sigma_{\text{year}=2018}(\text{section}))$

![Aggregate Functions Examples](../images/ch2_slides/slide_028.png)

### Aggregate Functions – Group By
- Find the average salary of instructors in each department:
  - ${}_{\text{dept\_name}}\gamma_{\text{avg}(\text{salary})}(\text{instructor})$

### Equivalent Queries
- There is more than one way to write a query in relational algebra.
- **Example 1**: Find information about courses taught by instructors in the Physics department with a salary greater than 90,000.
  - Query 1: $\sigma_{\text{dept\_name}=\text{"Physics"} \land \text{salary} > 90000}(\text{instructor})$
  - Query 2: $\sigma_{\text{dept\_name}=\text{"Physics"}}(\sigma_{\text{salary} > 90000}(\text{instructor}))$
- **Example 2**: Find information about courses taught by instructors in the Physics department.
  - Query 1: $\sigma_{\text{dept\_name}=\text{"Physics"}}(\text{instructor} \bowtie_{\text{instructor.ID} = \text{teaches.ID}} \text{teaches})$
  - Query 2: $(\sigma_{\text{dept\_name}=\text{"Physics"}}(\text{instructor})) \bowtie_{\text{instructor.ID} = \text{teaches.ID}} \text{teaches}$
- The queries in each example are not identical; they are, however, **equivalent** — they give the same result on any database.
