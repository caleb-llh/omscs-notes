# Chapter 9: Application Development

## 1. Application Programs and User Interfaces
Most database users do not use a query language like SQL. An application program acts as the intermediary between users and the database.

Applications are typically split into:
- **Front-end**: User interface (Forms, Graphical user interfaces, Web-based interfaces).
- **Middle layer**: Business logic.
- **Back-end**: Database system.

### Application Architecture Evolution
There are three distinct eras of application architecture:
1. **Mainframe** (1960s and 70s)
2. **Personal computer era** (1980s)
3. **Web era** (mid 1990s onwards) and **Web and Smartphone era** (2010 onwards)

### Web Interface
Web browsers have become the de-facto standard user interface to databases.
- Enable large numbers of users to access databases from anywhere.
- Avoid the need for downloading/installing specialized code, while providing a good graphical user interface.
- **Javascript, Flash, and other scripting languages** run in the browser but are downloaded transparently.
- Examples include banks, airline and rental car reservations, university course registration, and grading.

### Three-Layer Web Architecture
![Three-Layer Web Architecture](../images/ch9_slides/slide_007.png)
Follows a standard three-tier model involving Presentation (UI), Business Logic, and Data Access layers.

---

## 2. HTTP and Sessions
The HTTP protocol is **connectionless**: once the server replies to a request, it closes the connection with the client and forgets about the request. In contrast, Unix logins and JDBC/ODBC connections stay connected until the client disconnects.
- **Motivation for connectionless**: Reduces load on the server, as operating systems have tight limits on the number of open connections on a machine.
- **Challenge**: Information services need session information (e.g., user authentication should be done only once per session).
- **Solution**: Use **cookies**.

### Sessions and Cookies
A cookie is a small piece of text containing identifying information.
- Sent by the server to the browser on the first interaction to identify the session.
- Sent by the browser to the server that created the cookie on further interactions (part of the HTTP protocol).
- The server saves information about cookies it issued and can use it when serving a request (e.g., authentication information and user preferences).
- Cookies can be stored permanently or for a limited time.

---

## 3. Servlets
The Java Servlet specification defines an API for communication between the Web/application server and the application program running in the server (e.g., methods to get parameter values from Web forms and send HTML text back to the client).
- The application program (servlet) is loaded into the server.
- Each request spawns a new thread in the server, which is closed once the request is serviced.
- Programmers create a class that inherits from `HttpServlet` and overrides methods like `doGet`, `doPost`, etc.
- Mapping from the servlet name to the servlet class is done in a `web.xml` file.

### Servlet Sessions
The Servlet API supports handling of sessions:
- Sets a cookie on the first interaction with the browser and uses it to identify the session on further interactions.
- Methods to manage sessions: `request.getSession(true)` to create a new session, `request.getSession(false)` to check if a session is already active.
- Store/retrieve attribute-value pairs for a particular session: `session.setAttribute("userid", userid)`.

### Servlet Support
Servlets run inside application servers such as Apache Tomcat, Glassfish, JBoss, BEA Weblogic, IBM WebSphere, and Oracle Application Servers.
Application servers support:
- Deployment and monitoring of servlets.
- Java 2 Enterprise Edition (J2EE) platform supporting objects, parallel processing across multiple application servers, etc.

---

## 4. Server-Side Scripting
Server-side scripting simplifies the task of connecting a database to the Web.
- Defines an HTML document with embedded executable code/SQL queries.
- Input values from HTML forms can be used directly in the embedded code/SQL queries.
- When the document is requested, the Web server executes the embedded code to generate the actual HTML document.
- Languages: **JSP**, **PHP**, and general-purpose scripting languages (**VBScript**, **Perl**, **Python**).

### Java Server Pages (JSP)
- A JSP page has embedded Java code.
- JSP is compiled into Java + Servlets.
- Allows new tags to be defined in tag libraries (like library functions, used to build rich user interfaces such as paginated displays of large datasets).

### PHP
- Widely used for Web server scripting.
- Extensive libraries including for database access using ODBC.

### Javascript
- Forms the basis of the new generation of Web applications (Web 2.0 applications) offering rich user interfaces.
- **Javascript functions can:**
  - Check input for validity.
  - Modify the displayed Web page by altering the underlying Document Object Model (DOM) tree representation.
  - Communicate with a Web server to fetch data and modify the current page using fetched data without reloading/refreshing the page (**AJAX technology**).
  - Example: On selecting a country in a drop-down menu, the list of states is automatically populated.

---

## 5. Application Architectures
![Application Architectures](../images/ch9_slides/slide_020.png)

### Application Layers
![Application Architecture](../images/ch9_slides/slide_022.png)
- **Presentation or User Interface**:
  - Uses **Model-View-Controller (MVC) architecture**:
    - **Model**: Business logic.
    - **View**: Presentation of data (depends on display device).
    - **Controller**: Receives events, executes actions, and returns a view to the user.
- **Business-Logic Layer**:
  - Provides a high-level view of data and actions on data, often using an object data model.
  - Hides details of the data storage schema.
  - Provides abstractions of entities (e.g., students, instructors, courses).
  - Enforces business rules for carrying out actions (e.g., a student can enroll only if prerequisites are met).
  - Supports workflows which define how a task involving multiple participants is carried out (sequence of steps, error handling).
- **Data Access Layer**:
  - Interfaces between the business logic layer and the underlying database.
  - Provides mapping from the object model of the business layer to the relational model of the database.

### Object-Relational Mapping (ORM)
Allows application code to be written on top of an object-oriented data model while storing data in a traditional relational database.
- Schema designers provide a mapping between object data and relational schema (e.g., Java class `Student` mapped to relation `student`).
- Applications open a session to connect to the database. Objects can be created and saved to the database using `session.save(object)`.
- **Hibernate**: A widely used ORM system that supports a complex query language involving joins and translates queries into SQL.
- **Entity Data Model** (Microsoft): Provides an entity-relationship model directly to the application and maps data between the entity model and underlying storage. Uses Entity SQL language.

### Web Services
Allows data on the Web to be accessed using remote procedure call mechanisms. Two widely used approaches:
- **Representation State Transfer (REST)**: Allows use of standard HTTP requests to a URL to execute a request and return data (encoded in XML or JSON).
- **Big Web Services**: Uses XML representation for sending request data and returning results. Built on top of HTTP as a standard protocol layer.

### Disconnected Operations
Tools for applications to use the Web when connected, but operate locally when disconnected, making use of **HTML5 local storage**.

### Rapid Application Development (RAD)
Speeds up Web application development using:
- Function libraries to generate UI elements.
- Drag-and-drop features in an IDE.
- Automatic code generation for UI from a declarative specification.
- Web application development frameworks like **Java Server Faces (JSF)** and **Ruby on Rails** (allows easy creation of CRUD interfaces).

---

## 6. Application Performance
Performance is a major issue for popular websites handling millions of users and thousands of requests per second.
**Caching techniques** are used to reduce the cost of serving pages by exploiting commonalities between requests:
- **At the server site:**
  - Caching of JDBC connections between servlet requests (**connection pooling**).
  - Caching results of database queries (cached results must be updated if the underlying database changes).
  - Caching of generated HTML.
- **At the client’s network:**
  - Caching of pages by Web proxy.

---

## 7. Application Security

### Cross-Site Scripting (XSS / XSRF / CSRF)
- **XSS (Cross-Site Scripting)**: HTML code on one page executes an action on another page.
- **Risk**: If a user is logged into a site and views a malicious page, unwanted actions (like transferring money) may succeed.
- **Prevention on your site**:
  - Disallow HTML tags in user-provided text input by detecting and stripping such tags.
  - Use the `referer` value provided by the HTTP protocol to check that the link was followed from a valid page.
  - Ensure the IP of the request is the same as the authenticated IP (prevents cookie hijacking).
  - Never use a `GET` method to perform any updates (recommended by HTTP standard).

### Password Leakage
- Never store passwords in clear text in scripts accessible to users.
- Web servers may not serve script source files (like `.jsp` or `.php`), but editor backup files (like `.jsp~` or `.jsp.swp`) might be served accidentally.
- Restrict access to the database server from IPs of machines running application servers.

### Application Authentication
Single factor authentication (passwords) is too risky due to guessing, packet sniffing, password reuse, and spyware.
- **Two-factor authentication**: Password plus one-time password sent by SMS or device.
- **Man-in-the-middle attack**: A fake website pretends to be a legitimate one and passes requests. Two-factor authentication cannot fully prevent this.
  - **Solution**: Authenticate the Web site to the user using digital certificates and secure HTTP (HTTPS).
- **Central authentication**: Applications redirect to a central authentication service (like LDAP or Active Directory) to avoid multiple sites accessing the user's password.
- **Single Sign-On (SSO)**: Allows a user to authenticate once. Applications communicate with the authentication service.
  - **SAML (Security Assertion Markup Language)**: Standard for exchanging authentication and authorization information.
  - **OpenID**: Standard allowing sharing of authentication across organizations (e.g., using Yahoo! as an OpenID provider).

### Application-Level Authorization
The current SQL standard does not allow fine-grained authorization (e.g., row-level access control like "students can see only their own grades").
- Workaround: Use views (e.g., `where takes.ID = syscontext.user_id()`). End user identity must be provided to the database.
- Application-level authorization is often done entirely in the application code, which has access to the entire database, increasing the attack surface.
- **Alternative**: Fine-grained authorization schemes like Oracle Virtual Private Database (VPD), which transparently adds predicates to all SQL queries.

### Audit Trails
Applications must log actions to an audit trail to detect who carried out updates or accessed sensitive data.
- Used after the fact to detect security breaches, repair damage, and trace the breach source.
- Needed at both the database level and application level.
