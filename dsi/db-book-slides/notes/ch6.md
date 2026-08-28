# Chapter 6: Database Design Using the E-R Model

**Database System Concepts, 7th Ed.**
© Silberschatz, Korth and Sudarshan

---

## 1. Design Phases

*   **Initial Phase**: Characterize fully the data needs of the prospective database users.
*   **Second Phase**: Choosing a data model.
    *   Applying the concepts of the chosen data model.
    *   Translating these requirements into a conceptual schema of the database.
    *   A fully developed conceptual schema indicates the functional requirements of the enterprise.
    *   Describe the kinds of operations (or transactions) that will be performed on the data.
*   **Final Phase**: Moving from an abstract data model to the implementation of the database.
    *   **Logical Design**: Deciding on the database schema.
        *   Database design requires that we find a "good" collection of relation schemas.
        *   *Business decision*: What attributes should we record in the database?
        *   *Computer Science decision*: What relation schemas should we have and how should the attributes be distributed among the various relation schemas?
    *   **Physical Design**: Deciding on the physical layout of the database.

## 2. Design Alternatives and Approaches

### 2.1 Design Alternatives
In designing a database schema, we must ensure that we avoid two major pitfalls:
*   **Redundancy**: A bad design may result in repeat information. Redundant representation of information may lead to data inconsistency among the various copies of information.
*   **Incompleteness**: A bad design may make certain aspects of the enterprise difficult or impossible to model.

*Note*: Avoiding bad designs is not enough. There may be a large number of good designs from which we must choose.

### 2.2 Design Approaches
*   **Entity Relationship Model** (covered in this chapter): Models an enterprise as a collection of entities and relationships.
    *   *Entity*: A "thing" or "object" in the enterprise that is distinguishable from other objects. Described by a set of attributes.
    *   *Relationship*: An association among several entities.
    *   Represented diagrammatically by an entity-relationship (E-R) diagram.
*   **Normalization Theory** (Chapter 7): Formalize what designs are bad, and test for them.

---

## 3. The Entity-Relationship (ER) Model

### 3.1 Entity Sets

![Representing Entity sets in ER Diagram](../images/ch6_slides/slide_008.png)

*   An **entity** is an object that exists and is distinguishable from other objects.
    *   *Example*: specific person, company, event, plant.
*   An **entity set** is a set of entities of the same type that share the same properties.
    *   *Example*: set of all persons, companies, trees, holidays.
*   An entity is represented by a set of **attributes** (descriptive properties possessed by all members of an entity set).
    *   *Example*: `instructor = (ID, name, salary)`, `course = (course_id, title, credits)`.
*   A subset of the attributes forms a **primary key** of the entity set (uniquely identifying each member of the set).

**Representing Entity Sets in ER Diagram**:
*   **Rectangles** represent entity sets.
*   Attributes are listed inside the entity rectangle.
*   **Underlining** indicates primary key attributes.

### 3.2 Complex Attributes

![Representing Complex Attributes in ER Diagram](../images/ch6_slides/slide_019.png)

*   **Attribute types**:
    *   **Simple** vs. **Composite** attributes: Composite attributes allow us to divide attributes into subparts (e.g., `name` divided into `first_name`, `middle_initial`, `last_name`; `address` divided into `street`, `city`, `state`, `postal_code`).
    *   **Single-valued** vs. **Multivalued** attributes: Example of a multivalued attribute is `phone_numbers`.
    *   **Derived attributes**: Can be computed from other attributes (e.g., `age`, given `date_of_birth`).
*   **Domain**: The set of permitted values for each attribute.

### 3.3 Relationship Sets

![Representing Relationship Sets via ER Diagrams](../images/ch6_slides/slide_011.png)

*   A **relationship** is an association among several entities.
    *   *Example*: `44553 (Peltier)` (student entity) — `advisor` (relationship set) — `22222 (Einstein)` (instructor entity).
*   A **relationship set** is a mathematical relation among $n \ge 2$ entities, each taken from entity sets.
    *   $\{(e_1, e_2, \dots, e_n) \mid e_1 \in E_1, e_2 \in E_2, \dots, e_n \in E_n\}$
*   An attribute can also be associated with a relationship set (e.g., the `advisor` relationship between `instructor` and `student` may have a `date` attribute to track when the student started being associated with the advisor).

**Representing Relationship Sets via ER Diagrams**:
*   **Diamonds** represent relationship sets.
*   Pictorially, we draw a line between related entities.

**Degree of a Relationship Set**:
*   **Binary relationship**: Involves two entity sets (degree two). Most relationship sets in a database system are binary.
*   **Non-binary relationship**: Relationships between more than two entity sets are rare but sometimes convenient.
    *   *Example*: `proj_guide` is a ternary relationship between `instructor`, `student`, and `project`.

**Roles**:
*   Entity sets of a relationship need not be distinct. Each occurrence of an entity set plays a "role" in the relationship (e.g., labels `course_id` and `prereq_id`).

---

## 4. Constraints

### 4.1 Mapping Cardinality Constraints

![Representing Cardinality Constraints in ER Diagram](../images/ch6_slides/slide_023.png)
![One-to-Many Relationship](../images/ch6_slides/slide_024.png)
![Many-to-One Relationships](../images/ch6_slides/slide_025.png)
![Many-to-Many Relationship](../images/ch6_slides/slide_026.png)

Express the number of entities to which another entity can be associated via a relationship set. Most useful in describing binary relationship sets.

Types of mapping cardinality:
*   **One to one (1:1)**: A student is associated with at most one instructor; an instructor is associated with at most one student.
*   **One to many (1:M)**: An instructor is associated with several (including 0) students; a student is associated with at most one instructor.
*   **Many to one (M:1)**: An instructor is associated with at most one student; a student is associated with several (including 0) instructors.
*   **Many to many (M:M)**: An instructor is associated with several students; a student is associated with several instructors.

**Representing Cardinality Constraints in ER Diagram**:
*   **Directed line ($\rightarrow$)**: Signifies "one".
*   **Undirected line (—)**: Signifies "many".

### 4.2 Participation Constraints
*   **Total participation** (indicated by double line): Every entity in the entity set participates in at least one relationship in the relationship set.
    *   *Example*: Every student must have an associated instructor.
*   **Partial participation**: Some entities may not participate in any relationship in the relationship set.
    *   *Example*: Participation of instructor in `advisor` is partial.

### 4.3 Notation for Expressing More Complex Constraints
*   A line may have an associated minimum and maximum cardinality, shown in the form `l..h` (where `l` = min, `h` = max).
*   Minimum value of 1 indicates total participation.
*   Maximum value of `*` indicates no limit.
*   Maximum value of 1 indicates that the entity participates in at most one relationship.
*   *Example*: Instructor can advise 0 or more students (`0..*`). A student must have 1 advisor (`1..1`).

### 4.4 Cardinality Constraints on Ternary Relationship
*   We allow at most one arrow out of a ternary (or greater degree) relationship to indicate a cardinality constraint.
*   If there is more than one arrow, it can create confusion, so it is outlawed to avoid ambiguity.

---

## 5. Primary Keys

Primary keys provide a way to specify how entities and relations are distinguished.

### 5.1 Primary Key for Entity Sets
*   The values of the attribute values of an entity must be such that they can uniquely identify the entity (no two entities are allowed to have exactly the same value for all attributes).
*   A key for an entity is a set of attributes that suffice to distinguish entities from each other.

### 5.2 Primary Key for Relationship Sets

![Choice of Primary key for Binary Relationship](../images/ch6_slides/slide_033.png)

*   To distinguish among the various relationships, we use the individual primary keys of the entities in the relationship set.
*   Let $R$ be a relationship set involving entity sets $E_1, E_2, \dots, E_n$. The primary key for $R$ consists of the union of the primary keys of these entity sets.
*   If the relationship set has attributes $a_1, a_2, \dots, a_m$, the primary key of $R$ also includes these attributes.

**Choice of Primary Key for Binary Relationships**:
*   **Many-to-Many**: The union of the primary keys is a minimal superkey and is chosen as the primary key.
*   **One-to-Many / Many-to-One**: The primary key of the "Many" side is a minimal superkey and is used as the primary key.
*   **One-to-One**: The primary key of either one of the participating entity sets forms a minimal superkey and can be chosen as the primary key.

---

## 6. Weak Entity Sets

![E-R Diagram for a University Enterprise](../images/ch6_slides/slide_039.png)


*   A **weak entity set** is one whose existence is dependent on another entity, called its **identifying entity**.
    *   It does not have enough attributes to identify a particular entity uniquely on its own.
*   Instead of associating a primary key with a weak entity, we use the identifying entity, along with extra attributes called a **discriminator**, to uniquely identify a weak entity.
*   An entity set that is not a weak entity set is termed a **strong entity set**.
*   The relationship associating the weak entity set with the identifying entity set is called the **identifying relationship**.

**Expressing Weak Entity Sets in ER Diagrams**:
*   Depicted via a **double rectangle**.
*   We underline the discriminator of a weak entity set with a **dashed line**.
*   The identifying relationship set is depicted by a **double diamond**.
    *   *Example*: Primary key for `section` is `(course_id, sec_id, semester, year)` where `course_id` comes from the identifying strong entity set `course`.

---

## 7. Reduction to Relation Schemas

![Reduction to Relation Schemas](../images/ch6_slides/slide_040.png)
![Reduction to Relation Schemas](../images/ch6_slides/slide_041.png)


Entity sets and relationship sets can be expressed uniformly as relation schemas that represent the contents of the database.

*   **Representing Entity Sets**:
    *   A strong entity set reduces to a schema with the same attributes: `student(ID, name, tot_cred)`
    *   A weak entity set becomes a table that includes a column for the primary key of the identifying strong entity set: `section(course_id, sec_id, sem, year)`
*   **Representing Complex Attributes**:
    *   **Composite attributes** are flattened out by creating a separate attribute for each component attribute (e.g., `name` becomes `first_name`, `middle_initial`, `last_name`).
    *   **Multivalued attributes** ($M$) of an entity $E$ are represented by a separate schema $E_M$. It has attributes corresponding to the primary key of $E$ and an attribute for $M$. Each value maps to a separate tuple.
*   **Representing Relationship Sets**:
    *   A many-to-many relationship set is represented as a schema with attributes for the primary keys of the two participating entity sets, and any descriptive attributes.
        *   *Example*: `advisor = (s_id, i_id)`
*   **Redundancy of Schemas**:
    *   Many-to-one and one-to-many relationship sets that are total on the many-side can be represented by adding an extra attribute to the "many" side, containing the primary key of the "one" side.
    *   For one-to-one relationship sets, either side can act as the "many" side. (If participation is partial, this could result in null values).
    *   The schema corresponding to a relationship set linking a weak entity set to its identifying strong entity set is redundant (the weak entity schema already contains those attributes).

---

## 8. Extended E-R Features

### 8.1 Specialization and Generalization

![Specialization Example](../images/ch6_slides/slide_051.png)

*   **Specialization**: A top-down design process. We designate sub-groupings within an entity set that are distinctive from other entities in the set (lower-level entity sets).
    *   Depicted by a triangle component labeled **ISA** (e.g., instructor "is a" person).
    *   **Attribute inheritance**: A lower-level entity set inherits all the attributes and relationship participation of the higher-level entity set.
*   **Generalization**: A bottom-up design process. Combine a number of entity sets that share the same features into a higher-level entity set.
    *   Specialization and generalization are simple inversions of each other and are used interchangeably.

**Constraints on Specialization/Generalization**:
*   **Overlapping** (e.g., employee and student) vs. **Disjoint** (e.g., instructor and secretary).
*   **Completeness constraint**:
    *   **Total**: An entity must belong to one of the lower-level entity sets.
    *   **Partial** (default): An entity need not belong to one of the lower-level entity sets.

**Representing Specialization via Schemas**:
*   *Method 1*: Form a schema for the higher-level entity and a schema for each lower-level entity set (includes primary key of higher-level entity + local attributes).
    *   *Drawback*: Requires accessing two relations to get all information.
*   *Method 2*: Form a schema for each entity set with all local and inherited attributes.
    *   *Drawback*: Inherited attributes may be stored redundantly for overlapping sets.

### 8.2 Aggregation

![Reduction to Relational Schemas](../images/ch6_slides/slide_060.png)

*   Eliminates redundancy when relationships overlap (e.g., relationships between relationships).
*   Treats a relationship as an abstract entity (abstraction of relationship into a new entity).
*   **Reduction to Relational Schemas**: Create a schema containing the primary key of the aggregated relationship, the primary key of the associated entity set, and any descriptive attributes.

---

## 9. Design Issues

### 9.1 Common Mistakes in E-R Diagrams

![Common Mistakes in E-R Diagrams](../images/ch6_slides/slide_062.png)
![Common Mistakes in E-R Diagrams (Cont.)](../images/ch6_slides/slide_063.png)

*   **Entities vs. Attributes**: E.g., Using `phone` as an entity allows extra information about phone numbers (and multiple numbers), whereas using it as an attribute does not.
*   **Entities vs. Relationship Sets**: Guideline is to designate a relationship set to describe an action that occurs between entities.
*   **Placement of relationship attributes**: Ensure attributes belong to the right relationship (e.g., date of advising belongs to `advisor`, not `student`).

### 9.2 Binary vs. Non-Binary Relationships
*   Any non-binary relationship can be represented using binary relationships by creating an artificial entity set (replace $R$ between $A, B, C$ with entity set $E$ and three binary relationships $R_A, R_B, R_C$).
*   Some non-binary relationships are better represented using binary relationships (e.g., ternary relationship `parents` is better as `father` and `mother` to allow partial information).
*   However, a non-binary relationship set shows more clearly that several entities participate in a single relationship (e.g., `proj_guide`).

### 9.3 E-R Design Decisions
*   The use of an attribute or entity set to represent an object.
*   Whether a real-world concept is best expressed by an entity set or a relationship set.
*   The use of a ternary relationship versus a pair of binary relationships.
*   The use of a strong or weak entity set.
*   The use of specialization/generalization (contributes to modularity).
*   The use of aggregation (can treat the aggregate entity set as a single unit).

---

## 10. Alternative Notations and UML

![Summary of Symbols Used in E-R Notation](../images/ch6_slides/slide_070.png)
![Symbols Used in E-R Notation (Cont.)](../images/ch6_slides/slide_071.png)
![Alternative ER Notations](../images/ch6_slides/slide_073.png)
![ER vs. UML Class Diagrams](../images/ch6_slides/slide_075.png)


*   **Alternative ER Notations**: Chen, IDE1FX (Crows feet notation).
*   **UML (Unified Modeling Language)**:
    *   UML Class Diagrams correspond to E-R Diagrams, but with several differences (e.g., reversal of position in cardinality constraint depiction).
    *   Binary relationship sets are represented by drawing a line connecting the entity sets (relationship set name written adjacent to the line).
    *   Role played by an entity set may be specified by writing the role name on the line.

---

## 11. Other Aspects of Database Design
*   Functional Requirements
*   Data Flow, Workflow
*   Schema Evolution
