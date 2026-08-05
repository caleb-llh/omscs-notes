# Module 5: Structuring Complex Application Servers (Enterprise Java Beans)

## 1. Introduction
*   **Evolution:** Operating system structuring has evolved from single CPUs to parallel machines, then distributed systems, and now to large-scale distributed system services.
*   **Object Technology:** Uses innate concepts of inheritance and reuse to structure operating systems at different levels.
*   **Focus:** How to structure system software for large-scale distributed services (e.g., e-commerce, internet services).
*   **Definition - Java Bean:** A reusable software component. It is a bundle of Java objects providing a specific functionality (e.g., a shopping cart) that can be easily passed around from one application to another for reuse.

## 2. Enterprise Views and Challenges
*   **User View:** Users interact with an enterprise (e.g., Google, eBay) as a monolithic entity.
*   **Intra-Enterprise View:** Internally complex, consisting of interconnected services and servers (marketing, sales, production, inventory, etc.).
*   **Inter-Enterprise View (Supply Chain Model):** Enterprises talk to one another to fulfill requests. Service requests may involve multiple external entities.
*   **Mergers & Acquisitions:** When companies merge (e.g., DEC, Compaq, HP), the enterprise becomes an amalgam of different entities.
*   **Enterprise Transformation Challenges:**
    *   Interoperability of systems.
    *   Interface compatibility.
    *   System evolution.
    *   Scalability and reliability.
    *   Cost of maintaining complex systems.

## 3. Giant Scale Services vs. Local Services
*   **Definition - Giant Scale Services:** Internet-scale services used daily (e.g., Expedia, Gmail) as opposed to local organizational services (e.g., a local file server).
*   **Resource Conflicts:** Multiple concurrent users competing for physical resources (e.g., a seat on a flight) across space and time.
*   **System Issues:** Synchronization, communication, atomicity of actions, and concurrency are critical.
*   **Component Reuse:** Common features (like shopping carts) are needed across different domains (airline, train, hotel). Object technology allows reusing components to avoid "reinventing the wheel."

## 4. N-Tier Applications
*   **Definition:** Applications structured into multiple logical layers (tiers) to separate concerns.
*   **Application Stack Layers:**
    1.  **Presentation Layer:** Paints the screen on the browser and dynamically generates pages.
    2.  **Application Logic:** The specific service being provided.
    3.  **Business Logic:** Rules and decisions (e.g., how airfares are decided, seats allocated).
    4.  **Database Layer:** Accesses and stores necessary data.
*   **Key Issues in N-Tier Applications:**
    *   **Persistence:** Saving state for incomplete actions (e.g., unfinished booking).
    *   **Transactions:** Ensuring atomicity of operations.
    *   **Caching:** Storing pulled database data for faster access.
    *   **Clustering:** Grouping related services or data to improve performance.
    *   **Security:** Protecting financial and personal information.
*   **Structuring Goals:**
    *   Reduce network communication (lower latency).
    *   Reduce security risks (protect business logic).
    *   Increase concurrency (exploit "embarrassingly parallel" opportunities).
    *   Cluster computation for common queries.
    *   Reuse components aggressively (application logic and execution).

## 5. Structuring N-Tier Applications: JEE Framework
*   **Java Enterprise Edition (JEE):** A framework using containers (protection domains typically implemented in a JVM) to construct application services.
*   **Four JEE Containers:**
    1.  **Client Container:** Resides on the client side.
    2.  **Applet Container:** Interfaces with the end client's web browser.
    3.  **Web Container:** Manages presentation logic and dynamically creates web pages.
    4.  **EJB Container:** Manages the business logic.
*   **Types of Beans (Units of Reuse):**
    1.  **Entity Bean:** Represents persistent data (e.g., a row in a database with a primary key).
        *   *Bean Managed Persistence (BMP):* Persistence is built into the bean itself.
        *   *Container Managed Persistence (CMP):* Persistence is handled by the container hosting the bean.
    2.  **Session Bean:** Associated with a specific client and temporal session.
        *   *Stateful Session Bean:* Remembers client choices across the session (e.g., a Dell shopping cart).
        *   *Stateless Session Bean:* Retains no state between sessions (e.g., logging into Gmail).
    3.  **Message Driven Bean:** Handles asynchronous behavior (e.g., stock tickers, RSS news feeds).
*   **Granularity Trade-off:** Fine-grained beans enhance concurrency but increase business logic complexity. Coarse-grained beans keep logic simple but reduce concurrency.

## 6. Design Alternatives for Application Servers

### Design Alternative 1: Coarse-Grained Session Beans
*   **Structure:**
    *   *Web Container:* Contains Servlets (one per client) and Presentation Logic.
    *   *EJB Container:* Contains Coarse-Grained Session Beans.
*   **Workflow:** The session bean handles all specific needs and database accesses for its associated client servlet.
*   **Pros:**
    *   Requires minimal container services (mostly coordinating concurrent DB accesses).
    *   Business logic is confined within the corporate network (secure).
*   **Cons:**
    *   Monolithic structure.
    *   Lost opportunity for parallel database access (limited concurrency).

### Design Alternative 2: Data Access Objects (Entity Beans)
*   **Goal:** Increase parallelism for database access (the slowest link).
*   **Structure:**
    *   *Web Container:* Contains Servlet, Presentation Logic, AND Business Logic (3-tier structure).
    *   *EJB Container:* Contains Data Access Objects (DAOs) implemented as Entity Beans.
*   **Workflow:** Business logic fans out parallel requests to multiple entity beans, which access different parts of the database concurrently.
*   **Pros:**
    *   High concurrency and reduced latency (exploits parallel I/O and amortizes DB access across clients).
*   **Cons:**
    *   Moving business logic into the web container exposes it outside the corporate network, creating a security risk.

### Design Alternative 3: Session Bean with Entity Bean (Session Facade)
*   **Goal:** Achieve high concurrency without exposing business logic.
*   **Structure:**
    *   *Web Container:* Contains Servlet and Presentation Logic only.
    *   *EJB Container:* Contains Session Facade, Business Logic, and Entity Beans.
*   **Workflow:** The Session Facade (associated with a client) sits with the business logic in the EJB container. It fans out data access requests to multiple Entity Beans in parallel.
*   **Communication Choices (Session Facade to Entity Bean):**
    *   *Remote Interface (RMI):* Entity beans can be distributed anywhere on the network.
    *   *Local Interface:* Co-locates entity beans in the same EJB container, avoiding network communication overhead.
*   **Pros:**
    *   Best of both worlds: High concurrency (via Entity Beans) AND protected business logic (kept within the EJB container).
*   **Cons:**
    *   Incurs additional network access overhead (which can be mitigated by using Local Interfaces).

## 7. Conclusion
*   **Separation of Concerns:** Object technology (like EJB) allows developers to write pure business logic without worrying about cross-cutting concerns (security, logging, persistence), which are handled by the framework.
*   **Performance Implications:** Different design choices directly impact concurrency, resource pooling, network overhead, and code complexity.
