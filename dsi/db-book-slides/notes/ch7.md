# Chapter 7: Normalization

## Features of Good Relational Design

![Features of Good Relational Designs](../images/ch7_slides/slide_003.png)

- **Problem with Combined Schemas**: Combining schemas (e.g., `instructor` and `department` into `in_dep` via a natural join) can lead to:
  - Repetition of information.
  - The need to use null values (e.g., if we add a new department with no instructors).

## Decomposition

![A Lossy Decomposition](../images/ch7_slides/slide_005.png)

- **Purpose**: To avoid repetition-of-information problems, schemas can be decomposed into smaller schemas (e.g., decomposing `in_dep` into `instructor` and `department`).
- **Lossy vs. Lossless Decomposition**: Not all decompositions are good. 
  - A decomposition is **lossy** if we lose information and cannot reconstruct the original relation (e.g., decomposing `employee(ID, name, street, city, salary)` into `employee1(ID, name)` and `employee2(name, street, city, salary)` fails when two employees have the same name).
  - A decomposition is **lossless** if there is no loss of information when replacing relation $R$ with the two relation schemas $R_1 \cup R_2$.
    - Formally: $\Pi_{R_1}(r) \bowtie \Pi_{R_2}(r) = r$.
    - Conversely, a decomposition is lossy if $r \subset \Pi_{R_1}(r) \bowtie \Pi_{R_2}(r)$.
  - **Example of Lossless Decomposition**: $R = (A, B, C)$ decomposed into $R_1 = (A, B)$ and $R_2 = (B, C)$.

## Normalization Theory
- **Goal**: Decide whether a particular relation $R$ is in "good" form. If not, decompose it into a set of relations $\{R_1, R_2, ..., R_n\}$ such that:
  - Each relation is in good form.
  - The decomposition is a lossless decomposition.
- The theory is based on:
  - Functional dependencies.
  - Multivalued dependencies.

## Functional Dependencies (FDs)
- **Concept**: A generalization of the notion of a key. These are constraints on the set of legal relations that require the value for a certain set of attributes to uniquely determine the value for another set of attributes.
- **Definition**: Let $R$ be a relation schema, $\alpha \subseteq R$ and $\beta \subseteq R$. The functional dependency $\alpha \rightarrow \beta$ holds on $R$ if and only if for any legal relations $r(R)$, whenever any two tuples $t_1$ and $t_2$ of $r$ agree on the attributes $\alpha$, they also agree on the attributes $\beta$. That is: $t_1[\alpha] = t_2[\alpha] \Rightarrow t_1[\beta] = t_2[\beta]$.
- **Uses**: 
  - To test relations to see if they are legal under a given set of functional dependencies.
  - To specify constraints on the set of legal relations.
- **Trivial Functional Dependencies**: A functional dependency is trivial if it is satisfied by all instances of a relation (e.g., $ID, name \rightarrow ID$, or $name \rightarrow name$). In general, $\alpha \rightarrow \beta$ is trivial if $\beta \subseteq \alpha$.

### Keys and Functional Dependencies
- $K$ is a **superkey** for relation schema $R$ if and only if $K \rightarrow R$.
- $K$ is a **candidate key** for $R$ if and only if:
  - $K \rightarrow R$, and
  - for no $\alpha \subset K$, $\alpha \rightarrow R$.

### Closure of a Set of Functional Dependencies
- Given a set $F$ of functional dependencies, there are certain other functional dependencies that are logically implied by $F$.
- The set of all functional dependencies logically implied by $F$ is the **closure** of $F$, denoted by $F^+$.
- **Armstrong's Axioms** (used to compute $F^+$):
  - **Reflexive rule**: if $\beta \subseteq \alpha$, then $\alpha \rightarrow \beta$.
  - **Augmentation rule**: if $\alpha \rightarrow \beta$, then $\gamma \alpha \rightarrow \gamma \beta$.
  - **Transitivity rule**: if $\alpha \rightarrow \beta$ and $\beta \rightarrow \gamma$, then $\alpha \rightarrow \gamma$.
- These rules are **sound** (generate only FDs that actually hold) and **complete** (generate all FDs that hold).
- **Additional Rules**:
  - **Union rule**: If $\alpha \rightarrow \beta$ and $\alpha \rightarrow \gamma$ hold, then $\alpha \rightarrow \beta\gamma$ holds.
  - **Decomposition rule**: If $\alpha \rightarrow \beta\gamma$ holds, then $\alpha \rightarrow \beta$ and $\alpha \rightarrow \gamma$ hold.
  - **Pseudotransitivity rule**: If $\alpha \rightarrow \beta$ and $\gamma\beta \rightarrow \delta$ hold, then $\alpha\gamma \rightarrow \delta$ holds.

### Closure of Attribute Sets
- Given a set of attributes $\alpha$, the closure of $\alpha$ under $F$ (denoted by $\alpha^+$) is the set of attributes that are functionally determined by $\alpha$ under $F$.
- **Uses of Attribute Closure**:
  - **Testing for superkey**: To test if $\alpha$ is a superkey, compute $\alpha^+$ and check if it contains all attributes of $R$.
  - **Testing functional dependencies**: To check if $\alpha \rightarrow \beta$ holds, check if $\beta \subseteq \alpha^+$.
  - **Computing closure of $F$**.

### Lossless Decomposition using FDs

![Example of Lossless Decomposition](../images/ch7_slides/slide_007.png)

- A decomposition of $R$ into $R_1$ and $R_2$ is a lossless decomposition if at least one of the following dependencies is in $F^+$:
  - $R_1 \cap R_2 \rightarrow R_1$
  - $R_1 \cap R_2 \rightarrow R_2$
- This is a sufficient condition for lossless join decomposition.

### Dependency Preservation
- Testing functional dependency constraints each time the database is updated can be costly. It is useful to design the database in a way that constraints can be tested efficiently without having to perform a Cartesian product (join).
- If a decomposition makes it computationally hard to enforce functional dependencies, it is said to be **NOT dependency preserving**.
- **Testing for Dependency Preservation**:
  - Let $F_i$ be the restriction of $F$ to $R_i$.
  - A decomposition is dependency preserving if $(F_1 \cup F_2 \cup ... \cup F_n)^+ = F^+$.

### Extraneous Attributes and Canonical Cover

![Examples of Extraneous Attributes](../images/ch7_slides/slide_047.png)

- **Extraneous Attribute**: An attribute of a functional dependency in $F$ is extraneous if we can remove it without changing $F^+$.
  - Removing an attribute from the left side could make it a stronger constraint.
  - Removing an attribute from the right side could make it a weaker constraint.
- **Canonical Cover**: A canonical cover for $F$ is a simplified set of dependencies $F_c$ such that:
  - $F$ logically implies all dependencies in $F_c$, and vice versa.
  - No functional dependency in $F_c$ contains an extraneous attribute.
  - Each left side of a functional dependency in $F_c$ is unique.

## Normal Forms

### First Normal Form (1NF)
- A relational schema is in 1NF if the domains of all attributes are **atomic** (considered to be indivisible units).
- Non-atomic values (e.g., sets, composite attributes) complicate storage and encourage redundant storage of data. We generally assume all relations are in 1NF.

### Boyce-Codd Normal Form (BCNF)

![Decomposing a Schema into BCNF](../images/ch7_slides/slide_022.png)
![Example](../images/ch7_slides/slide_023.png)
![BCNF Decomposition (Cont.)](../images/ch7_slides/slide_059.png)

- A relation schema $R$ is in BCNF with respect to a set $F$ of functional dependencies if for all functional dependencies in $F^+$ of the form $\alpha \rightarrow \beta$ (where $\alpha \subseteq R$ and $\beta \subseteq R$), at least one of the following holds:
  - $\alpha \rightarrow \beta$ is trivial (i.e., $\beta \subseteq \alpha$).
  - $\alpha$ is a superkey for $R$.
- **Decomposing a Schema into BCNF**:
  - If $\alpha \rightarrow \beta$ causes a violation of BCNF, decompose $R$ into:
    - $(\alpha \cup \beta)$
    - $(R - (\beta - \alpha))$
- **Dependency Preservation Issue**: It is not always possible to achieve both BCNF and dependency preservation.
- **Testing for BCNF**: Compute $\alpha^+$ and verify it includes all attributes of $R$ (i.e., is a superkey). To test a decomposition for BCNF, we can use $F$ with a special test rather than computing all of $F^+$.

### Third Normal Form (3NF)

![3NF Example](../images/ch7_slides/slide_061.png)

- A relation schema $R$ is in 3NF if for all $\alpha \rightarrow \beta$ in $F^+$, at least one of the following holds:
  - $\alpha \rightarrow \beta$ is trivial (i.e., $\beta \subseteq \alpha$).
  - $\alpha$ is a superkey for $R$.
  - Each attribute $A$ in $\beta - \alpha$ is contained in a candidate key for $R$.
- **Advantages over BCNF**: It is always possible to obtain a 3NF design without sacrificing losslessness or dependency preservation.
- **Disadvantages over BCNF**: May require null values to represent relationships, and there can be repetition of information.
- **3NF Decomposition Algorithm**: Uses the canonical cover $F_c$ to build relations for each FD, ensuring candidate keys are included. It guarantees lossless-join and dependency preservation.

### Multivalued Dependencies (MVDs)

![MVD -- Tabular representation](../images/ch7_slides/slide_071.png)
![Example](../images/ch7_slides/slide_073.png)

- MVDs are needed for schemas where a single attribute is associated with a set of independent values (e.g., an instructor with multiple children and multiple phone numbers).
- **Definition**: $\alpha \rightarrow\rightarrow \beta$ holds on $R$ if for all pairs of tuples $t_1, t_2$ that agree on $\alpha$, there exist tuples $t_3, t_4$ that also agree on $\alpha$, and take their $\beta$ values from $t_1, t_2$ and their $R-\beta$ values from $t_2, t_1$.
- Every functional dependency is also a multivalued dependency (if $\alpha \rightarrow \beta$, then $\alpha \rightarrow\rightarrow \beta$).

### Fourth Normal Form (4NF)
- A relation schema $R$ is in 4NF with respect to a set $D$ of functional and multivalued dependencies if for all MVDs in $D^+$ of the form $\alpha \rightarrow\rightarrow \beta$ (where $\alpha \subseteq R$ and $\beta \subseteq R$), at least one holds:
  - $\alpha \rightarrow\rightarrow \beta$ is trivial (i.e., $\beta \subseteq \alpha$ or $\alpha \cup \beta = R$).
  - $\alpha$ is a superkey for schema $R$.
- If a relation is in 4NF, it is also in BCNF.

### Further Normal Forms
- **Project-Join Normal Form (PJNF / 5NF)** and **Domain-Key Normal Form (DKNF)** generalize dependencies further but are rarely used because they are hard to reason with and lack complete inference rules.

## Overall Database Design Process

![Modeling Temporal Data (Cont.)](../images/ch7_slides/slide_086.png)

- Schema $R$ could be generated when converting an E-R diagram or from a universal relation.
- **ER Model and Normalization**: A carefully designed E-R diagram identifying all entities correctly typically doesn't need further normalization, but imperfect designs might.
- **Denormalization for Performance**: Sometimes we intentionally use non-normalized schemas (e.g., pre-joining tables) for faster lookups, at the cost of extra space and extra execution time for updates. An alternative is using materialized views.
- **Other Design Issues**: Schemas like crosstabs (e.g., `earnings_2004`, `earnings_2005` as columns) might be in BCNF but make querying difficult and require new attributes periodically.
- **Modeling Temporal Data**: Temporal data have an associated time interval during which the data are valid.
  - Adding a temporal component results in typical functional dependencies (e.g., $ID \rightarrow street, city$) no longer holding because the address varies over time.
  - A temporal functional dependency $X \rightarrow Y$ holds if the FD holds on all snapshots for all legal instances.
