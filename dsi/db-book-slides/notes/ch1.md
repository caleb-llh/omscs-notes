# Chapter 1: Introduction to Database Systems

## 1. Database Applications Examples
Database applications are ubiquitous across various domains:
- **Enterprise Information:**
  - *Sales:* Customers, products, purchases.
  - *Accounting:* Payments, receipts, assets.
  - *Human Resources:* Employee information, salaries, payroll taxes.
- **Manufacturing:** Management of production, inventory, orders, supply chain.
- **Banking and Finance:**
  - Customer information, accounts, loans, and banking transactions.
  - Credit card transactions.
  - Sales and purchases of financial instruments (e.g., stocks, bonds) and storing real-time market data.
- **Universities:** Registration, grades.
- **Airlines:** Reservations, schedules.
- **Telecommunication:** Records of calls, texts, and data usage, generating monthly bills, maintaining balances on prepaid calling cards.
- **Web-based Services:**
  - *Online retailers:* Order tracking, customized recommendations.
  - *Online advertisements.*
- **Document Databases**
- **Navigation Systems:** Maintaining locations of various places of interest along with the exact routes of roads, train systems, buses, etc.

## 2. Purpose of Database Systems
In the early days, database applications were built directly on top of file systems, which led to several issues that database systems solve:
- **Data Redundancy and Inconsistency:** Data is stored in multiple file formats, resulting in the duplication of information in different files.
- **Difficulty in Accessing Data:** Needed to write a new program to carry out each new task.
- **Data Isolation:** Multiple files and formats made it hard to link data.
- **Integrity Problems:**
  - Integrity constraints (e.g., account balance > 0) become "buried" in program code rather than being stated explicitly.
  - Hard to add new constraints or change existing ones.
- **Atomicity of Updates:** Failures may leave the database in an inconsistent state with partial updates carried out. For example, a transfer of funds from one account to another should either complete fully or not happen at all.
- **Concurrent Access by Multiple Users:** Needed for performance, but uncontrolled concurrent accesses can lead to inconsistencies (e.g., two people reading a balance and updating it at the same time).
- **Security Problems:** Hard to provide user access to some, but not all, data.

*Database systems offer solutions to all the above problems.*

## 3. Data Models
A data model is a collection of tools for describing data, data relationships, data semantics, and data constraints. 
Types of data models include:
- **Relational Model**
- **Entity-Relationship Data Model:** Mainly used for database design.
- **Object-based Data Models:** Object-oriented and Object-relational.
- **Semi-structured Data Model:** XML.
- **Older Models:** Network model, Hierarchical model.

### The Relational Model
- All data is stored in various tables.
- Composed of **Rows** and **Columns**.
- *Note: Ted Codd invented the relational model and won the Turing Award in 1981.*

![Relational Model](../images/ch1_slides/slide_007.png)
![A Sample Relational Database](../images/ch1_slides/slide_008.png)

## 4. View of Data

![View of Data](../images/ch1_slides/slide_009.png)

### Instances and Schemas
Similar to types and variables in programming languages.
- **Logical Schema:** The overall logical structure of the database. 
  - *Example:* The database consists of information about a set of customers and accounts in a bank and the relationship between them.
  - Analogous to type information of a variable in a program.
- **Physical Schema:** The overall physical structure of the database.
- **Instance:** The actual content of the database at a particular point in time.
  - Analogous to the value of a variable.

### Physical Data Independence
- The ability to modify the physical schema without changing the logical schema.
- Applications depend on the logical schema.
- Interfaces between the various levels and components should be well defined so that changes in some parts do not seriously influence others.

## 5. Database Languages
### Data Definition Language (DDL)
- Specification notation for defining the database schema.
- Example:
  ```sql
  create table instructor (
      ID          char(5),
      name        varchar(20),
      dept_name   varchar(20),
      salary      numeric(8,2)
  )
  ```
- The DDL compiler generates a set of table templates stored in a data dictionary.
- **Data Dictionary:** Contains metadata (data about data), including:
  - Database schema
  - Integrity constraints (e.g., Primary key)
  - Authorization (Who can access what)

### Data Manipulation Language (DML)
- Language for accessing and updating the data organized by the appropriate data model. Also known as a query language.
- Two classes of languages:
  - **Pure DMLs:** Used for proving properties about computational power and for optimization.
    - Relational Algebra
    - Tuple relational calculus
    - Domain relational calculus
  - **Commercial DMLs:** Used in commercial systems. SQL is the most widely used.
- Types of DMLs:
  - **Procedural DML:** Require a user to specify *what* data are needed and *how* to get those data.
  - **Declarative (Non-procedural) DML:** Require a user to specify *what* data are needed without specifying how to get them. Easier to learn and use.
- The portion of a DML that involves information retrieval is called a **query language**.

## 6. SQL Query Language & Application Programs
- SQL query language is nonprocedural. A query takes as input several tables and always returns a single table.
  ```sql
  select name
  from instructor
  where dept_name = 'Comp. Sci.'
  ```
- SQL is NOT a Turing machine equivalent language. It does not support actions such as user input, output to displays, or network communication.
- To compute complex functions, SQL is usually embedded in a higher-level host language (C/C++, Java, Python).
- **Application Programs:** Programs used to interact with the database. They access databases through:
  - Language extensions to allow embedded SQL.
  - Application program interfaces (e.g., ODBC/JDBC) which allow SQL queries to be sent to a database.

## 7. Database Design
The process of designing the general structure of the database:
- **Logical Design:** Deciding on the database schema. Finding a "good" collection of relation schemas.
  - *Business decision:* What attributes should we record in the database?
  - *Computer Science decision:* What relation schemas should we have and how should the attributes be distributed among them?
- **Physical Design:** Deciding on the physical layout of the database.

## 8. Database Engine
A database system is partitioned into modules that deal with each responsibility of the overall system. Functional components include:
- The Storage Manager
- The Query Processor Component
- The Transaction Management Component

### Storage Manager
- Provides the interface between the low-level data stored in the database and the application programs and queries submitted to the system.
- Responsible for:
  - Interaction with the OS file manager.
  - Efficient storing, retrieving, and updating of data.
- Components include:
  - Authorization and integrity manager
  - Transaction manager
  - File manager
  - Buffer manager
- Implements several physical data structures:
  - **Data files:** Store the database itself.
  - **Data dictionary:** Stores metadata about the database structure/schema.
  - **Indices:** Provide fast access to data items that hold a particular value.

### Query Processor
- Components include:
  - **DDL interpreter:** Interprets DDL statements and records definitions in the data dictionary.
  - **DML compiler:** Translates DML statements into an evaluation plan consisting of low-level instructions. It also performs **query optimization** (picking the lowest cost evaluation plan).
  - **Query evaluation engine:** Executes low-level instructions generated by the DML compiler.
- **Query Processing Steps:**
  1. Parsing and translation
  2. Optimization
  3. Evaluation

![Query Processing](../images/ch1_slides/slide_022.png)

### Transaction Management
- **Transaction:** A collection of operations that performs a single logical function in a database application.
- **Transaction-management component:** Ensures the database remains in a consistent state despite system failures (e.g., power failures, OS crashes) and transaction failures.
- **Concurrency-control manager:** Controls the interaction among concurrent transactions to ensure database consistency.

## 9. Database Architecture & Applications
### Database Architecture
- **Centralized databases:** One to a few cores, shared memory.
- **Client-server:** One server machine executes work on behalf of multiple client machines.
- **Parallel databases:** Many cores, shared memory, shared disk, or shared nothing.
- **Distributed databases:** Geographical distribution, schema/data heterogeneity.

### Application Architecture
Applications are usually partitioned into two or three parts:
- **Two-tier architecture:** The application resides at the client machine, where it invokes database system functionality at the server machine.
- **Three-tier architecture:** The client machine acts as a front end and does not contain direct database calls. It communicates with an application server, which in turn communicates with a database system to access data.

![Two-tier and three-tier architectures](../images/ch1_slides/slide_026.png)

## 10. Database Users & Administrators
### Database Users
Four different types of database-system users:
1. **Naive users:** Unsophisticated users who interact with the system by invoking previously written application programs.
2. **Application programmers:** Computer professionals who write application programs.
3. **Sophisticated users:** Interact with the system without writing programs (using query languages or data analysis software).
4. **Specialized users:** Write specialized database applications that don't fit into the traditional framework (e.g., CAD, graphic data, audio, video).

### Database Administrator (DBA)
A person who has central control over the system. Functions include:
- Schema definition.
- Storage structure and access-method definition.
- Schema and physical-organization modification.
- Granting of authorization for data access.
- Routine maintenance (periodically backing up, ensuring enough free disk space, upgrading disk space).
- Monitoring jobs to ensure performance is not degraded by expensive tasks.

## 11. History of Database Systems
- **1950s and early 1960s:** Data processing using magnetic tapes (sequential access only) and punched cards.
- **Late 1960s and 1970s:** Hard disks allowed direct access. Network and hierarchical models in widespread use. Ted Codd defined the relational model (IBM System R, UC Berkeley Ingres, Oracle).
- **1980s:** Relational prototypes evolved into commercial systems. SQL became an industrial standard. Parallel, distributed, and object-oriented database systems emerged.
- **1990s:** Large decision support and data-mining applications. Multi-terabyte data warehouses. Emergence of Web commerce.
- **2000s:** Big data storage systems (Google BigTable, Yahoo PNuts, Amazon, "NoSQL"). Big data analysis (MapReduce).
- **2010s:** SQL reloaded (SQL front end to MapReduce systems, massively parallel databases, multi-core main-memory databases).
