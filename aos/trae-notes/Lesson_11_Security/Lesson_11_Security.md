# Lesson_11_Security (Synthesized Notes)

> **Purpose:** To explore the foundational principles of computer system security (using Jerome Saltzer's early concepts) and examine how these principles are applied in distributed environments, specifically through the case study of the Andrew File System (AFS) using private key cryptography.
> **Philosophy:** Security is not an absolute state but a system function designed to enforce user intent (privacy) by making unauthorized access computationally infeasible and ensuring that violations are detectable. Positive statements of security goals are preferable to impossible negative guarantees.
> **Mental Model:** Think of security as a series of defensive layers and ephemeral interactions. Just as a physical vault uses multiple keys (Separation of Privilege) and only grants access when strictly necessary (Least Privilege), a secure distributed system like AFS limits the exposure of master secrets by establishing short-lived, verifiable sessions (ephemeral keys and random numbers) for ongoing operations.
> **Connective Information:** This module bridges the theoretical design principles of early computing pioneers with practical implementations in distributed systems. The concepts of mutual authentication, least privilege, and ephemeral session keys discussed here are the direct precursors to modern network security protocols (like Kerberos, TLS, and MFA) and foundational for understanding secure cloud architectures discussed by Yousef Khalidi.

# Module 9: Computer System Security

## Introduction
- **Overview**: Computer system security is of enormous importance in today's connected world.
- **Goals of the Module**:
  - Introduce terminologies in computer system security for operating system designers.
  - Learn cryptographic techniques used for authentication in distributed systems (via case study).
  - Discuss early terminologies articulated by **Jerome Saltzer**, demonstrating how computer visionaries foresaw information security issues before widespread computer connectivity.

## Firsts from Computing Pioneers
Reviewing early thought pieces provides historical context on information security.
> **Background Context:** The transition from isolated mainframes to interconnected networks introduced entirely new attack vectors, shifting security from physical access control to cryptographic network protocols.
- **Intergalactic Computer Networks (1963)**: An early memorandum conceptualizing global computer networks.
- **First Computer-to-Computer Communication (October 29, 1969)**: A host-to-host call made from UCLA to the Stanford Research Institute, recorded in the logbook of networking pioneer **Professor Leonard Kleinrock**.
- **First Email (1971)**: Written by **Ray Tomlinson** from BBN Technologies.
- **The Entire Internet in One Chart (March 1977)**: A single chart that mapped all the computers in the world.
- **Computer System Model (1975)**: Consisted of a mainframe computer (CPU, memory, I/O devices like disks) accessed via cathode-ray terminals in a time-shared manner, with no network connections.
- **Relevance**: Despite the isolated nature of early systems, Jerome Saltzer's seminal paper identified security issues and terminologies relevant today (e.g., denial of service, firewalls, sandboxing).

## Terminologies and Concepts (Jerome Saltzer, 1975)
Jerome Saltzer's seminal paper outlines critical issues in computer security.

### Privacy vs. Security
> **Intuition:** Privacy is about the user's intent with their data, whereas security is the mechanism the system uses to enforce that intent.
> **Common Confusion:** People often use "privacy" and "security" interchangeably. However, privacy defines *what* needs to be protected (the policy), while security provides the *how* (the mechanisms to enforce that policy).
- **Privacy**: An individual's right and responsibility concerning when their information is released or protected. It deals with the user and the data they own.
- **Security**: A system function responsible for guaranteeing properties about the information it preserves on behalf of users. It ensures that data is protected and only released with the owner's authorization.
  - **Authentication**: The system must verify a user's identity before granting access.
  - **Protection**: The system must ensure accessed information does not violate the privacy of others. Protection and authentication are foundational to a secure system.

### Core Security Concerns
Saltzer identified a comprehensive set of security concerns:
1. **Unauthorized Information Release**: The system must prevent data from being released without the owner's authorization.
   > **Example:** A modern data breach where hackers steal a database of user passwords and credit card numbers from a corporate server.
2. **Unauthorized Modification of Information**: The system must ensure that authorized access to view data does not improperly grant authority to modify it.
   > **Conceptual Framework:** This aligns with the "Integrity" aspect of the CIA (Confidentiality, Integrity, Availability) triad. It ensures data remains accurate and unaltered by unauthorized parties.
3. **Unauthorized Denial of Use**: The system must ensure that authorized users are not prevented from accessing their data. This is the first literature mention of what is now commonly known as a **Denial of Service (DoS)** attack.
> **Example:** A modern Denial of Service (DoS) attack might involve a botnet flooding a web server with requests so legitimate users cannot access the site.

### Goals of a Secure System
- **Negative Statements (Flawed Approach)**: Defining security as "preventing all violations" or being "bulletproof" is a negative statement. It is impossible to achieve or prove (similar to proving a program has no bugs) and gives a false sense of security.
- **Positive Statements (Preferred Approach)**: The goal should be stated positively, focusing on verifiable actions rather than impossible guarantees.

## Levels of Protection
*(No transcript available)*

## Design Principles
Saltzer laid out eight positive design principles that remain highly applicable to today's connected systems:

1. **Economy of Mechanisms**: Security mechanisms should be simple and easy enough to verify whether they work correctly.
   > **Background Context:** Complex security mechanisms often contain hidden bugs. By keeping the design simple, it becomes easier to audit, formally verify, and trust the implementation.
2. **Fail-Safe Defaults**: Access to the system or information should be explicitly allowed. The default state should be a "fail-safe" mode rather than implicitly assuming access or using negative statements.
   > **Example:** A firewall that defaults to "deny all" incoming traffic, requiring explicit rules to allow specific connections.
3. **Complete Mediation**: Security mechanisms must not take shortcuts. Every access must be fully checked against the authentication system.
   > **Conceptual Framework:** This means no access path should bypass the security check. Even if a user was previously authenticated, their permissions could have been revoked, so caching access rights without a validation mechanism is dangerous.
   - *Example*: Caching a password file in memory for performance can cause security violations if the persistent storage copy changes but the cached copy does not.
4. **Open Design**: The system's design should be completely open and published, but the keys used for authentication must be protected.
   > **Conceptual Framework:** Also known as Kerckhoffs's principle. Security through obscurity is fragile; a robust system remains secure even if the attacker knows everything about how it works, as long as they don't have the keys.
   - **Underlying Tenet**: Cracking the design is useless without the keys. Breaking the keys should be computationally infeasible. It also fosters the idea that **detection is easier than prevention**.
5. **Separation of Privilege**: Requiring multiple conditions or parties to grant access.
   - *Example*: Two different individuals holding two separate keys required to open a bank vault.
   > **Modern Example:** Multi-Factor Authentication (MFA), which requires both a password (something you know) and a one-time code from a mobile device (something you have).
6. **Least Privilege**: Users and processes should operate using the absolute minimum capabilities necessary to carry out a task based on a "need to know."
   - *Example*: Standard user privileges for daily tasks versus administrative/super-user privileges for installing software. This principle is the origin of modern organizational **firewalls**.
   > **Intuition:** A process should only have enough permissions to do its job and nothing more, limiting the blast radius if it gets compromised.
7. **Least Common Mechanism**: The design should limit shared security mechanisms to contain potential damage.
   > **Hypothetical:** If a single, monolithic security module handles both authentication for users and access control for system files, a bug in the user login portion could compromise the entire file system's integrity.
   - *Example*: Implementing a mechanism as a library outside the kernel rather than inside it limits the damage a malfunctioning mechanism can cause to the entire system.
8. **Psychological Acceptability**: Security mechanisms must be easy for the end-user to use and understand. A good user interface is crucial for ensuring users comprehend their actions.
   > **Example:** If password requirements are too complex (e.g., requiring special characters, numbers, and frequent changes), users might write them on sticky notes, defeating the security mechanism entirely.

### Key Takeaways from Design Principles
- **Positive Formulation**: All principles are stated positively, focusing on what the system *can* do, avoiding the impossible claim of being "bulletproof."
- **Timeless Applicability**: Despite being crafted in the early 1970s for disconnected systems, they perfectly apply to modern networks.
- **Core Strategy 1**: Build systems where cracking the protection boundary is computationally infeasible.
- **Core Strategy 2**: Build systems to **detect** violations when they occur rather than trying to entirely **prevent** them, as prevention is much harder to guarantee than detection.

## Conclusion
*(No transcript available)*


---

# Module 10: Andrew File System and Security

## 1. Introduction
- **Overview**: The Andrew File System (AFS) was a bold experiment in the CS department at Carnegie Mellon University (CMU).
- **Goal**: Enable students across campus to walk up to any workstation, log in, and securely access all their files stored on a central server over a local area network (LAN).
- **Core Assumption**: The network itself is untrusted.
- **Focus**: Using AFS as a case study to understand how private key cryptographic infrastructure can provide security and authentication for a distributed file system available to a user community.

## 2. State of Computing Circa 1988
> **Intuition:** AFS was essentially a precursor to modern cloud storage like Dropbox or Google Drive, but built specifically for a campus network environment.
- **Environment**: CMU campus, user community, client workstations connected via LAN to file servers.
- **Workstations**: Local disks served as efficient caches for files downloaded from the server.
- **Vision of AFS (and Coda File System)**: Afford users the ability to access their personal information spread out throughout the campus securely and centrally.
- **Legacy**: Modest beginnings of today's cloud computing and mobile device concepts.

## 3. Andrew Architecture
- **Virtue (Client Environment)**: Client workstations connected by insecure network links to the LAN. Run a flavor of the UNIX operating system.
  - **Venus**: A special process running on the Virtue workstation responsible for user authentication and client caching of files fetched from the Vice servers. It acts as a surrogate for the user, utilizing RPC (Remote Procedure Call) to fetch files.
- **Vice (Server Environment)**: Secure servers (S1, S2, S3, etc.) located in a secure environment. Communication within Vice is secure (no encryption needed inside the boundary).
- **Communication Boundary**: Clients access Vice servers over insecure links, requiring encryption for data on the wire to prevent packet sniffing. Secure RPC is used for both passing parameters and receiving results.

## 4. Encryption Primer
> **Example:** In a symmetric key system, Alice and Bob share the same secret key for both encrypting and decrypting. In an asymmetric key system, Alice uses Bob's public key to encrypt a message, and Bob uses his private key to decrypt it.
- **Private Key Cryptosystem (Symmetric)**: 
  > **Conceptual Framework:** Think of a physical lockbox where both the sender and the receiver have an identical copy of the only key that can open it.
  - Sender and receiver use the same symmetric key for encryption and decryption.
  - *Process*: Sender encrypts data with the private key to produce *ciphertext*, which travels over insecure links. Receiver decrypts it using the same key.
  - *Saltzer's Principle*: Publish the design but protect the keys. Breaking the key must be computationally hard.
  - *Challenge*: Key distribution problem, especially as organizations scale.
- **Public Key Cryptosystem (Asymmetric)**: 
  > **Background Context:** Invented in the 1970s (Diffie-Hellman, RSA), asymmetric cryptography revolutionized secure communication over untrusted networks by eliminating the need to securely transmit a shared secret beforehand.
  - Overcomes the key distribution problem.
  - *Keys*: A pair of keys—a *public key* (published, used for encryption) and a *private key* (kept secret, used for decryption).
  - *Process*: Sender encrypts data using the receiver's public key (a one-way function). Only the entity with the private key can decrypt the ciphertext back into the original data.
> **Tradeoff:** Asymmetric encryption solves the key distribution problem but is significantly more computationally expensive than symmetric encryption, which is why systems often use public keys to securely exchange a symmetric session key for the bulk of communication.

## 5. Private Key Encryption System in Action
- Two entities (A and B) exchange keys (e.g., $K_a$ for A, $K_b$ for B).
- A uses $K_a$ to encrypt a message to B. B decrypts it using $K_a$.
- **Requirement**: The receiver needs to know the identity of the sender to select the correct decryption key.
- **Implementation**: The sender's identity must be sent in *clear text* alongside the ciphertext. 

## 6. Challenges for the Andrew System
1. **Authenticating the User**: Unambiguously verifying the user's identity (e.g., proving "I am Kishore").
2. **Authenticating the Server**: Ensuring messages received by the client are from a genuine server, not a Trojan horse.
   > **Hypothetical:** Without server authentication, an attacker could set up a rogue "Vice" server on the campus network. When a student tries to log in, the rogue server could capture their credentials.
3. **Preventing Replay Attacks**: Ensuring intercepted packets cannot be resent to fool the sender or receiver.
4. **Isolating Users**: Shielding the user community from unintended or malicious interference by other users.
   > **Conceptual Framework:** In a multi-tenant environment, the actions of one user (whether accidental or malicious) must not impact the privacy, integrity, or availability of another user's data.
- **Design Decisions**: AFS uses secure RPC and private key cryptography (suitable for closed communities like a campus, avoiding the key distribution problem).
- **Dilemma**: Overexposing a username/password pair (as the clear text identity and private key) for all communications poses a security hole. 

## 7. The Andrew Solution: Three Classes of Interaction
To avoid overexposing the username and password, AFS uses ephemeral IDs and keys.
> **Intuition:** By using temporary (ephemeral) keys for ongoing session and file operations, AFS limits the exposure of the user's master password to just the initial login phase.
1. **Logging In**: Username and password are used exactly once to log in and securely authenticate with the server.
2. **RPC Session Establishment**: Establishing an RPC session to fetch or store files. Uses ephemeral IDs and keys.
3. **File System Access**: Actual secure RPC calls during the session for file operations (open, close, read, write).

## 8. Login Process
1. User logs in with a username and password.
2. The Virtue login process securely communicates this to the Vice login server.
3. The Vice login server returns two tokens:
   - **Clear Token**: A data structure containing a Handshake Key ($HK_c$).
   - **Secret Token**: An encrypted version of the Clear Token, encrypted with a key known only to Vice. This serves as an *ephemeral client ID* for the session (a meaningless bit string to sniffers).
4. Vice sends both tokens securely back to the Virtue login process. Virtue extracts the $HK_c$.
5. **Usage**: The secret token acts as the client ID for future communication. When Vice receives it, it decrypts it using its own key to extract the clear token and $HK_c$, verifying the client. Venus stores these tokens for the duration of the login session and discards them at logoff.

## 9. RPC Session Establishment (The "Bind" Operation)
- Venus establishes an RPC session using the Secret Token (as client ID) and the Handshake Key ($HK_c$) to encrypt messages.
- **Message 1 (Client to Server)**: Venus generates a new random number ($X_r$), encrypts it with $HK_c$, and sends it with the Secret Token.
  - Server decrypts the Secret Token, retrieves $HK_c$, and decrypts the message to get $X_r$.
- **Message 2 (Server to Client)**: Server increments $X_r$ by 1 ($X_r+1$), generates a new random number ($Y_r$), encrypts both with $HK_s$ ($HK_s = HK_c$), and sends them to the client.
  - *Authenticates Server*: Client decrypts the message. Seeing $X_r+1$ proves the server is genuine (it successfully decrypted $X_r$).
- **Message 3 (Client to Server)**: Client increments $Y_r$ by 1 ($Y_r+1$), encrypts it, and sends it back.
  - *Authenticates Client*: Server verifies $Y_r+1$, proving the client is genuine.
- **Replay Protection**: The use of new random numbers back and forth prevents replay attacks.
> **Intuition:** The exchange and incrementing of random numbers ($X_r$ and $Y_r$) ensure that both parties are live and not just replaying intercepted old messages.
> **Hypothetical:** If the system did not use these random numbers ($X_r$ and $Y_r$), an attacker could record the encrypted messages from a legitimate user's session establishment and replay them later to trick the server into granting access without knowing the actual Handshake Key.

## 10. RPC Session Establishment (Continued)
- To prevent overexposing the Handshake Key ($HK_c$) during numerous file system operations, the server generates a **Session Key ($SK$)**.
- Server sends the $SK$ and a starting sequence number to the client, encrypted with $HK_c$.
- **File System Access**: For the remainder of the RPC session, Venus uses $SK$ for all secure RPC calls (opening, closing, writing files). The sequence number prevents replay attacks within the session.
- Once the RPC session ends, $SK$ is discarded. New RPC sessions require establishing a new $SK$ via the Bind operation using $HK_c$.

## 11. Login is a Special Case of Bind
- The initial login process is a special case of the Bind operation.
- **Client ID**: Username.
- **Handshake Key**: Password.
- After mutual authentication (validating client and server via random numbers), the server sends the Secret Token and Clear Token back to the client, encrypted using the password as the handshake key.

## 12. Putting It All Together
- **Login Session**: Exposes the username and password exactly once. Provides the Handshake Key ($HK_c$) and Secret Token, valid for the duration of the login session.
- **RPC Session**: Uses $HK_c$ to establish a session and obtain a Session Key ($SK$), valid only for that specific RPC session.
- **File Operations**: Uses the ephemeral Session Key ($SK$) for secure RPC calls.
- **Outcome**: Minimizes exposure of long-term credentials on insecure networks.

## 13. AFS Security Report Card
> **Intuition:** While AFS was pioneering in client-server authentication, it assumed the server network itself was physically secure, which would be a critical vulnerability in modern "zero-trust" environments.
- **Mutual Suspicion**: **Yes** (Addresses suspicion from fellow users and the server).
- **User Protection from System**: **No** (Users must trust the system; no protection against a compromised system).
- **Confinement of Resource Usage**: **No** (Users can consume excessive network bandwidth; vulnerable to denial-of-service attacks).
  > **Example:** A compromised student account could run a script that continuously downloads large files, exhausting the network bandwidth and preventing other students from using AFS (Denial of Service).
- **Authentication**: **Yes** (Mutual authentication between client and server).
- **Server Integrity**: **No** (Servers are assumed to be in a secure physical environment; links inside the server network are unencrypted. Physical and social constraints are the only defenses, presenting a significant vulnerability).

## 14. Conclusion
- **AFS Extensions**: AFS extended UNIX file system privileges with groups, subgroups, positive/negative access rights (useful for quick revocation), and audit trails for administrators.
- **Takeaway**: Operating system designers can implement secure distributed systems by applying information security principles (like Saltzer's) and benchmarking against known vulnerabilities to safeguard against attackers.

## 15. Interview With Yousef Khalidi
- **Background**: Dr. Yousef Khalidi (Georgia Tech PhD, 1989; worked at Sun Microsystems on Solaris MC; currently a Distinguished Engineer at Microsoft leading the Azure Cloud platform).
- **Evolution of Systems**: 
  - Fundamentals (security, isolation, separation of policy/mechanism, replication, consistency) remain the same since the 1980s.
  - Scale has increased by orders of magnitude (from 3-5 machines to millions of VMs).
  - Increased scale requires adjustments (e.g., loose consistency, optimizing for mean time to recovery over perfect prevention).
- **Cloud Architecture Trends**:
  > **Background Context:** The shift to cloud computing fundamentally changed distributed systems design. Instead of assuming hardware is reliable, cloud architectures assume hardware *will* fail and rely on software redundancy and distributed consensus to maintain uptime.
  - Shift from "scale-up" (adding to one big mainframe) to "scale-out" (horizontal scaling with many commodity servers).
  - Flat networks for efficient east-west traffic (computation/replication) and north-south traffic.
  - Applications composed of existing services (storage, databases, caching) rather than built from scratch.
  - Applications must be designed to withstand failures and assume network latency/unreliability.
- **Edge Computing & Latency**: 
  - Content Distribution Networks (CDNs) handle streaming by placing data closer to users.
  - For chatty, latency-sensitive applications, computation must move closer to the edge or the device due to physics constraints.
- **Advice for Students**:
  - Build a strong foundation in Operating Systems, Distributed Systems, Programming Languages, and Algorithms.
  - Be curious and keep track of industry trends outside of school.
  - Develop soft skills and study the humanities: leadership, critical thinking, and concise communication are crucial for working in teams and driving projects in the industry.
  - Push the envelope and try "impossible" things in academia, where you aren't bound by industry shipping constraints.


---

