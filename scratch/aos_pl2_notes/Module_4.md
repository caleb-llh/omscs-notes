# Module 4: Java RMI and Distributed Object Models

## Introduction
This module explores how distributed object technology influences commercial offerings, focusing specifically on **Java RMI (Remote Method Invocation)**, which is rooted in the fundamental principles of distributed systems.

## Java Language History
- **Origins**: Invented by James Gosling at Sun Microsystems in the early 90s.
- **Original Name**: Oak.
- **Initial Purpose**: Intended for use with embedded devices and PDAs.
- **Evolution**:
  - Sun initially considered Java for programming set-top boxes for video-on-demand (VOD) over the internet.
  - The cable TV industry chose SGI for VOD trials, causing Oak to fail in that market.
  - The rise of the World Wide Web gave Java new life due to the need for containing operations on client boxes connecting to the web.
  - Today, internet e-commerce and many enterprise applications rely heavily on the Java framework.

## Java Distributed Object Model
The Java remote object model abstracts much of the "heavy lifting" required in building a client-server system (e.g., RPC, marshalling, unmarshalling, publishing remote objects). This is handled under the covers by the Java distributed object runtime, similar to the **subcontract mechanism** in the Spring operating system.

### Key Definitions
- **Remote Object**: Objects that are accessible from different address spaces (often across a network).
- **Remote Interface**: Declarations for methods within a remote object that specify what is accessible to clients anywhere.
- **RMI Exception**: The failure semantics of the distributed object model. Clients must deal with exceptions that might occur during remote method invocations.

### Parameter Passing: Local vs. Remote Objects
- **Similarity**: Both local and remote object invocations can pass object references as parameters.
- **Difference**: 
  - **Local Objects**: Use **pass-by-reference**. The invoked method can modify the object passed to it, and changes are reflected in the original object.
  - **Remote Objects**: Use **pass-by-value-result**. A copy of the object is sent over the network. Modifications made by the invoked method are local to that copy and will not be seen by the client.

## Building a Service: Bank Account Example
To illustrate the Java distributed object model, consider a bank account server with APIs for deposit, withdrawal, and balance inquiries.

### Implementation Choices
1. **Reuse of Local Implementation**
   - **Process**: A developer extends a local `account` class to create a `bank account` implementation. Using the built-in `Remote` interface, the methods are made visible on the network.
   - **Drawback**: While the interface is public, the actual location of the instantiated object is hidden from the client. The implementer must manually do the heavy lifting to make the object's location visible.
   - **Virtue**: Allows the service provider to make selected servers visible only to selected clients.
2. **Reuse of Remote Object (Preferred)**
   - **Process**: The developer extends a remote object class.
   - **Advantage**: Java RMI does all the heavy lifting to make the server object visible and accessible to network clients. This is the preferred method for building network services.

## Java RMI at Work
### Client-Side Experience
- **Lookup**: The client contacts a bootstrap name server in the Java RMI system to look up the service provider's published URL.
- **Local Access Point**: Upon successful lookup, a local access point (stub) for the object is created on the client side.
- **Invocation**: The client calls methods (e.g., deposit, withdraw) as if they were normal local procedure calls. The client does not know or care about the server's actual location.
- **Failure Handling**: If a failure occurs, the server throws a remote exception back to the client via the Java runtime. The client must handle these exceptions, though it may not know exactly where or why the call failed mid-flight.

## RMI Implementation Layers

### 1. Remote Reference Layer (RRL)
The RRL is the core of the RMI implementation where the "magic" happens, heavily resembling the Spring system's subcontract mechanism.
- **Client Side**: The client-side **stub** initiates a remote call using the RRL. The RRL handles **marshalling** (serializing) arguments to send over the network and **unmarshalling** (deserializing) the results back into digestible data structures.
- **Server Side**: The **skeleton** unmarshals incoming arguments via the RRL and calls the server implementing the remote object. Once finished, it marshals the result and sends it back through the RRL.
- **Responsibilities**: The RRL handles details regarding server location, replication, persistence, and invocation protocols, making clients and servers oblivious to these underlying mechanics.

### 2. Transport Layer
The transport layer sits below the RRL. The RRL decides the most appropriate transport protocol (e.g., TCP or UDP) based on endpoint locations and network conditions, instructing the transport layer to establish the connection.

**Key Abstractions**:
- **Endpoint**: A protection domain or sandbox (like a Java Virtual Machine) where code executes. It maintains a table of accessible remote objects.
- **Connection Manager**: Responsible for setting up, tearing down, and listening for incoming connections. It locates the dispatcher for a invoked remote method and monitors the liveness of connections.
- **Channel**: A mutual agreement between two endpoints to communicate using a chosen transport protocol.
- **Connection**: Once a channel is established, the transport mechanism performs I/O over the channel using a connection.

*Note: A single endpoint can use different transport protocols (e.g., TCP for one, UDP for another) to communicate with various other endpoints based on connection manager decisions.*

## Conclusion
The Java RMI system turns advanced distributed systems research into highly usable technology. 
Further advanced topics in RMI implementation include:
- **Distributed Garbage Collection**
- **Dynamic Loading of Stubs** (on the client side)
- **Sophisticated Sandboxing Mechanisms** (to ward off security threats)
