# Chapter 5: Advanced SQL

## Outline
* Accessing SQL From a Programming Language
* Functions and Procedures
* Triggers
* Recursive Queries
* Advanced Aggregation Features

---

## 1. Accessing SQL from a Programming Language
A database programmer must have access to a general-purpose programming language for at least two reasons:
1. **Expressive Power:** Not all queries can be expressed in SQL, since SQL does not provide the full expressive power of a general-purpose language.
2. **Non-declarative Actions:** Actions such as printing a report, interacting with a user, or sending the results of a query to a graphical user interface cannot be done from within SQL.

There are two approaches to accessing SQL from a general-purpose programming language:
1. **Dynamic SQL / APIs:** A general-purpose program can connect to and communicate with a database server using a collection of functions (e.g., JDBC, ODBC).
2. **Embedded SQL:** Provides a means by which a program can interact with a database server. The SQL statements are translated at compile time into function calls. At runtime, these function calls connect to the database using an API that provides dynamic SQL facilities.

### 1.1 JDBC
JDBC is a Java API for communicating with database systems supporting SQL. It supports a variety of features for querying and updating data, and for retrieving query results. It also supports metadata retrieval, such as querying about relations present in the database and the names and types of relation attributes.

**Model for communicating with the database:**
1. Open a connection
2. Create a "statement" object
3. Execute queries using the statement object to send queries and fetch results
4. Exception mechanism to handle errors

#### Example: JDBC Code
```java
public static void JDBCexample(String dbid, String userid, String passwd) {
    try (Connection conn = DriverManager.getConnection(
            "jdbc:oracle:thin:@db.yale.edu:2000:univdb", userid, passwd);
        ) 
        Statement stmt = conn.createStatement();
    {
        // … Do Actual Work ….
    } catch (SQLException sqle) {
        System.out.println("SQLException : " + sqle);
    }
}
```
*Note:* The above syntax works with Java 7 and JDBC 4 onwards. Resources opened in the `try (...)` syntax ("try with resources") are automatically closed at the end of the try block. Older versions required `Class.forName(...)` and explicit `close()` calls.

#### Executing Updates and Queries
**Update to database:**
```java
try {
    stmt.executeUpdate("insert into instructor values('77987', 'Kim', 'Physics', 98000)");
} catch (SQLException sqle) {
    System.out.println("Could not insert tuple. " + sqle);
}
```

**Execute query and fetch results:**
```java
ResultSet rset = stmt.executeQuery(
    "select dept_name, avg(salary) from instructor group by dept_name");
while (rset.next()) {
    System.out.println(rset.getString("dept_name") + " " + rset.getFloat(2));
}
```
* Getting result fields: `rs.getString("dept_name")` and `rs.getString(1)` are equivalent if `dept_name` is the first argument of the select result.
* Dealing with Null values: `int a = rs.getInt("a"); if (rs.wasNull()) System.out.println("Got null value");`

#### Prepared Statements
```java
PreparedStatement pStmt = conn.prepareStatement("insert into instructor values(?,?,?,?)");
pStmt.setString(1, "88877");
pStmt.setString(2, "Perry");
pStmt.setString(3, "Finance");
pStmt.setInt(4, 125000);
pStmt.executeUpdate();
```
* **WARNING:** Always use prepared statements when taking input from the user and adding it to a query. NEVER create a query by concatenating strings. This prevents **SQL Injection** attacks (e.g., where a user inputs `"X' or 'Y' = 'Y"` or `"; update instructor set salary = salary + 10000; --"`).

#### Metadata Features

![Metadata Features](../images/ch5_slides/slide_014.png)

**ResultSet metadata:**
```java
ResultSetMetaData rsmd = rs.getMetaData();
for(int i = 1; i <= rsmd.getColumnCount(); i++) {
    System.out.println(rsmd.getColumnName(i));
    System.out.println(rsmd.getColumnTypeName(i));
}
```

**Database metadata:**
```java
DatabaseMetaData dbmd = conn.getMetaData();
// Get columns
ResultSet rs = dbmd.getColumns(null, "univdb", "department", "%");
// Get tables
ResultSet rsTables = dbmd.getTables("", "", "%", new String[] {"TABLES"});
// Get primary keys
ResultSet rsKeys = dbmd.getPrimaryKeys("", "", tableName);
```

#### Transaction Control in JDBC
* By default, each SQL statement is treated as a separate transaction that is committed automatically (bad idea for transactions with multiple updates).
* Turn off automatic commit: `conn.setAutoCommit(false);`
* Explicitly commit or rollback: `conn.commit();` or `conn.rollback();`

#### Other JDBC Features
* **Calling functions and procedures:** `CallableStatement cStmt1 = conn.prepareCall("{? = call some_function(?)}");`
* **Handling large object types:** `getBlob()` and `getClob()` return objects of type `Blob` and `Clob`. Get data via `getBytes()` or associate an open stream.

### 1.2 SQLJ
JDBC is overly dynamic, meaning errors cannot be caught by the compiler. SQLJ provides embedded SQL in Java.
```java
#sql iterator deptInfoIter (String dept_name, int avgSal);
deptInfoIter iter = null;
#sql iter = { select dept_name, avg(salary) from instructor group by dept_name };
while (iter.next()) {
    String deptName = iter.dept_name();
    int avgSal = iter.avgSal();
    System.out.println(deptName + " " + avgSal);
}
iter.close();
```

### 1.3 ODBC
Open DataBase Connectivity (ODBC) is a standard API for application programs (such as GUIs, spreadsheets, etc.) to communicate with a database server. It provides functions to open a connection, send queries/updates, and get back results.

### 1.4 Embedded SQL
The SQL standard defines embeddings of SQL in a variety of programming languages (C, C++, Java, Fortran, PL/1). The language into which SQL queries are embedded is referred to as a **host language**, and the SQL structures permitted in the host language comprise **embedded SQL**.

**Syntax:** `EXEC SQL <embedded SQL statement >;` (Note: Java embedding uses `# SQL { .... };`)

**Connection and Variables:**
* Connect: `EXEC-SQL connect to server user user-name using password;`
* Host language variables can be used within embedded SQL preceded by a colon (e.g., `:credit_amount`). They must be declared within a `DECLARE` section:
  ```c
  EXEC-SQL BEGIN DECLARE SECTION;
  int credit_amount;
  EXEC-SQL END DECLARE SECTION;
  ```

**Cursors:**
Used to execute queries and retrieve results tuple by tuple.
```c
EXEC SQL declare c cursor for 
    select ID, name from student where tot_cred > :credit_amount 
END_EXEC
```
* `EXEC SQL open c;` executes the query and saves results in a temporary relation.
* `EXEC SQL fetch c into :si, :sn END_EXEC` retrieves the values of one tuple into host variables. Repeated calls get successive tuples.
* `EXEC SQL close c;` deletes the temporary relation.
* A variable called `SQLSTATE` in the SQL communication area (SQLCA) gets set to `'02000'` to indicate no more data is available.

**Updates Through Embedded SQL:**
Can update tuples fetched by cursor by declaring that the cursor is `for update`:
```c
EXEC SQL declare c cursor for 
    select * from instructor where dept_name = 'Music' for update
// After fetching a tuple:
update instructor set salary = salary + 1000 where current of c
```

---

## 2. Functions and Procedures
Functions and procedures allow "business logic" to be stored in the database and executed from SQL statements. These can be defined either by the procedural component of SQL or by an external programming language such as Java, C, or C++.

### 2.1 Declaring SQL Functions
```sql
create function dept_count (dept_name varchar(20))
    returns integer
    begin
        declare d_count integer;
        select count(*) into d_count
        from instructor
        where instructor.dept_name = dept_name
        return d_count;
    end
```
Usage in a query:
```sql
select dept_name, budget
from department
where dept_count(dept_name) > 12
```

### 2.2 Table Functions
The SQL standard supports functions that can return tables as results.
```sql
create function instructor_of (dept_name char(20))
    returns table (
        ID varchar(5),
        name varchar(20),
        dept_name varchar(20),
        salary numeric(8,2))
    return table
        (select ID, name, dept_name, salary
         from instructor
         where instructor.dept_name = instructor_of.dept_name)
```
Usage: `select * from table (instructor_of ('Music'))`

### 2.3 Language Constructs

![Language Constructs](../images/ch5_slides/slide_034.png)

**For loop:** Permits iteration over all results of a query.
```sql
declare n integer default 0;
for r as
    select budget from department where dept_name = 'Music'
do
    set n = n + r.budget
end for
```

### 2.4 External Language Routines
SQL allows us to define functions in a programming language such as Java, C#, C, or C++. This can be more efficient than functions defined in SQL, and allows computations that cannot be carried out in SQL.
```sql
create procedure dept_count_proc(in dept_name varchar(20), out count integer)
    language C
    external name '/usr/avi/bin/dept_count_proc'
```

**Security with External Language Routines:**
* Use sandbox techniques (e.g., use a safe language like Java, which cannot access/damage other parts of the database code).
* Run external language functions/procedures in a separate process, with no access to the database process’ memory. Parameters and results are communicated via inter-process communication. (Both approaches have performance overheads).

---

## 3. Triggers
A trigger is a statement that is executed automatically by the system as a side effect of a modification to the database. To design a trigger mechanism, we must:
1. Specify the conditions under which the trigger is to be executed.
2. Specify the actions to be taken when the trigger executes.

### Example: Trigger to Maintain `credits_earned` Value
```sql
create trigger credits_earned after update of takes on (grade)
    referencing new row as nrow
    referencing old row as orow
    for each row
    when nrow.grade <> 'F' and nrow.grade is not null
         and (orow.grade = 'F' or orow.grade is null)
    begin atomic
        update student
        set tot_cred = tot_cred +
            (select credits from course where course.course_id = nrow.course_id)
        where student.id = nrow.id;
    end;
```

### Statement Level Triggers
Instead of executing a separate action for each affected row, a single action can be executed for all rows affected by a transaction.
* Use `for each statement` instead of `for each row`.
* Use `referencing old table` or `referencing new table` to refer to temporary transition tables containing the affected rows. This can be more efficient when dealing with SQL statements that update a large number of rows.

### When Not To Use Triggers
Triggers were previously used for maintaining summary data or replicating databases. There are better ways of doing these now:
* Databases today provide built-in materialized view facilities to maintain summary data.
* Databases provide built-in support for replication.
* Encapsulation facilities (defining methods to update fields) can be used instead of triggers in many cases.

**Risks with triggers:**
* Unintended execution (e.g., when loading data from a backup copy or replicating updates at a remote site). Trigger execution should be disabled before such actions.
* Errors in triggers can lead to the failure of critical transactions.
* Cascading execution of triggers.

---

## 4. Recursive Queries
### Recursion in SQL

![Example of Fixed-Point Computation](../images/ch5_slides/slide_046.png)

SQL:1999 permits recursive view definitions.
**Example:** Find which courses are a prerequisite, whether directly or indirectly, for a specific course (transitive closure).
```sql
with recursive rec_prereq(course_id, prereq_id) as (
    select course_id, prereq_id
    from prereq
    union
    select rec_prereq.course_id, prereq.prereq_id
    from rec_prereq, prereq
    where rec_prereq.prereq_id = prereq.course_id
)
select * from rec_prereq;
```

**The Power of Recursion:**
Recursive views make it possible to write queries, such as transitive closure queries, that cannot be written without recursion or iteration. Without recursion, a non-recursive query can perform only a fixed number of joins (e.g., finding only a fixed number of levels of managers/prerequisites).

---

## 5. Advanced Aggregation Features
### 5.1 Ranking
Ranking is done in conjunction with an `order by` specification.
```sql
select ID, rank() over (order by GPA desc) as s_rank
from student_grades
order by s_rank;
```
* `rank()` may leave gaps (e.g., if two students have the same top GPA, both have rank 1, and the next rank is 3).
* `dense_rank()` does not leave gaps (the next dense rank would be 2).
* Ranking can be done within partitions using `partition by`:
  ```sql
  select ID, dept_name,
      rank() over (partition by dept_name order by GPA desc) as dept_rank
  from dept_grades
  order by dept_name, dept_rank;
  ```
* Other ranking functions: `percent_rank`, `cume_dist` (cumulative distribution), `row_number`.
* `ntile(n)` takes the tuples in each partition in the specified order and divides them into `n` buckets with equal numbers of tuples.

### 5.2 Windowing
Used to smooth out random variations (e.g., calculating moving averages).
```sql
select date, sum(value) over
    (order by date between rows 1 preceding and 1 following)
from sales;
```
Other window specifications:
* `between rows unbounded preceding and current`
* `rows unbounded preceding`
* `range between 10 preceding and current row`
* `range interval 10 day preceding`

Windowing can also be done within partitions (e.g., finding the total balance of each account after each transaction):
```sql
select account_number, date_time,
    sum(value) over (partition by account_number order by date_time rows unbounded preceding) as balance
from transaction
order by account_number, date_time;
```

### 5.3 Data Analysis and OLAP

![Example sales relation](../images/ch5_slides/slide_058.png)

**Online Analytical Processing (OLAP):** Interactive analysis of data, allowing data to be summarized and viewed in different ways in an online fashion (with negligible delay).

**Multidimensional Data:**
* **Measure attributes:** Measure some value, can be aggregated upon (e.g., `number` of the sales relation).
* **Dimension attributes:** Define the dimensions on which measure attributes are viewed (e.g., `item_name`, `color`, `size`).

**Cross-Tabulation (Pivot-Table):**
Values for one dimension attribute form row headers, values for another form column headers. Other dimension attributes are listed on top. Values in individual cells are aggregates of the measure attributes.

**Data Cube:**
A multidimensional generalization of a cross-tab. Can have *n* dimensions. Cross-tabs can be used as views on a data cube. Can drill down or roll up on hierarchies.

#### Extended Aggregation to Support OLAP

![Relational Representation of Cross-tabs](../images/ch5_slides/slide_062.png)

* **cube:** Computes the union of `group by`s on every subset of the specified attributes.
  ```sql
  select item_name, color, size, sum(number)
  from sales
  group by cube(item_name, color, size)
  ```
* **grouping() function:** Returns 1 if the value is a null value representing `all`, and returns 0 otherwise.
* **decode() function:** Can be used to replace such nulls with a value like `'all'`.
* **rollup:** Generates the union on every prefix of the specified list of attributes. Useful for generating aggregates at multiple levels of a hierarchy.
  ```sql
  select item_name, color, size, sum(number)
  from sales
  group by rollup(item_name, color, size)
  ```

#### OLAP Operations
* **Pivoting:** Changing the dimensions used in a cross-tab.
* **Slicing (Dicing):** Creating a cross-tab for fixed values only.
* **Rollup:** Moving from finer-granularity data to a coarser granularity.
* **Drill down:** Moving from coarser-granularity data to finer-granularity data.

#### OLAP Implementation
* **MOLAP (Multidimensional OLAP):** Uses multidimensional arrays in memory to store data cubes.
* **ROLAP (Relational OLAP):** Uses only relational database features.
* **HOLAP (Hybrid OLAP):** Stores some summaries in memory and the base data/other summaries in a relational database.

Early OLAP systems precomputed all possible aggregates (space/time intensive for $2^n$ combinations). Optimizations include computing some aggregates on demand from other precomputed aggregates (e.g., computing `(item_name, color)` from `(item_name, color, size)`).
