# Chapter 8: Complex Data Types

## Introduction
Modern database systems extend beyond traditional atomic data types to manage complex data structures efficiently. This chapter covers the fundamental concepts of managing complex data types, which are categorized into:
- Semi-Structured Data
- Object Orientation
- Textual Data
- Spatial Data

---

## 1. Semi-Structured Data
Many applications require storage of complex data whose schema changes often. The relational model's strict requirement of atomic data types may be overkill. For instance, storing a user's set of interests as a set-valued attribute is simpler than fully normalizing it into separate tables.

Data exchange benefits greatly from semi-structured data:
- Information can be seamlessly exchanged between applications or between an application's back-end and front-end.
- Modern web services frequently fetch complex data to the front-end, where it is rendered using mobile apps or JavaScript.
- **JSON** and **XML** are the most widely used semi-structured data models.

### Features of Semi-Structured Data Models
- **Flexible Schema:**
  - **Wide column representation:** Allows each tuple to have a different set of attributes; new attributes can be added at any time.
  - **Sparse column representation:** The schema has a fixed but very large set of attributes, but each tuple may only store a small subset of them.
- **Multivalued Data Types:**
  - **Sets and Multisets:** e.g., a set of interests `{'basketball', 'La Liga', 'cooking', 'anime', 'jazz'}`.
  - **Key-Value Maps (Maps):** Stores a set of key-value pairs, such as `{(brand, Apple), (ID, MacBook Air), (size, 13), (color, silver)}`. Common operations include `put(key, value)`, `get(key)`, and `delete(key)`.
  - **Arrays:** Highly useful for scientific and monitoring applications. Readings taken at regular intervals can be stored as an array of values rather than multiple `(time, value)` pairs. For example, `[5, 8, 9, 11]` instead of `{(1,5), (2, 8), (3, 9), (4, 11)}`.
- **Multi-Valued Attribute Types:** Modeled using the Non First-Normal-Form (NFNF) data model. This is supported by most database systems today.
- **Array Databases:** Databases that provide specialized support for arrays, including compressed storage and query language extensions. Examples include Oracle GeoRaster, PostGIS, and SciDB.

### Nested Data Types
Hierarchical data is common in many applications.

#### JSON (JavaScript Object Notation)
- A textual representation that is ubiquitous in data exchange today, especially in web services.
- **Types:** Integer, real, string, objects (which act as key-value maps or sets of attribute name/value pairs), and arrays (which act as key-value maps from offset to value).
- **SQL Extensions for JSON:**
  - Built-in JSON types for native storage.
  - Extraction using path expressions (e.g., `v->ID` or `v.ID`).
  - Generating JSON from relational data (e.g., `json.build_object('ID', 12345, 'name', 'Einstein')`).
  - Creation of JSON collections using aggregation functions (e.g., `json_agg` in PostgreSQL).
  - Note: Syntax varies greatly across different databases.
- Because JSON is verbose, compressed representations such as **BSON** (Binary JSON) are used for efficient data storage.

#### XML (Extensible Markup Language)
- Uses tags to mark up text. The tags make the data self-documenting and hierarchical.
- **XQuery:** A specialized language developed to query nested XML structures (though not widely used currently).
- **SQL Extensions for XML:** Databases support storing XML data, generating XML from relational data, and extracting data via path expressions.

---

## 2. Knowledge Representation
The representation of human knowledge is a long-standing goal of AI. Over time, various methods for representing facts and inference rules have been proposed.

### RDF (Resource Description Format)
![Graph View of RDF Data](../images/ch8_slides/slide_013.png)
![Triple View of RDF Data](../images/ch8_slides/slide_014.png)
- A simplified representation for facts, formatted as **triples**: `(subject, predicate, object)`.
  - *Example 1:* `(NBA-2019, winner, Raptors)`
  - *Example 2:* `(Washington-DC, capital-of, USA)`
- Models objects that have attributes, and their relationships with other objects. It acts similarly to the Entity-Relationship (ER) model but provides a highly flexible schema.
- Triples can represent both attributes `(ID, attribute-name, value)` and relationships `(ID1, relationship-name, ID2)`.
- Has a natural graph representation (a Knowledge Graph).

### Querying RDF: SPARQL
- Uses **triple patterns** to match facts.
- **SPARQL queries** support aggregations, optional joins (similar to outer joins), subqueries, and computing transitive closures on paths.

### Representing n-ary Relationships in RDF
Since RDF natively represents binary relationships (triples), $n$-ary relationships can be modeled via:
1. **Approach 1:** Create an artificial entity and link it to each of the $n$ entities.
2. **Approach 2:** Use **quads** instead of triples, introducing a context entity.

RDF is widely used as the representation standard for knowledge bases (e.g., DBPedia, Yago, Freebase, WikiData). The **Linked Open Data** project aims to connect disparate knowledge graphs, allowing queries to span across multiple databases seamlessly.

---

## 3. Object Orientation
The **object-relational data model** provides a richer type system with complex data types and object orientation, helping bridge the gap between relational databases and object-oriented programming languages.

### Integration Approaches
1. **Object-Relational Databases:** Add object-oriented features natively to a relational database.
2. **Object-Relational Mapping (ORM):** Automatically convert data between the programming language model and the relational model.
3. **Object-Oriented Databases:** Build a database that natively supports object-oriented data and direct access from programming languages.

### Object-Relational Database Systems
- **User-Defined Types:** E.g., `create type Person (...)`.
- **Table Types:** Tables can be constructed from user-defined types.
- **Inheritance:** Databases support type inheritance (e.g., `under Person`) and table inheritance (e.g., `inherits people`).
- **Reference Types:** Objects can generate references, which can be retrieved using subqueries and queried using path expressions.

### Object-Relational Mapping (ORM)
ORM systems (such as Hibernate for Java and Django for Python) allow:
- Specification of mapping between programming language objects and database tuples.
- Automatic creation, update, and deletion of tuples when objects are manipulated.
- Interfaces to retrieve objects satisfying specific criteria.

---

## 4. Textual Data
**Information Retrieval (IR)** concerns the querying of unstructured textual data.

- **Keyword Queries:** A simple model where, given query keywords, documents containing all the keywords are retrieved.
- **Relevance Ranking:** Essential because keyword queries often return many matching documents. Advanced models rank the relevance of documents to prioritize the best matches.

### Ranking using TF-IDF
- **Term Frequency (TF):** The relevance of a term $t$ to a document $d$. One definition is $TF(d, t) = \log(1 + n(d,t)/n(d))$, where $n(d,t)$ is the number of occurrences of term $t$ in document $d$.
- **Inverse Document Frequency (IDF):** One definition is $IDF(t) = 1/n(t)$.
- **Relevance:** The relevance of a document $d$ to a query $Q$ is computed as $r(d, Q) = \sum_{t \in Q} TF(d, t) \times IDF(t)$.
- Enhancements include factoring in the proximity of words and ignoring common "stop words."

### Ranking Using Hyperlinks
- Hyperlinks provide vital clues to a page's importance.
- **PageRank:** Introduced by Google, it measures popularity based on hyperlinks. Pages linked from many other pages, or from highly ranked pages, get a higher PageRank. It is formalized using a random walk model and computed iteratively using linear equations.
- Other relevance measures include keywords found in anchor text and click-through rates.

### Retrieval Effectiveness
- **Precision:** The percentage of returned results that are actually relevant.
- **Recall:** The percentage of relevant results that were successfully returned.
- Keyword searching on structured data and knowledge bases matches keywords to tuples and returns closely connected tuples that form a cohesive answer.

---

## 5. Spatial Data
**Spatial databases** store information related to spatial locations and provide efficient storage, indexing, and querying for spatial data.

- **Geographic Data:** Road maps, topographic maps, boundaries, etc. Geographic Information Systems (GIS) are special-purpose databases tailored for this. Uses a round-earth coordinate system (Latitude, Longitude, Elevation).
- **Geometric Data:** Design information about how objects are constructed (e.g., building designs, aircraft, IC layouts). Uses a 2D or 3D Euclidean space with $(X, Y, Z)$ coordinates.

### Representation of Geometric Information
![Representation of Geometric Constructs](../images/ch8_slides/slide_030.png)
- **Line Segments:** Represented by the coordinates of their endpoints.
- **Polylines / Linestrings:** Connected sequences of line segments, often used to approximate curves (e.g., roads).
- **Polygons:** Represented by a list of ordered vertices specifying the boundary. Can also be represented as a set of triangles (triangulation).
- **3D Objects:** Polyhedra can be divided into tetrahedrons, or represented by a list of their faces (polygons).
- **Database Support:** Many databases (e.g., SQL Server, PostGIS) natively support types like point, linestring, curve, polygons, and their collections. They also provide spatial operations like `ST_Union()` and `ST_Intersection()`.

### Design vs. Geographic Databases
- **Design Databases:** Represent design components as geometric objects. They enforce **spatial integrity constraints** (e.g., pipes should not intersect). They typically do not store raster data.
- **Geographic Data Formats:**
  - **Raster Data:** Bitmaps or pixel maps in multiple dimensions (e.g., satellite cloud cover images).
  - **Vector Data:** Constructed from basic geometric objects (lines, polygons). Frequently used for maps (e.g., representing roads as lines, regions as polygons).

### Spatial Queries
- **Region Queries:** Deals with spatial regions (e.g., finding objects that lie partially or fully inside a region using `ST_Contains()`).
- **Nearness & Nearest Neighbor Queries:** Finds objects near a specified location or the absolute closest object matching conditions.
- **Spatial Graph Queries:** E.g., finding the shortest path between two points in a road network.
- **Spatial Joins:** Joins two spatial relations where the location serves as the join attribute.
